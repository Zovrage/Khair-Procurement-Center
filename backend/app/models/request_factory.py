from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RequestFactory(Base):
    __tablename__ = "request_factories"

    id = Column(String, primary_key=True, index=True)
    procurement_request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False, index=True)
    factory_id = Column(String, ForeignKey("factories.id"), nullable=False, index=True)
    dispatch_datetime = Column(DateTime(timezone=True), nullable=True)
    dispatch_method = Column(String(50), nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    procurement_request = relationship("ProcurementRequest", back_populates="request_factories")
    factory = relationship("Factory", back_populates="request_factories")
    order_numbers = relationship("FactoryOrderNumber", back_populates="request_factory", cascade="all, delete-orphan")
