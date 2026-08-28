import pytest


@pytest.mark.asyncio
async def test_engine_run_all_locations(client):
    response = await client.post("/api/v1/engine/run", json={"force_fresh_fetch": True})
    assert response.status_code == 200
    data = response.json()
    assert "locations_evaluated" in data
    assert data["locations_evaluated"] > 0
    assert "highest_risk_score" in data
    assert "assessments" in data
    assert len(data["assessments"]) > 0

    first_assessment = data["assessments"][0]
    assert "location" in first_assessment
    assert "risk_score" in first_assessment
    assert "risk_level" in first_assessment
    assert "confidence" in first_assessment
    assert "factors" in first_assessment
    assert len(first_assessment["factors"]) > 0


@pytest.mark.asyncio
async def test_engine_run_single_location(client):
    # Fetch locations to get a valid ID
    loc_res = await client.get("/api/v1/locations")
    locations = loc_res.json()
    target_id = locations[0]["id"]

    response = await client.post("/api/v1/engine/run", json={"location_id": target_id, "force_fresh_fetch": True})
    assert response.status_code == 200
    data = response.json()
    assert data["location_id"] == target_id
    assert "risk_score" in data
    assert "factors" in data
