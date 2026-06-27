from __future__ import annotations

import asyncio
import logging

from app.core.retry_worker import RetryWorker
from app.queue.producer import publish_to_queue

from app.queue.schemas import (
    EmbeddingPayload,
    VectorIndexPayload,
    EMBEDDING_QUEUE,
    EMBEDDING_DLQ,
    VECTOR_INDEX_QUEUE,
)

logger = logging.getLogger(__name__)


class EmbeddingWorker(RetryWorker):

    # ==========================================
    # MAIN QUEUE
    # ==========================================

    queue_name = EMBEDDING_QUEUE

    # ==========================================
    # DLQ
    # ==========================================

    dlq_queue = EMBEDDING_DLQ

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

        return EmbeddingPayload.model_validate_json(
            body
        )

    # ==========================================
    # BUSINESS LOGIC
    # ==========================================

    async def handle(
        self,
        payload: EmbeddingPayload,
    ):

        logger.info(
            f"Generating embedding for "
            f"document={payload.document_id} "
            f"chunk={payload.chunk_index}"
        )

        # ======================================
        # TEMPORARY MOCK EMBEDDING
        # ======================================

        fake_embedding = [
            0.12,
            0.45,
            0.78,
            0.99,
        ]

        logger.info(
            "Embedding generated successfully"
        )

        # ======================================
        # SEND TO VECTOR INDEX QUEUE
        # ======================================

        vector_payload = VectorIndexPayload(
            document_id=payload.document_id,
            chunk_index=payload.chunk_index,
            chunk_text=payload.chunk_text,
            embedding=fake_embedding,
        )

        await publish_to_queue(
            VECTOR_INDEX_QUEUE,
            vector_payload.model_dump(),
        )

        logger.info(
            "Published to vector.index queue"
        )


# ==============================================
# START WORKER
# ==============================================

async def run():

    worker = EmbeddingWorker()

    await worker.run()


# ==============================================
# ENTRYPOINT
# ==============================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(run())