from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# EMAIL

EMAIL_PROCESS_QUEUE = "email.process"

EMAIL_RETRY_1M = "email.retry.1m"
EMAIL_RETRY_5M = "email.retry.5m"
EMAIL_RETRY_30M = "email.retry.30m"

EMAIL_DLQ = "email.process.dlq"


SMS_PROCESS_QUEUE = "sms.process"
SMS_RETRY_1M = "sms.retry.1m"
SMS_RETRY_5M = "sms.retry.5m"
SMS_RETRY_30M = "sms.retry.30m"
SMS_DLQ = "sms.process.dlq"


PUSH_PROCESS_QUEUE = "push.process"
PUSH_RETRY_1M = "push.retry.1m"
PUSH_RETRY_5M = "push.retry.5m"
PUSH_RETRY_30M = "push.retry.30m"
PUSH_DLQ= "push.process.dlq"



WHATSAPP_PROCESS_QUEUE = "whatsapp.process"
WHATSAPP_RETRY_1M = "whatsapp.retry.1m"
WHATSAPP_RETRY_5M = "whatsapp.retry.5m"
WHATSAPP_RETRY_30M = "whatsapp.retry.30m"
WHATSAPP_DLQ= "whatsapp.process.dlq"

FILE_UPLOAD_QUEUE = "file.uploads"

RAG_BULK_INGEST_QUEUE = "rag.bulk_ingest"

EMBEDDING_PROCESS_QUEUE = "embedding.process"

MEMORY_PROCESSING_QUEUE = "memory.processing"

AI_ORCHESTRATION_QUEUE = "ai.orchestration"


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

   
   
     "file_upload": FILE_UPLOAD_QUEUE,

    "rag_bulk_ingest": RAG_BULK_INGEST_QUEUE,

    "embedding_process": EMBEDDING_PROCESS_QUEUE,

    "memory_processing": MEMORY_PROCESSING_QUEUE,

    "ai_orchestration": AI_ORCHESTRATION_QUEUE,
    

}
# All primary queues. For every queue here, a matching DLQ
# ("<queue>.dlq") must also be declared — see producer.py.
ALL_QUEUES = [

    # EMAIL
   
 EMAIL_PROCESS_QUEUE, 

 EMAIL_DLQ,
   
    # SMS
SMS_PROCESS_QUEUE,

SMS_DLQ,

    # PUSH
   
PUSH_PROCESS_QUEUE,

PUSH_DLQ,

    # WHATSAPP
   
WHATSAPP_PROCESS_QUEUE,

WHATSAPP_DLQ,
 
FILE_UPLOAD_QUEUE,
RAG_BULK_INGEST_QUEUE,
EMBEDDING_PROCESS_QUEUE,
MEMORY_PROCESSING_QUEUE,
AI_ORCHESTRATION_QUEUE,
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


class FileUploadPayload(BaseModel):
    document_id: str
    file_path: str
    user_id: str


class RAGPayload(BaseModel):
    document_id: str
    text: str


class EmbeddingPayload(BaseModel):
    document_id: str
    chunks: list[str]


class MemoryPayload(BaseModel):
    document_id: str


class AIOrchestrationPayload(BaseModel):
    task_type: str
    payload: dict[str, Any]