from __future__ import annotations

import asyncio
import logging

import aio_pika

from app.channels.email import send_email
from app.config import settings
from app.queue.schemas import (
    NotifyPayload,
    EMAIL_PROCESS_QUEUE,
    EMAIL_RETRY_QUEUE,
    EMAIL_FAILED_QUEUE,
)

logger = logging.getLogger(__name__)

# Global RabbitMQ channel
channel: aio_pika.Channel | None = None



# PUBLISH TO QUEUE

async def publish_to_queue(
    queue_name: str,
    payload: NotifyPayload,
):

    global channel

    await channel.default_exchange.publish(

        aio_pika.Message(
            body=payload.model_dump_json().encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),

        routing_key=queue_name,
    )


# RETRY DELAY LOGIC


def retry_delay(attempt: int) -> int:
    """
    Returns delay in seconds based on retry attempt.

    Attempt 2 → 1 minute
    Attempt 3 → 5 minutes
    Attempt 4 → 30 minutes
    """

    delays = {
        2: 60,        # 1 minute
        3: 300,       # 5 minutes
        4: 1800,      # 30 minutes
    }

    return delays.get(attempt, 60)


# PROCESS MESSAGE

async def process_message(
    message: aio_pika.IncomingMessage,
):

    payload = NotifyPayload.model_validate_json(
        message.body.decode()
    )

    try:

        logger.info(
            f"Sending email to {payload.recipient}"
        )

      
        # SEND EMAIL
      

        await send_email(
            to=payload.recipient,
            subject=payload.subject or "",
            body=payload.body,
            html_body=payload.html_body,
        )

        logger.info(
            f"Email sent successfully to {payload.recipient}"
        )

        # acknowledge success
        await message.ack()

    except Exception:

        logger.exception(
            f"Email failed for {payload.recipient}"
        )

        # MAX RETRIES REACHED
        

        if payload.attempt >= payload.max_attempts:

            logger.error(
                f"Email permanently failed "
                f"for {payload.recipient}"
            )

            await publish_to_queue(
                EMAIL_FAILED_QUEUE,
                payload,
            )

        else:

           
            # RETRY
           

            payload.attempt += 1

            logger.warning(
                f"Retrying email "
                f"({payload.attempt}/{payload.max_attempts})"
            )

            # retry delay
            delay = retry_delay(payload.attempt)

            logger.warning(
            f"Waiting {delay} seconds before retry"
            )

            await asyncio.sleep(delay)

            await publish_to_queue(
                EMAIL_RETRY_QUEUE,
                payload,
            )

        # remove original failed message
        await message.ack()


# START WORKER

async def run():

    global channel

  
    # CONNECT RABBITMQ
   

    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    channel = await connection.channel()

   
    # DECLARE QUEUES
   

    process_queue = await channel.declare_queue(
        EMAIL_PROCESS_QUEUE,
        durable=True,
    )

    retry_queue = await channel.declare_queue(
        EMAIL_RETRY_QUEUE,
        durable=True,
    )

    failed_queue = await channel.declare_queue(
        EMAIL_FAILED_QUEUE,
        durable=True,
    )

    # CONSUMERS
   

    await process_queue.consume(process_message)

    await retry_queue.consume(process_message)

    logger.info("Email worker started")

    # keep worker alive forever
    await asyncio.Future()



# ENTRYPOINT

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())