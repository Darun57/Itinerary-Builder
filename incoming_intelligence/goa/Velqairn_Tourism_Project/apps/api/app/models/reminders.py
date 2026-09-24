from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class WhatsAppReminder(Base):
    """
    Stores scheduled and sent WhatsApp reminder messages.
    Linked to either a booking or a lead/client.
    """
    __tablename__ = "whatsapp_reminders"

    id = Column(Integer, primary_key=True, index=True)

    # Who to send to
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    phone_number = Column(String, nullable=False)
    client_name = Column(String)

    # Message content
    reminder_type = Column(String, default="custom")   # pre_trip | payment | followup | custom
    message_body = Column(Text, nullable=False)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)   # None = manual/now
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")   # pending | sent | failed | cancelled

    # Error tracking
    twilio_sid = Column(String, nullable=True)      # Twilio message SID when sent
    error_message = Column(String, nullable=True)   # Error reason if failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
