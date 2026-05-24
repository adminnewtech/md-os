from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def token() -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "crm-tester",
            "role": "admin",
            "company_id": "00000000-0000-0000-0000-000000000001",
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_crm_contact_lead_convert_and_pipeline():
    t = token()
    headers = {"Authorization": f"Bearer {t}"}
    company_id = "00000000-0000-0000-0000-000000000001"

    contact = client.post(
        "/api/crm/contacts",
        headers=headers,
        json={
            "company_id": company_id,
            "first_name": "Maha",
            "last_name": "Ali",
            "email": "maha@example.com",
            "company_name": "NewTech Kuwait",
        },
    )
    assert contact.status_code == 201
    contact_id = contact.json()["id"]

    lead = client.post(
        "/api/crm/leads",
        headers=headers,
        json={
            "company_id": company_id,
            "contact_id": contact_id,
            "title": "AI OS rollout",
            "status": "qualified",
            "score": 85,
        },
    )
    assert lead.status_code == 201
    lead_id = lead.json()["id"]

    converted = client.post(f"/api/crm/leads/{lead_id}/convert", headers=headers)
    assert converted.status_code == 200
    body = converted.json()
    assert body["lead"]["status"] == "converted"
    assert body["deal"]["lead_id"] == lead_id
    deal_id = body["deal"]["id"]

    stage_update = client.patch(
        f"/api/crm/deals/{deal_id}/stage",
        headers=headers,
        params={"stage": "closed_won"},
    )
    assert stage_update.status_code == 200
    assert stage_update.json()["stage"] == "closed_won"
    assert stage_update.json()["closed_at"] is not None

    activity = client.post(
        f"/api/crm/deals/{deal_id}/activities",
        headers=headers,
        json={
            "deal_id": deal_id,
            "activity_type": "note",
            "description": "Customer approved proposal",
        },
    )
    assert activity.status_code == 200
    assert activity.json()["deal_id"] == deal_id

    pipeline = client.get("/api/crm/pipeline", headers=headers)
    assert pipeline.status_code == 200
    pipeline_body = pipeline.json()
    assert pipeline_body["closed_won_count"] >= 1
    assert "closed_won" in pipeline_body["pipeline"]


def test_crm_rejects_invalid_stage():
    t = token()
    headers = {"Authorization": f"Bearer {t}"}
    company_id = "00000000-0000-0000-0000-000000000001"

    deal = client.post(
        "/api/crm/deals",
        headers=headers,
        json={
            "company_id": company_id,
            "title": "Invalid stage test",
            "value": 1200,
        },
    )
    assert deal.status_code == 201
    deal_id = deal.json()["id"]

    bad = client.patch(
        f"/api/crm/deals/{deal_id}/stage",
        headers=headers,
        params={"stage": "bad_stage"},
    )
    assert bad.status_code == 400
    assert bad.json()["detail"] == "invalid stage"
