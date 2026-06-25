"""
Email channel — sends via SMTP using aiosmtplib (fully async).

Why aiosmtplib instead of stdlib smtplib?
  smtplib is blocking — calling it inside an async FastAPI worker stalls the
  entire event loop while waiting for the SMTP handshake. aiosmtplib is a
  drop-in async replacement that plays well with asyncio workers and is already
  listed in requirements.txt.

Environment variables (set in .env):
  SMTP_HOST          — mail server hostname  (dev: localhost, prod: smtp.gmail.com)
  SMTP_PORT          — 465 (SSL), 587 (STARTTLS), or 1025 (Mailpit / no TLS)
  SMTP_USERNAME      — leave empty for servers that don't require auth (e.g. Mailpit)
  SMTP_PASSWORD      — leave empty for unauthenticated servers
  SMTP_FROM_EMAIL    — "From:" address shown to recipients
"""
import logging
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> str:
    """
    Send an email via SMTP.

    Builds a multipart/alternative message with a plain-text part and an
    optional HTML part. Email clients display the HTML version if supported,
    falling back to plain text.

    TLS mode is derived automatically from SMTP_PORT:
      465  → implicit SSL/TLS   (use_tls=True)
      587  → STARTTLS upgrade   (start_tls=True)
      other → no TLS            (e.g. Mailpit on port 1025 for local dev)

    Returns:
        A UUID string used as the message ID (SMTP does not return a
        server-assigned ID after send).

    Raises:
        aiosmtplib.SMTPException: On connection, auth, or delivery failure.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to

    # Plain text first — clients fall back to this when HTML is not supported
    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    # Derive TLS mode from port so the same code works in all environments:
    #   dev  → Mailpit (port 1025, no TLS, no auth)
    #   prod → Gmail / any SMTP (port 587 STARTTLS or 465 SSL)
    use_tls = settings.smtp_port == 465
    start_tls = settings.smtp_port == 587

    # Passing None for credentials disables AUTH entirely (required for Mailpit
    # and other unauthenticated SMTP relays). Empty strings would cause an error.
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        use_tls=use_tls,
        start_tls=start_tls,
    )

    msg_id = str(uuid.uuid4())
    logger.info("Email sent to %s (id=%s)", to, msg_id)
    return msg_id
