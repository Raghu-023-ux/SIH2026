import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_alerts_api_endpoints(client):
    # Seed event
    sim_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert sim_res.status_code == 200

    # 1. GET /api/v1/alerts/cap.xml
    cap_xml_res = await client.get("/api/v1/alerts/cap.xml")
    assert cap_xml_res.status_code == 200
    assert "application/xml" in cap_xml_res.headers["content-type"]
    assert "<alert" in cap_xml_res.text

    # 2. GET /api/v1/alerts/cap.json
    cap_json_res = await client.get("/api/v1/alerts/cap.json")
    assert cap_json_res.status_code == 200
    cap_items = cap_json_res.json()
    assert len(cap_items) >= 1
    event_id = cap_items[0]["identifier"].replace("IN-NER-CAP-", "")

    # 3. GET /api/v1/alerts/{event_id}/payloads
    payload_res = await client.get(f"/api/v1/alerts/{event_id}/payloads")
    assert payload_res.status_code == 200
    pkg = payload_res.json()
    assert "sms" in pkg
    assert "whatsapp" in pkg
    assert "email" in pkg

    # 4. POST /api/v1/alerts/broadcast
    bc_res = await client.post(
        "/api/v1/alerts/broadcast",
        json={
            "event_id": event_id,
            "location_id": "NER-ARU-ITANAGAR-01",
            "channels": ["SMS_GATEWAY", "WHATSAPP_BROADCAST", "CAP_FEED"],
            "recipient_group": "PUBLIC_AND_OFFICIALS"
        }
    )
    assert bc_res.status_code == 201
    bc_data = bc_res.json()
    assert bc_data["total_dispatched"] == 3

    # 5. GET /api/v1/alerts/broadcasts
    logs_res = await client.get("/api/v1/alerts/broadcasts")
    assert logs_res.status_code == 200
    assert len(logs_res.json()) >= 3

    # 6. GET /api/v1/alerts/sitrep/{event_id}
    sitrep_res = await client.get(f"/api/v1/alerts/sitrep/{event_id}")
    assert sitrep_res.status_code == 200
    sitrep_data = sitrep_res.json()
    assert "report_number" in sitrep_data
    assert len(sitrep_data["sections"]) >= 5
