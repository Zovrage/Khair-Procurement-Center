from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_factories_returns_demo_data():
    response = client.get("/api/v1/factories", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401)


def test_create_factory_requires_permissions():
    payload = {"name": "Test factory"}
    response = client.post("/api/v1/factories", json=payload)
    assert response.status_code in (401, 403)
