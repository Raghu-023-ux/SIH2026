import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_field_api_endpoints(client):
    # 1. GET /api/v1/field/summary
    sum_res = await client.get("/api/v1/field/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert "total_teams" in sum_data
    assert sum_data["total_teams"] >= 3

    # 2. GET /api/v1/field/assignments
    assign_res = await client.get("/api/v1/field/assignments?callsign=ALPHA-1")
    assert assign_res.status_code == 200
    assign_data = assign_res.json()
    assert assign_data["team"]["callsign"] == "ALPHA-1"
    assert "immediate_conditions" in assign_data

    # 3. POST /api/v1/field/reports
    rep_res = await client.post(
        "/api/v1/field/reports",
        json={
            "location_id": "NER-SIK-GANGTOK-01",
            "reported_by": "ALPHA-1 Lead",
            "report_type": "LANDSLIDE_OBSERVED",
            "severity": "HIGH",
            "description": "Active rockfall on hillside ridge.",
            "latitude": 27.3389,
            "longitude": 88.6065
        }
    )
    assert rep_res.status_code == 201
    rep_data = rep_res.json()
    assert rep_data["status"] == "SUBMITTED"

    # 4. PATCH /api/v1/field/reports/{id}
    patch_res = await client.patch(
        f"/api/v1/field/reports/{rep_data['id']}",
        json={"status": "ACKNOWLEDGED", "reviewed_by": "Duty Officer"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACKNOWLEDGED"

    # 5. POST /api/v1/field/messages
    msg_res = await client.post(
        "/api/v1/field/messages",
        json={
            "sender_id": "HQ Duty Officer",
            "recipient_team": "ALPHA-1",
            "priority": "URGENT",
            "message": "Caution: Secondary rockfall expected."
        }
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()

    # 6. POST /api/v1/field/messages/{id}/acknowledge
    ack_res = await client.post(f"/api/v1/field/messages/{msg_data['id']}/acknowledge?acknowledged_by=ALPHA-1")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged_at"] is not None
