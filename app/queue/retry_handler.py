import json
import aio_pika

from app.queue.dlq_handler import move_to_dlq
from app.queue.job_store import job_store
from app.queue.schemas import JobStatus


async def handle_retry(
    channel,
    queue_name,
    message_data,
):

    current_attempt = message_data.get(
        "attempt",
        1
    )

    max_attempts = message_data.get(
        "max_attempts",
        4
    )

    if current_attempt < max_attempts:

        await job_store.update(
            message_data["job_id"],
            JobStatus.RETRYING,
            message=f"Retry attempt {current_attempt + 1}"
        )

        message_data["attempt"] = (
            current_attempt + 1
        )

        retry_queue = (
            f"{queue_name}.retry"
        )

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    message_data
                ).encode()
            ),
            routing_key=retry_queue
        )

        print(
            f"Retry attempt {current_attempt + 1} "
            f"sent to {retry_queue}"
        )

    else:

        await job_store.update(
            message_data["job_id"],
            JobStatus.DLQ,
            message="Moved to Dead Letter Queue"
        )

        print(
            f"Max attempts reached for "
            f"{queue_name}"
        )

        await move_to_dlq(
            channel,
            queue_name,
            message_data
        )