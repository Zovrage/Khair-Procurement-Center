from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12, max_length=72)
    role: UserRole = UserRole.BUYER


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=72)


class UserRead(BaseModel):
    id: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
