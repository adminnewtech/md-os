from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin", company_id: str = COMPANY_ID) -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-tool-test",
            "role": role,
            "company_id": company_id,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin", company_id: str = COMPANY_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role, company_id)}"}


def test_get_tool_permissions_for_seeded_agent():
    res = client.get("/api/agents/agent:13-crm-agent/tool-permissions", headers=headers())
    assert res.status_code == 200
    data = res.json()
    assert data["agent_id"] == "agent:13-crm-agent"
    assert "crm manager" in data["role"].lower()
    assert "terminal" in data["allowed_tools"]
    assert data["tool_count"] >= 1


def test_check_tool_permission_allows_expected_tool():
    res = client.get(
        "/api/agents/agent:17-finance-agent/tool-permissions/check",
        headers=headers(),
        params={"tool_name": "terminal"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["allowed"] is True
    assert data["tool_name"] == "terminal"
    assert "finance" in data["role"].lower()


def test_check_tool_permission_denies_unknown_tool():
    res = client.get(
        "/api/agents/agent:17-finance-agent/tool-permissions/check",
        headers=headers(),
        params={"tool_name": "wire_money"},
    )
    assert res.status_code == 200
    assert res.json()["allowed"] is False


def test_tool_permissions_cross_company_denied():
    create = client.post(
        "/api/agents",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "name": "Private Agent",
            "role": "Custom Operator",
            "mission": "test",
            "config": {"tools": ["terminal"]},
        },
    )
    assert create.status_code == 201
    agent_id = create.json()["id"]

    res = client.get(
        f"/api/agents/{agent_id}/tool-permissions",
        headers=headers(company_id="00000000-0000-0000-0000-000000000999"),
    )
    assert res.status_code == 403
