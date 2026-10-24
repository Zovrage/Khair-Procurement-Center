from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, exists, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models import Factory, FactoryOrderNumber, ProcurementRequest, RequestFactory
from app.schemas.procurement import (
    OrderNumberCreate,
    OrderNumberRead,
    OrderNumberUpdate,
    RequestFactoryCreate,
    RequestFactoryRead,
    RequestFactoryUpdate,
)
from app.security import require_roles
from app.services.audit import log_audit

router = APIRouter(prefix="/api/v1", tags=["requests"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/requests", response_model=dict)
def list_requests(
    q: str | None = Query(default=None),
    stage: str | None = None,
    factory_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    only_completed: bool | None = None,
    responsible_id: str | None = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|title)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    history: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "buyer", "manager")),
):
    query = db.query(ProcurementRequest)
    if history and current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Only managers and administrators can view request history")
    query = query.filter(ProcurementRequest.is_active.is_(not history))
    if q:
        query = query.filter(or_(
            ProcurementRequest.bitrix_title.ilike(f"%{q}%"),
            ProcurementRequest.bitrix_deal_id.ilike(f"%{q}%"),
        ))
    if stage:
        query = query.filter(ProcurementRequest.bitrix_stage_id == stage)
    if responsible_id:
        query = query.filter(ProcurementRequest.bitrix_responsible_id == responsible_id)
    if factory_id:
        query = query.join(RequestFactory).filter(RequestFactory.factory_id == factory_id).distinct()
    if from_date:
        query = query.filter(ProcurementRequest.bitrix_created_at >= from_date)
    if to_date:
        query = query.filter(ProcurementRequest.bitrix_created_at <= to_date)
    if only_completed is not None:
        has_factories = db.query(RequestFactory.id).filter(
            RequestFactory.procurement_request_id == ProcurementRequest.id,
        ).exists()
        has_incomplete_factory = db.query(RequestFactory.id).filter(
            RequestFactory.procurement_request_id == ProcurementRequest.id,
            or_(
                RequestFactory.dispatch_datetime.is_(None),
                RequestFactory.dispatch_method.is_(None),
                ~db.query(FactoryOrderNumber.id).filter(
                    FactoryOrderNumber.request_factory_id == RequestFactory.id,
                ).exists(),
            ),
        ).exists()
        if only_completed:
            query = query.filter(has_factories, ~has_incomplete_factory)
        else:
            query = query.filter(or_(~has_factories, has_incomplete_factory))

    total = query.count()
    sort_column = ProcurementRequest.bitrix_title if sort_by == "title" else ProcurementRequest.bitrix_created_at
    sort_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    items = query.options(joinedload(ProcurementRequest.request_factories)).order_by(
        sort_expression.nullslast(),
        ProcurementRequest.bitrix_title.asc(),
    ).offset((page - 1) * page_size).limit(page_size).all()
    return {
      "items": [{
        "id": item.id,
        "bitrix_deal_id": item.bitrix_deal_id,
        "bitrix_portal_url": item.bitrix_portal_url,
        "is_active": item.is_active,
        "bitrix_title": item.bitrix_title,
        "bitrix_url": item.bitrix_url,
        "bitrix_responsible_id": item.bitrix_responsible_id,
        "bitrix_created_at": item.bitrix_created_at,
        "bitrix_stage_id": item.bitrix_stage_id,
        "factories_count": len(item.request_factories),
        "last_dispatch": max([rf.dispatch_datetime for rf in item.request_factories if rf.dispatch_datetime], default=None),
        "procurement_complete": bool(item.request_factories) and all(
            bool(rf.dispatch_datetime and rf.dispatch_method and rf.order_numbers)
            for rf in item.request_factories
        ),
      } for item in items],
      "total": total,
      "page": page,
      "page_size": page_size,
    }


@router.get("/requests/{request_id}", response_model=dict)
def get_request(request_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    item = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {
        "id": item.id,
        "bitrix_deal_id": item.bitrix_deal_id,
        "bitrix_title": item.bitrix_title,
        "bitrix_url": item.bitrix_url,
        "bitrix_category_id": item.bitrix_category_id,
        "bitrix_stage_id": item.bitrix_stage_id,
        "bitrix_responsible_id": item.bitrix_responsible_id,
        "bitrix_created_at": item.bitrix_created_at,
        "last_synced_at": item.last_synced_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/requests/{request_id}/history")
def get_request_history(request_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "manager"))):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    from app.models import AuditLog

    return db.query(AuditLog).filter(
        AuditLog.entity_type == "request",
        AuditLog.entity_id == request_id,
    ).order_by(AuditLog.created_at.desc()).limit(100).all()


@router.get("/requests/{request_id}/factories", response_model=list[RequestFactoryRead])
def get_request_factories(request_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    results = []
    for rf in request.request_factories:
        results.append(RequestFactoryRead(
            id=rf.id,
            procurement_request_id=rf.procurement_request_id,
            factory_id=rf.factory_id,
            dispatch_datetime=rf.dispatch_datetime,
            dispatch_method=rf.dispatch_method,
            created_by=rf.created_by,
            updated_by=rf.updated_by,
            created_at=rf.created_at,
            updated_at=rf.updated_at,
            factory_name=rf.factory.name,
            order_numbers=[n.order_number for n in rf.order_numbers],
            order_number_records=rf.order_numbers,
        ))
    return results


@router.get("/request-filters")
def request_filters(db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer", "manager"))):
    stages = [
        value for (value,) in db.query(ProcurementRequest.bitrix_stage_id)
        .filter(ProcurementRequest.bitrix_stage_id.is_not(None))
        .distinct().order_by(ProcurementRequest.bitrix_stage_id).all()
    ]
    responsibles = [
        value for (value,) in db.query(ProcurementRequest.bitrix_responsible_id)
        .filter(ProcurementRequest.bitrix_responsible_id.is_not(None))
        .distinct().order_by(ProcurementRequest.bitrix_responsible_id).all()
    ]
    return {"stages": stages, "responsible_ids": responsibles}


@router.post("/requests/{request_id}/factories", response_model=RequestFactoryRead, status_code=status.HTTP_201_CREATED)
def add_factory_to_request(request_id: str, payload: RequestFactoryCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    factory = db.query(Factory).filter(Factory.id == payload.factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")
    if factory.status.value != "active":
        raise HTTPException(status_code=400, detail="Archived factories cannot be added to new requests")
    if db.query(RequestFactory).filter(RequestFactory.procurement_request_id == request_id, RequestFactory.factory_id == payload.factory_id).first():
        raise HTTPException(status_code=409, detail="Factory already linked to this request")
    record = RequestFactory(
        id=str(uuid4()),
        procurement_request_id=request_id,
        factory_id=payload.factory_id,
        dispatch_datetime=payload.dispatch_datetime,
        dispatch_method=payload.dispatch_method,
        created_by=current_user.username,
        updated_by=current_user.username,
    )
    db.add(record)
    db.flush()
    log_audit(
        db,
        entity_type="request",
        entity_id=request_id,
        action="factory_added",
        actor_id=current_user.id,
        details={"factory_id": factory.id, "factory_name": factory.name},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Factory already linked to this request") from exc
    db.refresh(record)
    return RequestFactoryRead(
        id=record.id,
        procurement_request_id=record.procurement_request_id,
        factory_id=record.factory_id,
        dispatch_datetime=record.dispatch_datetime,
        dispatch_method=record.dispatch_method,
        created_by=record.created_by,
        updated_by=record.updated_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
        factory_name=record.factory.name,
        order_numbers=[],
        order_number_records=[],
    )


@router.patch("/request-factories/{request_factory_id}", response_model=RequestFactoryRead)
def update_request_factory(request_factory_id: str, payload: RequestFactoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    record = db.query(RequestFactory).filter(RequestFactory.id == request_factory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request factory relation not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(record, field, value)
    record.updated_by = current_user.username
    log_audit(
        db,
        entity_type="request",
        entity_id=record.procurement_request_id,
        action="dispatch_updated",
        actor_id=current_user.id,
        details=updates,
    )
    db.commit()
    db.refresh(record)
    return RequestFactoryRead(
        id=record.id,
        procurement_request_id=record.procurement_request_id,
        factory_id=record.factory_id,
        dispatch_datetime=record.dispatch_datetime,
        dispatch_method=record.dispatch_method,
        created_by=record.created_by,
        updated_by=record.updated_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
        factory_name=record.factory.name,
        order_numbers=[n.order_number for n in record.order_numbers],
        order_number_records=record.order_numbers,
    )


@router.delete("/request-factories/{request_factory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request_factory(request_factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    record = db.query(RequestFactory).filter(RequestFactory.id == request_factory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request factory relation not found")
    log_audit(
        db,
        entity_type="request",
        entity_id=record.procurement_request_id,
        action="factory_removed",
        actor_id=current_user.id,
        details={"factory_id": record.factory_id, "factory_name": record.factory.name},
    )
    db.delete(record)
    db.commit()


@router.post("/request-factories/{request_factory_id}/order-numbers", response_model=OrderNumberRead, status_code=status.HTTP_201_CREATED)
def create_order_number(request_factory_id: str, payload: OrderNumberCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    record = db.query(RequestFactory).filter(RequestFactory.id == request_factory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request factory not found")
    if not payload.order_number or not payload.order_number.strip():
        raise HTTPException(status_code=400, detail="Order number cannot be empty")
    if db.query(FactoryOrderNumber).filter(FactoryOrderNumber.request_factory_id == request_factory_id, FactoryOrderNumber.order_number == payload.order_number.strip()).first():
        raise HTTPException(status_code=409, detail="Order number already exists for this factory request")
    item = FactoryOrderNumber(id=str(uuid4()), request_factory_id=request_factory_id, order_number=payload.order_number.strip())
    db.add(item)
    db.flush()
    log_audit(
        db,
        entity_type="request",
        entity_id=record.procurement_request_id,
        action="order_number_added",
        actor_id=current_user.id,
        details={"factory_id": record.factory_id, "order_number": item.order_number},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Order number already exists for this factory request") from exc
    db.refresh(item)
    return item


@router.patch("/order-numbers/{order_number_id}", response_model=OrderNumberRead)
def update_order_number(order_number_id: str, payload: OrderNumberUpdate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(FactoryOrderNumber).filter(FactoryOrderNumber.id == order_number_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order number not found")
    if not payload.order_number or not payload.order_number.strip():
        raise HTTPException(status_code=400, detail="Order number cannot be empty")
    if db.query(FactoryOrderNumber).filter(FactoryOrderNumber.request_factory_id == item.request_factory_id, FactoryOrderNumber.order_number == payload.order_number.strip(), FactoryOrderNumber.id != order_number_id).first():
        raise HTTPException(status_code=409, detail="Order number already exists for this factory request")
    old_number = item.order_number
    item.order_number = payload.order_number.strip()
    log_audit(
        db,
        entity_type="request",
        entity_id=item.request_factory.procurement_request_id,
        action="order_number_updated",
        actor_id=current_user.id,
        details={"factory_id": item.request_factory.factory_id, "old_number": old_number, "order_number": item.order_number},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Order number already exists for this factory request") from exc
    db.refresh(item)
    return item


@router.delete("/order-numbers/{order_number_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_number(order_number_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(FactoryOrderNumber).filter(FactoryOrderNumber.id == order_number_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order number not found")
    log_audit(
        db,
        entity_type="request",
        entity_id=item.request_factory.procurement_request_id,
        action="order_number_removed",
        actor_id=current_user.id,
        details={"factory_id": item.request_factory.factory_id, "order_number": item.order_number},
    )
    db.delete(item)
    db.commit()
