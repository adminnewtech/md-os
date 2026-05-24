from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def token() -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "tester",
            "role": "admin",
            "company_id": "00000000-0000-0000-0000-000000000001",
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_seed_loaded_and_workflow_run_path():
    t = token()
    headers = {"Authorization": f"Bearer {t}"}

    agents = client.get("/api/agents", headers=headers)
    assert agents.status_code == 200
    assert len(agents.json()) >= 25

    workflows = client.get("/api/workflows", headers=headers)
    assert workflows.status_code == 200
    assert len(workflows.json()) >= 6

    wf_id = workflows.json()[0]["id"]
    run = client.post(f"/api/workflows/{wf_id}/run", headers=headers, json={"input": {"hello": "world"}})
    assert run.status_code == 202
    assert run.json()["status"] == "done"

    runs = client.get("/api/workflow-runs", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) >= 1


def test_tasks_crud():
    t = token()
    headers = {"Authorization": f"Bearer {t}"}

    create = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "company_id": "00000000-0000-0000-0000-000000000001",
            "title": "Task A",
            "description": "demo",
        },
    )
    assert create.status_code == 201
    task_id = create.json()["id"]

    get_one = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert get_one.status_code == 200

    update = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json={
            "company_id": "00000000-0000-0000-0000-000000000001",
            "title": "Task A1",
            "description": "demo updated",
        },
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Task A1"

    delete = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert delete.status_code == 200
