"""
RabbitMQ producer — publishes notification/job tasks from the backend API.

Called by the backend (admin bulk create, notification endpoints) to enqueue tasks.

Connection management
---------------------
  A new TCP connection per publish() call is too expensive for high-throughput
  workloads.  Use get_channel() to obtain a shared channel, or call
  setup_queues() once at app startup to pre-declare all queues, then reuse the
  module-level _channel for publishing.
"""
import json

import aio_pika
from aio_pika.abc import AbstractChannel

from app.config import settings
from app.queue.schemas import NotifyPayload, ALL_QUEUES

# ── Queue name maps ───────────────────────────────────────────────────────────

# Maps notification channel → primary queue.
QUEUE_NAMES: dict[str, str] = {
    "email":     "email.process",
    "sms":       "sms.process",
    "push":      "push.process",
    "whatsapp":  "whatsapp.process",  
     
}

# ── Module-level shared connection / channel ──────────────────────────────────
# Populated by setup_queues(); reused by publish() to avoid per-call reconnects.

_channel: AbstractChannel | None = None


async def _get_connection() -> aio_pika.RobustConnection:
    """Return a robust (auto-reconnecting) RabbitMQ connection."""
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def setup_queues() -> None:

    global _channel

    connection = await _get_connection()
    _channel = await connection.channel()

    # -------------------------------------------------
    # DECLARE MAIN PROCESS QUEUES
    # -------------------------------------------------

    process_queues = [
        "email.process",
        "sms.process",
        "push.process",
        "whatsapp.process",
        "file.uploads",
    ]

    # -------------------------------------------------
    # DECLARE DLQs
    # -------------------------------------------------

    for queue_name in process_queues:

        dlq_name = f"{queue_name}.dlq"

        # MAIN PROCESS QUEUE
        await _channel.declare_queue(
            queue_name,
            durable=True,
        )

        # FINAL DEAD LETTER QUEUE
        await _channel.declare_queue(
            dlq_name,
            durable=True,
        )

        # -------------------------------------------------
# FILE PROCESS QUEUE
# -------------------------------------------------

    await _channel.declare_queue(
    "file.uploads",
    durable=True,
)

    await _channel.declare_queue(
    "file.process.dlq",
    durable=True,
)

    # -------------------------------------------------
    # EMAIL RETRY QUEUES
    # -------------------------------------------------

    await _channel.declare_queue(
        "email.retry.1m",
        durable=True,
        arguments={
            "x-message-ttl": 60000,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "email.process",
        },
    )

    await _channel.declare_queue(
        "email.retry.5m",
        durable=True,
        arguments={
            "x-message-ttl": 300000,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "email.process",
        },
    )

    await _channel.declare_queue(
        "email.retry.30m",
        durable=True,
        arguments={
            "x-message-ttl": 1800000,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "email.process",
        },
    )

    # -------------------------------------------------
    # SMS RETRY QUEUES
    # -------------------------------------------------
    # -------------------------------------------------
# SMS RETRY QUEUES
# -------------------------------------------------

    await _channel.declare_queue(
    "sms.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "sms.process",
    },
)

    await _channel.declare_queue(
    "sms.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "sms.process",
    },
)

    await _channel.declare_queue(
    "sms.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "sms.process",
    },
)
    

    # -------------------------------------------------
# PUSH RETRY QUEUES
# -------------------------------------------------

    await _channel.declare_queue(
    "push.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "push.process",
    },
)

    await _channel.declare_queue(
    "push.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "push.process",
    },
)

    await _channel.declare_queue(
    "push.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "push.process",
    },
)
    

    # -------------------------------------------------
# WHATSAPP RETRY QUEUES
# -------------------------------------------------

    await _channel.declare_queue(
    "whatsapp.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "whatsapp.process",
    },
)

    await _channel.declare_queue(
    "whatsapp.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "whatsapp.process",
    },
)

    await _channel.declare_queue(
    "whatsapp.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "whatsapp.process",
    },
)
    # -------------------------------------------------
# FILE RETRY QUEUES
# -------------------------------------------------

    await _channel.declare_queue(
    "file.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "file.uploads",
    },
)

    await _channel.declare_queue(
    "file.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "file.uploads",
    },
)

    await _channel.declare_queue(
    "file.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "file.uploads",
    },
)
    

# DOC EXTRACT

    await _channel.declare_queue(
    "doc.extract",
    durable=True,
)

    await _channel.declare_queue(
    "doc.extract.dlq",
    durable=True,
)

    # =====================================================
# DOC EXTRACT RETRY QUEUES
# =====================================================

    await _channel.declare_queue(
    "doc.extract.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.extract",
    },
)

    await _channel.declare_queue(
    "doc.extract.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.extract",
    },
)

    await _channel.declare_queue(
    "doc.extract.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.extract",
    },
)
# DOC CHUNK

    await _channel.declare_queue(
        "doc.chunk",
    durable=True,
)

    await _channel.declare_queue(
    "doc.chunk.dlq",
    durable=True,
)  
    await _channel.declare_queue(
    "doc.chunk.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.chunk",
    },
)

    await _channel.declare_queue(
    "doc.chunk.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.chunk",
    },
)

    await _channel.declare_queue(
    "doc.chunk.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "doc.chunk",
    },
)
    
    # =====================================================
# EMBEDDING RETRY QUEUES
# =====================================================

    await _channel.declare_queue(
    "embedding.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "embedding.generate",
    },
)

    await _channel.declare_queue(
    "embedding.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "embedding.generate",
    },
)

    await _channel.declare_queue(
    "embedding.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "embedding.generate",
    },
)

# =====================================================
# VECTOR RETRY QUEUES
# =====================================================

    await _channel.declare_queue(
    "vector.retry.1m",
    durable=True,
    arguments={
        "x-message-ttl": 60000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "vector.index",
    },
)

    await _channel.declare_queue(
    "vector.retry.5m",
    durable=True,
    arguments={
        "x-message-ttl": 300000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "vector.index",
    },
)

    await _channel.declare_queue(
    "vector.retry.30m",
    durable=True,
    arguments={
        "x-message-ttl": 1800000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "vector.index",
    },
) 
    # =====================================================
# EMBEDDING QUEUES
# =====================================================

    await _channel.declare_queue(
    "embedding.generate",
    durable=True,
)

    await _channel.declare_queue(
    "embedding.generate.dlq",
    durable=True,
)
    # =========================================================
# VECTOR QUEUES
# =========================================================

    await _channel.declare_queue(
    "vector.index",
    durable=True,
)

    await _channel.declare_queue(
    "vector.index.dlq",
    durable=True,
)
    
# =========================================================
# RAG QUEUES
# =========================================================

    await _channel.declare_queue(
    "rag.query",
    durable=True,
)

    await _channel.declare_queue(
    "rag.query.dlq",
    durable=True,
)

    await _channel.declare_queue(
    "rag.retrieve",
    durable=True,
)

    await _channel.declare_queue(
    "rag.retrieve.dlq",
    durable=True,
)
    # =========================================================
# MEMORY QUEUES
# =========================================================

    await _channel.declare_queue(
    "memory.process",
    durable=True,
)

    await _channel.declare_queue(
    "memory.process.dlq",
    durable=True,
)
    await _channel.declare_queue(
    "ai.orchestration",
    durable=True,
)

    await _channel.declare_queue(
    "ai.orchestration.dlq",
    durable=True,
)
    await _channel.declare_queue(
    "automation.trigger",
    durable=True,
)

    await _channel.declare_queue(
    "automation.trigger.dlq",
    durable=True,
)
    print("RabbitMQ queues initialized")

async def publish(payload: NotifyPayload) -> None:
    """
    Publish a single notification task to the appropriate RabbitMQ queue.

    Reuses the shared channel created by setup_queues() when available;
    falls back to a fresh connection if called before startup (e.g. in tests).
    """
    global _channel

    queue_name = QUEUE_NAMES.get(payload.channel)
    if not queue_name:
        raise ValueError(f"Unknown channel: {payload.channel!r}")

    message = aio_pika.Message(
        body=payload.model_dump_json().encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )

    if _channel is not None and not _channel.is_closed:
        # Fast path — reuse the shared channel from setup_queues().
        await _channel.default_exchange.publish(message, routing_key=queue_name)
        print(f"PUBLISHING TO QUEUE: {queue_name}")
        return

    # Slow path — create a temporary connection (e.g. during tests or before
    # startup).  A new connection per call is expensive; avoid in production.
    connection = await _get_connection()
    async with connection:
        ch = await connection.channel()
        await ch.default_exchange.publish(message, routing_key=queue_name)


async def publish_to_queue(queue_name: str, body: dict) -> None:
    """
    Low-level helper — publish an arbitrary dict payload to any named queue.

    Useful for job types beyond the legacy notify channels (e.g. file_uploads,
    ai_orchestration, embedding_process, memory.processing, analytics.events).

    Example
    -------
        await publish_to_queue("ai_orchestration", {"task": "summarise", "doc_id": "abc"})
    """
    global _channel

    message = aio_pika.Message(
        body=json.dumps(body).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )

    if _channel is not None and not _channel.is_closed:
        await _channel.default_exchange.publish(message, routing_key=queue_name)
        return

    connection = await _get_connection()
    async with connection:
        ch = await connection.channel()
        await ch.default_exchange.publish(message, routing_key=queue_name)
