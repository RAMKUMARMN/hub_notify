from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

# Create session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""
    pass


async def get_db():
    """Dependency to yield database sessions to FastAPI routes."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
