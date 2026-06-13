"""
File upload worker — simulates receiving, validating, storing and indexing
large files of any size/type.

Queue: file.uploads
"""
from __future__ import annotations

import asyncio
import logging
import random

from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus
from app.workers.worker_base import RabbitMQWorker

logger = logging.getLogger(__name__)

# Keep this for backward compatibility until API integration is migrated
_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    _queue.put_nowait(job)

async def _process(job: Job) -> None:

   
    print(
        f"FILE WORKER PROCESSING: {job.job_id}"
    )
    
    logger.info(
        "FILE WORKER RECEIVED JOB %s",
        job.job_id
    )

    logger.info(
    "Processing file upload job %s",
    job.job_id
)

    steps = [
        (10, "Receiving file bytes…"),
        (25, "Validating file type & size…"),
        (45, "Saving to object storage (MinIO)…"),
        (65, "Extracting file metadata…"),
        (80, "Scanning for malware…"),
        (95, "Indexing for search…"),
        (100, "File stored & indexed ✓"),
    ]

    size_mb = job.payload.get(
        "size_mb",
        random.randint(5, 200)
    )

    delay_per_step = max(
        0.4,
        size_mb / 300
    )

    try:

        await job_store.update(
            job.job_id,
            JobStatus.PROCESSING,
            progress=0,
            message=f"Starting upload — {size_mb} MB file…"
        )

        for pct, msg in steps:

            await asyncio.sleep(
                delay_per_step + random.uniform(0.1, 0.4)
            )


            if pct == 100:

                await job_store.update(
                    job.job_id,
                    JobStatus.DONE,
                    progress=100,
                    message=msg,
                )

                

                

            else:

                await job_store.update(
                    job.job_id,
                    JobStatus.PROCESSING,
                    progress=pct,
                    message=msg,
                )

                

    

    except Exception as exc:

        print(
            f"FILE WORKER ERROR: {exc}"
        )

        raise
    
async def run() -> None:

    print("FILE WORKER STARTED")

    worker = RabbitMQWorker(
        queue_name="file.uploads",
        processor=_process,
        model=Job,
    )

    await worker.run()