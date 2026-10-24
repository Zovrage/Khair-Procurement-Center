from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Factory, FactoryStatus
from app.schemas.factory import FactoryCreate, FactoryRead, FactoryUpdate
from app.security import require_roles

router = APIRouter(prefix="/api/v1/factories", tags=["factories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[FactoryRead])
def list_factories(
    q: str | None = Query(default=None),
    status: FactoryStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "buyer", "manager")),
):
    query = db.query(Factory)
    if q:
        query = query.filter(or_(Factory.name.ilike(f"%{q}%"), Factory.contact_person.ilike(f"%{q}%")))
    if status is not None:
        query = query.filter(Factory.status == status)
    items = query.order_by(Factory.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{factory_id}", response_model=FactoryRead)
def get_factory(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    return item


@router.post("", response_model=FactoryRead, status_code=status.HTTP_201_CREATED)
def create_factory(payload: FactoryCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    existing = db.query(Factory).filter(Factory.name.ilike(payload.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Factory with this name already exists")
    item = Factory(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{factory_id}", response_model=FactoryRead)
def update_factory(factory_id: str, payload: FactoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{factory_id}/archive", response_model=FactoryRead)
def archive_factory(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    item.status = FactoryStatus.ARCHIVED
    db.commit()
    db.refresh(item)
    return item
