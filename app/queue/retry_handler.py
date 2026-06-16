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

        next_retry = current_retry + 1

        message_data["retry_count"] = (
            next_retry
        )

        retry_queue = {
            1: f"{queue_name}.retry.1",
            2: f"{queue_name}.retry.2",
            3: f"{queue_name}.retry.3",
        }[next_retry]

        print(
            f"Publishing retry "
            f"{next_retry}"
        )

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    message_data
                ).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=retry_queue
        )

        print(
            f"Retry {next_retry} "
            f"sent to {retry_queue}"
        )

    else:

        print(
            f"Max retries reached "
            f"for {queue_name}"
        )

        

        await move_to_dlq(
            channel,
            queue_name,
            message_data
        )