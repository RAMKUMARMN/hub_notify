"""
Notify router — /api/v1/notify/*

Handles single-send and bulk notification requests.
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.channels.email import send_email
from app.channels.sms import send_sms
from app.channels.push import send_push
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload

router = APIRouter(prefix="/notify", tags=["notify"])


class SingleSendRequest(BaseModel):
    channel: str
    recipient: str
    subject: str | None = None
    body: str = ""
    html_body: str | None = None
    title: str | None = None
    data: dict | None = None


class BulkRecipient(BaseModel):
    recipient: str
    subject: str | None = None
    body: str = ""
    html_body: str | None = None


class BulkSendRequest(BaseModel):
    channel: str
    recipients: list[BulkRecipient]


@router.post("/send")
async def send_single(
    body: SingleSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a single notification immediately."""

    notification = Notification(
        recipient=body.recipient,
        channel=body.channel,
        subject=body.subject,
        body=body.body,
        status="PENDING",
        attempts=0,
    )

    db.add(notification)

    await db.commit()

    await db.refresh(notification)

    try:

        notification.status = "PROCESSING"

        await db.commit()

        match body.channel:

            case "email":
                msg_id = await send_email(
                    to=body.recipient,
                    subject=body.subject or "",
                    body=body.body,
                    html_body=body.html_body,
                )

            case "sms":
                msg_id = send_sms(
                    to=body.recipient,
                    body=body.body,
                )

            case "push":
                msg_id = send_push(
                    device_token=body.recipient,
                    title=body.title or "CixioHub",
                    body=body.body,
                    data=body.data,
                )

            case _:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown channel: {body.channel}",
                )

        notification.status = "SENT"

        await db.commit()

        return {
            "status": "sent",
            "message_id": msg_id,
            "notification_id": notification.id,
        }

    except Exception as exc:

        notification.status = "FAILED"

        notification.attempts += 1

        notification.error_message = str(exc)

        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def send_bulk(body: BulkSendRequest):
    """Enqueue a bulk notification job. Returns job_id immediately."""

    if not body.recipients:
        raise HTTPException(
            status_code=400,
            detail="Recipients list is empty",
        )

    job_id = str(uuid.uuid4())

    for r in body.recipients:

        payload = NotifyPayload(
            job_id=job_id,
            channel=body.channel,
            recipient=r.recipient,
            subject=r.subject,
            body=r.body,
            html_body=r.html_body,
        )

        await publish(payload)

    return {
        "job_id": job_id,
        "total": len(body.recipients),
        "status": "queued",
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the current status of a bulk notification job.
    """

    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": "Implement job tracking later",
    }
@router.post("/send")
async def send_single(
    body: SingleSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a single notification immediately."""

    notification = Notification(
        recipient=body.recipient,
        channel=body.channel,
        subject=body.subject,
        body=body.body,
        status="PENDING",
        attempts=0,
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    try:
        notification.status = "PROCESSING"
        await db.commit()

        match body.channel:
            case "email":
                # Updated to pass correct arguments to your email service
                msg_id = await send_email(
                    to=body.recipient,
                    subject=body.subject or "Notification",
                    body=body.body,
                    html_body=body.html_body,
                )

            case "sms":
                msg_id = send_sms(to=body.recipient, body=body.body)

            case "push":
                msg_id = send_push(
                    device_token=body.recipient,
                    title=body.title or "CixioHub",
                    body=body.body,
                    data=body.data,
                )

            case _:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown channel: {body.channel}",
                )

        notification.status = "SENT"
        await db.commit()

        return {
            "status": "sent",
            "message_id": msg_id,
            "notification_id": notification.id,
        }

    except Exception as exc:
        notification.status = "FAILED"
        notification.attempts += 1
        notification.error_message = str(exc)
        await db.commit()

        # Improved error reporting
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send {body.channel} notification: {str(exc)}",
        )