from __future__ import annotations

from app.services.document_pipeline import index_chunk
import asyncio
import logging

from app.core.retry_worker import RetryWorker
from app.services.document_pipeline import chunk_text

from app.queue.producer import publish_to_queue

from app.queue.schemas import (
ChunkPayload,
EmbeddingPayload,
DOC_CHUNK_QUEUE,
DOC_CHUNK_DLQ,
EMBEDDING_QUEUE,
)

logger = logging.getLogger(__name__)
class ChunkWorker(RetryWorker):
    queue_name = DOC_CHUNK_QUEUE
    dlq_queue = DOC_CHUNK_DLQ
    retry_1m_queue = "doc.chunk.retry.1m"
    retry_5m_queue = "doc.chunk.retry.5m"
    retry_30m_queue = "doc.chunk.retry.30m"
    def parse_message(self, body: str):
        return ChunkPayload.model_validate_json(body)
    
    
    async def handle(self, payload: ChunkPayload):

        print("CHUNK WORKER RECEIVED MESSAGE")

        chunks = chunk_text(payload.text)

        total = len(chunks)

        print("TOTAL CHUNKS:", total)

        for i, chunk in enumerate(chunks):

            print(f"Publishing embedding chunk {i}")

            await publish_to_queue(
            EMBEDDING_QUEUE,
            EmbeddingPayload(
                document_id=payload.document_id,
                chunk_index=i,
                chunk_text=chunk,
                filename=payload.filename,
                user_id=payload.user_id,
                total_chunks=total,
            ).model_dump(),
        )

        print("ALL CHUNKS PUBLISHED")

async def run():
    
    worker = ChunkWorker()

    await worker.run()





if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())



