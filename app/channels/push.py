"""
Push notification channel — Firebase FCM (Android) + AWS SNS APNs (iOS).

How to set up Firebase (required for Android push):
  1. Go to Firebase Console → Project Settings → Service Accounts
  2. Click "Generate new private key" → download the JSON file
  3. Base64-encode it:
       macOS/Linux:  base64 -i service-account.json
       Windows PS:   [Convert]::ToBase64String([IO.File]::ReadAllBytes("service-account.json"))
  4. Copy the output into FIREBASE_SERVICE_ACCOUNT_JSON in your .env file

iOS push (APNs) can be done via Firebase (if the Flutter app uses FlutterFire) or
via AWS SNS (set SNS_PLATFORM_ARN_IOS in .env). The FCM path handles both platforms
if the Flutter app registers with Firebase Messaging.

Environment variables (set in .env):
  FIREBASE_SERVICE_ACCOUNT_JSON  — base64-encoded service account JSON
  SNS_PLATFORM_ARN_IOS           — (optional) AWS SNS ARN for APNs direct path
"""
from __future__ import annotations

import base64
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level flag so firebase_admin.initialize_app() is only called once.
# Calling it again raises "Firebase app named '[DEFAULT]' already exists".
# Lazy initialization means the service starts cleanly even when
# FIREBASE_SERVICE_ACCOUNT_JSON is not set (email/SMS-only deployments).
_firebase_initialized = False


def _ensure_firebase() -> None:
    """
    Initialize the Firebase Admin SDK on first use.

    Reads the base64-encoded service account JSON from settings, decodes it,
    and passes it to firebase_admin as a certificate credential.
    Raises NotImplementedError with a helpful message when the env var is missing.
    """
    global _firebase_initialized
    if _firebase_initialized:
        return

    import firebase_admin
    from firebase_admin import credentials

    if not settings.firebase_service_account_json:
        raise NotImplementedError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not set in .env. "
            "Download the service account JSON from Firebase Console, "
            "base64-encode it, and add it to your .env file."
        )

    # Decode base64 → JSON string → dict, then hand to firebase_admin
    sa_json = json.loads(base64.b64decode(settings.firebase_service_account_json))
    cred = credentials.Certificate(sa_json)
    firebase_admin.initialize_app(cred)
    _firebase_initialized = True


def send_push(
    device_token: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> str:
    """
    Send a push notification via Firebase FCM.

    Works for both Android (FCM native) and iOS (FCM via APNs gateway),
    as long as the Flutter app is set up with FlutterFire (firebase_messaging).

    The device_token comes from the mobile app after FCM registration. The
    backend stores it in users.device_tokens[] (updated via PUT /auth/profile).

    Args:
        device_token: FCM registration token of the target device.
        title: Notification title shown in the system tray / lock screen.
        body: Notification body text.
        data: Optional key/value data payload (delivered even when the app is
              in the background). FCM requires all values to be strings —
              non-strings are coerced automatically.

    Returns:
        FCM message ID string in the format "projects/{id}/messages/{id}".

    Raises:
        NotImplementedError: FIREBASE_SERVICE_ACCOUNT_JSON not configured.
        firebase_admin.exceptions.FirebaseError: FCM delivery failure
            (invalid token, quota exceeded, etc.).
    """
    from firebase_admin import messaging

    _ensure_firebase()

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        # FCM only accepts string values in the data payload — coerce here
        # so callers don't need to pre-convert integers or booleans.
        data={k: str(v) for k, v in (data or {}).items()},
        token=device_token,
    )
    msg_id = messaging.send(message)
    logger.info("Push sent to %s — msg_id: %s", device_token, msg_id)
    return msg_id
