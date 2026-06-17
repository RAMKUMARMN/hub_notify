"""
Jobs router — /api/v1/jobs/*

Provides:
  POST /submit          submit a new job to any queue
  GET  /stream          SSE stream of all job events (real-time dashboard)
  GET  /stats           per-queue counts snapshot
  GET  /recent          last N jobs list
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.queue.job_store import job_store
from app.queue.schemas import (
    Job,
    JobType,
    QUEUE_FOR_TYPE,
    SubmitJobRequest,
)
from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])

_WORKER_MAP = {
    JobType.FILE_UPLOAD:    file_worker.enqueue,
    JobType.RAG_BULK_INGEST: rag_worker.enqueue,
    JobType.BULK_EMAIL:     email_worker.enqueue,
    JobType.BULK_SMS:       sms_worker.enqueue,
    JobType.ANALYTICS:      analytics_worker.enqueue,
}


@router.post("/submit", status_code=202)
async def submit_job(body: SubmitJobRequest):
    """Submit a job — immediately returns the job_id, processing happens async."""
    queue = QUEUE_FOR_TYPE[body.job_type.value]
    job = Job(
        job_type=body.job_type,
        queue=queue,
        label=body.label or body.job_type.value.replace("_", " ").title(),
        payload=body.payload,
    )
    await job_store.add(job)
    enqueue_fn = _WORKER_MAP[body.job_type]
    enqueue_fn(job)
    return {"job_id": job.job_id, "queue": queue, "status": "queued"}


@router.get("/stream")
async def stream_events():
    """
    Server-Sent Events stream.

    Connect with:
        const es = new EventSource('/api/v1/jobs/stream');
        es.onmessage = e => console.log(JSON.parse(e.data));

    Events:
        job.queued      — new job arrived in queue
        job.processing  — worker picked it up
        job.done        — completed successfully
        job.failed      — permanently failed
        ping            — keep-alive (every 15 s)
    """
    q = job_store.subscribe()

    async def generator():
        try:
            async for chunk in job_store.stream(q):
                yield chunk
        finally:
            job_store.unsubscribe(q)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/stats")
async def queue_stats():
    """Snapshot of per-queue counts — suitable for polling every few seconds."""
    return {"queues": list(job_store.stats().values())}


@router.get("/recent")
async def recent_jobs(limit: int = 60):
    """Most recent jobs across all queues."""
    return {"jobs": [j.model_dump() for j in job_store.recent(limit)]}

@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get a single job by job_id."""
    job = job_store.get(job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump()