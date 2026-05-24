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


def test_viewer_rbac_blocks_project_write():
    res = client.post(
        "/api/projects",
        headers=headers("viewer"),
        json={"company_id": COMPANY_ID, "workspace_id": "default", "name": "Viewer blocked"},
    )
    assert res.status_code == 403
    assert "missing permission" in res.json()["detail"]


def test_workspace_scope_filters_project_list_and_get():
    create_default = client.post(
        "/api/projects",
        headers=headers("admin", workspace_id="default"),
        json={"company_id": COMPANY_ID, "workspace_id": "default", "name": "Default workspace project"},
    )
    assert create_default.status_code == 201

    create_ops = client.post(
        "/api/projects",
        headers=headers("admin", workspace_id="ops"),
        json={"company_id": COMPANY_ID, "workspace_id": "ops", "name": "Ops workspace project"},
    )
    assert create_ops.status_code == 201

    listed = client.get("/api/projects", headers=headers("admin", workspace_id="default"))
    assert listed.status_code == 200
    names = {row["name"] for row in listed.json()}
    assert "Default workspace project" in names
    assert "Ops workspace project" not in names

    forbidden_get = client.get(
        f"/api/projects/{create_ops.json()['id']}", headers=headers("admin", workspace_id="default")
    )
    assert forbidden_get.status_code == 403
    assert forbidden_get.json()["detail"] == "cross-workspace access denied"


def test_cross_company_create_denied():
    res = client.post(
        "/api/projects",
        headers=headers("admin", company_id=COMPANY_ID),
        json={
            "company_id": "11111111-1111-1111-1111-111111111111",
            "workspace_id": "default",
            "name": "Wrong company",
        },
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "cross-company access denied"
