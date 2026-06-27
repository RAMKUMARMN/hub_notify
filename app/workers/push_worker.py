"""
Bulk Push worker — preprocesses push notification jobs
and publishes individual push tasks to RabbitMQ.

Queue: notify.bulk_push
"""
from __future__ import annotations

import asyncio
import logging

from app.channels.push import send_push
from app.core.retry_worker import RetryWorker
from app.queue.schemas import (
NotifyPayload,
PUSH_PROCESS_QUEUE,
PUSH_RETRY_1M,
PUSH_RETRY_5M,
PUSH_RETRY_30M,
PUSH_DLQ,
)

logger = logging.getLogger(__name__)

class PushWorker(RetryWorker):


  queue_name = PUSH_PROCESS_QUEUE

  retry_1m_queue = PUSH_RETRY_1M
  retry_5m_queue = PUSH_RETRY_5M
  retry_30m_queue = PUSH_RETRY_30M

  dlq_queue = PUSH_DLQ

# =============================================
# PARSE MESSAGE
# =============================================

  def parse_message(
        self,
        body: str,
    ):
        return NotifyPayload.model_validate_json(body)

# =============================================
# BUSINESS LOGIC
# =============================================

  async def handle(
    self,
    payload: NotifyPayload,
):

    logger.info(
        f"Sending push notification "
        f"to {payload.recipient}"
    )

    send_push(
        to=payload.recipient,
        title=payload.subject or "",
        body=payload.body,
    )

    logger.info(
        f"Push notification sent "
        f"to {payload.recipient}"
    )

async def run():


 worker = PushWorker()

 await worker.run()

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(run())

