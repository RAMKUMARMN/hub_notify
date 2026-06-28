from __future__ import annotations

import asyncio
import logging

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)


class RetryWorker:

    # =====================================================
    # MUST BE OVERRIDDEN
    # =====================================================

    queue_name: str = ""

    retry_1m_queue: str = ""
    retry_5m_queue: str = ""
    retry_30m_queue: str = ""

    dlq_queue: str = ""

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self):

        self.channel: aio_pika.Channel | None = None

    # =====================================================
    # ABSTRACT METHODS
    # =====================================================

    def parse_message(
        self,
        body: str,
    ):
        raise NotImplementedError

    async def handle(
        self,
        payload,
    ):
        raise NotImplementedError

    # =====================================================
    # PUBLISH TO QUEUE
    # =====================================================
   
    async def publish_to_queue(
        self,
        queue_name: str,
        payload,
    ):
        print("PUBLISHING TO:", queue_name)

        await self.channel.default_exchange.publish(

            aio_pika.Message(
                body=payload.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),

            routing_key=queue_name,
        )

    # =====================================================
    # PROCESS MESSAGE
    # =====================================================

    async def process_message(
        self,
        message: aio_pika.IncomingMessage,
    ):

        payload = self.parse_message(
            message.body.decode()
        )

        try:

            await self.handle(payload)

            await message.ack()

        except Exception:

            logger.exception(f"Worker failed: {payload}")

            payload.attempt += 1

            # =============================================
            # RETRY 1 MIN
            # =============================================

            if payload.attempt == 2:

                logger.warning(
                    "Retrying after 1 minute"
                )

                await self.publish_to_queue(
                    self.retry_1m_queue,
                    payload,
                )

            # =============================================
            # RETRY 5 MIN
            # =============================================

            elif payload.attempt == 3:

                logger.warning(
                    "Retrying after 5 minutes"
                )

                await self.publish_to_queue(
                    self.retry_5m_queue,
                    payload,
                )

            # =============================================
            # RETRY 30 MIN
            # =============================================

            elif payload.attempt == 4:

                logger.warning(
                    "Retrying after 30 minutes"
                )

                await self.publish_to_queue(
                    self.retry_30m_queue,
                    payload,
                )

            # =============================================
            # FINAL DLQ
            # =============================================

            else:

                logger.error(
                    "Max retries exceeded"
                )

                await self.publish_to_queue(
                    self.dlq_queue,
                    payload,
                )

            await message.ack()

    # =====================================================
    # RUN WORKER
    # =====================================================

    async def run(self):

        # =============================================
        # CONNECT TO RABBITMQ
        # =============================================

        connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )

        self.channel = await connection.channel()

        # =============================================
        # GET MAIN QUEUE
        # =============================================

        process_queue = await self.channel.get_queue(
            self.queue_name
        )

        # =============================================
        # START CONSUMER
        # =============================================

        await process_queue.consume(
            self.process_message
        )

        logger.info(
            f"{self.queue_name} worker started"
        )

        # =============================================
        # KEEP WORKER ALIVE
        # =============================================

        await asyncio.Future()