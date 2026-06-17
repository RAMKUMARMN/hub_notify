import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db

from app.routers.notify import router as notify_router
from app.routers.jobs import router as jobs_router
from app.workers import (
    analytics_worker,
    email_worker,
    file_worker,
    rag_worker,
    sms_worker,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    from app.database import engine, Base
    from app.models import (  # noqa: F401 (Registers models with Base)
        IndividualNotification,
        NotificationJob,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start all queue workers as background tasks
    workers = [
        file_worker.run,
        rag_worker.run,
        email_worker.run,
        sms_worker.run,
        analytics_worker.run,
    ]
    tasks = [asyncio.create_task(w()) for w in workers]

    # Start the scheduled notification database poller
    from app.scheduler import start_scheduler, stop_scheduler
    scheduler = start_scheduler()

    yield

    # Stop the scheduled notification database poller
    await stop_scheduler(scheduler)

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    # Dispose of engine connection pool
    await engine.dispose()


app = FastAPI(
    title="CixioHub Notify Service",
    version="1.0.0",
    description=(
        "Notification service — Email, SMS, Push, WhatsApp + Queue Dashboard"
    ),
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
async def health(db=Depends(get_db)):
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {
        "status": "ok",
        "service": "cixiohub-notify",
        "database": db_status,
    }
