"""
Moves failed messages into DLQ.
"""

import json
import aio_pika


async def move_to_dlq(
    channel,
    queue_name,
    message_data
):

    dlq_name = f"{queue_name}.dlq"

    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(
                message_data
            ).encode()
        ),
        routing_key=dlq_name
    )

    print(
        f"Message moved to DLQ: {dlq_name}"
    )