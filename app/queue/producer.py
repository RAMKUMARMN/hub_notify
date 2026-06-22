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
from app.queue.schemas import NotifyPayload, ALL_QUEUES, ALL_DLQS

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
    """
    Declare all primary queues and their dead-letter queues (DLQs).

    Call once at application startup (e.g. in a FastAPI lifespan handler).
    Each primary queue is configured with a dead-letter exchange so that
    messages exceeding max retries are automatically routed to the
    corresponding "<queue>.dlq" queue instead of being discarded.

    Queue layout
    ─────────────
      Primary queue  ──(on reject/expire)──►  DLX exchange  ──►  <queue>.dlq

    The DLX (dead-letter exchange) is a simple direct exchange.
    """
    global _channel

    connection = await _get_connection()
    _channel = await connection.channel()

    # Name of the dead-letter exchange shared by all primary queues.
    dlx_name = "dlx"

    # Declare the single DLX that all primary queues point to.
    dlx = await _channel.declare_exchange(
        dlx_name,
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )

    for queue_name in ALL_QUEUES:
        dlq_name = f"{queue_name}.dlq"

        # 1. Declare the DLQ first (must exist before the primary queue
        #    tries to route rejected messages to it).
        dlq = await _channel.declare_queue(dlq_name, durable=True)

        # Bind the DLQ to the DLX using the primary queue name as the
        # routing key — that is what RabbitMQ uses when re-routing.
        await dlq.bind(dlx, routing_key=queue_name)

        # 2. Declare the primary queue with dead-letter routing arguments.
        await _channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                # Route rejected/expired messages to the DLX.
                "x-dead-letter-exchange": dlx_name,
                # Use the queue's own name as routing key so messages land
                # on the correct per-queue DLQ.
                "x-dead-letter-routing-key": queue_name,
            },
        )


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