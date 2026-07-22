import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
import openai

import models  # pyrefly: ignore [missing-import] # type: ignore
import schemas  # pyrefly: ignore [missing-import] # type: ignore
import auth  # pyrefly: ignore [missing-import] # type: ignore
from database import engine, get_db  # pyrefly: ignore [missing-import] # type: ignore
import chatbot  # pyrefly: ignore [missing-import] # type: ignore

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db = None
    try:
        models.Base.metadata.create_all(bind=engine)
        db = next(get_db())
        if db.query(models.User).count() == 0:
            print("Database is empty. Seeding initial data...")
            admin_pwd = auth.get_password_hash("admin123")
            provider_pwd = auth.get_password_hash("provider123")
            customer_pwd = auth.get_password_hash("customer123")
            
            admin = models.User(
                full_name="System Administrator",
                email="admin@smarthire.com",
                phone="0771234567",
                password_hash=admin_pwd,
                role="admin"
            )
            provider = models.User(
                full_name="John the Plumber",
                email="provider@smarthire.com",
                phone="0777654321",
                password_hash=provider_pwd,
                role="provider"
            )
            customer = models.User(
                full_name="Jane Customer",
                email="customer@smarthire.com",
                phone="0771122334",
                password_hash=customer_pwd,
                role="customer"
            )
            
            db.add_all([admin, provider, customer])
            db.commit()
            db.refresh(provider)
            db.refresh(customer)
            
            # Create Sample Services for John the Plumber
            s1 = models.Service(
                title="Emergency Plumbing Repair",
                category="Plumbing",
                price=45.0,
                description="Fixing leaks, broken pipes, clogged drains, and general plumbing repairs.",
                provider_id=provider.id
            )
            s2 = models.Service(
                title="Complete Bathroom Fitting",
                category="Plumbing",
                price=120.0,
                description="Professional installation of showers, toilets, sinks, and bathroom accessories.",
                provider_id=provider.id
            )
            s3 = models.Service(
                title="Deep Home Cleaning",
                category="Cleaning",
                price=35.0,
                description="Standard house cleaning, dusting, floor mopping, kitchen cleaning.",
                provider_id=provider.id
            )
            
            db.add_all([s1, s2, s3])
            db.commit()
            db.refresh(s1)
            
            # Create Sample Booking
            b1 = models.Booking(
                service_id=s1.id,
                user_id=customer.id,
                date="2026-07-25",
                time="10:00",
                status="confirmed"
            )
            db.add(b1)
            db.commit()
            print("Database seeding completed.")
        else:
            print("Database already has data. Skipping seed.")
    except Exception as e:
        print(f"Error during startup: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()
    yield
    # Shutdown logic (if any)

app = FastAPI(title="Smart Hire Backend API", lifespan=lifespan)

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Smart Hire Backend API is running successfully!",
        "documentation": "/docs"
    }


# ================= AUTH ENDPOINTS =================

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_pwd = auth.get_password_hash(user_data.password)
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_pwd,
        role=user_data.role,
        provider_category=user_data.provider_category if user_data.role == "provider" else None
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}


@app.post("/auth/login", response_model=schemas.UserLoginResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Find user
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate token
    token = auth.create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }


# ================= USER ENDPOINTS =================

@app.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(
    current_user: models.User = Depends(auth.require_role(["admin"])),
    db: Session = Depends(get_db)
):
    return db.query(models.User).all()


@app.get("/providers/search", response_model=List[schemas.UserResponse])
def search_providers(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.User).filter(models.User.role == "provider")
    if category:
        # Simple case-insensitive match for category
        query = query.filter(models.User.provider_category.ilike(f"%{category}%"))
    return query.all()


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user_profile(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Standard users can only get their own profile, admin can get any profile
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user_profile(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check email conflict
    if user.email != user_data.email:
        email_conflict = db.query(models.User).filter(models.User.email == user_data.email).first()
        if email_conflict:
            raise HTTPException(status_code=400, detail="Email is already taken")
            
    user.full_name = user_data.full_name
    user.email = user_data.email
    user.phone = user_data.phone
    
    if user_data.role and current_user.role == "admin":
        user.role = user_data.role
    
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.require_role(["admin"])),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# ================= SERVICE ENDPOINTS =================

@app.post("/services", response_model=schemas.ServiceResponse)
def create_service(
    service_data: schemas.ServiceCreate,
    current_user: models.User = Depends(auth.require_role(["provider", "admin"])),
    db: Session = Depends(get_db)
):
    new_service = models.Service(
        title=service_data.title,
        category=service_data.category,
        price=service_data.price,
        description=service_data.description,
        provider_id=current_user.id
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service


@app.get("/services", response_model=List[schemas.ServiceResponse])
def get_services(provider_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Service)
    if provider_id is not None:
        query = query.filter(models.Service.provider_id == provider_id)
    return query.all()


@app.get("/services/search", response_model=List[schemas.ServiceResponse])
def search_services(
    category: Optional[str] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    db_query = db.query(models.Service)
    if category:
        db_query = db_query.filter(models.Service.category.ilike(category))
    if query:
        db_query = db_query.filter(
            models.Service.title.ilike(f"%{query}%") |
            models.Service.description.ilike(f"%{query}%")
        )
    return db_query.all()


@app.get("/services/{service_id}", response_model=schemas.ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.put("/services/{service_id}", response_model=schemas.ServiceResponse)
def update_service(
    service_id: int,
    service_data: schemas.ServiceUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    if current_user.role != "admin" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own services"
        )
        
    service.title = service_data.title
    service.category = service_data.category
    service.price = service_data.price
    service.description = service_data.description
    
    db.commit()
    db.refresh(service)
    return service


@app.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # Check permission: owner of service or admin
    if current_user.role != "admin" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own services"
        )
        
    db.delete(service)
    db.commit()
    return {"message": "Service deleted successfully"}


# ================= BOOKING ENDPOINTS =================

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: schemas.BookingCreate,
    current_user: models.User = Depends(auth.require_role(["customer", "admin"])),
    db: Session = Depends(get_db)
):
    # Verify service exists
    service = db.query(models.Service).filter(models.Service.id == booking_data.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    new_booking = models.Booking(
        service_id=booking_data.service_id,
        user_id=current_user.id,
        date=booking_data.date,
        time=booking_data.time,
        status="pending"
    )
    db.add(new_booking)
    db.commit()
    return {"message": "Booking placed successfully"}


@app.get("/bookings", response_model=List[schemas.BookingResponse])
def get_bookings(
    provider_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Query join models.Booking and models.Service to fetch service_title
    query = db.query(models.Booking, models.Service.title.label("service_title")).join(
        models.Service, models.Booking.service_id == models.Service.id
    )
    
    # Filter based on query parameters and user privileges
    if current_user.role == "admin":
        # Admin can view all bookings or filter by any user_id/provider_id
        if user_id is not None:
            query = query.filter(models.Booking.user_id == user_id)
        if provider_id is not None:
            query = query.filter(models.Service.provider_id == provider_id)
    elif current_user.role == "provider":
        # Provider can only view bookings of their own services
        query = query.filter(models.Service.provider_id == current_user.id)
        if user_id is not None:
            query = query.filter(models.Booking.user_id == user_id)
    else:
        # Customers can only view their own bookings
        query = query.filter(models.Booking.user_id == current_user.id)
    
    if limit is not None:
        query = query.limit(limit)
        
    results = query.all()
    
    bookings_response = []
    for booking, service_title in results:
        bookings_response.append(
            schemas.BookingResponse(
                id=booking.id,
                service_id=booking.service_id,
                user_id=booking.user_id,
                date=booking.date,
                time=booking.time,
                status=booking.status,
                service_title=service_title
            )
        )
    return bookings_response


@app.put("/bookings/{booking_id}")
def update_booking_status(
    booking_id: int,
    status_data: schemas.BookingUpdateStatus,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    
    # Authentication check:
    # 1. Admin can change anything
    # 2. Provider who owns the service can change status (e.g. confirm, complete, cancel)
    # 3. Customer who booked the service can only cancel it
    if current_user.role == "admin":
        pass
    elif current_user.role == "provider" and service and service.provider_id == current_user.id:
        pass
    elif current_user.role == "customer" and booking.user_id == current_user.id:
        if status_data.status.lower() != "cancelled":
            raise HTTPException(
                status_code=403,
                detail="Customers can only change booking status to 'cancelled'"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update this booking"
        )
        
    booking.status = status_data.status
    db.commit()
    return {"message": "Booking status updated successfully"}


@app.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Only Admin or the Customer who booked can delete the booking log
    if current_user.role != "admin" and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this booking"
        )
        
    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}


# ================= ADMIN STATS ENDPOINT =================

@app.get("/admin/stats", response_model=schemas.AdminStatsResponse)
def get_admin_stats(
    current_user: models.User = Depends(auth.require_role(["admin"])),
    db: Session = Depends(get_db)
):
    total_users = db.query(models.User).count()
    total_providers = db.query(models.User).filter(models.User.role == "provider").count()
    total_bookings = db.query(models.Booking).count()
    
    # Calculate revenue: sum of service prices where booking is not cancelled
    revenue_query = db.query(func.sum(models.Service.price)).join(
        models.Booking, models.Booking.service_id == models.Service.id
    ).filter(models.Booking.status != "cancelled")
    
    total_revenue = revenue_query.scalar() or 0.0
    
    return {
        "total_users": total_users,
        "total_providers": total_providers,
        "total_bookings": total_bookings,
        "total_revenue": float(total_revenue)
    }


# ================= CHAT SUPPORT ENDPOINT =================
app.include_router(chatbot.router)
