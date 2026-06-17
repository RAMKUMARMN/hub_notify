from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobType(str, Enum):
    FILE_UPLOAD = "file_upload"
    RAG_BULK_INGEST = "rag_bulk_ingest"
    BULK_EMAIL = "bulk_email"
    BULK_SMS = "bulk_sms"
    ANALYTICS = "analytics"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


QUEUE_FOR_TYPE: dict[str, str] = {
    "file_upload":     "file.uploads",
    "rag_bulk_ingest": "rag.bulk_ingest",
    "bulk_email":      "notify.bulk_email",
    "bulk_sms":        "notify.bulk_sms",
    "analytics":       "analytics.events",
    "email":           "email.process",
    "sms":             "sms.process",
    "push":            "push.process",
}

ALL_QUEUES = [
    "file.uploads",
    "rag.bulk_ingest",
    "notify.bulk_email",
    "notify.bulk_sms",
    "analytics.events",
    "email.process",
    "sms.process",
    "push.process",
]


class Job(BaseModel):
    """Unified job model tracked across all queues."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType
    queue: str
    label: str = ""
    payload: dict = {}
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0       # 0–100
    message: str = ""
    total: int = 0          # total work items
    done_count: int = 0     # items completed so far
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class SubmitJobRequest(BaseModel):
    job_type: JobType
    label: str = ""
    payload: dict = {}


# ── Legacy payload (backward compat with existing notify router) ──────────

class NotifyPayload(BaseModel):
    """A single notification task — published to RabbitMQ as JSON."""
    job_id: str
    notification_id: str | None = None
    channel: str            # 'email' | 'sms' | 'push' | 'whatsapp'
    recipient: str          # email address, phone number, or FCM token
    subject: str | None = None
    body: str = ""
    html_body: str | None = None
    title: str | None = None    # for push notifications
    data: dict | None = None    # for push notification data payload
    attempt: int = 1
    max_attempts: int = 4
