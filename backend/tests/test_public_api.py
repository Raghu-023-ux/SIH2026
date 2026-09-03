import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_public_api_endpoints(client):
    # Seed a critical event via simulation scenario
    sim_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert sim_res.status_code == 200

    # 1. GET /api/v1/public/status
    status_res = await client.get("/api/v1/public/status")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["system_status"] == "OPERATIONAL"
    assert st_data["active_public_alerts_count"] >= 1

    # 2. GET /api/v1/public/alerts
    alerts_res = await client.get("/api/v1/public/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    target_alert = alerts[0]
    assert target_alert["public_status"] in ["URGENT", "ALERT"]

    # 3. GET /api/v1/public/alerts/{id}
    detail_res = await client.get(f"/api/v1/public/alerts/{target_alert['event_id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "guidance" in detail
    assert len(detail["guidance"]) >= 3
    assert "safer_reference_points" in detail
    assert "emergency_contacts" in detail

    # 4. GET /api/v1/public/risk
    risk_res = await client.get("/api/v1/public/risk?location_id=NER-SIK-GANGTOK-01")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert "public_status" in risk_data
    assert "user_zone" in risk_data

    # 5. POST /api/v1/public/acknowledge
    ack_res = await client.post(
        "/api/v1/public/acknowledge",
        json={
            "event_id": target_alert["event_id"],
            "location_id": target_alert["location_id"],
            "user_id": "TEST_CITIZEN_001"
        }
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # 6. GET /api/v1/public/safety-points
    pts_res = await client.get("/api/v1/public/safety-points")
    assert pts_res.status_code == 200
    pts = pts_res.json()
    assert len(pts) >= 3
