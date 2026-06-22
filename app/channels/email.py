"""
Email channel — sends via SMTP (dev) or AWS SES (prod).

Students: the send_email() function is partially implemented.
TODO: add HTML template support and handle SES in production.
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate

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
    Send email using SMTP.

    Supports:
    - Plain text
    - HTML
    - TLS
    - SMTP authentication

    Returns:
        str: SMTP Message-ID

    Raises:
        Exception on failure
    """

    # Create MIME message
    msg = MIMEMultipart("alternative")

    # Generate unique Message-ID
    message_id = make_msgid()

    # Email headers
    msg["Message-Id"] = message_id
    msg["Date"] = formatdate(localtime=True)
    msg["From"] = settings.smtp_from_email
    msg["To"] = to
    msg["Subject"] = subject

    # Plain-text version
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # HTML version (optional)
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        logger.info("Sending email to %s", to)

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=settings.smtp_starttls,
            timeout=30,
        )

        logger.info("Email sent successfully to %s", to)

        return message_id

    except aiosmtplib.SMTPException as exc:
        logger.exception("SMTP error while sending email to %s", to)
        raise Exception(f"SMTP error: {exc}") from exc
    

    except Exception as exc:
        logger.exception("Unexpected email error for %s", to)
        raise Exception(f"Email send failed: {exc}") from exc