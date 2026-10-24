from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class FactoryOrderNumber(Base):
    __tablename__ = "factory_order_numbers"
    __table_args__ = (UniqueConstraint("request_factory_id", "order_number", name="uq_request_factory_order_number"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid4()), index=True)
    request_factory_id = Column(String, ForeignKey("request_factories.id"), nullable=False, index=True)
    order_number = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    request_factory = relationship("RequestFactory", back_populates="order_numbers")
