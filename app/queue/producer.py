"""
RabbitMQ producer — publishes notification tasks from the backend API.

Called by the backend (admin bulk create, notification endpoints)
to enqueue tasks.
"""

import aio_pika

from app.config import settings
from app.queue.schemas import NotifyPayload

QUEUE_NAMES = {
    "email": "email.process",
    "sms": "sms.process",
    "push": "push.process",
    "whatsapp": "push.process",  # shares push queue for now
}


async def publish(
    payload: NotifyPayload, routing_key: str | None = None
) -> None:
    """Publish a single notification task to the appropriate RabbitMQ queue."""
    queue_name = routing_key or QUEUE_NAMES.get(payload.channel)
    if not queue_name:
        raise ValueError(f"Unknown channel: {payload.channel}")

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()

        arguments = None
        if ".retry." in queue_name:
            parts = queue_name.split(".")
            try:
                delay_str = parts[-1].replace("s", "")
                delay_sec = int(delay_str)
                base_channel = parts[0]
                arguments = {
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": f"{base_channel}.process",
                    "x-message-ttl": delay_sec * 1000,
                }
            except Exception:
                pass

        queue = await channel.declare_queue(
            queue_name, durable=True, arguments=arguments
        )
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=payload.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )


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
    )
    await publish(payload)
