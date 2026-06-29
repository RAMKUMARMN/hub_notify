from __future__ import annotations

import asyncio
import logging

from app.core.retry_worker import RetryWorker
from app.queue.producer import publish_to_queue
from app.services.document_pipeline import encode_text

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

    retry_1m_queue = "embedding.retry.1m"
    retry_5m_queue = "embedding.retry.5m"
    retry_30m_queue = "embedding.retry.30m"
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


    async def handle(self, payload: EmbeddingPayload):
        print("\n========== EMBEDDING WORKER ==========")
        print("Document ID:", payload.document_id)
        print("Chunk Index:", payload.chunk_index)
        print("Filename:", payload.filename)
        print("Chunk Length:", len(payload.chunk_text))
        print("======================================")
    # CPU-heavy — run off the event loop
        print("STEP 1: generating embedding")
        embedding = await asyncio.to_thread(encode_text, payload.chunk_text)
        print("STEP 2: embedding generated")
        print("Embedding dimensions:", len(embedding))
        print("STEP 3: publishing vector payload")
        await publish_to_queue(VECTOR_INDEX_QUEUE, {
        "document_id": payload.document_id,
        "chunk_index": payload.chunk_index,
        "chunk_text": payload.chunk_text,
        "embedding": embedding,
        "filename": payload.filename,
        "user_id": payload.user_id,
        "total_chunks": payload.total_chunks,
    })
        print("STEP 4: vector payload published")
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