import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.notify import router as notify_router
from app.routers.jobs import router as jobs_router
from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
)
from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
    reminder_worker,
)
# 👈 Import the actual central queue consumer entry point
from app.queue.consumer import run_consumer as start_queue_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start all queue workers + central consumer as background tasks
    workers = [
    file_worker.run,
    rag_worker.run,
    email_worker.run,
    sms_worker.run,
    analytics_worker.run,
    reminder_worker.run,
    start_queue_consumer,
]
    tasks = [asyncio.create_task(w()) for w in workers]
    yield
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


@app.get("/api/v1/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "cixiohub-notify"}