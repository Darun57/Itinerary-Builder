"""
Pydantic schemas for WhatsApp Reminder API.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReminderCreate(BaseModel):
    """Schema for creating a new reminder (manual or auto-scheduled)."""
    phone_number: str
    client_name: Optional[str] = None
    client_id: Optional[int] = None
    lead_id: Optional[int] = None
    booking_id: Optional[int] = None
    reminder_type: str = "custom"           # pre_trip | payment | followup | inquiry | custom
    message_body: str
    scheduled_at: Optional[datetime] = None  # None = send now


class ReminderResponse(BaseModel):
    id: int
    phone_number: str
    client_name: Optional[str] = None
    client_id: Optional[int] = None
    lead_id: Optional[int] = None
    booking_id: Optional[int] = None
    reminder_type: str
    message_body: str
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str
    twilio_sid: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReminderCancel(BaseModel):
    reason: Optional[str] = None


class SendNowPayload(BaseModel):
    """For quick send — phone number + message, optionally tied to a record."""
    phone_number: str
    client_name: Optional[str] = None
    client_id: Optional[int] = None
    lead_id: Optional[int] = None
    booking_id: Optional[int] = None
    reminder_type: str = "custom"
    message_body: str


class PreviewTemplatePayload(BaseModel):
    """Preview a rendered template before sending."""
    reminder_type: str
    booking_id: Optional[int] = None
    lead_id: Optional[int] = None
    client_id: Optional[int] = None
    custom_message: Optional[str] = None
