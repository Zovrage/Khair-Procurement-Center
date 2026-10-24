import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DEMO_MODE"] = "true"
os.environ["SECRET_KEY"] = "pytest-only-secret"

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert "httponly" in response.headers.get("set-cookie", "").lower()
    csrf_token = response.cookies.get("khair_csrf")
    assert csrf_token
    return {"X-CSRF-Token": csrf_token}


def test_factory_lifecycle_and_role_permissions(client: TestClient):
    admin_headers = login(client, "admin", "admin123")
    csrf_rejected = client.post("/api/v1/factories", json={"name": "Missing CSRF"})
    assert csrf_rejected.status_code == 403
    name = f"Test factory {uuid4()}"

    created = client.post("/api/v1/factories", headers=admin_headers, json={"name": name})
    assert created.status_code == 201
    factory_id = created.json()["id"]

    duplicate = client.post("/api/v1/factories", headers=admin_headers, json={"name": name})
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/factories/{factory_id}",
        headers=admin_headers,
        json={"contact_person": "Тестовый контакт", "phone": "+7 900 000-00-00"},
    )
    assert updated.status_code == 200
    assert updated.json()["contact_person"] == "Тестовый контакт"

    archived = client.post(f"/api/v1/factories/{factory_id}/archive", headers=admin_headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    active_factories = client.get("/api/v1/factories?active_only=true", headers=admin_headers)
    assert factory_id not in {factory["id"] for factory in active_factories.json()["items"]}

    manager_headers = login(client, "manager", "manager123")
    forbidden = client.post("/api/v1/factories", headers=manager_headers, json={"name": "Manager forbidden"})
    assert forbidden.status_code == 403


def test_request_factory_orders_dispatch_and_persistence(client: TestClient):
    headers = login(client, "admin", "admin123")
    request_page = client.get("/api/v1/requests", headers=headers)
    request_id = request_page.json()["items"][0]["id"]

    first_factory = client.post(
        "/api/v1/factories",
        headers=headers,
        json={"name": f"Workflow factory 1 {uuid4()}"},
    ).json()
    second_factory = client.post(
        "/api/v1/factories",
        headers=headers,
        json={"name": f"Workflow factory 2 {uuid4()}"},
    ).json()

    first_link = client.post(
        f"/api/v1/requests/{request_id}/factories",
        headers=headers,
        json={"factory_id": first_factory["id"]},
    )
    second_link = client.post(
        f"/api/v1/requests/{request_id}/factories",
        headers=headers,
        json={"factory_id": second_factory["id"]},
    )
    assert first_link.status_code == 201
    assert second_link.status_code == 201

    duplicate_link = client.post(
        f"/api/v1/requests/{request_id}/factories",
        headers=headers,
        json={"factory_id": first_factory["id"]},
    )
    assert duplicate_link.status_code == 409

    relation_id = first_link.json()["id"]
    first_order = client.post(
        f"/api/v1/request-factories/{relation_id}/order-numbers",
        headers=headers,
        json={"order_number": "T-100"},
    )
    second_order = client.post(
        f"/api/v1/request-factories/{relation_id}/order-numbers",
        headers=headers,
        json={"order_number": "T-101"},
    )
    assert first_order.status_code == 201
    assert second_order.status_code == 201
    duplicate_order = client.post(
        f"/api/v1/request-factories/{relation_id}/order-numbers",
        headers=headers,
        json={"order_number": "T-100"},
    )
    assert duplicate_order.status_code == 409

    changed_order = client.patch(
        f"/api/v1/order-numbers/{first_order.json()['id']}",
        headers=headers,
        json={"order_number": "T-100-EDITED"},
    )
    assert changed_order.status_code == 200
    deleted_order = client.delete(f"/api/v1/order-numbers/{second_order.json()['id']}", headers=headers)
    assert deleted_order.status_code == 204

    saved_dispatch = client.patch(
        f"/api/v1/request-factories/{relation_id}",
        headers=headers,
        json={"dispatch_datetime": "2026-10-24T10:30:00+03:00", "dispatch_method": "WhatsApp"},
    )
    assert saved_dispatch.status_code == 200

    persisted = client.get(f"/api/v1/requests/{request_id}/factories", headers=headers)
    relation = next(item for item in persisted.json() if item["id"] == relation_id)
    assert relation["dispatch_datetime"] is not None
    assert relation["dispatch_method"] == "WhatsApp"
    assert [order["order_number"] for order in relation["order_number_records"]] == ["T-100-EDITED"]
    history = client.get(f"/api/v1/requests/{request_id}/history", headers=headers)
    assert history.status_code == 200
    assert {entry["action"] for entry in history.json()} >= {"factory_added", "order_number_added", "dispatch_updated"}

    cleared_dispatch = client.patch(
        f"/api/v1/request-factories/{relation_id}",
        headers=headers,
        json={"dispatch_datetime": None},
    )
    assert cleared_dispatch.status_code == 200


def test_bitrix_sync_is_idempotent_and_keeps_inactive_request_history(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from app.api.routes import integration
    from app.database import SessionLocal
    from app.models import ProcurementRequest

    previous = (
        settings.bitrix_webhook_url,
        settings.bitrix_deal_pipeline_id,
        settings.bitrix_portal_url,
    )
    settings.bitrix_webhook_url = "https://portal.example/rest/user/secret"
    settings.bitrix_deal_pipeline_id = "17"
    settings.bitrix_portal_url = "https://portal.example"
    deals = [{
        "ID": "90001",
        "TITLE": "Сделка интеграционного теста",
        "CATEGORY_ID": "17",
        "STAGE_ID": "C17:NEW",
        "ASSIGNED_BY_ID": "31",
        "DATE_CREATE": "2026-10-24T10:00:00+03:00",
    }]
    monkeypatch.setattr(integration, "call_bitrix", lambda _method, _params: {"result": deals})
    headers = login(client, "admin", "admin123")
    try:
        first = client.post("/api/v1/integrations/bitrix24/sync", headers=headers)
        second = client.post("/api/v1/integrations/bitrix24/sync", headers=headers)
        assert first.status_code == 200
        assert second.status_code == 200

        db = SessionLocal()
        try:
            query = db.query(ProcurementRequest).filter(
                ProcurementRequest.bitrix_portal_url == "https://portal.example",
                ProcurementRequest.bitrix_deal_id == "90001",
            )
            assert query.count() == 1
            assert query.one().is_active is True
        finally:
            db.close()

        monkeypatch.setattr(integration, "call_bitrix", lambda _method, _params: {"result": []})
        departed = client.post("/api/v1/integrations/bitrix24/sync", headers=headers)
        assert departed.status_code == 200
        active_requests = client.get("/api/v1/requests", headers=headers).json()["items"]
        assert "90001" not in {request["bitrix_deal_id"] for request in active_requests}
        history = client.get("/api/v1/requests?history=true", headers=headers)
        assert history.status_code == 200
        assert "90001" in {request["bitrix_deal_id"] for request in history.json()["items"]}
    finally:
        (
            settings.bitrix_webhook_url,
            settings.bitrix_deal_pipeline_id,
            settings.bitrix_portal_url,
        ) = previous


def test_admin_can_manage_users_and_last_admin_is_protected(client: TestClient):
    headers = login(client, "admin", "admin123")
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": f"test-user-{uuid4()}",
            "full_name": "Тестовый пользователь",
            "password": "strong-test-password",
            "role": "buyer",
        },
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]
    assert "password_hash" not in created.json()

    updated = client.patch(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"role": "manager", "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "manager"
    assert updated.json()["is_active"] is False

    users = client.get("/api/v1/users", headers=headers)
    active_admins = [
        user for user in users.json()
        if user["role"] == "admin" and user["is_active"]
    ]
    assert len(active_admins) >= 1

    manager_headers = login(client, "manager", "manager123")
    forbidden = client.get("/api/v1/users", headers=manager_headers)
    assert forbidden.status_code == 403
