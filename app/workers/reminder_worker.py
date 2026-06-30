import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session
from app.models import Todo, UserDevice
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60
REMINDER_WINDOW = timedelta(hours=1)


async def check_and_send_reminders() -> None:
    now = datetime.now(timezone.utc)
    window_end = now + REMINDER_WINDOW

    async with async_session() as session:
        result = await session.execute(
            select(Todo).where(
                Todo.completed.is_(False),
                Todo.reminder_sent.is_(False),
                Todo.due_date.is_not(None),
                Todo.due_date <= window_end,
                Todo.due_date > now,
            )
        )
        due_todos = result.scalars().all()

        for todo in due_todos:
            device_result = await session.execute(
                select(UserDevice)
                .where(UserDevice.user_id == todo.user_id)
                .order_by(UserDevice.id.desc())
            )
            device = device_result.scalars().first()

            if device:
                payload = NotifyPayload(
                    job_id=f"todo-reminder-{todo.id}",
                    channel="push",
                    recipient=device.device_token,
                    title="To-do reminder",
                    body=f"'{todo.title}' is due soon",
                    data={"type": "todo_reminder", "todo_id": str(todo.id)},
                    attempt=1,
                    max_attempts=3,
                )
                await publish(payload)
                logger.info("Queued reminder for todo %s (user %s)", todo.id, todo.user_id)

            todo.reminder_sent = True

        if due_todos:
            await session.commit()


async def run() -> None:
    logger.info("Reminder worker started. Checking every %d seconds...", CHECK_INTERVAL_SECONDS)
    while True:
        try:
            await check_and_send_reminders()
        except Exception as exc:
            logger.error("Reminder worker check failed: %s", exc)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)