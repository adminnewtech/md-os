from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
COMPANY_ID = "00000000-0000-0000-0000-000000000001"


def token(role: str = "admin") -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "hr-logistics-tester",
            "role": role,
            "company_id": COMPANY_ID,
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def auth(role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(role)}"}


def test_hr_employee_and_summary_flow():
    created = client.post(
        "/api/hr/employees",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "first_name": "Sara",
            "last_name": "Ali",
            "email": "sara@newtech.kw",
            "department": "Engineering",
            "role": "Backend Developer",
        },
    )
    assert created.status_code == 201
    emp_id = created.json()["id"]

    updated = client.patch(
        f"/api/hr/employees/{emp_id}",
        headers=auth(),
        params={"status": "active", "department": "AI"},
    )
    assert updated.status_code == 200
    assert updated.json()["department"] == "AI"

    summary = client.get("/api/hr/summary", headers=auth())
    assert summary.status_code == 200
    assert summary.json()["total_employees"] >= 1


def test_hr_recruitment_pipeline_flow():
    rec = client.post(
        "/api/hr/recruitment",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "candidate_name": "Fahad",
            "email": "fahad@example.com",
            "position": "DevOps Engineer",
            "stage": "applied",
        },
    )
    assert rec.status_code == 201
    rec_id = rec.json()["id"]

    promoted = client.patch(
        f"/api/hr/recruitment/{rec_id}/stage",
        headers=auth(),
        params={"stage": "interview"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["stage"] == "interview"


def test_logistics_vehicle_shipment_summary_flow():
    veh = client.post(
        "/api/logistics/vehicles",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "name": "Truck 1",
            "plate_number": "KW-1234",
            "vehicle_type": "truck",
            "status": "available",
        },
    )
    assert veh.status_code == 201
    veh_id = veh.json()["id"]

    ship = client.post(
        "/api/logistics/shipments",
        headers=auth(),
        json={
            "company_id": COMPANY_ID,
            "tracking_number": "TRK-1001",
            "vehicle_id": veh_id,
            "origin": "Kuwait City",
            "destination": "Ahmadi",
            "status": "in_transit",
        },
    )
    assert ship.status_code == 201
    ship_id = ship.json()["id"]

    delivered = client.patch(
        f"/api/logistics/shipments/{ship_id}/status",
        headers=auth(),
        params={"status": "delivered"},
    )
    assert delivered.status_code == 200
    assert delivered.json()["status"] == "delivered"

    summary = client.get("/api/logistics/summary", headers=auth())
    assert summary.status_code == 200
    assert summary.json()["total_shipments"] >= 1


def test_permissions_for_hr_and_logistics():
    viewer_denied = client.post(
        "/api/hr/employees",
        headers=auth(role="viewer"),
        json={
            "company_id": COMPANY_ID,
            "first_name": "No",
            "last_name": "Access",
            "email": "x@x.com",
        },
    )
    assert viewer_denied.status_code == 403

    manager_ok = client.get("/api/logistics/summary", headers=auth(role="manager"))
    assert manager_ok.status_code == 200
