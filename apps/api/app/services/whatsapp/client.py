"""
WhatsApp Client — Twilio integration.
Sends messages via Twilio WhatsApp API.

Set these environment variables in apps/api/.env:
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886   (sandbox number)
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── graceful import ──────────────────────────────────────────────────────────
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("twilio package not installed. Run: pip install twilio")


def _get_client() -> Optional["TwilioClient"]:
    """Return a Twilio client if credentials are configured."""
    if not TWILIO_AVAILABLE:
        return None
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not sid or not token or sid.startswith("AC_DEMO"):
        logger.info("Twilio credentials not configured — running in DEMO mode.")
        return None
    return TwilioClient(sid, token)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format for WhatsApp.
    Accepts:
        - 9876543210          → +919876543210
        - +919876543210       → +919876543210
        - 09876543210         → +919876543210
    """
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("+"):
        return phone
    if phone.startswith("91") and len(phone) == 12:
        return "+" + phone
    if phone.startswith("0") and len(phone) == 11:
        return "+91" + phone[1:]
    if len(phone) == 10:
        return "+91" + phone
    return "+" + phone  # fallback — prepend +


def send_whatsapp(phone: str, message: str) -> dict:
    """
    Send a WhatsApp message via Twilio.

    Returns a result dict:
        { "success": True, "sid": "SM...", "mode": "live" }
        { "success": True, "sid": "DEMO_...", "mode": "demo" }
        { "success": False, "error": "...", "mode": "live" }
    """
    to_phone = normalize_phone(phone)
    from_phone = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Format to Twilio's expected format
    if not to_phone.startswith("whatsapp:"):
        to_phone_wa = f"whatsapp:{to_phone}"
    else:
        to_phone_wa = to_phone

    client = _get_client()

    if client is None:
        # ── DEMO MODE ─ logs message without sending ──────────────────────────
        demo_sid = f"DEMO_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        logger.info(
            f"[DEMO] WhatsApp → {to_phone}\n"
            f"  From: {from_phone}\n"
            f"  Message: {message[:120]}...\n"
            f"  SID: {demo_sid}"
        )
        return {"success": True, "sid": demo_sid, "mode": "demo", "to": to_phone}

    # ── LIVE MODE ─────────────────────────────────────────────────────────────
    try:
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=to_phone_wa,
        )
        logger.info(f"[LIVE] WhatsApp sent → {to_phone} | SID: {msg.sid}")
        return {"success": True, "sid": msg.sid, "mode": "live", "to": to_phone}
    except TwilioRestException as e:
        logger.error(f"Twilio error sending to {to_phone}: {e}")
        return {"success": False, "error": str(e), "mode": "live", "to": to_phone}
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp to {to_phone}: {e}")
        return {"success": False, "error": str(e), "mode": "live", "to": to_phone}
