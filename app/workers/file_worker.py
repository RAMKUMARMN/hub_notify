from __future__ import annotations

import asyncio
import logging

from app.core.retry_worker import RetryWorker
from app.queue.schemas import (
    FileUploadPayload,
    FILE_UPLOAD_QUEUE,
    FILE_RETRY_1M,
    FILE_RETRY_5M,
    FILE_RETRY_30M,
    FILE_UPLOAD_DLQ,
)
from app.queue.producer import publish_to_queue

from app.queue.schemas import (
    DOC_EXTRACT_QUEUE,
)

logger = logging.getLogger(__name__)


class FileWorker(RetryWorker):

    queue_name = FILE_UPLOAD_QUEUE

    retry_1m_queue = FILE_RETRY_1M
    retry_5m_queue = FILE_RETRY_5M
    retry_30m_queue = FILE_RETRY_30M

    dlq_queue = FILE_UPLOAD_DLQ 

    # =====================================================
    # PARSE MESSAGE
    # =====================================================

    def parse_message(
        self,
        body: str,
    ):

        return FileUploadPayload.model_validate_json(
            body
        )

    # =====================================================
    # BUSINESS LOGIC
    # =====================================================

    async def handle(
        self,
        payload: FileUploadPayload,
      
    ):
        await publish_to_queue(
             DOC_EXTRACT_QUEUE,
             payload.model_dump(),
            )

        logger.info(
            f"Processing file: "
            f"{payload.filename}"
        )

        # =================================================
        # PLACEHOLDER PROCESSING
        # =================================================

        # Later:
        # - OCR
        # - Chunking
        # - Embeddings
        # - Metadata extraction
        # - AI indexing

        await asyncio.sleep(2)

        logger.info(
            f"File processed successfully: "
            f"{payload.filename}"
        )


# =========================================================
# START WORKER
# =========================================================

async def run():

    worker = FileWorker()

    await worker.run()


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())