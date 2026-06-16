"""
RabbitMQ consumer worker — dispatches notifications from the queue.

Run with: python -m app.queue.worker

Students: implement the retry delay logic and the actual channel dispatch.
"""
import asyncio
import json
import logging

import aio_pika

from app.channels.email import send_email
from app.channels.sms import send_sms
from app.channels.push import send_push
from app.channels.whatsapp import send_whatsapp
from app.config import settings
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload

from app.database import async_session
from app.models import NotificationJob, IndividualNotification

logger = logging.getLogger(__name__)

RETRY_DELAYS = {1: 0, 2: 60, 3: 300, 4: 1800}  # seconds before retry


async def dispatch(payload: NotifyPayload) -> None:
    """Call the correct channel sender based on payload.channel."""
    match payload.channel:
        case "email":
            await send_email(
                to=payload.recipient,
                subject=payload.subject or "",
                body=payload.body,
                html_body=payload.html_body,
            )
        case "sms":
            send_sms(to=payload.recipient, body=payload.body)
        case "push":
            send_push(
                device_token=payload.recipient,
                title=payload.title or "CixioHub",
                body=payload.body,
                data=payload.data,
            )
        case "whatsapp":
            send_whatsapp(to=payload.recipient, body=payload.body)
        case _:
            raise ValueError(f"Unknown channel: {payload.channel}")


async def process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload = NotifyPayload(**json.loads(message.body))
        
        # Get base channel name
        base_channel = payload.channel
        if base_channel == "whatsapp":
            base_channel = "push"

        try:
            await dispatch(payload)
            logger.info("Sent %s to %s (job %s)", payload.channel, payload.recipient, payload.job_id)
            
            # Update database
            async with async_session() as db:
                # 1. Update individual notification status first to check was_retrying status
                from sqlalchemy import select
                result = await db.execute(
                    select(IndividualNotification)
                    .where(IndividualNotification.job_id == payload.job_id)
                    .where(IndividualNotification.recipient == payload.recipient)
                )
                ind = result.scalars().first()
                was_retrying = False
                if ind:
                    was_retrying = (ind.status == "retrying")
                    ind.status = "sent"
                    ind.attempt = payload.attempt
                
                # 2. Update main job metrics
                job = await db.get(NotificationJob, payload.job_id)
                if job:
                    job.sent += 1
                    if was_retrying and job.retrying > 0:
                        job.retrying -= 1
                    if job.sent + job.failed >= job.total:
                        job.completed = True
                
                await db.commit()
        except Exception as exc:
            logger.warning("Failed attempt %d for job %s: %s", payload.attempt, payload.job_id, exc)
            if payload.attempt < payload.max_attempts:
                # Determine retry delay queue
                # 2nd attempt -> 60s
                # 3rd attempt -> 300s
                # 4th attempt -> 1800s
                next_attempt = payload.attempt + 1
                delay_sec = {2: 60, 3: 300, 4: 1800}.get(next_attempt, 60)
                retry_q_name = f"{base_channel}.retry.{delay_sec}s"

                # Update database for retry
                async with async_session() as db:
                    # 1. Update individual notification status first to check already_retrying status
                    from sqlalchemy import select
                    result = await db.execute(
                        select(IndividualNotification)
                        .where(IndividualNotification.job_id == payload.job_id)
                        .where(IndividualNotification.recipient == payload.recipient)
                    )
                    ind = result.scalars().first()
                    already_retrying = False
                    if ind:
                        already_retrying = (ind.status == "retrying")
                        ind.status = "retrying"
                        ind.attempt = payload.attempt
                    
                    # 2. Update main job retry metric
                    job = await db.get(NotificationJob, payload.job_id)
                    if job:
                        if not already_retrying:
                            job.retrying += 1
                    
                    await db.commit()

                # Re-enqueue by publishing to the specific retry queue
                payload.attempt = next_attempt
                await publish(payload, routing_key=retry_q_name)
                logger.info("Enqueued retry attempt %d to %s", next_attempt, retry_q_name)
            else:
                logger.error("Permanently failed job %s channel %s", payload.job_id, payload.channel)
                # Update database for permanent failure (5th try / failed queue)
                async with async_session() as db:
                    # 1. Update individual notification status first to check was_retrying status
                    from sqlalchemy import select
                    result = await db.execute(
                        select(IndividualNotification)
                        .where(IndividualNotification.job_id == payload.job_id)
                        .where(IndividualNotification.recipient == payload.recipient)
                    )
                    ind = result.scalars().first()
                    was_retrying = False
                    if ind:
                        was_retrying = (ind.status == "retrying")
                        ind.status = "failed"
                        ind.attempt = payload.attempt + 1
                    
                    # 2. Update main job metrics
                    job = await db.get(NotificationJob, payload.job_id)
                    if job:
                        job.failed += 1
                        if was_retrying and job.retrying > 0:
                            job.retrying -= 1
                        if job.sent + job.failed >= job.total:
                            job.completed = True
                    
                    await db.commit()

                # Publish to failed queue
                failed_q_name = f"{base_channel}.failed"
                await publish(payload, routing_key=failed_q_name)
                logger.info("Enqueued permanently failed message to %s", failed_q_name)


async def run_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        for base in ["email", "sms", "push"]:
            process_q_name = f"{base}.process"
            failed_q_name = f"{base}.failed"

            # 1. Declare main processing queue
            process_queue = await channel.declare_queue(process_q_name, durable=True)

            # 2. Declare failed queue
            await channel.declare_queue(failed_q_name, durable=True)

            # 3. Declare three separate retry queues for each delay: 60s, 300s, 1800s
            for delay in [60, 300, 1800]:
                retry_q_name = f"{base}.retry.{delay}s"
                await channel.declare_queue(
                    retry_q_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": "",                  # Default direct exchange
                        "x-dead-letter-routing-key": process_q_name,     # Dead letter back to main queue
                        "x-message-ttl": delay * 1000,                  # TTL in milliseconds
                    }
                )

            # Consume from main process queue
            await process_queue.consume(process_message)

        logger.info("Notify worker started. Waiting for messages...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_consumer())
