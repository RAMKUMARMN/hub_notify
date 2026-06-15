import json
import logging
from typing import Callable, Type

import aio_pika

from app.config import settings
from app.queue.retry_handler import handle_retry

logger = logging.getLogger(__name__)


class RabbitMQWorker:

    def __init__(
        self,
        queue_name: str,
        processor: Callable,
        model: Type,
    ):
        self.queue_name = queue_name
        self.processor = processor
        self.model = model
        self.channel = None

    async def process_message(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        
        payload_dict = {}

        async with message.process(requeue=False):

            try:

                raw_body = message.body.decode()

                payload_dict = json.loads(raw_body)

                payload = self.model(**payload_dict)

                logger.info(
                    "Received message from %s",
                    self.queue_name,
                )

                await self.processor(payload)

                logger.info(
                    "Successfully processed message from %s",
                    self.queue_name,
                )

            except Exception as exc:

                print("\nERROR OCCURRED:")
                print(type(exc).__name__)
                print(exc)

                logger.exception(
                    "Error processing message from %s: %s",
                    self.queue_name,
                    exc,
                )

                await handle_retry(
                    self.channel,
                    self.queue_name,
                    payload_dict,
                )

    async def run(self) -> None:

        print(
            f"WORKER BASE STARTING: {self.queue_name}"
        )

        connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )

        self.channel = await connection.channel()

        await self.channel.set_qos(
            prefetch_count=10
        )

        main_queue = await self.channel.declare_queue(
            self.queue_name,
             durable=True,
        )

        retry_queue = await self.channel.declare_queue(
             f"{self.queue_name}.retry",
             durable=True,
)

        await main_queue.consume(
            self.process_message
        )

        await retry_queue.consume(
         self.process_message
        )
        print(
            f"LISTENING ON QUEUE: {self.queue_name}"
             f" and {self.queue_name}.retry"
        )

        import asyncio
        await asyncio.Future()