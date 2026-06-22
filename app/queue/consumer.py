"""
RabbitMQ consumer worker — dispatches notifications from the queue.

Run with: python -m app.queue.worker

Queue architecture
------------------
  Each primary queue (email.process, sms.process, …) is bound to a DLX so
  that messages rejected after max retries land in "<queue>.dlq" automatically.
  This worker consumes both primary and DLQ queues.

  Primary:  email.process  sms.process  push.process  …
  DLQ:      email.process.dlq  sms.process.dlq  …  (dead-letter inspection)
"""
import asyncio
import json
import logging
import os
import sys

import aio_pika

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)
sys.path.insert(0, BASE_DIR)

from app.channels.email import send_email
from app.channels.sms import send_sms
from app.channels.push import send_push
from app.channels.whatsapp import send_whatsapp
from app.config import settings
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload, JobStatus, ALL_QUEUES, ALL_DLQS
from app.queue.job_store import job_store
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.notification_job import NotificationJob

logger = logging.getLogger(__name__)

# Delay in seconds before each retry attempt.
# Attempt 1 = immediate (no delay), 2 = 1 min, 3 = 5 min, 4 = 30 min.
RETRY_DELAYS = {1: 0, 2: 60, 3: 300, 4: 1800}

# Only these queues carry NotifyPayload — the generic job queues (ai_orchestration,
# embedding_process, etc.) have their own dedicated workers and are not consumed here.
NOTIFY_QUEUES = [
    "email.process",
    "sms.process",
    "push.process",
    "whatsapp.process",
    "notify.bulk_email",
    "notify.bulk_sms",
]

# DLQs for the notification queues — consumed for visibility/alerting only.
NOTIFY_DLQS = [f"{q}.dlq" for q in NOTIFY_QUEUES]


# ── Database helpers ──────────────────────────────────────────────────────────

async def _get_job(session, job_id: str) -> NotificationJob | None:
    """Fetch a NotificationJob row by id, or return None if missing."""
    result = await session.execute(
        select(NotificationJob).where(NotificationJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def increment_sent(job_id: str) -> None:
    """Increment the sent counter; mark job completed if all items are done."""
    async with AsyncSessionLocal() as session:
        job = await _get_job(session, job_id)
        if not job:
            return
        job.sent += 1
        if (job.sent + job.failed) >= job.total:
            job.completed = True
        await session.commit()


async def increment_failed(job_id: str) -> None:
    """Increment the failed counter; mark job completed if all items are done."""
    async with AsyncSessionLocal() as session:
        job = await _get_job(session, job_id)
        if not job:
            return
        job.failed += 1
        if (job.sent + job.failed) >= job.total:
            job.completed = True
        await session.commit()


async def increment_retrying(job_id: str) -> None:
    """Increment the retrying counter (does not affect completion check)."""
    async with AsyncSessionLocal() as session:
        job = await _get_job(session, job_id)
        if not job:
            return
        job.retrying += 1
        await session.commit()


# ── Dispatch ──────────────────────────────────────────────────────────────────

async def dispatch(payload: NotifyPayload) -> None:
    """Route the payload to the correct channel sender."""
    match payload.channel:
        case "email":
            await send_email(
                to=payload.recipient,
                subject=payload.subject or "",
                body=payload.body,
                html_body=payload.html_body,
            )
        case "sms":
            send_sms(to=payload.recipient, body=payload.body)
        case "push":
            send_push(
                device_token=payload.recipient,
                title=payload.title or "CixioHub",
                body=payload.body,
                data=payload.data,
            )
        case "whatsapp":
            send_whatsapp(to=payload.recipient, body=payload.body)
        case _:
            raise ValueError(f"Unknown channel: {payload.channel!r}")


async def retry_with_delay(payload: NotifyPayload) -> None:
    """
    Sleep for the retry back-off period, then re-publish the message.

    The attempt counter is incremented before re-publishing so the next
    consumer picks up the correct attempt number and delay.
    """
    delay = RETRY_DELAYS.get(payload.attempt, 0)
    if delay > 0:
        logger.info(
            "Retrying job %s in %ds (attempt %d → %d)",
            payload.job_id, delay, payload.attempt, payload.attempt + 1,
        )
        await asyncio.sleep(delay)

    payload.attempt += 1
    await publish(payload)


# ── Message handlers ──────────────────────────────────────────────────────────

async def process_message(message: aio_pika.IncomingMessage) -> None:
    """
    Primary queue handler — dispatch notification and handle retries.

    On success  → increments sent counter, marks job DONE in job_store.
    On failure  → retries up to max_attempts with back-off delay;
                  after final failure increments failed counter and marks FAILED.
                  RabbitMQ DLX then routes the message to <queue>.dlq automatically.
    """
    async with message.process(requeue=False):
        payload = NotifyPayload(**json.loads(message.body))#converts queue message back into Python object:

        try:
            await job_store.update(
                payload.job_id,
                JobStatus.PROCESSING,
                message=f"Sending {payload.channel} notification",
            )
            await dispatch(payload)
            await increment_sent(payload.job_id)
            await job_store.update(
                payload.job_id,
                JobStatus.DONE,
                message=f"{payload.channel} notification sent",
            )
            logger.info(
                "Sent %s to %s (job %s)",
                payload.channel, payload.recipient, payload.job_id,
            )

        except Exception as exc:
            logger.warning(
                "Failed attempt %d for job %s: %s",
                payload.attempt, payload.job_id, exc,
            )
            if payload.attempt < payload.max_attempts:
                # Not yet exhausted — schedule a retry.
                await increment_retrying(payload.job_id)
                await retry_with_delay(payload)
            else:
                # All attempts exhausted — mark as permanently failed.
                # RabbitMQ will route this message to the DLQ via the DLX.
                await increment_failed(payload.job_id)
                await job_store.update(
                    payload.job_id,
                    JobStatus.FAILED,
                    message=str(exc),
                )
                logger.error(
                    "Permanently failed job %s channel %s — routed to DLQ",
                    payload.job_id, payload.channel,
                )


async def process_dlq_message(message: aio_pika.IncomingMessage) -> None:
    """
    Dead-letter queue handler — log and acknowledge without re-dispatching.

    Messages arrive here after exhausting all retries on the primary queue.
    Extend this handler to: alert on-call, write to a dead_letters DB table,
    or trigger a human-review workflow.
    """
    async with message.process(requeue=False):
        try:
            # x-death header added by RabbitMQ — tells us the origin queue
            # and how many times the message was dead-lettered.
            x_death = message.headers.get("x-death", [])
            origin_queue = x_death[0].get("queue", "unknown") if x_death else "unknown"
            death_count = x_death[0].get("count", 1) if x_death else 1

            body = json.loads(message.body)
            logger.error(
                "DLQ message from %s (dead %dx): job_id=%s channel=%s recipient=%s",
                origin_queue,
                death_count,
                body.get("job_id"),
                body.get("channel"),
                body.get("recipient"),
            )
            # TODO: insert into dead_letters table or fire an alert here.

        except Exception as exc:
            # Never crash the DLQ consumer — bad messages should still be acked.
            logger.exception("Error processing DLQ message: %s", exc)


# ── Consumer entry-point ──────────────────────────────────────────────────────

async def run_consumer() -> None:
    """
    Start the notification worker.

    Consumes all NOTIFY_QUEUES for live dispatch and all NOTIFY_DLQS
    for dead-letter visibility. Queues are declared here with the same
    DLX arguments used in producer.setup_queues() so the worker can
    also run standalone without a prior setup_queues() call.
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url) #opens connection to RabbitMQ server.
    async with connection:
        channel = await connection.channel() #Consumer creates channel
        # Limit in-flight messages per worker instance to avoid overload.
        await channel.set_qos(prefetch_count=10)

        dlx_name = "dlx"

        # Declare the shared DLX (idempotent — safe to re-declare).
        dlx = await channel.declare_exchange(
            dlx_name,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        # Declare and subscribe to each primary notification queue.
        for queue_name in NOTIFY_QUEUES:
            dlq_name = f"{queue_name}.dlq"

            # DLQ must be declared and bound before the primary queue
            # so RabbitMQ has somewhere to route rejected messages.
            dlq = await channel.declare_queue(dlq_name, durable=True)
            await dlq.bind(dlx, routing_key=queue_name)

            # Primary queue — messages rejected here go to dlx → dlq.
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": dlx_name,
                    "x-dead-letter-routing-key": queue_name,
                },
            )
            await queue.consume(process_message)
            logger.info("Consuming primary queue: %s", queue_name)

        # Subscribe to DLQs for visibility (no re-dispatch).
        for dlq_name in NOTIFY_DLQS:
            dlq = await channel.declare_queue(dlq_name, durable=True)
            await dlq.consume(process_dlq_message)
            logger.info("Consuming DLQ: %s", dlq_name)

        logger.info("Notify worker started — waiting for messages.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_consumer())