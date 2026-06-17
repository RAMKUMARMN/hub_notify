"""
Notify router — /api/v1/notify/*

Handles single-send and bulk notification requests.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import NotificationJob, IndividualNotification

from app.queue.producer import publish_notification

router = APIRouter(prefix="/notify", tags=["notify"])


class SingleSendRequest(BaseModel):
    channel: str
    recipient: str
    subject: str | None = None
    body: str = ""
    html_body: str | None = None
    title: str | None = None
    data: dict | None = None
    scheduled_at: datetime | None = None


class BulkRecipient(BaseModel):
    recipient: str
    subject: str | None = None
    body: str = ""
    html_body: str | None = None


class BulkSendRequest(BaseModel):
    channel: str
    recipients: list[BulkRecipient]
    scheduled_at: datetime | None = None


@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_single(
    body: SingleSendRequest, db: AsyncSession = Depends(get_db)
):
    """Enqueue a single notification job. Returns job_id immediately."""
    if body.channel not in ["email", "sms", "push", "whatsapp"]:
        raise HTTPException(
            status_code=400, detail=f"Unknown channel: {body.channel}"
        )

    job_id = str(uuid.uuid4())

    # Create NotificationJob record in DB
    job = NotificationJob(
        job_id=job_id,
        channel=body.channel,
        total=1,
        sent=0,
        failed=0,
        retrying=0,
        completed=False,
        scheduled_at=body.scheduled_at,
    )
    db.add(job)

    # Determine status based on whether it is scheduled
    status_val = "scheduled" if body.scheduled_at else "queued"

    notif_id = str(uuid.uuid4())

    # Create IndividualNotification record in DB
    ind_notification = IndividualNotification(
        id=notif_id,
        job_id=job_id,
        recipient=body.recipient,
        status=status_val,
        attempt=1,
        subject=body.subject,
        body=body.body,
        html_body=body.html_body,
        title=body.title,
        data=body.data,
    )
    db.add(ind_notification)
    await db.commit()

    if not body.scheduled_at:
        try:
            await publish_notification(ind_notification, body.channel)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return {"job_id": job_id, "status": status_val}


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def send_bulk(body: BulkSendRequest, db: AsyncSession = Depends(get_db)):
    """Enqueue a bulk notification job. Returns job_id immediately."""
    if not body.recipients:
        raise HTTPException(status_code=400, detail="Recipients list is empty")

    job_id = str(uuid.uuid4())

    # Create NotificationJob record in DB
    job = NotificationJob(
        job_id=job_id,
        channel=body.channel,
        total=len(body.recipients),
        sent=0,
        failed=0,
        retrying=0,
        completed=False,
        scheduled_at=body.scheduled_at,
    )
    db.add(job)

    # Determine status based on whether it is scheduled
    status_val = "scheduled" if body.scheduled_at else "queued"

    # Create IndividualNotification records in DB
    notifications_data = []
    for r in body.recipients:
        notif_id = str(uuid.uuid4())
        ind_notification = IndividualNotification(
            id=notif_id,
            job_id=job_id,
            recipient=r.recipient,
            status=status_val,
            attempt=1,
            subject=r.subject,
            body=r.body,
            html_body=r.html_body,
        )
        db.add(ind_notification)
        notifications_data.append(ind_notification)
    await db.commit()

    if not body.scheduled_at:
        for ind_notification in notifications_data:
            await publish_notification(ind_notification, body.channel)

    return {
        "job_id": job_id,
        "total": len(body.recipients),
        "status": status_val,
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the current status of a bulk notification job.

    Query the notification_jobs table and return progress.
    """
    job = await db.get(NotificationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch individual notifications for this job
    from sqlalchemy import select
    result = await db.execute(
        select(IndividualNotification)
        .where(IndividualNotification.job_id == job_id)
    )
    notifications = result.scalars().all()

    return {
        "job_id": job.job_id,
        "channel": job.channel,
        "total": job.total,
        "sent": job.sent,
        "failed": job.failed,
        "retrying": job.retrying,
        "completed": job.completed,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "scheduled_at": (
            job.scheduled_at.isoformat() if job.scheduled_at else None
        ),
        "notifications": [
            {
                "job_id": n.job_id,
                "recipient": n.recipient,
                "status": n.status,
                "attempt": n.attempt,
                "updated_at": (
                    n.updated_at.isoformat() if n.updated_at else None
                ),
            }
            for n in notifications
        ],
    }
