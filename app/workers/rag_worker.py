"""
RAG bulk-ingest worker — simulates processing many PDF/DOCX files,
extracting text, chunking, embedding with Ollama, and storing in ChromaDB.

Queue: rag.bulk_ingest
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
        f"RAG WORKER PROCESSING: {job.job_id}"
    )
    
    num_files = job.payload.get("num_files", random.randint(3, 20))
    job.total = num_files

    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=0,
                           message=f"Starting bulk RAG ingest — {num_files} documents…",
                           done_count=0)

    # Phase 1: text extraction (0–40 %)
    for i in range(num_files):
        await asyncio.sleep(random.uniform(0.3, 0.8))
        pct = int(10 + (i + 1) / num_files * 30)
        await job_store.update(job.job_id, JobStatus.PROCESSING, progress=pct,
                               message=f"Extracting text from document {i + 1}/{num_files}…",
                               done_count=i + 1)

    # Phase 2: chunking + embedding (40–85 %)
    total_chunks = num_files * random.randint(6, 15)
    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=42,
                           message=f"Chunking {total_chunks} text segments…")
    await asyncio.sleep(0.5)

    for c in range(total_chunks):
        await asyncio.sleep(random.uniform(0.05, 0.15))
        pct = int(42 + (c + 1) / total_chunks * 43)
        if c % 5 == 0:
            await job_store.update(job.job_id, JobStatus.PROCESSING, progress=pct,
                                   message=f"Embedding chunk {c + 1}/{total_chunks} via nomic-embed-text…")

    # Phase 3: ChromaDB write (85–100 %)
    await job_store.update(job.job_id, JobStatus.PROCESSING, progress=88,
                           message=f"Storing {total_chunks} vectors in ChromaDB…")
    await asyncio.sleep(random.uniform(0.4, 0.9))
    await job_store.update(job.job_id, JobStatus.DONE, progress=100,
                           message=f"✓ {num_files} docs · {total_chunks} vectors indexed",
                           done_count=num_files)


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="rag.bulk_ingest",
        processor=_process,
        model=Job,
    )

    await worker.run()
