import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.auth import router as auth_router
from app.api.routes.factories import router as factories_router
from app.api.routes.integration import router as integration_router, sync_bitrix
from app.api.routes.requests import router as requests_router
from app.api.routes.users import router as users_router
from app.config import settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403
from app.services.demo_users import ensure_initial_admin, ensure_production_database_is_clean, seed_demo_users
from app.seed_demo import seed_demo_data
from app.database import SessionLocal

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env == "production":
        if settings.demo_mode:
            raise RuntimeError("DEMO_MODE must be false when APP_ENV=production")
        if len(settings.secret_key) < 32 or settings.secret_key == "dev-secret-key":
            raise RuntimeError("Set a unique SECRET_KEY with at least 32 characters for production")
    Base.metadata.create_all(bind=engine)
    if settings.demo_mode:
        seed_demo_users()
        seed_demo_data()
    else:
        if settings.app_env == "production":
            ensure_production_database_is_clean()
        ensure_initial_admin()
    sync_task = None
    if settings.bitrix_webhook_url and settings.bitrix_deal_pipeline_id:
        sync_task = asyncio.create_task(periodic_bitrix_sync())
    yield
    if sync_task is not None:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


async def periodic_bitrix_sync() -> None:
    while True:
        await asyncio.sleep(settings.bitrix_sync_interval_seconds)
        try:
            await asyncio.to_thread(run_bitrix_sync)
        except (HTTPException, SQLAlchemyError):
            logger.warning("Scheduled Bitrix24 sync failed; next retry will run on the next interval")


def run_bitrix_sync() -> None:
    db = SessionLocal()
    try:
        sync_bitrix(db=db, current_user=None)
    finally:
        db.close()


app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(factories_router)
app.include_router(requests_router)
app.include_router(integration_router)
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "demo_mode": settings.demo_mode,
        "timezone": settings.timezone,
    }
