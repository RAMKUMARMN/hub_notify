from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)

class BaseWorker(ABC):


    queue_name: str = ""

def __init__(self):

    self.connection = None
    self.channel = None
    self.queue = None

# =====================================================
# CONNECT TO RABBITMQ
# =====================================================

async def connect(self):

    self.connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    self.channel = await self.connection.channel()

    self.queue = await self.channel.get_queue(
        self.queue_name
    )

# =====================================================
# ABSTRACT HANDLER
# =====================================================

@abstractmethod
async def handle(
    self,
    payload,
):
    """
    Implement business logic
    in child worker.
    """
    pass

# =====================================================
# PROCESS MESSAGE
# =====================================================

async def process_message(
    self,
    message: aio_pika.IncomingMessage,
):

    try:

        payload = self.parse_message(
            message.body.decode()
        )

        logger.info(
            f"[{self.queue_name}] "
            f"Processing message"
        )

        await self.handle(payload)

        await message.ack()

        logger.info(
            f"[{self.queue_name}] "
            f"Message processed"
        )

    except Exception:

        logger.exception(
            f"[{self.queue_name}] "
            f"Worker failed"
        )

        await self.on_failure(
            message
        )

# =====================================================
# FAILURE HANDLER
# =====================================================

async def on_failure(
    self,
    message: aio_pika.IncomingMessage,
):

    await message.reject(
        requeue=False
    )

# =====================================================
# PARSE MESSAGE
# =====================================================

def parse_message(
    self,
    body: str,
):

    return body

# =====================================================
# START WORKER
# =====================================================

async def run(self):

    await self.connect()

    await self.queue.consume(
        self.process_message
    )

    logger.info(
        f"{self.__class__.__name__} started"
    )

    await asyncio.Future()

