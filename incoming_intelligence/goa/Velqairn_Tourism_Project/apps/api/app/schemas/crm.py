from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------
class StaffBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "agent"
    is_active: Optional[bool] = True
    avatar_initials: Optional[str] = None

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_initials: Optional[str] = None

class StaffResponse(StaffBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------
class LeadBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = "website"
    status: Optional[str] = "new"
    destination: Optional[str] = None
    trip_type: Optional[str] = None
    travel_date: Optional[str] = None
    budget: Optional[float] = None
    pax: Optional[int] = 2
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    destination: Optional[str] = None
    trip_type: Optional[str] = None
    travel_date: Optional[str] = None
    budget: Optional[float] = None
    pax: Optional[int] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class LeadResponse(LeadBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_staff: Optional[StaffResponse] = None
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class ClientBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    anniversary_date: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class ClientCreate(ClientBase):
    lead_id: Optional[int] = None

class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    anniversary_date: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class ClientResponse(ClientBase):
    id: int
    lead_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_staff: Optional[StaffResponse] = None
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
class BookingBase(BaseModel):
    client_id: int
    booking_ref: Optional[str] = None
    destination: Optional[str] = None
    hotel_name: Optional[str] = None
    trip_type: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    nights: Optional[int] = None
    pax: Optional[int] = 2
    status: Optional[str] = "inquiry"
    total_price: Optional[float] = None
    amount_paid: Optional[float] = 0.0
    profit: Optional[float] = 0.0
    itinerary_text: Optional[str] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    destination: Optional[str] = None
    hotel_name: Optional[str] = None
    trip_type: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    nights: Optional[int] = None
    pax: Optional[int] = None
    status: Optional[str] = None
    total_price: Optional[float] = None
    amount_paid: Optional[float] = None
    profit: Optional[float] = None
    itinerary_text: Optional[str] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class BookingProfitUpdate(BaseModel):
    profit: float

class BookingResponse(BookingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client: Optional[ClientResponse] = None
    assigned_staff: Optional[StaffResponse] = None
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[str] = None
    is_done: Optional[bool] = False
    lead_id: Optional[int] = None
    client_id: Optional[int] = None
    booking_id: Optional[int] = None
    assigned_staff_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    is_done: Optional[bool] = None
    assigned_staff_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_staff: Optional[StaffResponse] = None
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Dashboard Stats
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_leads: int
    new_leads_today: int
    total_clients: int
    total_bookings: int
    bookings_confirmed: int
    bookings_completed: int
    revenue_total: float
    revenue_this_month: float
    profit_total: float = 0.0
    profit_this_month: float = 0.0
    pending_tasks: int
    total_staff: int
