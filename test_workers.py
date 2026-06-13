import asyncio
import json
from datetime import datetime, timezone

import aio_pika

from app.config import settings


def create_job(queue_name: str):

    return {
        "job_id": f"test-{queue_name}",
        "job_type": "analytics",
        "queue": queue_name,
        "label": f"Test {queue_name}",
        "payload": {
            "size_mb": 50,
            "num_files": 5,
        },
        "status": "queued",
        "progress": 0,
        "message": "",
        "total": 0,
        "done_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def publish(queue_name: str):

    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    async with connection:

        channel = await connection.channel()

        job = create_job(queue_name)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(job).encode()
            ),
            routing_key=queue_name,
        )

        print(f"✅ Published to {queue_name}")


async def main():

    queues = [
        "file.uploads",
        "rag.bulk_ingest",
        "analytics.events",
        "ai.orchestration",
        "embedding.processing",
        "memory.processing",
    ]

    for queue in queues:
        await publish(queue)


if __name__ == "__main__":
    asyncio.run(main())