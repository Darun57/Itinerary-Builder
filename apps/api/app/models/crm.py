from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    source = Column(String, default="website")
    status = Column(String, default="new")
    destination = Column(String)
    trip_type = Column(String)
    travel_date = Column(String)
    budget = Column(Float, nullable=True)
    pax = Column(Integer, default=2)
    notes = Column(Text)
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assigned_staff = relationship("Staff", back_populates="leads")
    client = relationship("Client", back_populates="lead", uselist=False)
    tasks = relationship("Task", back_populates="lead", foreign_keys="Task.lead_id")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, unique=True)
    full_name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    address = Column(String)
    passport_number = Column(String)
    date_of_birth = Column(String)
    anniversary_date = Column(String)
    preferences = Column(Text)
    notes = Column(Text)
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("Lead", back_populates="client")
    assigned_staff = relationship("Staff", back_populates="clients")
    bookings = relationship("Booking", back_populates="client")
    tasks = relationship("Task", back_populates="client", foreign_keys="Task.client_id")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    booking_ref = Column(String, unique=True, index=True)
    destination = Column(String)
    hotel_name = Column(String)
    trip_type = Column(String)
    check_in = Column(String)
    check_out = Column(String)
    nights = Column(Integer)
    pax = Column(Integer, default=2)
    status = Column(String, default="inquiry")
    total_price = Column(Float, nullable=True)
    amount_paid = Column(Float, default=0.0)
    profit = Column(Float, nullable=True, default=0.0)
    itinerary_text = Column(Text)
    notes = Column(Text)
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="bookings")
    assigned_staff = relationship("Staff", back_populates="bookings")
    tasks = relationship("Task", back_populates="booking", foreign_keys="Task.booking_id")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default="medium")
    due_date = Column(String)
    is_done = Column(Boolean, default=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("Lead", back_populates="tasks", foreign_keys=[lead_id])
    client = relationship("Client", back_populates="tasks", foreign_keys=[client_id])
    booking = relationship("Booking", back_populates="tasks", foreign_keys=[booking_id])
    assigned_staff = relationship("Staff", back_populates="tasks")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    role = Column(String, default="agent")
    is_active = Column(Boolean, default=True)
    avatar_initials = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    leads = relationship("Lead", back_populates="assigned_staff")
    clients = relationship("Client", back_populates="assigned_staff")
    bookings = relationship("Booking", back_populates="assigned_staff")
    tasks = relationship("Task", back_populates="assigned_staff")
