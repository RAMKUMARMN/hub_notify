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
async def send_single(body: SingleSendRequest, db: AsyncSession = Depends(get_db)):
    """Enqueue a single notification job. Returns job_id immediately."""
    if body.channel not in ["email", "sms", "push", "whatsapp"]:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {body.channel}")

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

    # Create IndividualNotification record in DB
    ind_notification = IndividualNotification(
        job_id=job_id,
        recipient=body.recipient,
        status="queued",
        attempt=1,
    )
    db.add(ind_notification)
    await db.commit()

    payload = NotifyPayload(
        job_id=job_id,
        channel=body.channel,
        recipient=body.recipient,
        subject=body.subject,
        body=body.body,
        html_body=body.html_body,
        title=body.title,
        data=body.data,
    )
    try:
        await publish(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"job_id": job_id, "status": "queued"}



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

    # Create IndividualNotification records in DB
    for r in body.recipients:
        ind_notification = IndividualNotification(
            job_id=job_id,
            recipient=r.recipient,
            status="queued",
            attempt=1,
        )
        db.add(ind_notification)
    await db.commit()

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

    return {"job_id": job_id, "total": len(body.recipients), "status": "queued"}


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
        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        "notifications": [
            {
                "job_id": n.job_id,
                "recipient": n.recipient,
                "status": n.status,
                "attempt": n.attempt,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
            }
            for n in notifications
        ],
    }
