from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "finance-inventory-api-tester",
            "role": role,
            "company_id": COMPANY_ID,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role)}"}


def test_finance_invoice_payment_and_aging_api():
    invoice = client.post(
        "/api/finance/invoices",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "invoice_number": "INV-API-001",
            "customer_id": "customer-001",
            "customer_name": "NewTech Kuwait",
            "total_amount": 150.0,
            "status": "sent",
        },
    )
    assert invoice.status_code == 201
    invoice_body = invoice.json()
    assert invoice_body["paid_amount"] == 0.0

    listed = client.get("/api/finance/invoices", headers=headers())
    assert listed.status_code == 200
    assert any(row["id"] == invoice_body["id"] for row in listed.json())

    payment = client.post(
        "/api/finance/payments",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "invoice_id": invoice_body["id"],
            "amount": 150.0,
            "method": "bank_transfer",
        },
    )
    assert payment.status_code == 201

    paid_invoice = client.get(f"/api/finance/invoices/{invoice_body['id']}", headers=headers())
    assert paid_invoice.status_code == 200
    assert paid_invoice.json()["status"] == "paid"
    assert paid_invoice.json()["paid_amount"] == 150.0

    payments = client.get(f"/api/finance/invoices/{invoice_body['id']}/payments", headers=headers())
    assert payments.status_code == 200
    assert len(payments.json()) == 1

    aging = client.get("/api/finance/summary/aging", headers=headers())
    assert aging.status_code == 200
    assert "total_outstanding" in aging.json()


def test_inventory_sku_movement_and_summary_api():
    sku = client.post(
        "/api/inventory/skus",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "sku_code": "SKU-API-001",
            "name": "AI OS License",
            "quantity_on_hand": 2,
            "reorder_point": 3,
        },
    )
    assert sku.status_code == 201
    sku_body = sku.json()

    inbound = client.post(
        "/api/inventory/movements",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "sku_id": sku_body["id"],
            "movement_type": "in",
            "quantity": 5,
            "reason": "initial stock",
        },
    )
    assert inbound.status_code == 201

    updated = client.get(f"/api/inventory/skus/{sku_body['id']}", headers=headers())
    assert updated.status_code == 200
    assert updated.json()["quantity_on_hand"] == 7

    outbound = client.post(
        "/api/inventory/movements",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "sku_id": sku_body["id"],
            "movement_type": "out",
            "quantity": 2,
        },
    )
    assert outbound.status_code == 201

    low_stock = client.get("/api/inventory/skus", headers=headers(), params={"low_stock_only": True})
    assert low_stock.status_code == 200

    summary = client.get("/api/inventory/summary", headers=headers())
    assert summary.status_code == 200
    assert summary.json()["total_skus"] >= 1


def test_inventory_rejects_insufficient_stock_api():
    sku = client.post(
        "/api/inventory/skus",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "sku_code": "SKU-API-LOW",
            "name": "Low Stock Item",
            "quantity_on_hand": 1,
        },
    )
    assert sku.status_code == 201

    movement = client.post(
        "/api/inventory/movements",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "sku_id": sku.json()["id"],
            "movement_type": "out",
            "quantity": 10,
        },
    )
    assert movement.status_code == 400
    assert movement.json()["detail"] == "insufficient stock"
