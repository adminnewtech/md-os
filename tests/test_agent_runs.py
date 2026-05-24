"""Tests for agent run state machine and API."""
from fastapi.testclient import TestClient

from api.agent_state_machine import can_transition, is_valid_transition
from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": f"{role}-tester",
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
# State machine unit tests
# ---------------------------------------------------------------------------


def test_valid_transition_queued_to_running():
    assert is_valid_transition("queued", "running") is True


def test_valid_transition_running_to_waiting_approval():
    assert is_valid_transition("running", "waiting_approval") is True


def test_valid_transition_running_to_done():
    assert is_valid_transition("running", "done") is True


def test_valid_transition_running_to_failed():
    assert is_valid_transition("running", "failed") is True


def test_valid_transition_waiting_approval_to_running():
    assert is_valid_transition("waiting_approval", "running") is True


def test_valid_transition_waiting_approval_to_failed():
    assert is_valid_transition("waiting_approval", "failed") is True


def test_invalid_transition_queued_to_done():
    assert is_valid_transition("queued", "done") is False


def test_invalid_transition_done_to_running():
    assert is_valid_transition("done", "running") is False


def test_invalid_transition_failed_to_done():
    assert is_valid_transition("failed", "done") is False


def test_can_transition_from_queued():
    run = {"status": "queued"}
    assert can_transition(run, "running") is True
    assert can_transition(run, "done") is False


def test_can_transition_from_running():
    run = {"status": "running"}
    assert can_transition(run, "waiting_approval") is True
    assert can_transition(run, "done") is True
    assert can_transition(run, "failed") is True


def test_can_transition_from_waiting_approval():
    run = {"status": "waiting_approval"}
    assert can_transition(run, "running") is True
    assert can_transition(run, "failed") is True
    assert can_transition(run, "done") is False


def test_terminal_states_cannot_transition():
    for terminal in ("done", "failed"):
        run = {"status": terminal}
        for state in ("queued", "running", "waiting_approval", "done", "failed"):
            assert can_transition(run, state) is False, f"{terminal} -> {state} should be blocked"


# ---------------------------------------------------------------------------
# Agent run API tests
# ---------------------------------------------------------------------------


def test_create_agent_run():
    res = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={
            "agent_id": "agent:01",
            "company_id": COMPANY_ID,
            "input": {"task": "build report"},
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id"]
    assert data["status"] == "queued"
    assert data["agent_id"] == "agent:01"
    assert data["company_id"] == COMPANY_ID


def test_list_agent_runs():
    # Create a run first
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:02", "company_id": COMPANY_ID},
    )
    assert create.status_code == 201

    # List runs
    listed = client.get("/api/agent-runs", headers=headers())
    assert listed.status_code == 200
    assert any(r["agent_id"] == "agent:02" for r in listed.json())


def test_get_agent_run():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:03", "company_id": COMPANY_ID},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]

    get = client.get(f"/api/agent-runs/{run_id}", headers=headers())
    assert get.status_code == 200
    assert get.json()["id"] == run_id


def test_get_agent_run_not_found():
    res = client.get("/api/agent-runs/nonexistent-id", headers=headers())
    assert res.status_code == 404


def test_transition_queued_to_running():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:04", "company_id": COMPANY_ID},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]

    trans = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "running"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "running"


def test_transition_running_to_waiting_approval():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:05", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    # queued → running
    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})

    # running → waiting_approval
    trans = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "waiting_approval"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "waiting_approval"


def test_transition_waiting_approval_to_running():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:06", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    client.post(
        f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "waiting_approval"}
    )

    # waiting_approval → running (resume after approval)
    trans = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "running"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "running"


def test_transition_running_to_done():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:07", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    trans = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "done"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "done"


def test_transition_running_to_failed():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:08", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    trans = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "failed"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "failed"


def test_invalid_transition_returns_409():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:09", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    # queued → done is invalid
    res = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "done"},
    )
    assert res.status_code == 409
    assert "invalid transition" in res.json()["detail"]


def test_terminal_transition_blocked():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:10", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "done"})

    # done is terminal — any further transition fails
    res = client.post(
        f"/api/agent-runs/{run_id}/transition",
        headers=headers(),
        json={"to_status": "running"},
    )
    assert res.status_code == 409


def test_agent_run_request_approval_interrupts_and_links_approval():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:approval", "company_id": COMPANY_ID},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]
    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})

    interrupt = client.post(
        f"/api/agent-runs/{run_id}/request-approval",
        headers=headers(),
        json={
            "category": "financial",
            "title": "Approve vendor payment",
            "risk_level": "high",
            "payload": {"amount_kwd": 1200},
        },
    )

    assert interrupt.status_code == 201
    approval = interrupt.json()["approval"]
    run = interrupt.json()["agent_run"]
    assert approval["status"] == "pending"
    assert approval["category"] == "financial"
    assert run["status"] == "waiting_approval"
    assert run["waiting_approval_id"] == approval["id"]


def test_approval_decision_resumes_waiting_agent_run_when_approved():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:resume", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]
    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    interrupt = client.post(
        f"/api/agent-runs/{run_id}/request-approval",
        headers=headers(),
        json={"category": "production", "title": "Deploy change"},
    )
    approval_id = interrupt.json()["approval"]["id"]

    decision = client.post(
        f"/api/approvals/{approval_id}/decide",
        headers=headers(),
        json={"decision": "approved", "decided_by": "ops-lead"},
    )

    assert decision.status_code == 200
    body = decision.json()
    assert body["approval"]["status"] == "approved"
    assert body["agent_run"]["status"] == "running"
    assert body["agent_run"]["waiting_approval_id"] is None


def test_approval_decision_fails_waiting_agent_run_when_rejected():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:reject", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]
    client.post(f"/api/agent-runs/{run_id}/transition", headers=headers(), json={"to_status": "running"})
    interrupt = client.post(
        f"/api/agent-runs/{run_id}/request-approval",
        headers=headers(),
        json={"category": "secret", "title": "Read secret"},
    )
    approval_id = interrupt.json()["approval"]["id"]

    decision = client.post(
        f"/api/approvals/{approval_id}/decide",
        headers=headers(),
        json={"decision": "rejected", "decided_by": "security-lead"},
    )

    assert decision.status_code == 200
    body = decision.json()
    assert body["approval"]["status"] == "rejected"
    assert body["agent_run"]["status"] == "failed"
    assert body["agent_run"]["error"] == "approval rejected"


def test_request_approval_on_non_running_run_does_not_create_orphan_approval():
    create = client.post(
        "/api/agent-runs",
        headers=headers(),
        json={"agent_id": "agent:queued", "company_id": COMPANY_ID},
    )
    run_id = create.json()["id"]

    before = client.get("/api/approvals", headers=headers())
    before_count = len(before.json())

    interrupt = client.post(
        f"/api/agent-runs/{run_id}/request-approval",
        headers=headers(),
        json={"category": "financial", "title": "Should fail while queued"},
    )
    assert interrupt.status_code == 409

    after = client.get("/api/approvals", headers=headers())
    assert len(after.json()) == before_count


def test_viewer_cannot_create_agent_run():
    res = client.post(
        "/api/agent-runs",
        headers=headers("viewer"),
        json={"agent_id": "agent:11", "company_id": COMPANY_ID},
    )
    assert res.status_code == 403
