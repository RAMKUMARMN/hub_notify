"""
Bulk email worker — sends large batches of emails via SMTP (Mailpit locally).
Simulates template rendering, rate-limiting, and per-recipient delivery.

Queue: notify.bulk_email
"""
from __future__ import annotations

import asyncio
import logging
import random
from app.workers.worker_base import RabbitMQWorker
from app.channels.email import send_email
from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    _queue.put_nowait(job)


async def _process(job: Job) -> None:
    
    print(
        f"EMAIL WORKER PROCESSING: {job.job_id}"
    )


    recipients: list[str] = job.payload.get("recipients", [])
    subject: str = job.payload.get("subject", "CixioHub Notification")
    body: str = job.payload.get("body", "Hello from CixioHub!")

    if not recipients:
        # Generate synthetic recipients for demo
        n = job.payload.get("count", random.randint(10, 100))
        recipients = [f"student{i + 1}@tkm.edu" for i in range(n)]

    total = len(recipients)
    job.total = total

    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=0,
                           message=f"Preparing bulk email to {total} recipients…",
                           done_count=0)
    await asyncio.sleep(0.3)

    sent = 0
    failed = 0
    for i, recipient in enumerate(recipients):
        try:
            await send_email(to=recipient, subject=subject, body=body)
        except Exception:
            failed += 1
        sent += 1
        pct = int((sent / total) * 100)
        if sent % max(1, total // 10) == 0 or sent == total:
            await job_store.update(
                job.job_id, JobStatus.PROCESSING, progress=pct,
                message=f"Sent {sent}/{total} emails{f' ({failed} failed)' if failed else ''}…",
                done_count=sent,
            )
        await asyncio.sleep(random.uniform(0.02, 0.08))

    final_status = JobStatus.DONE if failed == 0 else (
        JobStatus.FAILED if failed == total else JobStatus.DONE
    )
    await job_store.update(
        job.job_id, final_status, progress=100,
        message=f"✓ {sent - failed}/{total} delivered · {failed} failed",
        done_count=sent,
    )


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="notify.bulk_email",
        processor=_process,
        model=Job,
    )

    await worker.run()

    
