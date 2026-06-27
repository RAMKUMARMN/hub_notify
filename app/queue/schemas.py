from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

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

# =========================================================
# FILE PIPELINE
# =========================================================


FILE_UPLOAD_QUEUE = "file.uploads"

FILE_RETRY_1M = "file.retry.1m"
FILE_RETRY_5M = "file.retry.5m"
FILE_RETRY_30M = "file.retry.30m"

FILE_UPLOAD_DLQ = "file.uploads.dlq"

# =========================================================
# DOCUMENT PIPELINE
# =========================================================

DOC_EXTRACT_QUEUE = "doc.extract"
DOC_EXTRACT_DLQ = "doc.extract.dlq"

DOC_CHUNK_QUEUE = "doc.chunk"
DOC_CHUNK_DLQ = "doc.chunk.dlq"

EMBEDDING_QUEUE = "embedding.generate"
EMBEDDING_DLQ = "embedding.generate.dlq"

VECTOR_INDEX_QUEUE = "vector.index"
VECTOR_INDEX_DLQ = "vector.index.dlq"

# =========================================================
# RAG PIPELINE
# =========================================================

RAG_QUERY_QUEUE = "rag.query"
RAG_QUERY_DLQ = "rag.query.dlq"

RAG_RETRIEVAL_QUEUE = "rag.retrieve"
RAG_RETRIEVAL_DLQ = "rag.retrieve.dlq"

# =========================================================
# MEMORY PIPELINE
# =========================================================

MEMORY_PROCESS_QUEUE = "memory.process"
MEMORY_PROCESS_DLQ = "memory.process.dlq"

MEMORY_SUMMARY_QUEUE = "memory.summary"
MEMORY_SUMMARY_DLQ = "memory.summary.dlq"

# =========================================================
# AI ORCHESTRATION
# =========================================================

AI_ORCHESTRATION_QUEUE = "ai.orchestration"
AI_ORCHESTRATION_DLQ = "ai.orchestration.dlq"

MODEL_ROUTER_QUEUE = "model.router"
MODEL_ROUTER_DLQ = "model.router.dlq"

# =========================================================
# ANALYTICS
# =========================================================

ANALYTICS_EVENTS_QUEUE = "analytics.events"
ANALYTICS_EVENTS_DLQ = "analytics.events.dlq"

# =========================================================
# AUTOMATION / WORKFLOW
# =========================================================

AUTOMATION_TRIGGER_QUEUE = "automation.trigger"
AUTOMATION_TRIGGER_DLQ = "automation.trigger.dlq"



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
 

    # FILE
    FILE_UPLOAD_QUEUE,
FILE_RETRY_1M,
FILE_RETRY_5M,
FILE_RETRY_30M,
FILE_UPLOAD_DLQ ,

    # DOC
    DOC_EXTRACT_QUEUE,
    DOC_CHUNK_QUEUE,
    EMBEDDING_QUEUE,
    VECTOR_INDEX_QUEUE,

    # RAG
    RAG_QUERY_QUEUE,
    RAG_RETRIEVAL_QUEUE,

    # MEMORY
    MEMORY_PROCESS_QUEUE,
    MEMORY_SUMMARY_QUEUE,

    # AI
    AI_ORCHESTRATION_QUEUE,
    MODEL_ROUTER_QUEUE,

    # ANALYTICS
    ANALYTICS_EVENTS_QUEUE,

    # AUTOMATION
    AUTOMATION_TRIGGER_QUEUE,
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

# =========================================================
# FILE PAYLOAD
# =========================================================

class FileUploadPayload(BaseModel):

    document_id: str

    filename: str

    file_type: str

    file_size: int

    storage_path: str

    uploaded_by: str | None = None

    attempt: int = 1

class ChunkPayload(BaseModel):


    document_id: str
    text: str
    attempt: int = 1

class EmbeddingPayload(BaseModel):

    document_id: str

    chunk_index: int

    chunk_text: str

    attempt: int = 1
class EmbeddingPayload(BaseModel):


   document_id: str

   chunk_index: int

   chunk_text: str

   attempt: int = 1

# =========================================================

# EMBEDDING PAYLOAD

# =========================================================

class EmbeddingPayload(BaseModel):

   document_id: str

   chunk_index: int

   chunk_text: str

   attempt: int = 1

# =========================================================

# VECTOR INDEX PAYLOAD

# =========================================================

class VectorIndexPayload(BaseModel):

   document_id: str

   chunk_index: int

   chunk_text: str

   embedding: list[float]

   attempt: int = 1




class AIOrchestrationPayload(BaseModel):
    task_type: str
    payload: dict[str, Any]
