"""In-memory job store + SSE broadcaster for the queue dashboard."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._subscribers: list[asyncio.Queue] = []

    # ── write ─────────────────────────────────────────────────────────────────

    async def add(self, job: Job) -> None:
        self._jobs[job.job_id] = job
        await self._broadcast("job.queued", job)

    async def update(
        self,
        job_id: str,
        status: JobStatus,
        *,
        progress: int = 0,
        message: str = "",
        done_count: int | None = None,
    ) -> None:
        from datetime import datetime, timezone
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = status
        job.progress = progress
        job.message = message
        job.updated_at = datetime.now(timezone.utc).isoformat()
        if done_count is not None:
            job.done_count = done_count
        await self._broadcast(f"job.{status.value}", job)

    # ── read ──────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Per-queue counts by status."""
        result: dict[str, dict] = {}
        for job in self._jobs.values():
            q = result.setdefault(
                job.queue,
                {
                    "queue": job.queue,
                    "queued": 0,
                    "processing": 0,
                    "done": 0,
                    "failed": 0,
                    "total": 0,
                },
            )
            q[job.status.value] += 1
            q["total"] += 1
        return result
    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)
    def recent(self, limit: int = 80) -> list[Job]:
        return sorted(
            self._jobs.values(), key=lambda j: j.created_at, reverse=True
        )[:limit]

    # ── SSE ───────────────────────────────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=300)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    async def stream(self, q: asyncio.Queue) -> AsyncIterator[str]:
        """Yield SSE-formatted strings. Sends keep-alive ping every 15 s."""
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield 'data: {"event":"ping"}\n\n'
        except asyncio.CancelledError:
            pass

    async def _broadcast(self, event: str, job: Job) -> None:
        payload = json.dumps({"event": event, "data": job.model_dump()})
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)


# singleton
job_store = JobStore()
