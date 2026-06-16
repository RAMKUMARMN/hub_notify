"""
RabbitMQ producer — publishes notification tasks from the backend API.

Called by the backend (admin bulk create, notification endpoints) to enqueue tasks.
"""
import json

import aio_pika

from app.config import settings
from app.queue.schemas import NotifyPayload

QUEUE_NAMES = {
    "email": "email.process",
    "sms": "sms.process",
    "push": "push.process",
    "whatsapp": "push.process",  # shares push queue for now
}


async def publish(payload: NotifyPayload, routing_key: str | None = None) -> None:
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

        queue = await channel.declare_queue(queue_name, durable=True, arguments=arguments)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=payload.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
