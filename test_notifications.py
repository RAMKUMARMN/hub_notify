import asyncio
import json

import aio_pika

from app.config import settings


async def publish(queue_name):

    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    async with connection:

        channel = await connection.channel()

        payload = {
            "job_id": "test-notification",
            "job_type": "bulk_email",
            "queue": queue_name,
            "label": "Notification Test",
            "payload": {
                "recipient": "test@example.com",
                "message": "Hello from RabbitMQ"
            },
            "status": "queued",
            "progress": 0,
            "message": "",
            "total": 0,
            "done_count": 0,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode()
            ),
            routing_key=queue_name,
        )

        print(f"Published to {queue_name}")


async def main():

    await publish("notify.bulk_email")
    await publish("notify.bulk_sms")


asyncio.run(main())