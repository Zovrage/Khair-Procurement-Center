import json
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: str,
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        id=str(uuid4()),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
    ))
