import asyncio
from contextlib import asynccontextmanager
from app.queue.producer import setup_queues
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.files import router as files_router

from app.routers.notify import router as notify_router
from app.routers.jobs import router as jobs_router
from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
)
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app):

    await setup_queues()

    print("Application started")

    yield




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
app.include_router(
    files_router,
    prefix="/api/v1",
)

@app.get("/api/v1/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "cixiohub-notify"}

