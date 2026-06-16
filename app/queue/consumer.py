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
        try:
            await dispatch(payload)
            logger.info("Sent %s to %s (job %s)", payload.channel, payload.recipient, payload.job_id)
            
            # Update database
            async with async_session() as db:
                # 1. Update main job metrics
                job = await db.get(NotificationJob, payload.job_id)
                if job:
                    job.sent += 1
                    if payload.attempt > 1 and job.retrying > 0:
                        job.retrying -= 1
                    if job.sent + job.failed >= job.total:
                        job.completed = True
                
                # 2. Update individual notification status
                from sqlalchemy import select
                result = await db.execute(
                    select(IndividualNotification)
                    .where(IndividualNotification.job_id == payload.job_id)
                    .where(IndividualNotification.recipient == payload.recipient)
                )
                ind = result.scalars().first()
                if ind:
                    ind.status = "sent"
                    ind.attempt = payload.attempt
                
                await db.commit()
        except Exception as exc:
            logger.warning("Failed attempt %d for job %s: %s", payload.attempt, payload.job_id, exc)
            if payload.attempt < payload.max_attempts:
                # Update database for retry
                async with async_session() as db:
                    # 1. Update main job retry metric
                    job = await db.get(NotificationJob, payload.job_id)
                    if job:
                        job.retrying += 1
                    
                    # 2. Update individual notification status
                    from sqlalchemy import select
                    result = await db.execute(
                        select(IndividualNotification)
                        .where(IndividualNotification.job_id == payload.job_id)
                        .where(IndividualNotification.recipient == payload.recipient)
                    )
                    ind = result.scalars().first()
                    if ind:
                        ind.status = "retrying"
                        ind.attempt = payload.attempt
                    
                    await db.commit()

                # Re-enqueue with incremented attempt count
                # TODO: add delay (publish after RETRY_DELAYS[payload.attempt] seconds)
                payload.attempt += 1
                await publish(payload)
            else:
                logger.error("Permanently failed job %s channel %s", payload.job_id, payload.channel)
                # Update database for permanent failure
                async with async_session() as db:
                    # 1. Update main job metrics
                    job = await db.get(NotificationJob, payload.job_id)
                    if job:
                        job.failed += 1
                        if payload.attempt > 1 and job.retrying > 0:
                            job.retrying -= 1
                        if job.sent + job.failed >= job.total:
                            job.completed = True
                    
                    # 2. Update individual notification status
                    from sqlalchemy import select
                    result = await db.execute(
                        select(IndividualNotification)
                        .where(IndividualNotification.job_id == payload.job_id)
                        .where(IndividualNotification.recipient == payload.recipient)
                    )
                    ind = result.scalars().first()
                    if ind:
                        ind.status = "failed"
                        ind.attempt = payload.attempt
                    
                    await db.commit()
                # TODO: publish to *.failed queue for investigation


async def run_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        for queue_name in ["email.process", "sms.process", "push.process"]:
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.consume(process_message)

        logger.info("Notify worker started. Waiting for messages...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_consumer())
