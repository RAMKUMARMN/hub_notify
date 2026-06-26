from __future__ import annotations

import logging
import os
import httpx

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000/api/v1",
)


class BackendClient:
    """
    Client responsible for communicating with hub_backend.
    """

    async def mark_document_processed(
        self,
        document_id: str,
    ) -> dict:

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.patch(
                f"{BACKEND_URL}/documents/{document_id}/processed"
            )

            response.raise_for_status()

            result = response.json()

            logger.info(
                "Marked document %s as processed.",
                document_id,
            )

            return result


backend_client = BackendClient()