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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
