import logging

from app.queue.schemas import Job
from app.workers.worker_base import RabbitMQWorker
from app.queue.producer import publish_job
from app.queue.schemas import JobType

logger = logging.getLogger(__name__)


async def _process(job: Job) -> None:

    print(
        f"AI WORKER PROCESSING: {job.job_id}"
    )

    logger.info(
        "Processing AI orchestration job %s",
        job.job_id,
    )

    next_job = Job(
        job_type=JobType.MEMORY_PROCESSING,
        queue="memory.processing",
        label="Memory processing",
        payload=job.payload,
    )

    await publish_job(next_job)

    print(
        f"AI ORCHESTRATION COMPLETE → {next_job.queue}"
    )

   

    


async def run() -> None:

    worker = RabbitMQWorker(
        queue_name="ai.orchestration",
        processor=_process,
        model=Job,
    )

    await worker.run()