from __future__ import annotations

import asyncio
import logging

from app.core.retry_worker import RetryWorker

from app.queue.producer import publish_to_queue

from app.queue.schemas import (
FileUploadPayload,
DOC_EXTRACT_QUEUE,
DOC_EXTRACT_DLQ,
DOC_CHUNK_QUEUE,
)


logger = logging.getLogger(__name__)

class ExtractWorker(RetryWorker):

    queue_name = DOC_EXTRACT_QUEUE
 
    dlq_queue = DOC_EXTRACT_DLQ

    retry_1m_queue = None
    retry_5m_queue = None
    retry_30m_queue = None

    def parse_message(
        self,
        body: str,
    ):

       return FileUploadPayload.model_validate_json(
        body
    )

    async def handle(
    self,
    payload: FileUploadPayload,
):

        logger.info(
        f"Extracting document: "
        f"{payload.filename}"
    )

    # ==========================================
    # SIMULATED EXTRACTION
    # ==========================================

        extracted_text = """
    This is extracted text from the document.
    """

        logger.info(
        f"Extraction completed: "
        f"{payload.filename}"
    )

    # ==========================================
    # SEND TO CHUNK PIPELINE
    # ==========================================
        logger.info(
    f"Publishing to {DOC_CHUNK_QUEUE}"
)
        await publish_to_queue(
            DOC_CHUNK_QUEUE,
        {
            "document_id": payload.document_id,
            "text": extracted_text,
        },
    )

async def run():
    worker = ExtractWorker()

    await worker.run()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())




