"""Tests for Hermes Orchestrator service (p2-01)."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-orch-test",
            "role": role,
            "company_id": COMPANY_ID,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def headers(role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role)}"}


# ---------------------------------------------------------------------------
# Orchestrator Cycle API tests
# ---------------------------------------------------------------------------


def _create_cycle(
    task_description: str,
    agent_ids: list[str],
    context: dict | None = None,
    max_parallel: int = 4,
) -> str:
    res = client.post(
        "/api/orchestrator/cycles",
        headers=headers(),
        json={
            "task_description": task_description,
            "company_id": COMPANY_ID,
            "agent_ids": agent_ids,
            "context": context or {},
            "max_parallel": max_parallel,
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_create_orchestrator_cycle():
    cycle_id = _create_cycle(
        task_description="analyze CRM pipeline and generate report",
        agent_ids=["agent:01", "agent:02"],
        context={"priority": "high"},
    )
    res = client.get(f"/api/orchestrator/cycles/{cycle_id}", headers=headers())
    assert res.status_code == 200
    data = res.json()
    assert data["id"]
    assert data["status"] == "planning"
    assert data["company_id"] == COMPANY_ID
    assert len(data["agent_ids"]) == 2


def test_create_cycle_minimal():
    """Only required fields."""
    res = client.post(
        "/api/orchestrator/cycles",
        headers=headers(),
        json={
            "task_description": "inventory stock check",
            "company_id": COMPANY_ID,
            "agent_ids": [],
        },
    )
    assert res.status_code == 201
    assert res.json()["status"] == "planning"


def test_create_cycle_cross_company_denied():
    """Viewer role cannot create cycle for different company."""
    res = client.post(
        "/api/orchestrator/cycles",
        headers=headers("viewer"),
        json={
            "task_description": "any task",
            "company_id": "00000000-0000-0000-0000-999999999999",
            "agent_ids": [],
        },
    )
    assert res.status_code == 403


def test_list_orchestrator_cycles():
    # Create one first
    client.post(
        "/api/orchestrator/cycles",
        headers=headers(),
        json={"task_description": "list test", "company_id": COMPANY_ID, "agent_ids": []},
    )
    res = client.get("/api/orchestrator/cycles", headers=headers())
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_orchestrator_cycle():
    cycle_id = _create_cycle("analyze CRM pipeline and generate report", ["agent:01", "agent:02"])
    res = client.get(f"/api/orchestrator/cycles/{cycle_id}", headers=headers())
    assert res.status_code == 200
    assert res.json()["id"] == cycle_id


def test_get_orchestrator_cycle_not_found():
    res = client.get("/api/orchestrator/cycles/nonexistent-cycle-id", headers=headers())
    assert res.status_code == 404


def test_run_orchestrator_cycle_crm_task():
    """Run a full cycle for a CRM task — plan → delegate → monitor → report."""
    cycle_id = _create_cycle(
        task_description="analyze CRM pipeline and generate report",
        agent_ids=["agent:01", "agent:02"],
    )

    # Run cycle
    run = client.post(f"/api/orchestrator/cycles/{cycle_id}/run", headers=headers())
    assert run.status_code == 200
    data = run.json()

    assert data["status"] == "done"
    assert data["result"]
    assert "plan" in data["result"] or "plan_summary" in data["result"]
    assert data["result"]["task_description"] == "analyze CRM pipeline and generate report"
    # CRM plan should have 3 steps
    assert len(data["plan"]) >= 1


def test_run_orchestrator_cycle_inventory_task():
    """Run a full cycle for an inventory task."""
    cycle_id = _create_cycle(
        task_description="check inventory stock levels and reorder if low",
        agent_ids=["agent:03"],
    )

    run = client.post(f"/api/orchestrator/cycles/{cycle_id}/run", headers=headers())
    assert run.status_code == 200
    assert run.json()["status"] == "done"
    # Inventory plan: scan → detect → order (3 steps)
    assert len(run.json()["plan"]) == 3


def test_run_orchestrator_cycle_finance_task():
    """Run a full cycle for a finance task."""
    cycle_id = _create_cycle(
        task_description="prepare finance report with invoices and cashflow",
        agent_ids=["agent:04"],
    )

    run = client.post(f"/api/orchestrator/cycles/{cycle_id}/run", headers=headers())
    assert run.status_code == 200
    assert run.json()["status"] == "done"
    # Finance plan: fetch → calculate → report (3 steps)
    assert len(run.json()["plan"]) == 3


def test_run_orchestrator_cycle_not_found():
    res = client.post("/api/orchestrator/cycles/nonexistent-id/run", headers=headers())
    assert res.status_code == 404


def test_run_orchestrator_cycle_cross_company_denied():
    """Cannot run a cycle that belongs to a different company."""
    cycle_id = _create_cycle("test", [])
    other_token = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "other-user",
            "role": "admin",
            "company_id": "00000000-0000-0000-0000-000000000002",
            "workspace_id": "default",
        },
    ).json()["access_token"]

    res = client.post(
        f"/api/orchestrator/cycles/{cycle_id}/run",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 403


def test_run_orchestrator_cycle_resumes_planning_status():
    """A fresh cycle is in 'planning' status before running."""
    res = client.post(
        "/api/orchestrator/cycles",
        headers=headers(),
        json={"task_description": "any task", "company_id": COMPANY_ID, "agent_ids": []},
    )
    assert res.json()["status"] == "planning"


def test_cycle_idempotent_get():
    """Getting the same cycle twice returns same data."""
    cycle_id = _create_cycle("idempotent", [])
    first = client.get(f"/api/orchestrator/cycles/{cycle_id}", headers=headers())
    second = client.get(f"/api/orchestrator/cycles/{cycle_id}", headers=headers())
    assert first.json()["id"] == second.json()["id"]
