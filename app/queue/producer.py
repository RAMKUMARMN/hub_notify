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
    "whatsapp": "push.process",
      "notify.bulk_email": "notify.bulk_email",
        "ai_orchestration":"ai_orchestration",
          "analytics.events":"analytics.events" ,
           "embedding_process":"embedding_process",
            "file_uploads":"file_uploads",
             "memory.processing": "memory.processing"  ,
             "notify.bulk_sms": "notify.bulk_sms",
             "rag.bulk_ingest": "rag.bulk_ingest" ,
               # shares push queue for now
             # shares push queue for now
}


async def publish(payload: NotifyPayload) -> None:
    """Publish a single notification task to the appropriate RabbitMQ queue."""
    queue_name = QUEUE_NAMES.get(payload.channel)
    if not queue_name:
        raise ValueError(f"Unknown channel: {payload.channel}")

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=payload.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
