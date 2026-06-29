"""
RabbitMQ producer — publishes notification tasks from the backend API.

Called by the backend (admin bulk create, notification endpoints)
to enqueue tasks.
"""

import asyncio
import aio_pika

from app.config import settings
from app.queue.schemas import NotifyPayload

QUEUE_NAMES = {
    "email": "email.process",
    "sms": "sms.process",
    "push": "push.process",
    "whatsapp": "whatsapp.process",
}


async def publish(
    payload: NotifyPayload, routing_key: str | None = None
) -> None:
    """Publish notification task to RabbitMQ with publisher retries."""
    import logging
    logger = logging.getLogger(__name__)

    max_publish_attempts = 4
    for attempt in range(1, max_publish_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()

                # Declare main direct exchange
                exchange = await channel.declare_exchange(
                    "notification.exchange",
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )

                # Declare Dead Letter Exchange (DLX)
                await channel.declare_exchange(
                    "dla.exchange",
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )

                priority = payload.priority
                if priority not in ("high", "medium", "low"):
                    priority = "high"

                if routing_key:
                    # Parse delay and declare retry queue
                    arguments = None
                    if ".retry." in routing_key:
                        parts = routing_key.split(".")
                        try:
                            delay_str = parts[-1].replace("s", "")
                            delay_sec = int(delay_str)
                            base_channel = parts[0]
                            rt_key = f"{base_channel}.process"
                            arguments = {
                                "x-dead-letter-exchange": "",
                                "x-dead-letter-routing-key": rt_key,
                                "x-message-ttl": delay_sec * 1000,
                            }
                        except Exception:
                            arguments = None

                    # Declare the retry queue
                    queue = await channel.declare_queue(
                        routing_key, durable=True, arguments=arguments
                    )
                    # Publish to the retry queue
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=payload.model_dump_json().encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key=queue.name,
                    )
                else:
                    # Publish to the main exchange with priority routing key
                    # Format must strictly match notification_queues.md (no job_id, notification_id, etc.)
                    allowed_fields = {
                        "channel",
                        "recipient",
                        "subject",
                        "body",
                        "html_body",
                        "title",
                        "message_type",
                        "priority",
                        "data",
                    }
                    priority_payload = payload.model_dump(include=allowed_fields)
                    if not priority_payload.get("title"):
                        priority_payload["title"] = payload.subject
                    if priority_payload.get("data") is None:
                        priority_payload["data"] = {}
                    
                    import json
                    await exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(priority_payload).encode("utf-8"),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key=priority,
                    )
            # If we reached here, publishing succeeded!
            return
        except Exception as exc:
            if attempt == max_publish_attempts:
                logger.error(
                    "Failed to publish message after %d attempts: %s",
                    max_publish_attempts,
                    exc,
                )
                raise exc
            backoff = (2 ** attempt) * 0.1
            logger.warning(
                "Publish attempt %d failed: %s. Retrying in %.2f seconds...",
                attempt,
                exc,
                backoff,
            )
            await asyncio.sleep(backoff)


async def publish_notification(
    notification,
    channel: str | None = None,
    db=None,
) -> None:
    """Publish an IndividualNotification to the appropriate RabbitMQ queue.

    If channel is not specified, it will be fetched from the
    corresponding NotificationJob in the database.
    """
    if not channel:
        if not db:
            raise ValueError(
                "Either channel or db must be provided to "
                "publish_notification"
            )
        from app.models import NotificationJob
        job = await db.get(NotificationJob, notification.job_id)
        if not job:
            raise ValueError(
                f"NotificationJob not found for job_id: "
                f"{notification.job_id}"
            )
        channel = job.channel

    payload = NotifyPayload(
        notification_id=notification.id,
        job_id=notification.job_id,
        channel=channel,
        recipient=notification.recipient,
        subject=notification.subject,
        body=notification.body,
        html_body=notification.html_body,
        title=notification.title,
        data=notification.data,
        attempt=notification.attempt,
        priority=getattr(notification, "priority", "high"),
        message_type=getattr(notification, "message_type", "general"),
    )
    routing_key = QUEUE_NAMES.get(channel)
    await publish(payload, routing_key=routing_key)
