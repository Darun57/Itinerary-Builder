import random
import string
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.db.database import get_db
from app.models.crm import Lead, Client, Booking, Task, Staff
from app.schemas.crm import (
    LeadCreate, LeadUpdate, LeadResponse,
    ClientCreate, ClientUpdate, ClientResponse,
    BookingCreate, BookingUpdate, BookingResponse, BookingProfitUpdate,
    TaskCreate, TaskUpdate, TaskResponse,
    StaffCreate, StaffUpdate, StaffResponse,
    DashboardStats,
)
from app.api.reminders import sync_crm_to_pending_reminders

router = APIRouter()


def _gen_booking_ref() -> str:
    year = datetime.now().year
    suffix = "".join(random.choices(string.digits, k=4))
    return f"DT-{year}-{suffix}"


# ===========================================================================
# STAFF
# ===========================================================================

@router.get("/staff", response_model=List[StaffResponse])
def list_staff(db: Session = Depends(get_db)):
    return db.query(Staff).filter(Staff.is_active == True).all()

@router.post("/staff", response_model=StaffResponse)
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    obj = Staff(**payload.model_dump())
    if not obj.avatar_initials and obj.full_name:
        parts = obj.full_name.split()
        obj.avatar_initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/staff/{staff_id}", response_model=StaffResponse)
def get_staff(staff_id: int, db: Session = Depends(get_db)):
    obj = db.query(Staff).filter(Staff.id == staff_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Staff not found")
    return obj

@router.put("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(staff_id: int, payload: StaffUpdate, db: Session = Depends(get_db)):
    obj = db.query(Staff).filter(Staff.id == staff_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Staff not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/staff/{staff_id}")
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    obj = db.query(Staff).filter(Staff.id == staff_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Staff not found")
    obj.is_active = False
    db.commit()
    return {"ok": True}


# ===========================================================================
# LEADS
# ===========================================================================

@router.get("/leads", response_model=List[LeadResponse])
def list_leads(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Lead)
    if status:
        q = q.filter(Lead.status == status)
    return q.order_by(Lead.created_at.desc()).all()

@router.post("/leads", response_model=LeadResponse)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    obj = Lead(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    if obj.phone:
        sync_crm_to_pending_reminders(db)
    return obj

@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    obj = db.query(Lead).filter(Lead.id == lead_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
    return obj

@router.put("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    obj = db.query(Lead).filter(Lead.id == lead_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    if obj.phone:
        sync_crm_to_pending_reminders(db)
    return obj

@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    obj = db.query(Lead).filter(Lead.id == lead_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}

@router.post("/leads/{lead_id}/convert", response_model=ClientResponse)
def convert_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.client:
        raise HTTPException(status_code=400, detail="Lead already converted")
    client = Client(
        lead_id=lead.id,
        full_name=lead.full_name,
        email=lead.email,
        phone=lead.phone,
        assigned_staff_id=lead.assigned_staff_id,
    )
    lead.status = "converted"
    db.add(client)
    db.commit()
    db.refresh(client)
    sync_crm_to_pending_reminders(db)
    return client


# ===========================================================================
# CLIENTS
# ===========================================================================

@router.get("/clients", response_model=List[ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).order_by(Client.created_at.desc()).all()

@router.post("/clients", response_model=ClientResponse)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    obj = Client(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    if obj.phone:
        sync_crm_to_pending_reminders(db)
    return obj

@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    obj = db.query(Client).filter(Client.id == client_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Client not found")
    return obj

@router.put("/clients/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    obj = db.query(Client).filter(Client.id == client_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Client not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    if obj.phone:
        sync_crm_to_pending_reminders(db)
    return obj

@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    obj = db.query(Client).filter(Client.id == client_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ===========================================================================
# BOOKINGS
# ===========================================================================

@router.get("/bookings", response_model=List[BookingResponse])
def list_bookings(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Booking)
    if status:
        q = q.filter(Booking.status == status)
    return q.order_by(Booking.created_at.desc()).all()

@router.post("/bookings", response_model=BookingResponse)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("booking_ref"):
        data["booking_ref"] = _gen_booking_ref()
    obj = Booking(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    sync_crm_to_pending_reminders(db)
    return obj

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    obj = db.query(Booking).filter(Booking.id == booking_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Booking not found")
    return obj

@router.put("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, payload: BookingUpdate, db: Session = Depends(get_db)):
    obj = db.query(Booking).filter(Booking.id == booking_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Booking not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    sync_crm_to_pending_reminders(db)
    return obj

@router.patch("/bookings/{booking_id}/profit", response_model=BookingResponse)
def update_booking_profit(booking_id: int, payload: BookingProfitUpdate, db: Session = Depends(get_db)):
    obj = db.query(Booking).filter(Booking.id == booking_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Booking not found")
    obj.profit = float(payload.profit)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    obj = db.query(Booking).filter(Booking.id == booking_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ===========================================================================
# TASKS
# ===========================================================================

@router.get("/tasks", response_model=List[TaskResponse])
def list_tasks(is_done: Optional[bool] = None, db: Session = Depends(get_db)):
    q = db.query(Task)
    if is_done is not None:
        q = q.filter(Task.is_done == is_done)
    return q.order_by(Task.due_date.asc()).all()

@router.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    obj = Task(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    obj = db.query(Task).filter(Task.id == task_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    obj = db.query(Task).filter(Task.id == task_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ===========================================================================
# DASHBOARD STATS
# ===========================================================================

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today().isoformat()

    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    new_leads_today = db.query(func.count(Lead.id)).filter(
        func.substr(Lead.created_at, 1, 10) == today
    ).scalar() or 0
    total_clients = db.query(func.count(Client.id)).scalar() or 0
    total_bookings = db.query(func.count(Booking.id)).scalar() or 0
    bookings_confirmed = db.query(func.count(Booking.id)).filter(
        Booking.status == "confirmed"
    ).scalar() or 0
    bookings_completed = db.query(func.count(Booking.id)).filter(
        Booking.status == "completed"
    ).scalar() or 0

    effective_rev = case(
        (Booking.amount_paid > 0, Booking.amount_paid),
        else_=func.coalesce(Booking.total_price, 0.0)
    )

    revenue_total = db.query(func.sum(effective_rev)).filter(
        Booking.status != "cancelled"
    ).scalar() or 0.0
    
    this_month = datetime.now().strftime("%Y-%m")
    revenue_this_month = db.query(func.sum(effective_rev)).filter(
        Booking.status != "cancelled",
        func.substr(Booking.created_at, 1, 7) == this_month
    ).scalar() or 0.0

    profit_total = db.query(func.sum(func.coalesce(Booking.profit, 0.0))).filter(
        Booking.status != "cancelled"
    ).scalar() or 0.0

    profit_this_month = db.query(func.sum(func.coalesce(Booking.profit, 0.0))).filter(
        Booking.status != "cancelled",
        func.substr(Booking.created_at, 1, 7) == this_month
    ).scalar() or 0.0

    pending_tasks = db.query(func.count(Task.id)).filter(Task.is_done == False).scalar() or 0
    total_staff = db.query(func.count(Staff.id)).filter(Staff.is_active == True).scalar() or 0

    return DashboardStats(
        total_leads=total_leads,
        new_leads_today=new_leads_today,
        total_clients=total_clients,
        total_bookings=total_bookings,
        bookings_confirmed=bookings_confirmed,
        bookings_completed=bookings_completed,
        revenue_total=float(revenue_total),
        revenue_this_month=float(revenue_this_month),
        profit_total=float(profit_total),
        profit_this_month=float(profit_this_month),
        pending_tasks=pending_tasks,
        total_staff=total_staff,
    )


# ===========================================================================
# REVENUE TREND
# ===========================================================================

@router.get("/dashboard/revenue-trend")
def get_revenue_trend(period: str = "monthly", db: Session = Depends(get_db)):
    """Return revenue totals for monthly (YTD) or last 7 days."""
    from datetime import timedelta

    today = date.today()
    effective_rev = case(
        (Booking.amount_paid > 0, Booking.amount_paid),
        else_=func.coalesce(Booking.total_price, 0.0)
    )

    result = []
    if period == "7d":
        days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]  # oldest → newest
        for d in days:
            day_str = d.isoformat()
            total = db.query(func.sum(effective_rev)).filter(
                Booking.status != "cancelled",
                (func.substr(Booking.created_at, 1, 10) == day_str) | (func.substr(Booking.updated_at, 1, 10) == day_str)
            ).scalar() or 0.0
            result.append({
                "date": day_str,
                "label": d.strftime("%a"),   # Mon, Tue, etc.
                "amount": float(total),
            })
    else:
        # Monthly trend (YTD, matching Jan, Feb, Mar, etc.)
        month_count = max(7, today.month)
        for m in range(1, month_count + 1):
            m_date = date(today.year, m, 1)
            month_str = f"{today.year}-{m:02d}"
            total = db.query(func.sum(effective_rev)).filter(
                Booking.status != "cancelled",
                (func.substr(Booking.created_at, 1, 7) == month_str) | (func.substr(Booking.updated_at, 1, 7) == month_str)
            ).scalar() or 0.0
            result.append({
                "date": month_str,
                "label": m_date.strftime("%b"),  # Jan, Feb, etc.
                "amount": float(total),
            })

    max_amount = max((r["amount"] for r in result), default=0)
    for r in result:
        if max_amount > 0 and r["amount"] > 0:
            r["height"] = max(15, round((r["amount"] / max_amount) * 100))
        else:
            r["height"] = 0

    return result


# ===========================================================================
# PROFIT TREND
# ===========================================================================

@router.get("/dashboard/profit-trend")
def get_profit_trend(period: str = "monthly", db: Session = Depends(get_db)):
    """Return profit totals for monthly (YTD) or last 7 days from manually entered profits."""
    from datetime import timedelta

    today = date.today()
    effective_profit = func.coalesce(Booking.profit, 0.0)

    result = []
    if period == "7d":
        days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]  # oldest → newest
        for d in days:
            day_str = d.isoformat()
            total = db.query(func.sum(effective_profit)).filter(
                Booking.status != "cancelled",
                (func.substr(Booking.created_at, 1, 10) == day_str) | (func.substr(Booking.updated_at, 1, 10) == day_str)
            ).scalar() or 0.0
            result.append({
                "date": day_str,
                "label": d.strftime("%a"),   # Mon, Tue, etc.
                "amount": float(total),
            })
    else:
        # Monthly trend (YTD, matching Jan, Feb, Mar, etc.)
        month_count = max(7, today.month)
        for m in range(1, month_count + 1):
            m_date = date(today.year, m, 1)
            month_str = f"{today.year}-{m:02d}"
            total = db.query(func.sum(effective_profit)).filter(
                Booking.status != "cancelled",
                (func.substr(Booking.created_at, 1, 7) == month_str) | (func.substr(Booking.updated_at, 1, 7) == month_str)
            ).scalar() or 0.0
            result.append({
                "date": month_str,
                "label": m_date.strftime("%b"),  # Jan, Feb, etc.
                "amount": float(total),
            })

    max_amount = max((r["amount"] for r in result), default=0)
    for r in result:
        if max_amount > 0 and r["amount"] > 0:
            r["height"] = max(15, round((r["amount"] / max_amount) * 100))
        else:
            r["height"] = 0

    return result

