from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DispatchMethod(str, PyEnum):
    WHATSAPP = "WhatsApp"
    EMAIL = "Почта"
    WEBSITE = "Сайт"


class FactoryStatus(str, PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Factory(Base):
    __tablename__ = "factories"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    short_name = Column(String(100), nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    products = Column(Text, nullable=True)
    default_dispatch_method = Column(Enum(DispatchMethod, native_enum=False), nullable=True)
    payment_terms = Column(Text, nullable=True)
    production_lead_time_days = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(Enum(FactoryStatus, native_enum=False), default=FactoryStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    request_factories = relationship("RequestFactory", back_populates="factory")
