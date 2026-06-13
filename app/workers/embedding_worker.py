import logging

from app.queue.schemas import Job
from app.workers.worker_base import RabbitMQWorker

logger = logging.getLogger(__name__)


async def _process(job: Job) -> None:

    print(
        f"EMBEDDING WORKER PROCESSING: {job.job_id}"
    )

    logger.info(
        "Processing embedding job %s",
        job.job_id,
    )

    # Future embedding logic
    # Generate vector embeddings
    # Store vectors in ChromaDB


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="embedding.processing",
        processor=_process,
        model=Job,
    )

    await worker.run()