from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

EMAIL_PROCESS_QUEUE = "email.process"
EMAIL_RETRY_QUEUE = "email.retry"
EMAIL_FAILED_QUEUE = "email.failed"


SMS_PROCESS_QUEUE = "sms.process"
SMS_RETRY_QUEUE = "sms.retry"
SMS_FAILED_QUEUE = "sms.failed"

PUSH_PROCESS_QUEUE = "push.process"
PUSH_RETRY_QUEUE = "push.retry"
PUSH_FAILED_QUEUE = "push.failed"

WHATSAPP_PROCESS_QUEUE = "whatsapp.process"
WHATSAPP_RETRY_QUEUE = "whatsapp.retry"
WHATSAPP_FAILED_QUEUE = "whatsapp.failed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobType(str, Enum):
    FILE_UPLOAD = "file_upload"
    RAG_BULK_INGEST = "rag_bulk_ingest"
    BULK_EMAIL = "bulk_email"
    BULK_SMS = "bulk_sms"
    ANALYTICS = "analytics"
    BULK_PUSH = "bulk_push"
    # New job types
    AI_ORCHESTRATION = "ai_orchestration"
    EMBEDDING_PROCESS = "embedding_process"
    MEMORY_PROCESSING = "memory_processing"
    WHATSAPP = "whatsapp"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


# Maps job/channel type → primary queue name.
# Each queue also has a corresponding DLQ named with a ".dlq" suffix
# (e.g. "file.uploads" → DLQ is "file.uploads.dlq").
QUEUE_FOR_TYPE: dict[str, str] = {

     "email": EMAIL_PROCESS_QUEUE,
    "sms": SMS_PROCESS_QUEUE,
    "push": PUSH_PROCESS_QUEUE,
    "whatsapp": WHATSAPP_PROCESS_QUEUE,

    "bulk_email": EMAIL_PROCESS_QUEUE,
    "bulk_sms": SMS_PROCESS_QUEUE,
    "bulk_push": PUSH_PROCESS_QUEUE,

    # Single notification queues
   

    

    # File handling
    "file_upload": "file.uploads",

    # RAG / ML
    "rag_bulk_ingest": "rag.bulk_ingest",
    "embedding_process": "embedding_process",
    "memory_processing": "memory.processing",
    "ai_orchestration": "ai_orchestration",

    # Analytics
    "analytics": "analytics.events",
}
# All primary queues. For every queue here, a matching DLQ
# ("<queue>.dlq") must also be declared — see producer.py.
ALL_QUEUES = [

    # EMAIL
   
  EMAIL_PROCESS_QUEUE,
  EMAIL_RETRY_QUEUE,
  EMAIL_FAILED_QUEUE,
   
    # SMS
  SMS_PROCESS_QUEUE,
    SMS_RETRY_QUEUE,
    SMS_FAILED_QUEUE,

    # PUSH
   
    PUSH_PROCESS_QUEUE,
    PUSH_RETRY_QUEUE,
    PUSH_FAILED_QUEUE,

  
    # WHATSAPP
   
    WHATSAPP_PROCESS_QUEUE,
    WHATSAPP_RETRY_QUEUE,
    WHATSAPP_FAILED_QUEUE,

   
    # FILES
   
    "file.uploads",

  
    # RAG / ML
   
    "rag.bulk_ingest",
    "embedding_process",
    "memory.processing",
    "ai_orchestration",

  
    # ANALYTICS
  
    "analytics.events",
]

# Dead-letter queues (DLQs) — messages are routed here automatically
# after exhausting retries on their primary queue. Declared alongside
# primary queues so they exist before any consumer starts.
ALL_DLQS = [f"{q}.dlq" for q in ALL_QUEUES]


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


# ── Legacy payload (backward compat with existing notify router) ──────────────

class NotifyPayload(BaseModel):
    """A single notification task — published to RabbitMQ as JSON."""
    job_id: str
    channel: str            # 'email' | 'sms' | 'push' | 'whatsapp'
    recipient: str          # email address, phone number, or FCM token
    subject: str | None = None
    body: str = ""
    html_body: str | None = None
    title: str | None = None    # for push notifications
    data: dict | None = None    # for push notification data payload
    attempt: int = 1
    max_attempts: int = 4