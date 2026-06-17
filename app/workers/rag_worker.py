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
from app.services.ai_client import (
    ai_client,
)
from app.queue.job_store import job_store
from app.queue.schemas import Job, JobStatus

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[Job] = asyncio.Queue()


def enqueue(job: Job) -> None:
    _queue.put_nowait(job)


async def _process(job: Job) -> None:

    print("=" * 60)
    print("RAG WORKER STARTED")
    print(job)
    print("=" * 60)

    try:

        payload = job.payload

        print("PAYLOAD:", payload)

        document_id = payload.get("document_id")
        user_id = payload.get("user_id")
        storage_path = payload.get("storage_path")
        file_type = payload.get("file_type")
        filename = payload.get("filename")

        print("DOCUMENT:", filename)

        logger.info(
            "Processing document %s",
            filename,
        )

        await job_store.update(
            job.job_id,
            JobStatus.PROCESSING,
            progress=10,
            message=f"Received {filename}",
        )

        print("JOB STORE UPDATE SUCCESS")

        await ai_client.ingest_document(
            document_id=document_id,
            user_id=user_id,
            storage_path=storage_path,
            file_type=file_type,
        )

        print("AI CLIENT SUCCESS")

    except Exception as e:

        print("RAG WORKER ERROR:", e)

        raise

    
async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="rag.bulk_ingest",
        processor=_process,
        model=Job,
    )

    await worker.run()
