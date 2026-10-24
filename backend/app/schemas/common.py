from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseSchema):
    success: bool = True
    message: str


class ErrorResponse(BaseSchema):
    success: bool = False
    message: str
    code: str | None = None


class PaginationMeta(BaseSchema):
    page: int = 1
    page_size: int = 20
    total: int = 0
    pages: int = 0
