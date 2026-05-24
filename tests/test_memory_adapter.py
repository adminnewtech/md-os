from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"
OTHER_COMPANY_ID = "00000000-0000-0000-0000-000000000099"


def token(company_id: str = COMPANY_ID, role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-memory-test",
            "role": role,
            "company_id": company_id,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(company_id: str = COMPANY_ID, role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(company_id, role)}"}


def _embed(val: float) -> list[float]:
    return [val] * 768


def test_memory_write_list_get_delete_flow() -> None:
    res = client.post(
        "/api/memory",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "agent_id": "agent-1",
            "key": "crm:lead:priority",
            "value": "high intent lead",
            "embedding": _embed(1.0),
            "metadata": {"source": "crm"},
        },
    )
    assert res.status_code == 201
    mem = res.json()

    list_res = client.get("/api/memory", headers=headers())
    assert list_res.status_code == 200
    assert any(x["id"] == mem["id"] for x in list_res.json())

    get_res = client.get(f"/api/memory/{mem['id']}", headers=headers())
    assert get_res.status_code == 200
    assert get_res.json()["key"] == "crm:lead:priority"

    del_res = client.delete(f"/api/memory/{mem['id']}", headers=headers())
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True


def test_memory_search_returns_top_similar_with_filters() -> None:
    client.post(
        "/api/memory",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "agent_id": "a1",
            "key": "sales:note:1",
            "value": "close fit",
            "embedding": _embed(1.0),
            "metadata": {},
        },
    )
    client.post(
        "/api/memory",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "agent_id": "a2",
            "key": "hr:note:1",
            "value": "far fit",
            "embedding": _embed(-1.0),
            "metadata": {},
        },
    )

    res = client.post(
        "/api/memory/search",
        headers=headers(),
        json={
            "query_embedding": _embed(1.0),
            "top_k": 3,
            "key_prefix": "sales:",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["key"].startswith("sales:")


def test_memory_cross_company_denied() -> None:
    create = client.post(
        "/api/memory",
        headers=headers(),
        json={
            "company_id": COMPANY_ID,
            "key": "secret:key",
            "value": "top secret",
            "embedding": _embed(0.5),
            "metadata": {},
        },
    )
    assert create.status_code == 201
    mem_id = create.json()["id"]

    get_other = client.get(f"/api/memory/{mem_id}", headers=headers(OTHER_COMPANY_ID))
    assert get_other.status_code == 403
