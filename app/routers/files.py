from fastapi import APIRouter

from app.queue.producer import publish_to_queue
from app.queue.schemas import (
    FILE_UPLOAD_QUEUE,
    FileUploadPayload,
)

router = APIRouter(tags=["Files"])


@router.post("/files/upload")

async def upload_file(
    payload: FileUploadPayload,
):

    await publish_to_queue(
        FILE_UPLOAD_QUEUE,
        payload.model_dump(),
    )

    return {
        "success": True,
        "message": "File queued for processing",
    }