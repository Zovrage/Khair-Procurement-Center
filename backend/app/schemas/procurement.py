from datetime import datetime
from typing import Optional
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class ProcurementRequestRead(BaseSchema):
    id: str
    bitrix_deal_id: str
    bitrix_category_id: Optional[str] = None
    bitrix_stage_id: Optional[str] = None
    bitrix_title: str
    bitrix_url: Optional[str] = None
    bitrix_responsible_id: Optional[str] = None
    bitrix_created_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OrderNumberRead(BaseSchema):
    id: str
    request_factory_id: str
    order_number: str
    created_at: datetime
    updated_at: datetime


class RequestFactoryRead(BaseSchema):
    id: str
    procurement_request_id: str
    factory_id: str
    dispatch_datetime: Optional[datetime] = None
    dispatch_method: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    factory_name: Optional[str] = None
    order_numbers: list[str] = []
    order_number_records: list[OrderNumberRead] = []


class RequestFactoryCreate(BaseSchema):
    factory_id: str = Field(..., min_length=1)
    dispatch_datetime: Optional[datetime] = None
    dispatch_method: Optional[Literal["WhatsApp", "Почта", "Сайт"]] = None


class RequestFactoryUpdate(BaseSchema):
    dispatch_datetime: Optional[datetime] = None
    dispatch_method: Optional[Literal["WhatsApp", "Почта", "Сайт"]] = None


class OrderNumberCreate(BaseSchema):
    order_number: str = Field(..., min_length=1)


class OrderNumberUpdate(BaseSchema):
    order_number: str = Field(..., min_length=1)
