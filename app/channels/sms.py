"""
SMS channel — sends via Twilio.

Students: implement send_sms() using the Twilio Python SDK.
"""


def send_sms(to: str, body: str) -> str:
    """
    Send an SMS via Twilio.

    Returns the Twilio message SID on success.

    TODO:
      from twilio.rest import Client
      client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
      message = client.messages.create(
          body=body,
          from_=settings.twilio_phone_number,
          to=to,
      )
      return message.sid
    """
    raise NotImplementedError(
        "Install twilio and implement send_sms() in app/channels/sms.py"
    )
