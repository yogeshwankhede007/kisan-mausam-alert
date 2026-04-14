"""
Notification dispatcher – sends SMS, WhatsApp, and/or email.
Supports Twilio (SMS & WhatsApp) and SMTP email.
"""

from __future__ import annotations

import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Literal, Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from twilio.rest import Client as TwilioClient

from config.settings import (
    EMAIL_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_MESSAGING_SERVICE_SID,
    TWILIO_SMS_FROM,
    TWILIO_WHATSAPP_FROM,
)

logger = logging.getLogger(__name__)

_twilio_client: Optional[TwilioClient] = None


def _get_twilio() -> TwilioClient:
    global _twilio_client
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) are not set."
            )
        _twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


# ── SMS ─────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def send_sms(to_phone: str, message: str) -> str:
    """
    Send an SMS via Twilio.
    to_phone must be E.164 e.g. +919876543210.
    Returns the Twilio message SID.
    """
    client = _get_twilio()
    kwargs: dict = {"body": message, "to": to_phone}
    if TWILIO_MESSAGING_SERVICE_SID:
        kwargs["messaging_service_sid"] = TWILIO_MESSAGING_SERVICE_SID
    else:
        kwargs["from_"] = TWILIO_SMS_FROM
    msg = client.messages.create(**kwargs)
    logger.info("SMS sent to %s — SID: %s", to_phone, msg.sid)
    return msg.sid


# ── WhatsApp ────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def send_whatsapp(to_phone: str, message: str) -> str:
    """
    Send a WhatsApp message via Twilio.
    to_phone must be E.164 e.g. +919876543210  (no 'whatsapp:' prefix here).
    Returns the Twilio message SID.
    """
    client = _get_twilio()
    msg = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{to_phone}",
    )
    logger.info("WhatsApp sent to %s — SID: %s", to_phone, msg.sid)
    return msg.sid


# ── Email ────────────────────────────────────────────────────────────────────

def send_email(to_address: str, subject: str, body: str) -> None:
    """Send a plain-text email via SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured; skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM or SMTP_USER
    msg["To"] = to_address
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_address, msg.as_string())
    logger.info("Email sent to %s", to_address)


# ── Batch dispatcher ─────────────────────────────────────────────────────────

Channel = Literal["sms", "whatsapp", "both"]


def dispatch_alert(
    to_phone: str,
    message: str,
    channel: Channel = "sms",
    rate_limit_delay: float = 0.3,
) -> dict:
    """
    Dispatch a weather alert over one or both channels.
    Returns dict: {"sms": sid|None, "whatsapp": sid|None, "errors": [...]}
    """
    result: dict = {"sms": None, "whatsapp": None, "errors": []}
    send_sms_flag = channel in ("sms", "both")
    send_wa_flag = channel in ("whatsapp", "both")

    if send_sms_flag:
        try:
            result["sms"] = send_sms(to_phone, message)
        except Exception as exc:
            err = f"SMS to {to_phone} failed: {exc}"
            logger.error(err)
            result["errors"].append(err)
        time.sleep(rate_limit_delay)

    if send_wa_flag:
        try:
            result["whatsapp"] = send_whatsapp(to_phone, message)
        except Exception as exc:
            err = f"WhatsApp to {to_phone} failed: {exc}"
            logger.error(err)
            result["errors"].append(err)
        time.sleep(rate_limit_delay)

    return result
