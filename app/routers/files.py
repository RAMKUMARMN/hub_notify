from fastapi import APIRouter, UploadFile, File, HTTPException
from app.queue.producer import publish
from app.queue.schemas import NotifyPayload
import uuid
import aiofiles
import os

router = APIRouter(prefix="/files", tags=["files"])

async def _save_and_publish(file: UploadFile, mode: str):
    try:
        os.makedirs("storage", exist_ok=True)
        file_path = f"storage/{uuid.uuid4()}_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # LOGIC CHANGE: Select channel based on mode
        # 'ai_analyze' goes to AI queue, 'store_only' goes to file upload queue
        target_channel = "ai_orchestration" if mode == "ai_analyze" else "file_upload"
        
        payload = NotifyPayload(
            job_id=str(uuid.uuid4()),
            channel=target_channel,
            recipient="system",
            data={
                "file_path": file_path,
                "process_mode": mode
            }
        )
        
        try:
            await publish(payload)
        except Exception as e:
            print(f"CRITICAL: Failed to publish to RabbitMQ: {e}")
            raise HTTPException(status_code=500, detail="Could not queue task")
            
        return {
            "status": "queued",
            "job_id": payload.job_id,
            "file_path": file_path,
            "channel": target_channel,
            "mode": mode
        }
        
    except Exception as e:
        print(f"ERROR: File process failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/store")
async def upload_for_storage(file: UploadFile = File(...)):
    """Stores the file (Queue: file_upload)."""
    return await _save_and_publish(file, "store_only")

@router.post("/upload/ai")
async def upload_for_ai(file: UploadFile = File(...)):
    """Stores the file and triggers AI analysis (Queue: ai_orchestration)."""
    return await _save_and_publish(file, "ai_analyze")