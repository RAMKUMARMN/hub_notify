import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your queue setup utility
from app.queue.utils import setup_queues

from app.routers.notify import router as notify_router
from app.routers.jobs import router as jobs_router
from app.routers.files import router as files_router

from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
    ai_worker,
    embedding_worker,
    memory_worker,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize RabbitMQ infrastructure first
    await setup_queues()
    
    # 2. Start all queue workers as background tasks
    workers = [

    file_worker.run,
    rag_worker.run,
    email_worker.run,
    sms_worker.run,
    analytics_worker.run,
    ai_worker.run,
    embedding_worker.run,
    memory_worker.run,

    

]

    tasks = [asyncio.create_task(w()) for w in workers]
    
    yield
    
    # 3. Graceful shutdown
    for t in tasks:
        t.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    title="CixioHub Notify Service",
    version="1.0.0",
    description="Notification service — Email, SMS, Push, WhatsApp + Queue Dashboard",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notify_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")



@app.get("/api/v1/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "cixiohub-notify"}