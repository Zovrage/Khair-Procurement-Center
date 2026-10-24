from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/api/v1", tags=["requests"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/requests", response_model=list[dict])
def list_requests(
    q: str | None = Query(default=None),
    stage: str | None = None,
    factory_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    only_completed: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "buyer", "manager")),
):
    query = db.query(ProcurementRequest)
    if q:
        query = query.filter(ProcurementRequest.bitrix_title.ilike(f"%{q}%"))
    if factory_id:
        query = query.join(RequestFactory).filter(RequestFactory.factory_id == factory_id)
    if from_date:
        query = query.filter(ProcurementRequest.created_at >= from_date)
    if to_date:
        query = query.filter(ProcurementRequest.created_at <= to_date)
    items = query.order_by(ProcurementRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [{
        "id": item.id,
        "bitrix_deal_id": item.bitrix_deal_id,
        "bitrix_title": item.bitrix_title,
        "bitrix_stage_id": item.bitrix_stage_id,
        "factories_count": len(item.request_factories),
        "last_dispatch": max([rf.dispatch_datetime for rf in item.request_factories if rf.dispatch_datetime], default=None),
    } for item in items]


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
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


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
        ))
    return results


@router.post("/requests/{request_id}/factories", response_model=RequestFactoryRead, status_code=status.HTTP_201_CREATED)
def add_factory_to_request(request_id: str, payload: RequestFactoryCreate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    factory = db.query(Factory).filter(Factory.id == payload.factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")
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
        order_numbers=[],
    )


@router.patch("/request-factories/{request_factory_id}", response_model=RequestFactoryRead)
def update_request_factory(request_factory_id: str, payload: RequestFactoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    record = db.query(RequestFactory).filter(RequestFactory.id == request_factory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request factory relation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_by = current_user.username
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
    )


@router.delete("/request-factories/{request_factory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request_factory(request_factory_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    record = db.query(RequestFactory).filter(RequestFactory.id == request_factory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request factory relation not found")
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
    db.commit()
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
    item.order_number = payload.order_number.strip()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/order-numbers/{order_number_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_number(order_number_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("admin", "buyer"))):
    item = db.query(FactoryOrderNumber).filter(FactoryOrderNumber.id == order_number_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order number not found")
    db.delete(item)
    db.commit()
