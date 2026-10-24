from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    actor_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="audit_logs", foreign_keys="User.id")
