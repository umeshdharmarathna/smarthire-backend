import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # pyrefly: ignore [missing-import] # type: ignore

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")  # customer, provider, admin
    provider_category = Column(String(255), nullable=True)

    services = relationship("Service", back_populates="provider", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(1000), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    provider = relationship("User", back_populates="services")
    bookings = relationship("Booking", back_populates="service", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(50), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(50), nullable=False)  # Format: HH:MM
    status = Column(String(50), nullable=False, default="pending")  # pending, confirmed, completed, cancelled

    service = relationship("Service", back_populates="bookings")
    user = relationship("User", back_populates="bookings")
