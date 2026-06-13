"""
Bulk SMS worker — dispatches SMS to a large list of recipients via Twilio
(stubbed locally — no real Twilio credentials required for demo).

Queue: notify.bulk_sms
"""
from __future__ import annotations
from app.workers.worker_base import RabbitMQWorker
import asyncio
import logging
import random

from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    _queue.put_nowait(job)


async def _process(job: Job) -> None:

    print(
        f"SMS WORKER PROCESSING: {job.job_id}"
    )
    
    recipients: list[str] = job.payload.get("recipients", [])
    body: str = job.payload.get("body", "CixioHub: Your notification.")

    if not recipients:
        n = job.payload.get("count", random.randint(20, 200))
        recipients = [f"+6091234{str(i).zfill(4)}" for i in range(n)]

    total = len(recipients)
    job.total = total

    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=0,
                           message=f"Queuing {total} SMS messages via gateway…",
                           done_count=0)
    await asyncio.sleep(0.2)

    sent = 0
    failed = 0
    for i, phone in enumerate(recipients):
        # Simulate 2 % failure rate for realism
        if random.random() < 0.02:
            failed += 1
        sent += 1
        pct = int((sent / total) * 100)
        if sent % max(1, total // 8) == 0 or sent == total:
            await job_store.update(
                job.job_id, JobStatus.PROCESSING, progress=pct,
                message=f"Dispatched {sent}/{total} SMS{f' ({failed} failed)' if failed else ''}…",
                done_count=sent,
            )
        await asyncio.sleep(random.uniform(0.01, 0.05))

    await job_store.update(
        job.job_id, JobStatus.DONE, progress=100,
        message=f"✓ {sent - failed}/{total} delivered · {failed} failed",
        done_count=sent,
    )


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="notify.bulk_sms",
        processor=_process,
        model=Job,
    )

    await worker.run()
