"""
Bulk email worker — dispatches emails to a list of recipients.

Queue: notify.bulk_email

This worker follows the same asyncio pattern used by every other worker in
this service (file_worker, sms_worker, rag_worker, analytics_worker):

  _queue     asyncio.Queue that receives Job objects from the HTTP router
  enqueue()  called synchronously by jobs.py router right after job creation
  _process() does the actual work, updating job_store at each step so the SSE
             dashboard gets live progress events
  run()      infinite loop started once at app startup (see main.py lifespan)

Why asyncio queues instead of running workers as separate processes?
  For the demo / internship context, in-process asyncio tasks are simpler to
  set up and debug. The RabbitMQ consumer (queue/consumer.py) is the production
  path for durability across restarts.
"""
from __future__ import annotations

import asyncio
import logging
import random

from sqlalchemy import update

from app.channels.email import send_email
from app.database import AsyncSessionLocal
from app.models.job import NotificationJob
from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)

# In-process queue shared between enqueue() (writer) and run() (reader).
# No locking needed — asyncio is single-threaded.
_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    """Hand a job to this worker. Called by jobs.py router (sync context)."""
    _queue.put_nowait(job)


async def _sync_db(job_id: str, status: str, sent: int, failed: int) -> None:
    """
    Write live progress to the notification_jobs table.

    This runs periodically during processing so that the /notify/jobs/{id}
    REST endpoint returns accurate counts even when no SSE client is watching.
    Failure here is non-fatal — the in-memory job_store still holds the state.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(NotificationJob)
                .where(NotificationJob.job_id == job_id)
                .values(status=status, sent=sent, failed=failed)
            )
            await session.commit()
    except Exception:
        logger.warning("DB sync failed for job %s", job_id)


async def _process(job: Job) -> None:
    """
    Send bulk emails for a single job.

    Expected payload keys (all optional):
      recipients  list[str]   real email addresses to send to
      count       int         number of fake addresses to generate when
                              'recipients' is absent (demo mode, default: random 20–100)
      subject     str         email subject line
      body        str         plain-text body
      html_body   str|None    optional HTML body
    """
    recipients: list[str] = job.payload.get("recipients", [])
    subject: str = job.payload.get("subject", "CixioHub Notification")
    body: str = job.payload.get("body", "You have a new notification from CixioHub.")
    html_body: str | None = job.payload.get("html_body")

    # Demo mode: generate synthetic addresses when no real list is provided.
    # These will fail at SMTP delivery (which is expected and counted as failures).
    if not recipients:
        n = job.payload.get("count", random.randint(20, 100))
        recipients = [f"intern{i}@cixiohub.dev" for i in range(n)]

    total = len(recipients)
    job.total = total  # store in-memory so SSE can report it

    await job_store.update(
        job.job_id,
        JobStatus.PROCESSING,
        progress=0,
        message=f"Preparing to send {total} emails…",
        done_count=0,
    )
    # Brief pause so the "processing" status event reaches SSE clients before
    # the worker immediately finishes (visible for small recipient lists).
    await asyncio.sleep(0.2)

    sent = 0
    failed = 0

    for email in recipients:
        try:
            await send_email(to=email, subject=subject, body=body, html_body=html_body)
            logger.info("Email sent to %s (job %s)", email, job.job_id)
        except Exception as exc:
            failed += 1
            logger.warning("Failed to send email to %s (job %s): %s", email, job.job_id, exc)

        sent += 1
        pct = int((sent / total) * 100)

        # Broadcast every ~12.5 % of recipients and on the final one.
        # Avoids flooding the SSE stream while still giving smooth progress.
        if sent % max(1, total // 8) == 0 or sent == total:
            await job_store.update(
                job.job_id,
                JobStatus.PROCESSING,
                progress=pct,
                message=f"Sent {sent}/{total} emails"
                f"{f' ({failed} failed)' if failed else ''}…",
                done_count=sent,
            )
            await _sync_db(job.job_id, "processing", sent, failed)

        # Yield control between sends so SSE streaming and other asyncio tasks
        # (e.g. incoming HTTP requests) are not starved.
        await asyncio.sleep(random.uniform(0.05, 0.15))

    # Mark as FAILED only when *every* recipient failed.
    # Partial failures are expected (bounces, bad addresses) and counted in the
    # final message, but the job itself is considered done.
    final_status = JobStatus.FAILED if failed == total else JobStatus.DONE
    await job_store.update(
        job.job_id,
        final_status,
        progress=100,
        message=f"✓ {sent - failed}/{total} delivered · {failed} failed",
        done_count=sent,
    )
    await _sync_db(job.job_id, final_status.value, sent - failed, failed)


async def run() -> None:
    """Long-running worker loop — started once at app startup via main.py lifespan."""
    logger.info("notify.bulk_email worker started")
    while True:
        job = await _queue.get()
        try:
            await _process(job)
        except Exception as exc:
            # Catch unexpected errors so the worker loop never crashes.
            # The job is marked failed and the loop continues.
            logger.exception("email_worker error for job %s", job.job_id)
            await job_store.update(
                job.job_id,
                JobStatus.FAILED,
                progress=job.progress,
                message=str(exc),
            )
        finally:
            _queue.task_done()
