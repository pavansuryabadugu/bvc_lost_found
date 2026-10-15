import logging

import httpx
from sqlalchemy.orm import Session

from .config import TWILIO_FROM, TWILIO_SID, TWILIO_TOKEN
from .models import Notification

log = logging.getLogger("lostfound")


def add_notification(db: Session, user_id: int, message: str, item_id: int | None = None) -> None:
    db.add(Notification(user_id=user_id, message=message, item_id=item_id))


def send_whatsapp(phone: str, text: str) -> None:
    """Send one WhatsApp message (Twilio). Without credentials, print it instead."""
    if not (TWILIO_SID and TWILIO_TOKEN):
        log.warning("[WhatsApp dry-run] to +91%s:\n%s", phone, text)
        return
    try:
        httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            auth=(TWILIO_SID, TWILIO_TOKEN),
            data={"From": TWILIO_FROM, "To": f"whatsapp:+91{phone}", "Body": text},
            timeout=15,
        ).raise_for_status()
    except httpx.HTTPError as exc:
        log.error("WhatsApp send to +91%s failed: %s", phone, exc)


def broadcast_whatsapp(phones: list[str], text: str) -> None:
    for phone in phones:
        send_whatsapp(phone, text)
