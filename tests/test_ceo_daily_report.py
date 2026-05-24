from fastapi.testclient import TestClient
from uuid import uuid4

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"
OTHER_COMPANY_ID = "00000000-0000-0000-0000-000000000002"


def token(role: str = "admin", company_id: str = COMPANY_ID) -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-ceo-report-test",
            "role": role,
            "company_id": company_id,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin", company_id: str = COMPANY_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role, company_id)}"}


def create_agent_run(status: str, company_id: str = COMPANY_ID) -> dict:
    res = client.post(
        "/api/agent-runs",
        headers=headers(company_id=company_id),
        json={
            "agent_id": "agent:01-ceo-agent",
            "company_id": company_id,
            "input": {"source": "ceo-report-test", "status": status},
        },
    )
    assert res.status_code == 201
    run = res.json()
    if status != "queued":
        trans = client.post(
            f"/api/agent-runs/{run['id']}/transition",
            headers=headers(company_id=company_id),
            json={"to_status": "running"},
        )
        assert trans.status_code == 200
        if status in {"done", "failed", "waiting_approval"}:
            trans = client.post(
                f"/api/agent-runs/{run['id']}/transition",
                headers=headers(company_id=company_id),
                json={"to_status": status},
            )
            assert trans.status_code == 200
            run = trans.json()
    return run


def create_task(title: str, status: str = "todo", company_id: str = COMPANY_ID) -> dict:
    res = client.post(
        "/api/tasks",
        headers=headers(company_id=company_id),
        json={
            "company_id": company_id,
            "title": title,
            "status": status,
            "priority": "high",
        },
    )
    assert res.status_code == 201
    return res.json()


def create_approval(title: str, company_id: str = COMPANY_ID) -> dict:
    res = client.post(
        "/api/approvals",
        headers=headers(company_id=company_id),
        json={
            "company_id": company_id,
            "category": "financial",
            "title": title,
            "risk_level": "high",
            "payload": {"amount": 1000},
        },
    )
    assert res.status_code == 201
    return res.json()


def test_ceo_daily_report_aggregates_modules_and_action_items():
    company_id = str(uuid4())
    failed_run = create_agent_run("failed", company_id=company_id)
    waiting_run = create_agent_run("waiting_approval", company_id=company_id)
    done_run = create_agent_run("done", company_id=company_id)
    todo_task = create_task("Review pipeline", status="todo", company_id=company_id)
    create_task("Ship feature", status="in_progress", company_id=company_id)
    approval = create_approval("Approve spend", company_id=company_id)

    res = client.get("/api/reports/ceo-daily", headers=headers(company_id=company_id))
    assert res.status_code == 200
    data = res.json()

    assert data["company_id"] == company_id
    assert data["summary"]["agent_runs"]["total"] >= 3
    assert data["summary"]["agent_runs"]["failed"] >= 1
    assert failed_run["id"] in data["summary"]["agent_runs"]["failed_run_ids"]
    assert waiting_run["id"] in data["summary"]["agent_runs"]["approval_blocked_run_ids"]
    assert done_run["id"] not in data["summary"]["agent_runs"]["failed_run_ids"]
    assert data["summary"]["tasks"]["todo"] >= 1
    assert todo_task["id"] in data["summary"]["tasks"]["todo_task_ids"]
    assert data["summary"]["approvals"]["pending_count"] >= 1
    assert approval["id"] in data["summary"]["approvals"]["pending_ids"]
    assert isinstance(data["summary"]["action_items"], list)
    assert isinstance(data["summary"]["insights"], list)
    assert data["summary"]["day_name"]
    assert data["summary"]["greeting"].startswith("التقرير اليومي")


def test_ceo_daily_report_company_isolated():
    company_id = str(uuid4())
    other_company_id = str(uuid4())
    create_agent_run("done", company_id=company_id)
    other_failed = create_agent_run("failed", company_id=other_company_id)
    other_task = create_task("Other company task", company_id=other_company_id)
    other_approval = create_approval("Other approval", company_id=other_company_id)

    res = client.get("/api/reports/ceo-daily", headers=headers(company_id=company_id))
    assert res.status_code == 200
    data = res.json()

    assert other_failed["id"] not in data["summary"]["agent_runs"]["failed_run_ids"]
    assert other_task["id"] not in data["summary"]["tasks"]["todo_task_ids"]
    assert other_approval["id"] not in data["summary"]["approvals"]["pending_ids"]
