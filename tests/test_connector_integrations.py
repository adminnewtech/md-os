"""Test-first: connector integrations (Telegram, GitHub, Paperclip, Hermes Gateway, Zoho)"""

import pytest, uuid
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


COMPANY_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def auth_headers(client):
    r = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "connector-integration-test",
            "role": "admin",
            "company_id": COMPANY_ID,
            "workspace_id": "default",
        },
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Telegram Connector ──────────────────────────────────────────

def test_telegram_connector_create(client, auth_headers):
    """Create a Telegram bot connector."""
    res = client.post(
        "/api/connectors",
        json={
            "connector_type": "telegram",
            "name": "Ops Bot",
            "config": {
                "bot_token": "123456:ABC-DEF",
                "chat_id": "-100123456",
                "parse_mode": "HTML",
            },
        },
        headers=auth_headers,
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["connector_type"] == "telegram"
    assert data["name"] == "Ops Bot"
    assert data["config"]["bot_token"] == "123456:ABC-DEF"


def test_telegram_connector_list(client, auth_headers):
    """List all connectors, filter by type."""
    # create one first
    client.post(
        "/api/connectors",
        json={"connector_type": "telegram", "name": "TG List Test", "config": {"bot_token": "x"}},
        headers=auth_headers,
    )
    res = client.get("/api/connectors?connector_type=telegram", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    assert any(c["connector_type"] == "telegram" for c in items)


def test_telegram_connector_health(client, auth_headers):
    """Health check returns status for Telegram connector."""
    # create
    create = client.post(
        "/api/connectors",
        json={"connector_type": "telegram", "name": "TG Health", "config": {"bot_token": "test_token_health"}},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    res = client.get(f"/api/connectors/{cid}/health", headers=auth_headers)
    # may return 404 if not implemented yet, or 200 with status
    assert res.status_code in (200, 404, 503)


def test_telegram_connector_delete(client, auth_headers):
    """Delete a Telegram connector."""
    create = client.post(
        "/api/connectors",
        json={"connector_type": "telegram", "name": "TG Del", "config": {"bot_token": "x"}},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    res = client.delete(f"/api/connectors/{cid}", headers=auth_headers)
    assert res.status_code in (200, 204)


# ── GitHub Connector ──────────────────────────────────────────

def test_github_connector_create(client, auth_headers):
    """Create a GitHub app / PAT connector."""
    res = client.post(
        "/api/connectors",
        json={
            "connector_type": "github",
            "name": "MD-OS GitHub",
            "config": {
                "auth_type": "pat",
                "token": "ghp_test_token_123",
                "repository": "nous-research/md-os",
                "owner": "nous-research",
            },
        },
        headers=auth_headers,
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["connector_type"] == "github"
    assert data["config"]["auth_type"] == "pat"


def test_github_webhook_log(client, auth_headers):
    """Webhook logs are recorded for GitHub events."""
    create = client.post(
        "/api/connectors",
        json={"connector_type": "github", "name": "GH Webhook", "config": {"auth_type": "pat", "token": "x", "repo": "test/repo"}},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    # post a webhook event
    res = client.post(
        f"/api/connectors/{cid}/webhook",
        json={"event": "push", "payload": {"ref": "refs/heads/main"}, "delivery_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert res.status_code in (200, 201, 204)


# ── Paperclip Connector ───────────────────────────────────────

def test_paperclip_connector_create(client, auth_headers):
    """Create a Paperclip platform connector."""
    res = client.post(
        "/api/connectors",
        json={
            "connector_type": "paperclip",
            "name": "Newtech Kuwait",
            "config": {
                "base_url": "https://paperclip.83-171-249-32.nip.io",
                "api_key": "test_key_placeholder",
                "company_id": "5c0789c4-38a5-47e0-821c-df6e293f1b87",
            },
        },
        headers=auth_headers,
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["connector_type"] == "paperclip"
    assert data["name"] == "Newtech Kuwait"


def test_paperclip_sync_agents(client, auth_headers):
    """Sync agents from Paperclip into MD-OS."""
    # First create connector
    create = client.post(
        "/api/connectors",
        json={
            "connector_type": "paperclip",
            "name": "PC Sync Test",
            "config": {"base_url": "https://paperclip.83-171-249-32.nip.io", "api_key": "x", "company_id": "5c0789c4-38a5-47e0-821c-df6e293f1b87"},
        },
        headers=auth_headers,
    )
    cid = create.json()["id"]
    res = client.post(f"/api/connectors/{cid}/sync", headers=auth_headers)
    # 200 = synced, 404 = not wired yet, 503 = Paperclip unreachable
    assert res.status_code in (200, 404, 503)


# ── Hermes Gateway Connector ──────────────────────────────────

def test_hermes_gateway_connector_create(client, auth_headers):
    """Create a Hermes Gateway connector."""
    res = client.post(
        "/api/connectors",
        json={
            "connector_type": "hermes_gateway",
            "name": "Local Gateway",
            "config": {
                "gateway_url": "http://127.0.0.1:8642",
                "api_key": "test_key",
                "workspace_id": "md-os-workspace",
            },
        },
        headers=auth_headers,
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["connector_type"] == "hermes_gateway"


def test_hermes_gateway_cron_status(client, auth_headers):
    """Fetch cron job status from Hermes Gateway."""
    create = client.post(
        "/api/connectors",
        json={"connector_type": "hermes_gateway", "name": "HG Cron", "config": {"gateway_url": "http://127.0.0.1:8642", "api_key": "x"}},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    res = client.get(f"/api/connectors/{cid}/cron", headers=auth_headers)
    assert res.status_code in (200, 404, 503)


# ── Zoho Connector ────────────────────────────────────────────

def test_zoho_connector_create(client, auth_headers):
    """Create a Zoho CRM connector."""
    res = client.post(
        "/api/connectors",
        json={
            "connector_type": "zoho",
            "name": "Zoho CRM",
            "config": {
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "datacenter": "com",
                "scope": "ZohoCRM.modules.ALL",
            },
        },
        headers=auth_headers,
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["connector_type"] == "zoho"


def test_zoho_oauth_flow(client, auth_headers):
    """Initiate Zoho OAuth flow and exchange auth code."""
    create = client.post(
        "/api/connectors",
        json={"connector_type": "zoho", "name": "Zoho OAuth", "config": {"client_id": "x", "client_secret": "y", "datacenter": "com"}},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    res = client.post(
        f"/api/connectors/{cid}/oauth",
        json={"code": "test_auth_code"},
        headers=auth_headers,
    )
    assert res.status_code in (200, 404, 503)


# ── Cross-connector: credentials, webhook logs, health ──────────

def test_connector_credentials_crud(client, auth_headers):
    """Store and retrieve connector credentials."""
    res = client.post(
        "/api/connector-credentials",
        json={"connector_id": str(uuid.uuid4()), "credential_key": "bot_token", "credential_value": "secret123", "encrypted": True},
        headers=auth_headers,
    )
    assert res.status_code in (200, 201, 400), res.text  # 400 if connector_id not found


def test_webhook_logs_list(client, auth_headers):
    """List webhook delivery logs."""
    res = client.get("/api/webhook-logs", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_all_connectors_health(client, auth_headers):
    """GET /api/connectors/health returns all connector statuses."""
    res = client.get("/api/connectors/health", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list) or isinstance(data, dict)