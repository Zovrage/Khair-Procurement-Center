from uuid import uuid4

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.security import get_password_hash


def seed_demo_users() -> None:
    db = SessionLocal()
    try:
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
