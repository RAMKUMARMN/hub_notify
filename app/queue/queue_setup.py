"""
Creates Retry and DLQ queues
for all registered queues.
"""

import asyncio
import aio_pika
import logging
from app.config import settings
from app.queue.queue_names import ALL_QUEUES

logger = logging.getLogger(__name__)

async def declare_retry_dlq_queues(channel):
    print("declare_retry_dlq_queues() called")

    for queue in ALL_QUEUES:

        retry_queue = f"{queue}.retry"
        dlq_queue = f"{queue}.dlq"

        await channel.declare_queue(
            retry_queue,
            durable=True
        )

        await channel.declare_queue(
            dlq_queue,
            durable=True
        )

        logger.info(f"Created: {retry_queue}")
        logger.info(f"Created: {dlq_queue}")
    logger.info("All Retry and DLQ queues declared")


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