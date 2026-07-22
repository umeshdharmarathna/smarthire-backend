from pydantic import BaseModel, EmailStr
from typing import Optional, List

# ================= USER SCHEMAS =================
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: str  # customer, provider, admin
    provider_category: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int

class UserUpdate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[str] = None
    provider_category: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    provider_category: Optional[str] = None

    class Config:
        from_attributes = True


# ================= SERVICE SCHEMAS =================
class ServiceCreate(BaseModel):
    title: str
    category: str
    price: float
    description: str

class ServiceUpdate(BaseModel):
    title: str
    category: str
    price: float
    description: str

class ServiceResponse(BaseModel):
    id: int
    title: str
    category: str
    price: float
    description: str
    provider_id: int

    class Config:
        from_attributes = True


# ================= BOOKING SCHEMAS =================
class BookingCreate(BaseModel):
    service_id: int
    date: str
    time: str

class BookingUpdateStatus(BaseModel):
    status: str  # pending, confirmed, completed, cancelled

class BookingResponse(BaseModel):
    id: int
    service_id: int
    user_id: int
    date: str
    time: str
    status: str
    service_title: str

    class Config:
        from_attributes = True


# ================= ADMIN STATS SCHEMA =================
class AdminStatsResponse(BaseModel):
    total_users: int
    total_providers: int
    total_bookings: int
    total_revenue: float


# ================= CHAT SCHEMAS =================
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
