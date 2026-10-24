from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(String, primary_key=True, index=True)
    bitrix_deal_id = Column(String, unique=True, index=True, nullable=False)
    bitrix_category_id = Column(String, nullable=True)
    bitrix_stage_id = Column(String, nullable=True)
    bitrix_title = Column(String(255), nullable=False)
    bitrix_url = Column(String(500), nullable=True)
    bitrix_responsible_id = Column(String, nullable=True)
    bitrix_created_at = Column(DateTime(timezone=True), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    owner_id = Column(String, nullable=True)
    owner = relationship("User", back_populates="procurement_requests")
    request_factories = relationship("RequestFactory", back_populates="procurement_request", cascade="all, delete-orphan")
