import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register(client, email="owner@example.com"):
    response = client.post("/api/v1/auth/register", json={
        "name": "Test Owner",
        "email": email,
        "password": "test-password-123",
        "company": "Test Workspace",
    })
    assert response.status_code == 201
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_profile(client):
    token = register(client)
    assert client.get("/api/v1/auth/me", headers=auth(token)).status_code == 200
    login = client.post("/api/v1/auth/login", json={
        "email": "OWNER@example.com", "password": "test-password-123"
    })
    assert login.status_code == 200
    update = client.patch("/api/v1/auth/me", headers=auth(token), json={"name": "Updated Name"})
    assert update.status_code == 200
    assert update.json()["name"] == "Updated Name"


def test_product_crud_and_dashboard_summary(client):
    token = register(client)
    headers = auth(token)
    created = client.post("/api/v1/products", headers=headers, json={
        "sku": "sku-1", "name": "Widget", "category": "Tools",
        "stock": 10, "demand_30d": 30, "unit_cost": 25, "lead_time_days": 5,
    })
    assert created.status_code == 201
    product = created.json()
    assert product["sku"] == "SKU-1"

    duplicate = client.post("/api/v1/products", headers=headers, json={
        "sku": "SKU-1", "name": "Duplicate"
    })
    assert duplicate.status_code == 409

    adjusted = client.patch(f"/api/v1/products/{product['id']}/stock", headers=headers, json={"delta": -15})
    assert adjusted.status_code == 200
    assert adjusted.json()["stock"] == 0

    updated = client.patch(f"/api/v1/products/{product['id']}", headers=headers, json={"name": "Updated Widget"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Widget"

    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["active_products"] == 1
    assert summary.json()["inventory_value"] == 0

    archived = client.delete(f"/api/v1/products/{product['id']}", headers=headers)
    assert archived.status_code == 200
    assert client.get("/api/v1/products", headers=headers).json() == []


def test_user_cannot_access_another_users_product(client):
    owner_token = register(client)
    product = client.post("/api/v1/products", headers=auth(owner_token), json={
        "sku": "PRIVATE-1", "name": "Private item", "stock": 5,
    }).json()
    other_token = register(client, "other@example.com")
    response = client.patch(
        f"/api/v1/products/{product['id']}",
        headers=auth(other_token),
        json={"name": "Hijacked"},
    )
    assert response.status_code == 404


def test_authentication_required_for_inventory(client):
    assert client.get("/api/v1/products").status_code == 401
    assert client.get("/api/v1/dashboard/summary").status_code == 401
