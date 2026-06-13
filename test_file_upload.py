import asyncio
import aio_pika

from app.config import settings
from app.queue.schemas import Job, JobType


async def main():

    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    async with connection:

        channel = await connection.channel()

        job = Job(
            job_type=JobType.FILE_UPLOAD,
            queue="file.uploads",
            label="RabbitMQ Test Upload",
            payload={
                "size_mb": 50
            }
        )

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=job.model_dump_json().encode()
            ),
            routing_key="file.uploads"
        )

        print("Message published")


asyncio.run(main())