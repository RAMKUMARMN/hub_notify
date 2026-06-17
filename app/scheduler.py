import logging
from datetime import datetime, timezone
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import async_session
from app.models import NotificationJob, IndividualNotification
from app.queue.producer import publish_notification

logger = logging.getLogger(__name__)


async def poll_scheduled_notifications() -> None:
    """Poll the database for due scheduled notifications using optimized
    queries and publish them.
    """
    now = datetime.now(timezone.utc)
    try:
        async with async_session() as db:
            # 1. Query the jobs table using the indexed completed and
            # scheduled_at columns
            stmt = (
                select(NotificationJob.job_id, NotificationJob.channel)
                .where(NotificationJob.completed.is_(False))
                .where(NotificationJob.scheduled_at <= now)
            )
            result = await db.execute(stmt)
            eligible_jobs = result.all()

            if not eligible_jobs:
                return

            logger.info(
                "Found %d potential due scheduled notification jobs",
                len(eligible_jobs),
            )

            for job_id, channel in eligible_jobs:
                # 2. Use the indexed job_id column in the details table
                # to fetch associated records
                stmt_detail = (
                    select(IndividualNotification)
                    .where(IndividualNotification.job_id == job_id)
                )
                result_detail = await db.execute(stmt_detail)
                notifications = result_detail.scalars().all()

                for notification in notifications:
                    # 3. Verify status and publish only if status is
                    # 'scheduled'
                    if notification.status == "scheduled":
                        notification.status = "queued"
                        notification.updated_at = now
                        # Save state change to prevent double-processing
                        await db.commit()

                        try:
                            await publish_notification(
                                notification, channel=channel
                            )
                            logger.info(
                                "Successfully published scheduled "
                                "notification %s (job %s) to %s queue",
                                notification.id,
                                notification.job_id,
                                channel,
                            )
                        except Exception as exc:
                            logger.error(
                                "Failed to publish scheduled "
                                "notification %s: %s",
                                notification.id,
                                exc,
                            )
    except Exception as exc:
        logger.error("Error in scheduler polling loop: %s", exc, exc_info=True)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(poll_scheduled_notifications, "interval", seconds=30)
    scheduler.start()
    logger.info(
        "APScheduler started: polling database for scheduled "
        "notifications every 30 seconds."
    )
    return scheduler


async def stop_scheduler(scheduler: AsyncIOScheduler) -> None:
    scheduler.shutdown()
    logger.info("APScheduler shut down.")
