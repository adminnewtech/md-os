from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin", company_id: str = COMPANY_ID, workspace_id: str = "default") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-tester",
            "role": role,
            "company_id": company_id,
            "workspace_id": workspace_id,
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin", company_id: str = COMPANY_ID, workspace_id: str = "default") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role, company_id, workspace_id)}"}


def test_audit_log_captures_create():
    res = client.post(
        "/api/tasks",
        headers=headers("admin"),
        json={
            "company_id": COMPANY_ID,
            "title": "Audit test task",
            "description": "testing audit",
        },
    )
    assert res.status_code == 201
    task_id = res.json()["id"]

    logs = client.get("/api/audit-logs", headers=headers("admin"))
    assert logs.status_code == 200
    entries = [e for e in logs.json() if e["entity_id"] == task_id]
    assert len(entries) >= 1
    entry = entries[0]
    assert entry["action"] == "create"
    assert entry["entity_type"] == "task"
    assert entry["after"] is not None


def test_audit_log_captures_update():
    create = client.post(
        "/api/tasks",
        headers=headers("admin"),
        json={"company_id": COMPANY_ID, "title": "Audit update test"},
    )
    assert create.status_code == 201
    task_id = create.json()["id"]

    client.put(
        f"/api/tasks/{task_id}",
        headers=headers("admin"),
        json={"company_id": COMPANY_ID, "title": "Audit update test — updated"},
    )

    logs = client.get("/api/audit-logs", headers=headers("admin"))
    entries = [e for e in logs.json() if e["entity_id"] == task_id and e["action"] == "update"]
    assert len(entries) == 1
    assert entries[0]["before"]["title"] == "Audit update test"
    assert entries[0]["after"]["title"] == "Audit update test — updated"


def test_audit_log_captures_delete():
    create = client.post(
        "/api/tasks",
        headers=headers("admin"),
        json={"company_id": COMPANY_ID, "title": "Audit delete test"},
    )
    assert create.status_code == 201
    task_id = create.json()["id"]

    client.delete(f"/api/tasks/{task_id}", headers=headers("admin"))

    logs = client.get("/api/audit-logs", headers=headers("admin"))
    entries = [e for e in logs.json() if e["entity_id"] == task_id and e["action"] == "delete"]
    assert len(entries) == 1
    assert entries[0]["after"] is None


def test_approval_guard_blocks_without_approval_header():
    # Regular task — no action category → passes
    res = client.post(
        "/api/tasks",
        headers=headers("admin"),
        json={
            "company_id": COMPANY_ID,
            "title": "Secret action",
        },
    )
    assert res.status_code == 201
    task_id = res.json()["id"]

    # Try DELETE with category=destructive but no approval header
    combined = {"Authorization": f"Bearer {token()}", "X-Action-Category": "destructive"}
    res = client.delete(f"/api/tasks/{task_id}", headers=combined)
    assert res.status_code == 428
    assert "approval required" in res.json()["detail"]


def test_approval_guard_missing_header_skips_for_regular():
    res = client.post(
        "/api/tasks",
        headers=headers("admin"),
        json={
            "company_id": COMPANY_ID,
            "title": "Regular task",
        },
    )
    assert res.status_code == 201


def test_approval_guard_passes_with_approval_header():
    combined = {
        "Authorization": f"Bearer {token()}",
        "X-Action-Category": "destructive",
        "X-Approval-Id": "approved-123",
    }
    res = client.post(
        "/api/tasks",
        headers=combined,
        json={
            "company_id": COMPANY_ID,
            "title": "Destructive action",
        },
    )
    assert res.status_code == 201