import logging

logger = logging.getLogger(__name__)


class AIClient:

    async def ingest_document(
        self,
        document_id: str,
        user_id: str,
        storage_path: str,
        file_type: str,
    ):
        """
        Placeholder until AI Router exposes
        ingestion endpoints.
        """

        logger.info(
            "AI ingest request: %s",
            document_id,
        )

        return {
            "status": "pending",
        }


ai_client = AIClient()