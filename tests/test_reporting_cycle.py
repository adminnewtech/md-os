from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin", company_id: str = COMPANY_ID) -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-report-test",
            "role": role,
            "company_id": company_id,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin", company_id: str = COMPANY_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role, company_id)}"}


def create_agent_run(status: str) -> dict:
    res = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={
            "agent_id": "agent:01-ceo-agent",
            "company_id": COMPANY_ID,
            "input": {"source": "reporting-test", "status": status},
        },
    )
    assert res.status_code == 201
    run = res.json()
    if status != "queued":
        trans = client.post(
            f"/api/agent-runs/{run['id']}/transition",
            headers=headers(),
            json={"to_status": "running"},
        )
        assert trans.status_code == 200
        if status in {"done", "failed", "waiting_approval"}:
            trans = client.post(
                f"/api/agent-runs/{run['id']}/transition",
                headers=headers(),
                json={"to_status": status},
            )
            assert trans.status_code == 200
            run = trans.json()
    return run


def test_periodic_report_aggregates_agent_run_statuses():
    create_agent_run("queued")
    done_run = create_agent_run("done")
    failed_run = create_agent_run("failed")
    blocked_run = create_agent_run("waiting_approval")

    res = client.get("/api/reports/agent-periodic", headers=headers())
    assert res.status_code == 200
    data = res.json()

    assert data["company_id"] == COMPANY_ID
    assert data["window_hours"] == 6
    assert data["totals"]["agent_runs"] >= 4
    assert data["status_counts"]["queued"] >= 1
    assert data["status_counts"]["done"] >= 1
    assert data["status_counts"]["failed"] >= 1
    assert data["status_counts"]["waiting_approval"] >= 1
    assert done_run["id"] not in data["failed_run_ids"]
    assert failed_run["id"] in data["failed_run_ids"]
    assert blocked_run["id"] in data["approval_blocked_run_ids"]


def test_periodic_report_cross_company_isolated():
    other_company = "00000000-0000-0000-0000-000000000002"
    other_run = client.post(
        "/api/agent-runs",
        headers=headers(company_id=other_company),
        json={
            "agent_id": "agent:01-ceo-agent",
            "company_id": other_company,
            "input": {"source": "other-company"},
        },
    )
    assert other_run.status_code == 201

    res = client.get("/api/reports/agent-periodic", headers=headers())
    assert res.status_code == 200
    data = res.json()
    assert other_run.json()["id"] not in data["failed_run_ids"]
    assert other_run.json()["id"] not in data["approval_blocked_run_ids"]
