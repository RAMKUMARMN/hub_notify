import asyncio
import logging
from app.workers.file_worker import run as file_worker
from app.workers.rag_worker import run as rag_worker
from app.workers.email_worker import run as email_worker
from app.workers.sms_worker import run as sms_worker
from app.workers.analytics_worker import run as analytics_worker
from app.workers.ai_worker import run as ai_worker
from app.workers.embedding_worker import run as embedding_worker
from app.workers.memory_worker import run as memory_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():

    logger.info("=" * 60)
    logger.info("Starting SmartHub Notify Workers...")
    logger.info("=" * 60)
    
    await asyncio.gather(
        file_worker(),
        rag_worker(),
        email_worker(),
        sms_worker(),
        analytics_worker(),
        ai_worker(),
        embedding_worker(),
        memory_worker(),
    )


if __name__ == "__main__":
    asyncio.run(main())