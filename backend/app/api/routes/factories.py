from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Factory, FactoryStatus
from app.models import FactoryOrderNumber, ProcurementRequest, RequestFactory
from app.schemas.factory import FactoryCreate, FactoryList, FactoryRead, FactoryUpdate
from app.security import require_roles
from app.services.audit import log_audit

router = APIRouter(prefix="/api/v1/factories", tags=["factories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=FactoryList)
def list_factories(
    q: str | None = Query(default=None),
    status: FactoryStatus | None = None,
    active_only: bool = False,
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
    if active_only:
        query = query.filter(Factory.status == FactoryStatus.ACTIVE)
    total = query.count()
    items = query.order_by(Factory.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{factory_id}", response_model=FactoryRead)
def get_factory(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    return item


@router.get("/{factory_id}/requests")
def list_factory_requests(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    relations = (
        db.query(RequestFactory)
        .join(ProcurementRequest)
        .filter(RequestFactory.factory_id == factory_id)
        .order_by(ProcurementRequest.bitrix_created_at.desc().nullslast())
        .all()
    )
    return [{
        "id": relation.procurement_request.id,
        "bitrix_deal_id": relation.procurement_request.bitrix_deal_id,
        "bitrix_title": relation.procurement_request.bitrix_title,
        "bitrix_stage_id": relation.procurement_request.bitrix_stage_id,
        "dispatch_datetime": relation.dispatch_datetime,
        "dispatch_method": relation.dispatch_method,
        "factory_order_numbers": [
            order.order_number
            for order in db.query(FactoryOrderNumber).filter(FactoryOrderNumber.request_factory_id == relation.id).all()
        ],
    } for relation in relations]


@router.post("", response_model=FactoryRead, status_code=status.HTTP_201_CREATED)
def create_factory(payload: FactoryCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    existing = db.query(Factory).filter(func.lower(Factory.name) == payload.name.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Factory with this name already exists")
    item = Factory(**payload.model_dump(exclude={"name"}), name=payload.name.strip())
    db.add(item)
    db.flush()
    log_audit(db, entity_type="factory", entity_id=item.id, action="created", actor_id=current_user.id)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{factory_id}", response_model=FactoryRead)
def update_factory(factory_id: str, payload: FactoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    updates = payload.model_dump(exclude_unset=True)
    name = updates.get("name")
    if name:
        duplicate = db.query(Factory).filter(
            func.lower(Factory.name) == name.strip().lower(),
            Factory.id != factory_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Factory with this name already exists")
        updates["name"] = name.strip()
    for field, value in updates.items():
        setattr(item, field, value)
    log_audit(
        db,
        entity_type="factory",
        entity_id=item.id,
        action="updated",
        actor_id=current_user.id,
        details={"fields": sorted(updates.keys())},
    )
    db.commit()
    db.refresh(item)
    return item


@router.post("/{factory_id}/archive", response_model=FactoryRead)
def archive_factory(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    item.status = FactoryStatus.ARCHIVED
    log_audit(db, entity_type="factory", entity_id=item.id, action="archived", actor_id=current_user.id)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{factory_id}/history")
def list_factory_history(factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "manager"))):
    item = db.query(Factory).filter(Factory.id == factory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factory not found")
    from app.models import AuditLog

    return db.query(AuditLog).filter(
        AuditLog.entity_type == "factory",
        AuditLog.entity_id == factory_id,
    ).order_by(AuditLog.created_at.desc()).limit(100).all()
