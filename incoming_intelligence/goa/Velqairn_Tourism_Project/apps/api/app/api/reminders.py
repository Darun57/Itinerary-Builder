"""
WhatsApp Reminder API Router.

Endpoints:
    GET    /api/crm/reminders              - List all reminders
    POST   /api/crm/reminders              - Schedule a new reminder
    POST   /api/crm/reminders/send-now     - Send immediately
    POST   /api/crm/reminders/preview      - Preview a rendered template
    GET    /api/crm/reminders/logs         - Sent message log (last 100)
    PATCH  /api/crm/reminders/{id}/cancel  - Cancel a pending reminder
    DELETE /api/crm/reminders/{id}         - Delete a reminder record
    POST   /api/crm/reminders/auto-schedule- Auto-schedule reminders for all upcoming bookings
"""
import logging
from typing import List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crm import Booking, Client, Lead
from app.models.reminders import WhatsAppReminder
from app.schemas.reminders import (
    ReminderCreate,
    ReminderResponse,
    SendNowPayload,
    PreviewTemplatePayload,
)
from app.services.whatsapp.client import send_whatsapp, normalize_phone
from app.services.whatsapp.templates import (
    render_pre_trip,
    render_payment_reminder,
    render_post_trip_followup,
    render_inquiry_followup,
    render_custom,
    TEMPLATE_LABELS,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _send_and_update(reminder: WhatsAppReminder, db: Session):
    """Send a WhatsApp message and update the reminder record."""
    result = send_whatsapp(reminder.phone_number, reminder.message_body)
    now = datetime.utcnow()
    if result["success"]:
        reminder.status = "sent"
        reminder.sent_at = now
        reminder.twilio_sid = result.get("sid")
    else:
        reminder.status = "failed"
        reminder.error_message = result.get("error")
    reminder.updated_at = now
    db.commit()
    db.refresh(reminder)
    return result


def _build_message(reminder_type: str, db: Session, booking_id=None, lead_id=None,
                   client_id=None, custom_message=None, client_name=None) -> str:
    """Build message body from template type + linked data."""
    if reminder_type == "pre_trip" and booking_id:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking and booking.client:
            return render_pre_trip(
                client_name=booking.client.full_name,
                destination=booking.destination or "your destination",
                check_in=booking.check_in or "your travel date",
                hotel_name=booking.hotel_name,
                booking_ref=booking.booking_ref,
                pax=booking.pax,
            )
    elif reminder_type == "payment" and booking_id:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking and booking.client:
            amount_due = (booking.total_price or 0) - (booking.amount_paid or 0)
            return render_payment_reminder(
                client_name=booking.client.full_name,
                destination=booking.destination or "your trip",
                amount_due=amount_due,
                total_price=booking.total_price or 0,
                booking_ref=booking.booking_ref,
                check_in=booking.check_in,
            )
    elif reminder_type == "followup" and booking_id:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking and booking.client:
            return render_post_trip_followup(
                client_name=booking.client.full_name,
                destination=booking.destination or "your destination",
                check_out=booking.check_out,
            )
    elif reminder_type == "inquiry" and lead_id:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            return render_inquiry_followup(
                client_name=lead.full_name,
                destination=lead.destination,
                budget=lead.budget,
            )
    # fallback — custom or generic
    name = client_name or "Valued Client"
    msg = custom_message or "We wanted to reach out regarding your upcoming trip."
    return render_custom(client_name=name, custom_message=msg)


def sync_crm_to_pending_reminders(db: Session) -> int:
    """
    Scans all leads, clients, and bookings.
    Whenever a phone number exists and doesn't already have an active/sent reminder,
    automatically creates a pending reminder so it immediately appears in the
    'Pending & Scheduled' list. Also updates existing pending reminders if contact
    details change.
    """
    created_count = 0

    # 1. Sync from Leads (active leads only)
    leads = (
        db.query(Lead)
        .filter(
            Lead.phone.isnot(None),
            Lead.phone != "",
            Lead.status.notin_(["converted", "lost"]),
        )
        .all()
    )
    for lead in leads:
        existing = (
            db.query(WhatsAppReminder)
            .filter(
                WhatsAppReminder.lead_id == lead.id,
                WhatsAppReminder.status.in_(["pending", "sent", "cancelled", "dismissed"]),
            )
            .first()
        )
        if not existing:
            msg = render_inquiry_followup(
                client_name=lead.full_name,
                destination=lead.destination,
                budget=lead.budget,
            )
            r = WhatsAppReminder(
                phone_number=normalize_phone(lead.phone),
                client_name=lead.full_name,
                lead_id=lead.id,
                reminder_type="inquiry",
                message_body=msg,
                status="pending",
            )
            db.add(r)
            created_count += 1
        elif existing.status == "pending":
            clean_phone = normalize_phone(lead.phone)
            if existing.phone_number != clean_phone or existing.client_name != lead.full_name:
                existing.phone_number = clean_phone
                existing.client_name = lead.full_name

    # 2. Sync from Clients (direct clients without bookings)
    clients = db.query(Client).filter(Client.phone.isnot(None), Client.phone != "").all()
    for client in clients:
        existing = (
            db.query(WhatsAppReminder)
            .filter(
                WhatsAppReminder.client_id == client.id,
                WhatsAppReminder.booking_id.is_(None),
                WhatsAppReminder.status.in_(["pending", "sent", "cancelled", "dismissed"]),
            )
            .first()
        )
        if not existing:
            msg = (
                f"Hi {client.full_name}! 👋\n\n"
                f"Thank you for connecting with *Darun Tourism*. We're excited to assist you with your upcoming journeys!\n\n"
                f"Feel free to reply anytime for custom itineraries, hotel reservations, or any travel queries.\n\n"
                f"— *Darun Tourism*"
            )
            r = WhatsAppReminder(
                phone_number=normalize_phone(client.phone),
                client_name=client.full_name,
                client_id=client.id,
                reminder_type="custom",
                message_body=msg,
                status="pending",
            )
            db.add(r)
            created_count += 1
        elif existing.status == "pending":
            clean_phone = normalize_phone(client.phone)
            if existing.phone_number != clean_phone or existing.client_name != client.full_name:
                existing.phone_number = clean_phone
                existing.client_name = client.full_name

    # 3. Sync from Bookings (active bookings)
    bookings = (
        db.query(Booking)
        .join(Client, Booking.client_id == Client.id)
        .filter(
            Client.phone.isnot(None),
            Client.phone != "",
            Booking.status.notin_(["cancelled"]),
        )
        .all()
    )
    for booking in bookings:
        existing = (
            db.query(WhatsAppReminder)
            .filter(
                WhatsAppReminder.booking_id == booking.id,
                WhatsAppReminder.reminder_type == "pre_trip",
                WhatsAppReminder.status.in_(["pending", "sent", "cancelled", "dismissed"]),
            )
            .first()
        )
        if not existing and booking.client and booking.client.phone:
            msg = render_pre_trip(
                client_name=booking.client.full_name,
                destination=booking.destination or "your trip",
                check_in=booking.check_in or "Upcoming",
                hotel_name=booking.hotel_name,
                booking_ref=booking.booking_ref,
                pax=booking.pax,
            )
            r = WhatsAppReminder(
                phone_number=normalize_phone(booking.client.phone),
                client_name=booking.client.full_name,
                client_id=booking.client.id,
                booking_id=booking.id,
                reminder_type="pre_trip",
                message_body=msg,
                status="pending",
            )
            db.add(r)
            created_count += 1
        elif existing and existing.status == "pending" and booking.client and booking.client.phone:
            clean_phone = normalize_phone(booking.client.phone)
            if existing.phone_number != clean_phone or existing.client_name != booking.client.full_name:
                existing.phone_number = clean_phone
                existing.client_name = booking.client.full_name

    if created_count > 0:
        db.commit()
    return created_count


# ─── endpoints ────────────────────────────────────────────────────────────────

@router.get("/reminders", response_model=List[ReminderResponse])
def list_reminders(
    status: Optional[str] = Query(None),
    reminder_type: Optional[str] = Query(None),
    limit: int = Query(100, le=300),
    auto_sync: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List all reminders, optionally filtered by status or type."""
    if auto_sync:
        sync_crm_to_pending_reminders(db)

    q = db.query(WhatsAppReminder).filter(WhatsAppReminder.status != "dismissed")
    if status:
        q = q.filter(WhatsAppReminder.status == status)
    if reminder_type:
        q = q.filter(WhatsAppReminder.reminder_type == reminder_type)
    return q.order_by(WhatsAppReminder.created_at.desc()).limit(limit).all()


@router.post("/reminders/sync-crm")
def sync_crm(db: Session = Depends(get_db)):
    """Manually trigger sync of all numbers from Leads, Clients, and Bookings into Pending Reminders."""
    count = sync_crm_to_pending_reminders(db)
    return {
        "synced": count,
        "message": f"Successfully synced {count} CRM contact(s) to Pending WhatsApp Reminders!",
    }


@router.get("/reminders/logs", response_model=List[ReminderResponse])
def reminder_logs(db: Session = Depends(get_db)):
    """Return last 100 sent/failed reminders."""
    return (
        db.query(WhatsAppReminder)
        .filter(WhatsAppReminder.status.in_(["sent", "failed"]))
        .order_by(WhatsAppReminder.sent_at.desc())
        .limit(100)
        .all()
    )


@router.get("/reminders/templates")
def list_templates():
    """Return available template types with labels."""
    return [{"value": k, "label": v} for k, v in TEMPLATE_LABELS.items()]



@router.post("/reminders/preview")
def preview_template(payload: PreviewTemplatePayload, db: Session = Depends(get_db)):
    """Preview a rendered template message before sending."""
    msg = _build_message(
        reminder_type=payload.reminder_type,
        db=db,
        booking_id=payload.booking_id,
        lead_id=payload.lead_id,
        client_id=payload.client_id,
        custom_message=payload.custom_message,
    )
    return {"preview": msg, "reminder_type": payload.reminder_type}


@router.post("/reminders", response_model=ReminderResponse)
def schedule_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    """
    Schedule a reminder.
    - If scheduled_at is None → reminder is pending manual trigger.
    - If scheduled_at is set → reminder waits until that datetime.
    """
    reminder = WhatsAppReminder(
        phone_number=normalize_phone(payload.phone_number),
        client_name=payload.client_name,
        client_id=payload.client_id,
        lead_id=payload.lead_id,
        booking_id=payload.booking_id,
        reminder_type=payload.reminder_type,
        message_body=payload.message_body,
        scheduled_at=payload.scheduled_at,
        status="pending",
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/reminders/send-now", response_model=ReminderResponse)
def send_now(payload: SendNowPayload, db: Session = Depends(get_db)):
    """
    Send a WhatsApp message immediately.
    Creates a record and dispatches right away.
    """
    # Auto-build message from template if booking/lead attached
    msg = payload.message_body
    if not msg and (payload.booking_id or payload.lead_id):
        msg = _build_message(
            reminder_type=payload.reminder_type,
            db=db,
            booking_id=payload.booking_id,
            lead_id=payload.lead_id,
            client_id=payload.client_id,
            client_name=payload.client_name,
        )

    reminder = WhatsAppReminder(
        phone_number=normalize_phone(payload.phone_number),
        client_name=payload.client_name,
        client_id=payload.client_id,
        lead_id=payload.lead_id,
        booking_id=payload.booking_id,
        reminder_type=payload.reminder_type,
        message_body=msg or "Hello from Darun Tourism!",
        status="pending",
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # send immediately
    _send_and_update(reminder, db)
    return reminder


@router.patch("/reminders/{reminder_id}/cancel", response_model=ReminderResponse)
def cancel_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """Cancel a pending scheduled reminder."""
    reminder = db.query(WhatsAppReminder).filter(WhatsAppReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot cancel reminder with status '{reminder.status}'")
    reminder.status = "cancelled"
    reminder.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reminder)
    return reminder


@router.patch("/reminders/{reminder_id}/send", response_model=ReminderResponse)
def send_pending_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """Manually trigger a pending reminder to send now."""
    reminder = db.query(WhatsAppReminder).filter(WhatsAppReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status not in ("pending",):
        raise HTTPException(status_code=400, detail=f"Reminder is already '{reminder.status}'")
    _send_and_update(reminder, db)
    return reminder


@router.patch("/reminders/{reminder_id}/mark-sent", response_model=ReminderResponse)
def mark_reminder_sent(reminder_id: int, db: Session = Depends(get_db)):
    """Mark a pending reminder as sent (e.g. after sending via WhatsApp Web / manual chat)."""
    reminder = db.query(WhatsAppReminder).filter(WhatsAppReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    now = datetime.utcnow()
    reminder.status = "sent"
    reminder.sent_at = now
    reminder.updated_at = now
    reminder.twilio_sid = "WA_WEB_MANUAL"
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """Delete a reminder record by marking as dismissed so background sync won't recreate it."""
    reminder = db.query(WhatsAppReminder).filter(WhatsAppReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    # Set status to dismissed so it's excluded from pending and logs, and prevents re-sync
    reminder.status = "dismissed"
    reminder.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Reminder deleted"}


@router.post("/reminders/auto-schedule")
def auto_schedule_reminders(db: Session = Depends(get_db)):
    """
    Scan all upcoming bookings and auto-create reminders:
      - Pre-trip reminder 3 days before check_in (if not already scheduled)
      - Payment reminder if balance > 0 and trip within 7 days
    Returns count of new reminders created.
    """
    today = date.today()
    created = []

    bookings = (
        db.query(Booking)
        .join(Client, Booking.client_id == Client.id)
        .filter(
            Booking.status.in_(["confirmed", "in_progress"]),
            Client.phone.isnot(None),
        )
        .all()
    )

    for booking in bookings:
        client = booking.client
        phone = client.phone if client else None
        if not phone:
            continue

        # parse check_in date
        try:
            check_in_date = datetime.strptime(booking.check_in, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        days_until = (check_in_date - today).days

        # ── Pre-trip reminder (3 days before) ───────────────────────────────
        if 2 <= days_until <= 4:
            existing = (
                db.query(WhatsAppReminder)
                .filter(
                    WhatsAppReminder.booking_id == booking.id,
                    WhatsAppReminder.reminder_type == "pre_trip",
                    WhatsAppReminder.status.in_(["pending", "sent", "cancelled", "dismissed"]),
                )
                .first()
            )
            if not existing:
                msg = render_pre_trip(
                    client_name=client.full_name,
                    destination=booking.destination or "your destination",
                    check_in=booking.check_in,
                    hotel_name=booking.hotel_name,
                    booking_ref=booking.booking_ref,
                    pax=booking.pax,
                )
                r = WhatsAppReminder(
                    phone_number=normalize_phone(phone),
                    client_name=client.full_name,
                    client_id=client.id,
                    booking_id=booking.id,
                    reminder_type="pre_trip",
                    message_body=msg,
                    status="pending",
                )
                db.add(r)
                created.append(f"pre_trip for booking #{booking.id}")

        # ── Payment reminder (if balance pending and trip ≤ 7 days) ─────────
        balance = (booking.total_price or 0) - (booking.amount_paid or 0)
        if balance > 0 and 0 <= days_until <= 7:
            existing = (
                db.query(WhatsAppReminder)
                .filter(
                    WhatsAppReminder.booking_id == booking.id,
                    WhatsAppReminder.reminder_type == "payment",
                    WhatsAppReminder.status.in_(["pending", "sent", "cancelled", "dismissed"]),
                )
                .first()
            )
            if not existing:
                msg = render_payment_reminder(
                    client_name=client.full_name,
                    destination=booking.destination or "your trip",
                    amount_due=balance,
                    total_price=booking.total_price or 0,
                    booking_ref=booking.booking_ref,
                    check_in=booking.check_in,
                )
                r = WhatsAppReminder(
                    phone_number=normalize_phone(phone),
                    client_name=client.full_name,
                    client_id=client.id,
                    booking_id=booking.id,
                    reminder_type="payment",
                    message_body=msg,
                    status="pending",
                )
                db.add(r)
                created.append(f"payment for booking #{booking.id}")

    db.commit()
    return {
        "created": len(created),
        "details": created,
        "message": f"Auto-scheduled {len(created)} reminder(s).",
    }
