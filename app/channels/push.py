"""
Push notification channel — Firebase FCM (Android) + AWS SNS APNs (iOS).

Students: implement send_push() using firebase-admin and boto3.
"""
from app.config import settings


def send_push(device_token: str, title: str, body: str, data: dict | None = None) -> str:
    """
     Send a push notification via Firebase FCM.

    Returns the FCM message ID on success.

    TODO:
      import base64, json, firebase_admin
      from firebase_admin import credentials, messaging

      # Initialise once (use a module-level flag to avoid re-init)
      if not firebase_admin._apps:
          sa_json = json.loads(base64.b64decode(settings.firebase_service_account_json))
          cred = credentials.Certificate(sa_json)
          firebase_admin.initialize_app(cred)

      message = messaging.Message(
          notification=messaging.Notification(title=title, body=body),
          data=data or {},
          token=device_token,
      )
      return messaging.send(message)
    """
    raise NotImplementedError(
        "Install firebase-admin and implement send_push() in app/channels/push.py"
    )
