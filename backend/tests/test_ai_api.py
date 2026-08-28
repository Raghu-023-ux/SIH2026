import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_ai_api_analyze_and_audit_endpoints(client):
    # Seed location assessment via simulation scenario
    sim_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert sim_res.status_code == 200

    # 1. POST /api/v1/ai/analyze
    res = await client.post(
        "/api/v1/ai/analyze",
        json={
            "location_id": "NER-SIK-GANGTOK-01",
            "question": "What are the main risk drivers for this station?",
            "agent_type": "analyst"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "analysis" in data
    assert "evidence" in data
    assert len(data["evidence"]) > 0
    assert data["agent"] == "analyst"

    # 2. POST /api/v1/ai/explain-assessment
    exp_res = await client.post(
        "/api/v1/ai/explain-assessment",
        json={"location_id": "NER-SIK-GANGTOK-01"}
    )
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["agent"] == "explanation"

    # 3. POST /api/v1/ai/investigate-change
    inv_res = await client.post(
        "/api/v1/ai/investigate-change",
        json={"location_id": "NER-SIK-GANGTOK-01"}
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert inv_data["agent"] == "investigation"

    # 4. GET /api/v1/ai/audit-logs
    audit_res = await client.get("/api/v1/ai/audit-logs?limit=10")
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 3
    assert audit_logs[0]["status"] == "SUCCESS"
