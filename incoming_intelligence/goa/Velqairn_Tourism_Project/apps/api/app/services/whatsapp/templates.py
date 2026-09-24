"""
WhatsApp message templates for Darun Tourism.
All templates are personalized with client/booking data.
"""
from typing import Optional


def render_pre_trip(
    client_name: str,
    destination: str,
    check_in: str,
    hotel_name: Optional[str] = None,
    booking_ref: Optional[str] = None,
    pax: Optional[int] = None,
) -> str:
    hotel_line = f"\n🏨 Hotel: *{hotel_name}*" if hotel_name else ""
    ref_line = f"\n📋 Booking Ref: `{booking_ref}`" if booking_ref else ""
    pax_line = f"\n👥 Travellers: {pax}" if pax else ""
    return (
        f"Hi {client_name}! 🌴\n\n"
        f"Exciting news — your trip to *{destination}* is just around the corner!\n"
        f"📅 Check-in: *{check_in}*"
        f"{hotel_line}"
        f"{pax_line}"
        f"{ref_line}\n\n"
        f"Please make sure your documents, IDs, and packing are ready. "
        f"Have any questions? Just reply to this message.\n\n"
        f"Wishing you a wonderful journey! ✈️\n"
        f"— *Darun Tourism*"
    )


def render_payment_reminder(
    client_name: str,
    destination: str,
    amount_due: float,
    total_price: float,
    booking_ref: Optional[str] = None,
    check_in: Optional[str] = None,
) -> str:
    ref_line = f" (Ref: `{booking_ref}`)" if booking_ref else ""
    date_line = f"\nYour trip is on *{check_in}*." if check_in else ""
    return (
        f"Hi {client_name}! 👋\n\n"
        f"This is a friendly reminder that your payment for the *{destination}* trip is pending.\n\n"
        f"💰 Amount Due: *₹{amount_due:,.0f}*\n"
        f"📦 Total Package: ₹{total_price:,.0f}"
        f"{ref_line}"
        f"{date_line}\n\n"
        f"Please make the payment at your earliest convenience to confirm your booking. "
        f"Reply here if you have any queries!\n\n"
        f"— *Darun Tourism*"
    )


def render_post_trip_followup(
    client_name: str,
    destination: str,
    check_out: Optional[str] = None,
) -> str:
    hope_line = f"after your *{destination}* trip" if destination else "on your journey"
    return (
        f"Hi {client_name}! 😊\n\n"
        f"We hope you had an amazing experience {hope_line}! 🌟\n\n"
        f"We'd love to hear how everything went. "
        f"Your feedback helps us make every trip even better.\n\n"
        f"👉 Reply to this message with your experience or any suggestions!\n\n"
        f"Also, if you're thinking about your next adventure, we're here to make it unforgettable. 🗺️\n\n"
        f"Thank you for choosing Darun Tourism!\n"
        f"— *Darun Tourism*"
    )


def render_custom(
    client_name: str,
    custom_message: str,
) -> str:
    return (
        f"Hi {client_name}! 👋\n\n"
        f"{custom_message}\n\n"
        f"— *Darun Tourism*"
    )


def render_inquiry_followup(
    client_name: str,
    destination: Optional[str] = None,
    budget: Optional[float] = None,
) -> str:
    dest_line = f" to *{destination}*" if destination else ""
    budget_line = f"\nBudget noted: ₹{budget:,.0f}" if budget else ""
    return (
        f"Hi {client_name}! 👋\n\n"
        f"Thank you for your interest in a trip{dest_line} with Darun Tourism!"
        f"{budget_line}\n\n"
        f"We're working on a personalized itinerary for you. "
        f"We'll share the details soon!\n\n"
        f"In the meantime, feel free to reply with any specific requirements or questions.\n\n"
        f"— *Darun Tourism*"
    )


TEMPLATE_LABELS = {
    "pre_trip": "Pre-Trip Reminder (3 days before check-in)",
    "payment": "Payment Reminder",
    "followup": "Post-Trip Follow-up",
    "inquiry": "Inquiry Follow-up (New Lead)",
    "custom": "Custom Message",
}
