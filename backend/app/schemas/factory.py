from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.factory import DispatchMethod, FactoryStatus
from app.schemas.common import BaseSchema


class FactoryBase(BaseSchema):
    name: str = Field(..., min_length=1)
    short_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[str] = None
    products: Optional[str] = None
    default_dispatch_method: Optional[DispatchMethod] = None
    payment_terms: Optional[str] = None
    production_lead_time_days: Optional[int] = None
    comment: Optional[str] = None
    status: FactoryStatus = FactoryStatus.ACTIVE


class FactoryCreate(FactoryBase):
    pass


class FactoryUpdate(BaseSchema):
    name: Optional[str] = None
    short_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[str] = None
    products: Optional[str] = None
    default_dispatch_method: Optional[DispatchMethod] = None
    payment_terms: Optional[str] = None
    production_lead_time_days: Optional[int] = None
    comment: Optional[str] = None
    status: Optional[FactoryStatus] = None


class FactoryRead(FactoryBase):
    id: str
    created_at: str | None = None
    updated_at: str | None = None
