import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openai
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas  # pyrefly: ignore [missing-import] # type: ignore
import models  # pyrefly: ignore [missing-import] # type: ignore
from database import get_db  # pyrefly: ignore [missing-import] # type: ignore

router = APIRouter()

@router.post("/chat", response_model=schemas.ChatResponse)
def chat_bot(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    message = request.message.lower().strip()
    
    # Check if OpenAI API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            openai.api_key = api_key
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Smart Hire Assistant, a friendly support agent for Smart Hire, an on-demand local services platform. Assist the user with queries about services and bookings."},
                    {"role": "user", "content": request.message}
                ]
            )
            reply = response.choices[0].message.content
            return {"reply": reply}
        except Exception as e:
            print(f"OpenAI error: {e}. Falling back to rule-based system.")
            
    # Rule-based fallback system with DB queries
    if any(k in message for k in ["hello", "hi", "hey"]):
        reply = "Hello! Welcome to Smart Hire support. I'm your AI assistant. How can I help you book a service or manage your bookings today?"
    elif any(k in message for k in ["price", "cost", "fee", "how much"]):
        reply = "You can see the price of each service listed on the 'Services' page. Prices depend on the provider, ranging from $30 to $120. Which service category are you looking for?"
    
    # Dynamic DB Queries for Categories
    elif any(k in message for k in ["plumb", "pipe", "drain"]):
        plumbers = db.query(models.User).filter(models.User.role == "provider", models.User.provider_category == "Plumbing").all()
        if plumbers:
            names = ", ".join([p.full_name for p in plumbers])
            reply = f"We have these expert plumbers available right now: {names}. Go to the 'Providers' page, search for 'Plumbing', and book them instantly!"
        else:
            reply = "We currently don't have plumbers available, but they join everyday! Check the 'Providers' page later."
            
    elif any(k in message for k in ["clean", "wash", "housework"]):
        cleaners = db.query(models.User).filter(models.User.role == "provider", models.User.provider_category == "Cleaning").all()
        if cleaners:
            names = ", ".join([p.full_name for p in cleaners])
            reply = f"Our top cleaning professionals include: {names}. You can view their profiles on the 'Providers' page."
        else:
            reply = "We currently don't have cleaning providers available. Please check the 'Providers' page later."
            
    elif any(k in message for k in ["electric", "power", "light"]):
        electricians = db.query(models.User).filter(models.User.role == "provider", models.User.provider_category == "Electrician").all()
        if electricians:
            names = ", ".join([p.full_name for p in electricians])
            reply = f"Need electrical work? You can hire: {names}. Find them under 'Providers'!"
        else:
            reply = "No electricians are registered yet, but keep checking our 'Providers' page!"
            
    elif any(k in message for k in ["book", "reserve", "schedule"]):
        reply = "To book a service, browse our 'Providers' or 'Services' page, select what you need, choose your date and time, and click 'Confirm Booking'. Make sure you are logged in first!"
    elif any(k in message for k in ["login", "register", "signup"]):
        reply = "You can register an account as a 'Customer' or 'Service Provider' on the Register page. During registration as a provider, you can select your specialized category!"
    elif any(k in message for k in ["admin", "dashboard", "panel"]):
        reply = "Admin users can access the Admin Dashboard (/admin-dashboard.html) to view stats (revenue, users, bookings) and manage the system database."
    elif any(k in message for k in ["help", "support", "contact"]):
        reply = "I'm always here to help! If you need technical assistance, you can email us at support@smarthire.com or ask me here."
    else:
        # Default fallback: extract words and try a wildcard search
        reply = "Smart Hire connects you with trusted service providers. You can search for specific categories like 'Plumbing' or 'Cleaning', book services, and manage your schedule from your dashboard. How can I help you?"
        
    return {"reply": reply}
