from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Khair Procurement Center"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./app.db"
    demo_mode: bool = True
    bitrix_portal_url: str | None = None
    bitrix_access_token: str | None = None
    bitrix_deal_pipeline_id: str | None = None
    bitrix_webhook_secret: str | None = None
    bitrix_webhook_url: str | None = None
    timezone: str = "Europe/Moscow"
    frontend_url: str = "http://localhost:5173"
    bitrix_sync_interval_seconds: int = Field(default=300, ge=60)
    initial_admin_username: str | None = None
    initial_admin_password: str | None = None
    initial_admin_full_name: str = "Системный администратор"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("TIMEZONE must be a valid IANA time zone") from exc
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
