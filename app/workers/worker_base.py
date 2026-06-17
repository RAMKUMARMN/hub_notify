import json
import logging
from typing import Callable, Type
from app.queue.retry_handler import handle_retry
import aio_pika
import asyncio
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

                print(
                    f"PROCESSING "
                    f"retry_count="
                    f"{payload_dict.get('retry_count', 0)}"
                )

                await self.processor(payload)

                

            except Exception as exc:

                logger.exception(
                    "Error processing message from %s: %s",
                    self.queue_name,
                    exc,
                )

                await handle_retry(
                    channel=self.channel,
                    queue_name=self.queue_name,
                    message_data=payload_dict,
                )

    async def run(self) -> None:

        print(
            f"WORKER BASE STARTING: {self.queue_name}"
        )

        print(
            "CONNECTING TO:",
            settings.rabbitmq_url
        )

        try:
            connection = await aio_pika.connect_robust(
                settings.rabbitmq_url
            )

            print(
                "CONNECTED SUCCESSFULLY"
            )

        except Exception as e:

            print(
                "RABBITMQ ERROR:",
                e
            )

            raise

        channel = await connection.channel()
     

        main_queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
        )
        print(
            f"DECLARED QUEUE: {self.queue_name}"
        )


        await main_queue.consume(
            self.process_message
        )

        print(
            f"LISTENING ON QUEUE: {self.queue_name}"
        )

        await asyncio.Future()

        