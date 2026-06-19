import logging

from app.queue.schemas import Job
from app.workers.worker_base import RabbitMQWorker
from app.queue.producer import publish_job
from app.queue.schemas import JobType

logger = logging.getLogger(__name__)


async def _process(job: Job) -> None:

    print(
        f"EMBEDDING WORKER PROCESSING: {job.job_id}"
    )

    logger.info(
        "Processing embedding job %s",
        job.job_id,
    )

    next_job = Job(
        job_type=JobType.AI_ORCHESTRATION,
        queue="ai.orchestration",
        label="AI orchestration",
        payload=job.payload,
    )

    await publish_job(next_job)

    print(
        f"EMBEDDING COMPLETE → {next_job.queue}"
    )


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="embedding.processing",
        processor=_process,
        model=Job,
    )

    await worker.run()