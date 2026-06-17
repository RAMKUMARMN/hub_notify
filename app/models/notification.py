from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    recipient = Column(String)

    channel = Column(String)

    subject = Column(String)

    body = Column(Text)

    status = Column(String, default="PENDING")

    attempts = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )