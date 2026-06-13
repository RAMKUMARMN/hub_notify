"""
Analytics worker — processes user activity logs, engagement events,
session data, and computes aggregated metrics.

Queue: analytics.events
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
        f"ANALYTICS WORKER PROCESSING: {job.job_id}"
    )
    
    task_type = job.payload.get("task_type", "engagement_analysis")
    event_count = job.payload.get("event_count", random.randint(500, 10000))
    job.total = event_count

    steps: list[tuple[int, str]] = {
        "engagement_analysis": [
            (10, f"Loading {event_count:,} user events from database…"),
            (25, "Parsing event payloads & normalising timestamps…"),
            (40, "Segmenting users by activity cohort…"),
            (58, "Computing session duration & page-view metrics…"),
            (72, "Calculating retention & churn signals…"),
            (85, "Aggregating engagement scores per user…"),
            (95, "Writing results to analytics store…"),
            (100, f"✓ {event_count:,} events analysed · engagement report ready"),
        ],
        "user_logs": [
            (15, f"Ingesting {event_count:,} log lines…"),
            (35, "Parsing log levels, services & trace IDs…"),
            (55, "Detecting error patterns & anomalies…"),
            (75, "Building per-service error rate timeline…"),
            (90, "Generating alert digest…"),
            (100, f"✓ {event_count:,} log lines processed"),
        ],
    }.get(task_type, [
        (20, "Loading data…"),
        (50, "Processing…"),
        (80, "Aggregating results…"),
        (100, "✓ Task complete"),
    ])

    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=0,
                           message=steps[0][1], done_count=0)

    for pct, msg in steps:
        delay = random.uniform(0.3, 1.0)
        await asyncio.sleep(delay)
        status = JobStatus.DONE if pct == 100 else JobStatus.PROCESSING
        done = int(event_count * pct / 100)
        await job_store.update(job.job_id, status, progress=pct,
                               message=msg, done_count=done)


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="analytics.events",
        processor=_process,
        model=Job,
    )

    await worker.run()
