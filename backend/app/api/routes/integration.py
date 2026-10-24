from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import IntegrationSetting
from app.security import require_roles

router = APIRouter(prefix="/api/v1/integrations", tags=["integration"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/bitrix24/status")
def bitrix_status(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    portal_url = db.query(IntegrationSetting).filter(IntegrationSetting.key == "bitrix_portal_url").first()
    token = db.query(IntegrationSetting).filter(IntegrationSetting.key == "bitrix_access_token").first()
    pipeline = db.query(IntegrationSetting).filter(IntegrationSetting.key == "bitrix_deal_pipeline_id").first()
    configured = bool(portal_url and token and pipeline)
    return {
        "configured": configured,
        "portal_url": portal_url.value if portal_url else None,
        "pipeline_id": pipeline.value if pipeline else None,
        "last_sync_at": None,
    }


@router.post("/bitrix24/sync")
def sync_bitrix(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    settings = db.query(IntegrationSetting).all()
    configured = any(s.key == "bitrix_portal_url" and s.value for s in settings)
    if not configured:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bitrix24 integration is not configured")
    return {"success": True, "message": "Bitrix24 sync requested successfully"}
