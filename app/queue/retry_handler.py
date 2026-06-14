
import json
import aio_pika

from app.queue.dlq_handler import (
    move_to_dlq
)

MAX_RETRIES = 3


async def handle_retry(
    channel,
    queue_name,
    message_data
):

    current_retry = message_data.get(
        "retry_count",
        0
    )

    if current_retry < MAX_RETRIES:

        message_data["retry_count"] = (
            current_retry + 1
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
            f"Retry {current_retry + 1} "
            f"sent to {retry_queue}"
        )

    else:

        print(
            f"Max retries reached for "
            f"{queue_name}"
        )

        await move_to_dlq(
            channel,
            queue_name,
            message_data
        )