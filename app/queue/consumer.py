"""
RabbitMQ consumer worker — dispatches notifications from the queue.

Run with: python -m app.queue.worker

Students: implement the retry delay logic and the actual channel dispatch.
"""
import asyncio
import json
import logging

import aio_pika

from app.channels.email import send_email
from app.channels.sms import send_sms
from app.channels.push import send_push
from app.channels.whatsapp import send_whatsapp
from app.config import settings
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload

# Configure logging at import time so log output appears regardless of
# whether this module is run directly (`python -m app.queue.consumer`)
# or imported and started as a background task inside uvicorn (main.py's
# lifespan). Previously this was only called inside `if __name__ == "__main__"`,
# which meant the embedded consumer (started via import) had no logging
# handler/level configured and silently dropped all INFO-level logs.
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

RETRY_DELAYS = {1: 0, 2: 60, 3: 300, 4: 1800}  # seconds before retry


async def dispatch(payload: NotifyPayload) -> None:
    """Call the correct channel sender based on payload.channel."""
    match payload.channel:
        case "email":
            await send_email(
                to=payload.recipient,
                subject=payload.subject or "",
                body=payload.body,
                html_body=payload.html_body,
            )
        case "sms":
            # Made this awaitable if send_sms is an async function in your project
            await send_sms(to=payload.recipient, body=payload.body)
        case "push":
            # Triggers your Firebase delivery logic using the saved FCM tokens!
            await send_push(
                device_token=payload.recipient,
                title=payload.title or "CixioHub",
                body=payload.body,
                data=payload.data,
            )
        case "whatsapp":
            await send_whatsapp(to=payload.recipient, body=payload.body)
        case _:
            raise ValueError(f"Unknown channel: {payload.channel}")


async def process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload = NotifyPayload(**json.loads(message.body))
        try:
            await dispatch(payload)
            logger.info("Sent %s to %s (job %s)", payload.channel, payload.recipient, payload.job_id)
            # TODO: update notification_jobs table — increment sent count
        except Exception as exc:
            logger.warning("Failed attempt %d for job %s: %s", payload.attempt, payload.job_id, exc)
            if payload.attempt < payload.max_attempts:
                # Get the targeted delay period from the mapping dictionary
                delay_seconds = RETRY_DELAYS.get(payload.attempt, 0)

                if delay_seconds > 0:
                    logger.info("Waiting %d seconds before re-queuing job %s...", delay_seconds, payload.job_id)
                    await asyncio.sleep(delay_seconds)

                # Re-enqueue with incremented attempt count
                payload.attempt += 1
                await publish(payload)
            else:
                logger.error("Permanently failed job %s channel %s", payload.job_id, payload.channel)
                # TODO: update notification_jobs table — increment failed count
                # TODO: publish to *.failed queue for investigation


async def run_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        # Added whatsapp.process here so it matches the channel dispatch cases
        for queue_name in ["email.process", "sms.process", "push.process", "whatsapp.process"]:
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.consume(process_message)

        logger.info("Notify worker started. Waiting for messages...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(run_consumer())