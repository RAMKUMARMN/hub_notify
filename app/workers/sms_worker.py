
from __future__ import annotations

import asyncio
import logging

from app.channels.sms import send_sms
from app.core.retry_worker import RetryWorker
from app.queue.schemas import (
    NotifyPayload,
    SMS_PROCESS_QUEUE,
    SMS_RETRY_1M,
    SMS_RETRY_5M,
    SMS_RETRY_30M,
    SMS_DLQ,
)

logger = logging.getLogger(__name__)


class SMSWorker(RetryWorker):

    # =====================================================
    # MAIN PROCESS QUEUE
    # =====================================================

    queue_name = SMS_PROCESS_QUEUE

    # =====================================================
    # RETRY QUEUES
    # =====================================================

    retry_1m_queue = SMS_RETRY_1M
    retry_5m_queue = SMS_RETRY_5M
    retry_30m_queue = SMS_RETRY_30M

    # =====================================================
    # FINAL DLQ
    # =====================================================

    dlq_queue = SMS_DLQ

    # =====================================================
    # PARSE MESSAGE
    # =====================================================

    def parse_message(
        self,
        body: str,
    ):
        return NotifyPayload.model_validate_json(body)

    # =====================================================
    # BUSINESS LOGIC
    # =====================================================

    async def handle(
        self,
        payload: NotifyPayload,
    ):

        logger.info(
            f"Sending SMS to "
            f"{payload.recipient}"
        )

        send_sms(
            to=payload.recipient,
            body=payload.body,
        )

        logger.info(
            f"SMS sent successfully to "
            f"{payload.recipient}"
        )


# =========================================================
# START WORKER
# =========================================================

async def run():

    worker = SMSWorker()

    await worker.run()


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(run())

