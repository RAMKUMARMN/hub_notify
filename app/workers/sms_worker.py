"""
Bulk SMS worker — dispatches SMS to a large list of recipients via Twilio


Queue: notify.bulk_sms
"""
from __future__ import annotations

import asyncio
import logging
import random

from app.channels.sms import send_sms
from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    _queue.put_nowait(job)


async def _process(job: Job) -> None:
    recipients: list[str] = job.payload.get("recipients", [])
    body: str = job.payload.get("body", "CixioHub: Your notification.")

    if not recipients:
        n = job.payload.get("count", random.randint(20, 200))
        recipients = [f"+6091234{str(i).zfill(4)}" for i in range(n)]

    total = len(recipients)
    job.total = total

    await job_store.update(
        job.job_id,
        JobStatus.PROCESSING,
        progress=0,
        message=f"Queuing {total} SMS messages via gateway…",
        done_count=0,
    )

    await asyncio.sleep(0.2)

    sent = 0
    failed = 0

    for phone in recipients:
        try:
            send_sms(to=phone, body=body)
            logger.info(
                "SMS sent successfully to %s (job %s)",
                phone,
                job.job_id,
            )
        except Exception as exc:
            failed += 1
            logger.warning(
                "Failed to send SMS to %s (job %s): %s",
                phone,
                job.job_id,
                exc,
            )

        sent += 1
        pct = int((sent / total) * 100)

        if sent % max(1, total // 8) == 0 or sent == total:
            await job_store.update(
                job.job_id,
                JobStatus.PROCESSING,
                progress=pct,
                message=f"Dispatched {sent}/{total} SMS"
                f"{f' ({failed} failed)' if failed else ''}…",
                done_count=sent,
            )

        await asyncio.sleep(random.uniform(0.01, 0.05))

    final_status = (
        JobStatus.FAILED
        if failed == total
        else JobStatus.DONE
    )

    await job_store.update(
        job.job_id,
        final_status,
        progress=100,
        message=f"✓ {sent - failed}/{total} delivered · {failed} failed",
        done_count=sent,
    )


async def run() -> None:
    logger.info("notify.bulk_sms worker started")

    while True:
        job = await _queue.get()

        try:
            await _process(job)
        except Exception as exc:
            logger.exception("sms_worker error for job %s", job.job_id)
            await job_store.update(
                job.job_id,
                JobStatus.FAILED,
                progress=job.progress,
                message=str(exc),
            )
        finally:
            _queue.task_done()