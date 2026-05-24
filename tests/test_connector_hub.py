"""Test API Connector Hub module."""
from fastapi.testclient import TestClient


def test_connector_crud(client: TestClient):
    """Create → read → list → update → delete connector."""
    # Create
    r = client.post("/api/connectors", json={
        "name": "Telegram Bot",
        "connector_type": "telegram",
        "config": {"token": "123:telegram-bot-token"},
    })
    assert r.status_code == 201
    cid = r.json()["id"]

    # Read
    r = client.get(f"/api/connectors/{cid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Telegram Bot"

    # List
    r = client.get("/api/connectors")
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert cid in ids

    # Update
    r = client.put(f"/api/connectors/{cid}", json={"name": "Telegram Bot Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Telegram Bot Updated"

    # Delete
    r = client.delete(f"/api/connectors/{cid}")
    assert r.status_code == 200

    # Gone
    r = client.get(f"/api/connectors/{cid}")
    assert r.status_code == 404


def test_connector_types(client: TestClient):
    """Connector type enum — create one of each type."""
    types = ["telegram", "github", "paperclip", "hermes_gateway",
             "zoho_books", "quickbooks", "shopify", "woocommerce",
             "stripe", "tap", "myfatoorah", "whatsapp_business",
             "google_workspace", "n8n", "webhook"]
    created = []
    for ct in types:
        r = client.post("/api/connectors", json={
            "name": f"Connector {ct}",
            "connector_type": ct,
            "config": {},
        })
        assert r.status_code == 201, f"Failed to create {ct}: {r.json()}"
        created.append(r.json()["id"])

    # List all
    r = client.get("/api/connectors")
    assert r.status_code == 200
    assert len(r.json()) >= len(types)


def test_connector_health(client: TestClient):
    """Connector health check endpoint."""
    r = client.get("/api/connectors/health")
    assert r.status_code == 200
    data = r.json()
    assert "total_connectors" in data
    assert "healthy_connectors" in data
    assert "unhealthy_connectors" in data


def test_connector_company_isolation(client: TestClient):
    """Connectors scoped to company."""
    # Create two companies
    r1 = client.post("/api/companies", json={"name": "Company A"})
    r2 = client.post("/api/companies", json={"name": "Company B"})
    c1 = r1.json()["id"]
    c2 = r2.json()["id"]

    # Create connector for Company A
    r = client.post("/api/connectors", json={
        "company_id": c1,
        "name": "Conn A",
        "connector_type": "telegram",
        "config": {},
    })
    assert r.status_code == 201
    cid = r.json()["id"]

    # Conn A visible to Company A
    r = client.get("/api/connectors", headers={"x-company-id": c1})
    assert any(c["id"] == cid for c in r.json())

    # Conn A NOT visible to Company B
    r = client.get("/api/connectors", headers={"x-company-id": c2})
    assert not any(c["id"] == cid for c in r.json())


def test_connector_permissions(client: TestClient):
    """Viewer role blocked from write operations."""
    # Grant viewer role
    client.post("/api/roles", json={"name": "viewer", "permissions": ["connector:read"]})

    # Create user with viewer role
    r = client.post("/api/auth/dev-token", json={
        "user_id": "viewer-user",
        "company_id": "test-company",
        "role": "viewer",
    })
    token = r.json()["token"]

    # Viewer blocked from create
    r = client.post("/api/connectors", json={
        "name": "Conn Test",
        "connector_type": "telegram",
        "config": {},
    }, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 403

    # Viewer CAN read
    r = client.get("/api/connectors", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200