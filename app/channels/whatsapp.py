"""
WhatsApp channel — sends messages via the Twilio WhatsApp API.

Two modes depending on Twilio account status:

  Sandbox (dev / testing):
    1. Visit https://console.twilio.com → Messaging → Try it out → Send a WhatsApp message
    2. Have each recipient send the join code to the sandbox number to opt in
    3. Set TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886 (default sandbox number)

  Production (WhatsApp Business API):
    1. Apply for a WhatsApp-enabled number in the Twilio Console
    2. Set TWILIO_WHATSAPP_NUMBER to your approved number (with or without
       the 'whatsapp:' prefix — this module adds it automatically)

Environment variables (set in .env):
  TWILIO_ACCOUNT_SID       — found at console.twilio.com
  TWILIO_AUTH_TOKEN        — found at console.twilio.com
  TWILIO_WHATSAPP_NUMBER   — the sending number, e.g. whatsapp:+14155238886
"""
import logging

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)


def send_whatsapp(to: str, body: str) -> str:
    """
    Send a WhatsApp message via Twilio.

    Args:
        to: Recipient phone number in E.164 format (e.g. '+60123456789').
            The 'whatsapp:' URI scheme prefix is added automatically if missing,
            so callers can pass plain phone numbers without worrying about it.
        body: Message text (max 4096 characters per WhatsApp message limits).

    Returns:
        Twilio Message SID (a string starting with 'SM...').

    Raises:
        twilio.base.exceptions.TwilioRestException: If credentials are wrong,
            the recipient hasn't opted in to the sandbox, or the number is invalid.
    """
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    # Twilio requires the 'whatsapp:' URI scheme on both the from and to numbers.
    # Normalize both here so callers can provide plain E.164 numbers.
    from_number = settings.twilio_whatsapp_number
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

    message = client.messages.create(
        body=body,
        from_=from_number,
        to=to_number,
    )
    logger.info("WhatsApp sent to %s — SID: %s", to, message.sid)
    return message.sid
