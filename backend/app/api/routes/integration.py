import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import ProcurementRequest, SyncEvent
from app.security import require_roles

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/integrations", tags=["integration"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def bitrix_method_url(method: str) -> str:
    if not settings.bitrix_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitrix24 webhook URL is not configured on the server",
        )
    return f"{settings.bitrix_webhook_url.rstrip('/')}/{method}.json"


def call_bitrix(method: str, params: dict) -> dict:
    url = bitrix_method_url(method)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.post(url, json=params, timeout=20)
            response.raise_for_status()
            try:
                result = response.json()
            except ValueError as exc:
                raise HTTPException(status_code=502, detail="Bitrix24 вернул некорректный ответ") from exc
            if not isinstance(result, dict):
                raise HTTPException(status_code=502, detail="Bitrix24 вернул неожиданный формат ответа")
            if "error" in result:
                code = str(result.get("error", ""))
                if code in {"QUERY_LIMIT_EXCEEDED", "OPERATION_TIME_LIMIT"} and attempt < 2:
                    continue
                raise HTTPException(status_code=502, detail="Bitrix24 отклонил запрос. Проверьте права вебхука и настройки.")
            return result
        except httpx.TimeoutException as exc:
            last_error = exc
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code < 500:
                raise HTTPException(status_code=502, detail="Bitrix24 вернул ошибку. Проверьте URL вебхука и права доступа.") from exc
        except httpx.RequestError as exc:
            last_error = exc
        if attempt < 2:
            time.sleep(0.5 * (2 ** attempt))
            continue
    logger.warning("Bitrix24 request failed after retries: %s", type(last_error).__name__)
    raise HTTPException(status_code=503, detail="Bitrix24 временно недоступен. Повторите синхронизацию позже.") from last_error


@router.get("/bitrix24/status")
def bitrix_status(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    last_success = db.query(SyncEvent).filter(
        SyncEvent.category == "bitrix24",
        SyncEvent.status == "success",
    ).order_by(SyncEvent.created_at.desc()).first()
    return {
        "configured": bool(settings.bitrix_webhook_url and settings.bitrix_deal_pipeline_id),
        "demo_mode": settings.demo_mode,
        "portal_url": settings.bitrix_portal_url or None,
        "pipeline_id": settings.bitrix_deal_pipeline_id or None,
        "last_sync_at": last_success.created_at if last_success else None,
        "credentials_configured": bool(settings.bitrix_webhook_url),
        "timezone": settings.timezone,
    }


@router.get("/bitrix24/events")
def bitrix_events(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    return db.query(SyncEvent).filter(SyncEvent.category == "bitrix24").order_by(
        SyncEvent.created_at.desc(),
    ).limit(50).all()


@router.post("/bitrix24/sync")
def sync_bitrix(db: Session = Depends(get_db), current_user=Depends(require_roles("admin"))):
    if not settings.bitrix_deal_pipeline_id:
        raise HTTPException(status_code=400, detail="Не настроен ID воронки Bitrix24 на сервере")
    if not settings.bitrix_webhook_url:
        raise HTTPException(status_code=400, detail="Не настроен входящий вебхук Bitrix24 на сервере")

    category_id = settings.bitrix_deal_pipeline_id
    start = 0
    deals: list[dict] = []
    try:
        while True:
            result = call_bitrix(
                "crm.deal.list",
                {
                    "filter": {"CATEGORY_ID": category_id},
                    "select": ["ID", "TITLE", "CATEGORY_ID", "STAGE_ID", "ASSIGNED_BY_ID", "DATE_CREATE"],
                    "order": {"ID": "ASC"},
                    "start": start,
                },
            )
            page_deals = result.get("result", [])
            if not isinstance(page_deals, list):
                raise HTTPException(status_code=502, detail="Bitrix24 вернул неожиданный формат списка сделок")
            deals.extend(page_deals)
            next_start = result.get("next")
            if next_start is None:
                break
            try:
                start = int(next_start)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=502, detail="Bitrix24 вернул некорректный номер страницы") from exc
    except HTTPException as exc:
        db.add(SyncEvent(
            id=str(uuid4()),
            category="bitrix24",
            status="error",
            message=str(exc.detail),
        ))
        db.commit()
        raise

    sync_time = datetime.now(timezone.utc)
    portal_url = settings.bitrix_portal_url.rstrip("/") if settings.bitrix_portal_url else "bitrix24"
    try:
        for deal in deals:
            deal_id = str(deal["ID"])
            record = db.query(ProcurementRequest).filter(
                ProcurementRequest.bitrix_portal_url == portal_url,
                ProcurementRequest.bitrix_deal_id == deal_id,
            ).first()
            if record is None:
                record = ProcurementRequest(
                    id=str(uuid4()),
                    bitrix_deal_id=deal_id,
                    bitrix_portal_url=portal_url,
                    bitrix_title=str(deal.get("TITLE") or f"Сделка {deal_id}"),
                )
                db.add(record)
            record.is_active = True
            record.bitrix_category_id = str(deal.get("CATEGORY_ID", category_id))
            record.bitrix_stage_id = str(deal.get("STAGE_ID")) if deal.get("STAGE_ID") is not None else None
            record.bitrix_title = str(deal.get("TITLE") or f"Сделка {deal_id}")
            record.bitrix_responsible_id = str(deal.get("ASSIGNED_BY_ID")) if deal.get("ASSIGNED_BY_ID") else None
            record.bitrix_url = f"{settings.bitrix_portal_url.rstrip('/')}/crm/deal/details/{deal_id}/" if settings.bitrix_portal_url else None
            date_created = deal.get("DATE_CREATE")
            if date_created:
                parsed = datetime.fromisoformat(str(date_created).replace("Z", "+00:00"))
                record.bitrix_created_at = parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
            record.last_synced_at = sync_time
        active_deal_ids = {str(deal.get("ID")) for deal in deals if deal.get("ID") is not None}
        for record in db.query(ProcurementRequest).filter(
            ProcurementRequest.bitrix_portal_url == portal_url,
            ProcurementRequest.is_active.is_(True),
        ).all():
            if record.bitrix_deal_id not in active_deal_ids:
                record.is_active = False
        db.add(SyncEvent(
            id=str(uuid4()),
            category="bitrix24",
            status="success",
            message=f"Синхронизация завершена. Обработано сделок: {len(deals)}.",
        ))
        db.commit()
    except (KeyError, TypeError, ValueError):
        db.rollback()
        logger.exception("Bitrix24 response could not be applied to local deal records")
        db.add(SyncEvent(
            id=str(uuid4()),
            category="bitrix24",
            status="error",
            message="Сделки получены, но их не удалось сохранить из-за некорректных данных.",
        ))
        db.commit()
        raise HTTPException(status_code=500, detail="Не удалось сохранить сделки после синхронизации")
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database failure while saving Bitrix24 deal updates")
        raise HTTPException(status_code=503, detail="Не удалось сохранить данные. База данных временно недоступна.") from exc

    return {"success": True, "message": f"Синхронизация завершена. Обработано сделок: {len(deals)}.", "processed": len(deals)}
