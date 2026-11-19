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

def test_duplicate_email_registration_is_rejected_case_insensitively(client):
    register(client, "Owner@Example.com")
    response = client.post("/api/v1/auth/register", json={
        "name": "Another Owner",
        "email": "owner@example.com",
        "password": "different-password",
    })
    assert response.status_code == 409


def test_same_sku_is_allowed_for_different_workspaces(client):
    first_token = register(client, "first@example.com")
    second_token = register(client, "second@example.com")
    for token in (first_token, second_token):
        response = client.post("/api/v1/products", headers=auth(token), json={
            "sku": "COMMON-SKU", "name": "Shared SKU label", "stock": 3,
        })
        assert response.status_code == 201


def test_product_validation_rejects_negative_stock_and_cost(client):
    token = register(client)
    headers = auth(token)
    for payload in ({"sku": "NEG-STOCK", "name": "Bad", "stock": -1},
                    {"sku": "NEG-COST", "name": "Bad", "unit_cost": -1}):
        response = client.post("/api/v1/products", headers=headers, json=payload)
        assert response.status_code == 422


def test_sales_reduce_stock_and_are_persisted(client):
    token = register(client)
    headers = auth(token)
    product = client.post("/api/v1/products", headers=headers, json={
        "sku": "SALE-1", "name": "Sale item", "stock": 12, "unit_cost": 50,
    }).json()
    sale = client.post("/api/v1/sales", headers=headers, json={
        "product_id": product["id"], "quantity": 3, "unit_price": 75, "reference": "INV-100",
    })
    assert sale.status_code == 201
    assert sale.json()["stock_remaining"] == 9
    assert sale.json()["revenue"] == 225
    assert client.get("/api/v1/sales", headers=headers).json()[0]["reference"] == "INV-100"
    assert client.get("/api/v1/sales/summary", headers=headers).json()["units_sold"] == 3


def test_sale_cannot_overdraw_inventory(client):
    token = register(client)
    headers = auth(token)
    product = client.post("/api/v1/products", headers=headers, json={
        "sku": "SALE-2", "name": "Limited item", "stock": 2,
    }).json()
    response = client.post("/api/v1/sales", headers=headers, json={
        "product_id": product["id"], "quantity": 3,
    })
    assert response.status_code == 409


def test_supplier_purchase_order_and_receipt_workflow(client):
    token = register(client)
    headers = auth(token)
    supplier = client.post("/api/v1/suppliers", headers=headers, json={
        "name": "Reliable Supply Co", "lead_time_days": 5,
    })
    assert supplier.status_code == 201
    product = client.post("/api/v1/products", headers=headers, json={
        "sku": "PO-1", "name": "Restock item", "stock": 4, "unit_cost": 20,
    }).json()
    order = client.post("/api/v1/purchase-orders", headers=headers, json={
        "supplier_id": supplier.json()["id"],
        "items": [{"product_id": product["id"], "quantity": 8, "unit_cost": 18}],
    })
    assert order.status_code == 201
    assert order.json()["total"] == 144
    sent = client.patch(f"/api/v1/purchase-orders/{order.json()['id']}", headers=headers, json={"status": "sent"})
    assert sent.status_code == 200
    received = client.post(f"/api/v1/purchase-orders/{order.json()['id']}/receive", headers=headers)
    assert received.status_code == 200
    assert received.json()["status"] == "received"
    assert client.get("/api/v1/products", headers=headers).json()[0]["stock"] == 12
    assert client.post(f"/api/v1/purchase-orders/{order.json()['id']}/receive", headers=headers).status_code == 409


def test_supplier_and_purchase_orders_are_workspace_scoped(client):
    token = register(client)
    headers = auth(token)
    supplier = client.post("/api/v1/suppliers", headers=headers, json={"name": "Private Supplier"})
    other = auth(register(client, "other@example.com"))
    assert client.get("/api/v1/suppliers", headers=other).json() == []
    assert client.get("/api/v1/purchase-orders", headers=other).json() == []
    assert client.delete(f"/api/v1/suppliers/{supplier.json()['id']}", headers=other).status_code == 404
