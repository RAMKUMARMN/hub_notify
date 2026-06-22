"""
Notify router — /api/v1/notify/*

Handles:
1. Single notification sending
2. Bulk notification queue publishing via RabbitMQ
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.channels.email import send_email
from app.channels.sms import send_sms
from app.channels.push import send_push
from app.channels.whatsapp import send_whatsapp

from app.queue.producer import publish
from app.queue.schemas import NotifyPayload

router = APIRouter(
    prefix="/notify",
    tags=["notify"],
)


# REQUEST MODELS


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



# SINGLE SEND


@router.post("/send")
async def send_single(body: SingleSendRequest):
    """
    Send notification immediately.

    No RabbitMQ.
    No worker.
    Direct send.
    """

    try:

        match body.channel:

           
            # EMAIL
          

            case "email":

                msg_id = await send_email(
                    to=body.recipient,
                    subject=body.subject or "",
                    body=body.body,
                    html_body=body.html_body,
                )

           
            # SMS
          

            case "sms":

                msg_id = send_sms(
                    to=body.recipient,
                    body=body.body,
                )

            # PUSH
            

            case "push":

                msg_id = send_push(
                    device_token=body.recipient,
                    title=body.title or "CixioHub",
                    body=body.body,
                    data=body.data,
                )

           
            # WHATSAPP
         

            case "whatsapp":

                msg_id = send_whatsapp(
                    to=body.recipient,
                    body=body.body,
                )

         
            # INVALID CHANNEL
         

            case _:

                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown channel: {body.channel}",
                )

        return {
            "status": "sent",
            "message_id": msg_id,
        }

    except NotImplementedError as exc:

        raise HTTPException(
            status_code=501,
            detail=str(exc),
        )



# BULK SEND

@router.post("/bulk")
async def send_bulk(body: BulkSendRequest):

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
        "status": "queued",
    }


# JOB STATUS


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Placeholder for future DB-backed job tracking.
    """

    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": (
            "Implement notification_jobs table tracking"
        ),
    }