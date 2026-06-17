"""
WhatsApp channel — Twilio WhatsApp API.

Students: implement send_whatsapp() using the Twilio Python SDK.
"""


def send_whatsapp(to: str, body: str) -> str:
    """
    Send a WhatsApp message via Twilio.

    The 'to' number must be prefixed with 'whatsapp:+'
    (e.g. 'whatsapp:+919876543210').

    TODO:
      from twilio.rest import Client
      client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
      message = client.messages.create(
          body=body,
          from_=settings.twilio_whatsapp_number,
          to=f"whatsapp:{to}" if not to.startswith("whatsapp:") else to,
      )
      return message.sid
    """
    raise NotImplementedError(
        "Install twilio and implement send_whatsapp() "
        "in app/channels/whatsapp.py"
    )
