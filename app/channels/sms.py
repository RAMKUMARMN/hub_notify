"""
SMS channel — sends via Twilio
"""

from twilio.rest import Client

from app.config import settings


def send_sms(to: str, body: str) -> str:
    """
    Send SMS via Twilio.
    Returns message SID.
    """

    client = Client(
        settings.twilio_account_sid,
        settings.twilio_auth_token
    )

    message = client.messages.create(
        body=body,
        from_=settings.twilio_phone_number,
        to=to
    )

    return message.sid