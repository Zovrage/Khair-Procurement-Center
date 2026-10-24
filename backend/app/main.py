from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.factories import router as factories_router
from app.api.routes.integration import router as integration_router
from app.api.routes.requests import router as requests_router
from app.config import settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(factories_router)
app.include_router(requests_router)
app.include_router(integration_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}


# Ensure tables exist in demo mode when SQLite is used.
Base.metadata.create_all(bind=engine)
