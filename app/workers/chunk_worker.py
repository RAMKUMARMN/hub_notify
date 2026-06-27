from __future__ import annotations


import asyncio
import logging

from app.core.retry_worker import RetryWorker

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
     retry_1m_queue = None
     retry_5m_queue = None
     retry_30m_queue = None

     def parse_message(
       self,
       body: str,
    ):

        return ChunkPayload.model_validate_json(
        body
    )

     async def handle(
    self,
    payload: ChunkPayload,
):

          logger.info(
        f"Chunking document: "
        f"{payload.document_id}"
    )

    # ==========================================
    # SIMPLE CHUNKING
    # ==========================================

          text = payload.text

          chunk_size = 100

          chunks = [
           text[i:i + chunk_size]
           for i in range(
            0,
            len(text),
            chunk_size,
        )
    ]

          logger.info(
        f"Generated {len(chunks)} chunks"
    )

    # ==========================================
    # SEND TO EMBEDDING QUEUE
    # ==========================================

          for index, chunk in enumerate(chunks):
            embedding_payload = EmbeddingPayload(
            document_id=payload.document_id,
            chunk_index=index,
            chunk_text=chunk,
        )

            await publish_to_queue(
            EMBEDDING_QUEUE,
            embedding_payload.model_dump(),
        )

          logger.info(
        f"Chunks published for embeddings")


async def run():
    
    worker = ChunkWorker()

    await worker.run()





if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run())



