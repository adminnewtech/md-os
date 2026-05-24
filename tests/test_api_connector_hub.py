from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "integration-tester",
            "role": role,
            "company_id": COMPANY_ID,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def auth(role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role)}"}


def test_create_and_list_credentials():
    created = client.post(
        "/api/integrations/credentials",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "Telegram Bot",
            "provider": "telegram",
            "auth_type": "api_key",
            "credentials": {"token": "abc"},
            "base_url": "https://api.telegram.org",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["provider"] == "telegram"

    listed = client.get("/api/integrations/credentials", headers=auth())
    assert listed.status_code == 200
    assert any(c["id"] == body["id"] for c in listed.json())

    filtered = client.get("/api/integrations/credentials", headers=auth(), params={"provider": "telegram"})
    assert filtered.status_code == 200
    assert all(c["provider"] == "telegram" for c in filtered.json())


def test_delete_credential():
    created = client.post(
        "/api/integrations/credentials",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "GitHub OAuth",
            "provider": "github",
            "auth_type": "oauth2",
            "credentials": {"client_id": "x", "client_secret": "y"},
        },
    )
    assert created.status_code == 201
    cred_id = created.json()["id"]

    deleted = client.delete(f"/api/integrations/credentials/{cred_id}", headers=auth())
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/api/integrations/credentials/{cred_id}", headers=auth())
    assert missing.status_code == 404


def test_create_and_list_webhooks():
    created = client.post(
        "/api/integrations/webhooks",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "Paperclip Event Hook",
            "target_url": "https://example.com/hooks/paperclip",
            "events": ["invite.created", "invite.accepted"],
            "secret": "webhook-secret",
        },
    )
    assert created.status_code == 201
    body = created.json()

    listed = client.get("/api/integrations/webhooks", headers=auth())
    assert listed.status_code == 200
    assert any(w["id"] == body["id"] for w in listed.json())


def test_connector_health_endpoint():
    client.post(
        "/api/integrations/credentials",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "Stripe Connector",
            "provider": "stripe",
            "auth_type": "api_key",
            "credentials": {"api_key": "sk_test"},
            "is_active": True,
        },
    )

    health = client.get("/api/integrations/health", headers=auth())
    assert health.status_code == 200
    body = health.json()
    assert body["total_connectors"] >= 1
    assert body["active_connectors"] >= 1
    assert "providers" in body


def test_log_api_call_flow():
    cred = client.post(
        "/api/integrations/credentials",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "Paperclip API",
            "provider": "paperclip",
            "auth_type": "bearer_token",
            "credentials": {"token": "secret"},
        },
    )
    assert cred.status_code == 201
    connector_id = cred.json()["id"]

    log = client.post(
        "/api/integrations/logs",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "connector_id": connector_id,
            "direction": "outgoing",
            "method": "POST",
            "endpoint": "/invites",
            "status_code": 201,
            "duration_ms": 142,
            "request_body": "{\"email\":\"x@example.com\"}",
            "response_body": "{\"ok\":true}",
        },
    )
    assert log.status_code == 201

    logs = client.get("/api/integrations/logs", headers=auth(), params={"connector_id": connector_id})
    assert logs.status_code == 200
    assert any(l["connector_id"] == connector_id for l in logs.json())


def test_manager_has_integration_permissions():
    denied = client.post(
        "/api/integrations/credentials",
        headers=auth(role="viewer"),
        json={
            "company_id": COMPANY_ID,
            "name": "Denied",
            "provider": "github",
            "auth_type": "api_key",
            "credentials": {},
        },
    )
    assert denied.status_code == 403

    allowed = client.get("/api/integrations/health", headers=auth(role="manager"))
    assert allowed.status_code == 200
