from __future__ import annotations

import logging

import httpx
from app.config import settings


logger = logging.getLogger(__name__)

AI_SERVICE_URL = settings.ai_service_url


class AIClient:

    async def ingest_document(
        self,
        document_id: str,
        user_id: str,
        storage_path: str,
        file_type: str,
        filename: str,
    ):

        payload = {
            "document_id": document_id,
            "user_id": user_id,
            "file_path": storage_path,
            "file_type": file_type,
            "filename": filename,
        }

        logger.info(
            "Sending %s to AI service...",
            filename,
        )

        async with httpx.AsyncClient(timeout=300) as client:

            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/rag/ingest",
                json=payload,
            )

            response.raise_for_status()

            result = response.json()

            logger.info(
                "AI completed ingestion. Stored %d chunks.",
                result["chunks_stored"],
            )

            return result


ai_client = AIClient()