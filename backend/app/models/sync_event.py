from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(String, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
