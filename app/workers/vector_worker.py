from __future__ import annotations

import asyncio
import logging

from app.core.retry_worker import RetryWorker

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

    retry_1m_queue = None
    retry_5m_queue = None
    retry_30m_queue = None

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

    async def handle(
        self,
        payload: VectorIndexPayload,
    ):

        logger.info(
            f"Indexing vector for "
            f"document={payload.document_id} "
            f"chunk={payload.chunk_index}"
        )

        # ======================================
        # MOCK VECTOR DATABASE INSERT
        # ======================================

        vector_record = {
            "document_id": payload.document_id,
            "chunk_index": payload.chunk_index,
            "text": payload.chunk_text,
            "embedding": payload.embedding,
        }

        # Simulate DB insert
        print(
            "\nVECTOR STORED:\n",
            vector_record,
        )

        logger.info(
            "Vector indexing completed successfully"
        )


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