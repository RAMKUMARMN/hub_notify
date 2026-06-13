import json
import logging
from typing import Callable, Type

import aio_pika

from app.config import settings

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

    async def process_message(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:

        

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

                

            except Exception as exc:

                print("\nERROR OCCURRED:")
                print(type(exc).__name__)
                print(exc)

                logger.exception(
                    "Error processing message from %s: %s",
                    self.queue_name,
                    exc,
                )

                raise

    async def run(self) -> None:

        print(
            f"WORKER BASE STARTING: {self.queue_name}"
        )

        connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )

        channel = await connection.channel()

        await channel.set_qos(
            prefetch_count=10
        )

        queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
        )

        await queue.consume(
            self.process_message
        )

        print(
            f"LISTENING ON QUEUE: {self.queue_name}"
        )

        import asyncio
        await asyncio.Future()