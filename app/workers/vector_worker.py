from __future__ import annotations

import asyncio
import logging
import time

from app.core.retry_worker import RetryWorker
from app.services.document_pipeline import index_chunk

from app.queue.schemas import (
    VectorIndexPayload,
    VECTOR_INDEX_QUEUE,
    VECTOR_INDEX_DLQ,
)

logger = logging.getLogger(__name__)


class VectorWorker(RetryWorker):

    # ==========================================
    # MAIN QUEUE
    # ==========================================

    queue_name = VECTOR_INDEX_QUEUE

    # ==========================================
    # DLQ
    # ==========================================

    dlq_queue = VECTOR_INDEX_DLQ

    # ==========================================
    # NO RETRIES FOR NOW
    # ==========================================

    retry_1m_queue = "vector.retry.1m"
    retry_5m_queue = "vector.retry.5m"
    retry_30m_queue = "vector.retry.30m"

    # ==========================================
    # PARSE MESSAGE
    # ==========================================

    def parse_message(
        self,
        body: str,
    ):

        return VectorIndexPayload.model_validate_json(
            body
        )

    # ==========================================
    # BUSINESS LOGIC
    # ==========================================

   
  
    async def handle(self, payload: VectorIndexPayload):
        print("\n========== VECTOR WORKER ==========")
        print("Document ID:", payload.document_id)
        print("Chunk Index:", payload.chunk_index)
        print("Filename:", payload.filename)
        print("Embedding size:", len(payload.embedding))
        print("===================================")

        print("STEP 1: indexing chunk")

        chunk_id = await asyncio.to_thread(
        index_chunk,
        filename=payload.filename,
        chunk_index=payload.chunk_index,
        chunk_text=payload.chunk_text,
        embedding=payload.embedding,
        document_id=payload.document_id,
    )
        logger.info(f"Indexed {chunk_id}")
        print("STEP 2: indexed successfully")
        print("Stored Chunk ID:", chunk_id)

# ==============================================
# START WORKER
# ==============================================

async def run():

    worker = VectorWorker()

    await worker.run()


# ==============================================
# ENTRYPOINT
# ==============================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(run())