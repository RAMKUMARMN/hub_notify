from __future__ import annotations

import asyncio
import logging
import os
from app.core.retry_worker import RetryWorker

from app.queue.producer import publish_to_queue
from app.services.document_pipeline import extract_text
from app.queue.schemas import (
FileUploadPayload,
DOC_EXTRACT_QUEUE,
DOC_EXTRACT_DLQ,
DOC_CHUNK_QUEUE,
)
from app.queue.schemas import ChunkPayload



logger = logging.getLogger(__name__)

class ExtractWorker(RetryWorker):

    queue_name = DOC_EXTRACT_QUEUE
 
    dlq_queue = DOC_EXTRACT_DLQ

    retry_1m_queue = "doc.extract.retry.1m"
    retry_5m_queue = "doc.extract.retry.5m"
    retry_30m_queue = "doc.extract.retry.30m"

    def parse_message(
        self,
        body: str,
    ):

       return FileUploadPayload.model_validate_json(
        body
    )

    async def handle(self, payload: FileUploadPayload):

        logger.info(f"Extracting document: {payload.filename}")
        print("\n========== DEBUG ==========")
        print("Current Working Directory:", os.getcwd())
        print("Payload storage_path:", payload.storage_path)

        abs_path = os.path.abspath(payload.storage_path)

        print("Absolute path:", abs_path)
        print("File exists?:", os.path.exists(abs_path))

        if os.path.exists(abs_path):

            print("Filesize:", os.path.getsize(abs_path))

        print("===========================\n")
        print("STEP 1: starting extraction")

        extracted_text = extract_text(payload.storage_path, payload.filename)
        print("STEP 2: extraction complete")
        print("Extracted length:", len(extracted_text))

        if not extracted_text.strip():
           raise ValueError(f"No text extracted from {payload.filename}")

        chunk_payload = ChunkPayload(
        document_id=payload.document_id,
        text=extracted_text,
        filename=payload.filename,
        user_id=payload.uploaded_by,
    )
        print("STEP 3: creating chunk payload")
        print("SENDING TO QUEUE:", DOC_CHUNK_QUEUE)
        await publish_to_queue(DOC_CHUNK_QUEUE, chunk_payload.model_dump())
        

async def run():
    worker = ExtractWorker()

    await worker.run()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())




