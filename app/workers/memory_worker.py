import logging

from app.queue.schemas import Job
from app.workers.worker_base import RabbitMQWorker

logger = logging.getLogger(__name__)


async def _process(job: Job) -> None:

    print(
        f"MEMORY WORKER PROCESSING: {job.job_id}"
    )

    logger.info(
        "Processing memory job %s",
        job.job_id,
    )
    # Future memory logic
    # Conversation summarization
    # Long-term memory storage


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="memory.processing",
        processor=_process,
        model=Job,
    )

    await worker.run()