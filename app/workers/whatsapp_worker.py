from __future__ import annotations

import asyncio
import logging

from app.channels.whatsapp import send_whatsapp
from app.core.retry_worker import RetryWorker
from app.queue.schemas import (
NotifyPayload,
WHATSAPP_PROCESS_QUEUE,
WHATSAPP_RETRY_1M,
WHATSAPP_RETRY_5M,
WHATSAPP_RETRY_30M,
WHATSAPP_DLQ,
)

logger = logging.getLogger(__name__)

class WhatsAppWorker(RetryWorker):


  queue_name = WHATSAPP_PROCESS_QUEUE

  retry_1m_queue = WHATSAPP_RETRY_1M
  retry_5m_queue = WHATSAPP_RETRY_5M
  retry_30m_queue = WHATSAPP_RETRY_30M

  dlq_queue = WHATSAPP_DLQ

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
        f"Sending WhatsApp message "
        f"to {payload.recipient}"
    )

    send_whatsapp(
        to=payload.recipient,
        body=payload.body,
    )

    logger.info(
        f"WhatsApp message sent "
        f"to {payload.recipient}"
    )

async def run():

    worker = WhatsAppWorker()

    await worker.run()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(run())

