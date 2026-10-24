from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.database import Base


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    key = Column(String(255), primary_key=True, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
