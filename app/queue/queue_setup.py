"""
Creates Retry and DLQ queues
for all registered queues.
"""

import asyncio
import aio_pika

from app.config import settings
from app.queue.queue_names import ALL_QUEUES


async def declare_retry_dlq_queues(channel):
    print("declare_retry_dlq_queues() called")

    for queue in ALL_QUEUES:

        retry_queue = f"{queue}.retry"
        dlq_queue = f"{queue}.dlq"

        await channel.declare_queue(
            f"{queue}.retry.1",
            durable=True,
            arguments={
                "x-message-ttl": 60000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": queue,
            },
        )

        await channel.declare_queue(
            f"{queue}.retry.2",
            durable=True,
            arguments={
                "x-message-ttl": 300000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": queue,
            },
        )

        await channel.declare_queue(
            f"{queue}.retry.3",
            durable=True,
            arguments={
                "x-message-ttl": 1800000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": queue,
            },
        )

        await channel.declare_queue(
            f"{queue}.dlq",
            durable=True,
        )

        print(f"Created: {queue}.retry.1")
        print(f"Created: {queue}.retry.2")
        print(f"Created: {queue}.retry.3")
        print(f"Created: {queue}.dlq")
        print("All Retry and DLQ queues declared")


async def setup():
    print("Connecting to RabbitMQ...")

    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    async with connection:
        channel = await connection.channel()

        await declare_retry_dlq_queues(channel)


if __name__ == "__main__":
    asyncio.run(setup())