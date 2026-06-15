"""
Notify router — /api/v1/notify/*

Handles single-send and bulk notification requests.
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

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


@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_single(body: SingleSendRequest):
    """Enqueue a single notification job. Returns job_id immediately."""
    if body.channel not in ["email", "sms", "push", "whatsapp"]:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {body.channel}")

    job_id = str(uuid.uuid4())
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
async def send_bulk(body: BulkSendRequest):
    """Enqueue a bulk notification job. Returns job_id immediately."""
    if not body.recipients:
        raise HTTPException(status_code=400, detail="Recipients list is empty")

    job_id = str(uuid.uuid4())
    # TODO: create NotificationJob record in DB here

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
async def get_job_status(job_id: str):
    """
    Get the current status of a bulk notification job.

    TODO: query the notification_jobs table and return progress.
    """
    # Placeholder response
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": "Implement job tracking — query notification_jobs table",
    }
