from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.security import get_current_user, get_password_hash, require_roles
from app.services.audit import log_audit

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    return db.query(User).order_by(User.full_name.asc()).all()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    user = User(
        id=str(uuid4()),
        username=payload.username.strip(),
        full_name=payload.full_name.strip(),
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    log_audit(
        db,
        entity_type="user",
        entity_id=user.id,
        action="created",
        actor_id=current_user.id,
        details={"username": user.username, "role": user.role.value},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует") from exc
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    updates = payload.model_dump(exclude_unset=True)
    if user.id == current_user.id and (updates.get("is_active") is False or updates.get("role") not in (None, UserRole.ADMIN)):
        raise HTTPException(status_code=400, detail="Нельзя отключить или понизить роль собственной учётной записи")
    removing_admin = user.role == UserRole.ADMIN and user.is_active and (
        updates.get("is_active") is False or updates.get("role") not in (None, UserRole.ADMIN)
    )
    if removing_admin:
        active_admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Нельзя отключить последнего активного администратора")

    password = updates.pop("password", None)
    if password:
        if not 12 <= len(password.encode("utf-8")) <= 72:
            raise HTTPException(status_code=422, detail="Пароль должен содержать от 12 до 72 байт в UTF-8")
        user.password_hash = get_password_hash(password)
    for field, value in updates.items():
        setattr(user, field, value)
    log_audit(
        db,
        entity_type="user",
        entity_id=user.id,
        action="updated",
        actor_id=current_user.id,
        details={"fields": sorted(payload.model_dump(exclude_unset=True).keys())},
    )
    db.commit()
    db.refresh(user)
    return user
