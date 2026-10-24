from uuid import uuid4

from app.database import SessionLocal
from app.models import ProcurementRequest, User, UserRole
from app.config import settings
from app.security import get_password_hash


def seed_demo_users() -> None:
    db = SessionLocal()
    try:
        demo_records = db.query(ProcurementRequest).filter(ProcurementRequest.bitrix_portal_url == "demo").count()
        if demo_records:
            raise RuntimeError("Demo records detected in the production database; configure a separate clean production database")
        if db.query(User).count() > 0:
            return
        users = [
            User(id=str(uuid4()), username="admin", password_hash=get_password_hash("admin123"), full_name="Администратор системы", role=UserRole.ADMIN),
            User(id=str(uuid4()), username="buyer", password_hash=get_password_hash("buyer123"), full_name="Закупщик", role=UserRole.BUYER),
            User(id=str(uuid4()), username="manager", password_hash=get_password_hash("manager123"), full_name="Руководитель отдела закупок", role=UserRole.MANAGER),
        ]
        db.add_all(users)
        db.commit()
    finally:
        db.close()


def ensure_initial_admin() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        username = settings.initial_admin_username
        password = settings.initial_admin_password
        if not username or not password or len(password.encode("utf-8")) < 12 or len(password.encode("utf-8")) > 72:
            raise RuntimeError(
                "Set INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD (12-72 UTF-8 bytes) before first production start"
            )
        db.add(User(
            id=str(uuid4()),
            username=username,
            password_hash=get_password_hash(password),
            full_name=settings.initial_admin_full_name,
            role=UserRole.ADMIN,
            is_active=True,
        ))
        db.commit()
    finally:
        db.close()
