"""
SMS channel — sends via Twilio.
"""

import logging

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)


def send_sms(to: str, body: str) -> str:
    """
    Send an SMS via Twilio.

    Args:
        to: Recipient phone number in E.164 format.
        body: SMS message content.

    Returns:
        Twilio Message SID.

    Raises:
        Exception: Any Twilio or network-related exception.
    """

    logger.info("Sending SMS to %s", to)

    client = Client(
        settings.twilio_account_sid,
        settings.twilio_auth_token,
    )

    message = client.messages.create(
        body=body,
        from_=settings.twilio_phone_number,
        to=to,
    )

    logger.info("SMS sent successfully. SID=%s", message.sid)

    return message.sid