from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"
    BUYER = "buyer"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.BUYER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    comment = Column(Text, nullable=True)
