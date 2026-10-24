from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"
    __table_args__ = (UniqueConstraint("bitrix_portal_url", "bitrix_deal_id", name="uq_portal_bitrix_deal"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid4()), index=True)
    bitrix_deal_id = Column(String, index=True, nullable=False)
    bitrix_portal_url = Column(String(255), nullable=False, default="demo")
    bitrix_category_id = Column(String, nullable=True)
    bitrix_stage_id = Column(String, nullable=True)
    bitrix_title = Column(String(255), nullable=False)
    bitrix_url = Column(String(500), nullable=True)
    bitrix_responsible_id = Column(String, nullable=True)
    bitrix_created_at = Column(DateTime(timezone=True), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    owner_id = Column(String, nullable=True)
    request_factories = relationship("RequestFactory", back_populates="procurement_request", cascade="all, delete-orphan")
