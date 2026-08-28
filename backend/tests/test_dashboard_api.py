import pytest


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(client):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_monitored_locations" in data
    assert data["total_monitored_locations"] >= 1
    assert "active_events_count" in data
    assert "highest_risk_score" in data
    assert "data_sources_status" in data


@pytest.mark.asyncio
async def test_locations_map_endpoint(client):
    response = await client.get("/api/v1/locations/map")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    first = items[0]
    assert "latitude" in first
    assert "longitude" in first
    assert "risk_score" in first
    assert "risk_level" in first
    assert "active_event" in first


@pytest.mark.asyncio
async def test_location_investigate_endpoint(client):
    # Fetch locations
    loc_res = await client.get("/api/v1/locations")
    locations = loc_res.json()
    target_id = locations[0]["id"]

    response = await client.get(f"/api/v1/locations/{target_id}/investigate")
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert data["location"]["id"] == target_id
    assert "weather_history" in data
    assert "risk_history" in data
    assert "event_timeline" in data


@pytest.mark.asyncio
async def test_event_timeline_and_acknowledge(client):
    # First inject a critical scenario to create an event
    crit_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "critical", "seed": 42})
    assert crit_res.status_code == 200
    crit_data = crit_res.json()
    event_id = crit_data["assessment"]["event_id"]
    assert event_id is not None

    # Get event timeline
    timeline_res = await client.get(f"/api/v1/events/{event_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 2
    assert any(m["category"] == "event" for m in timeline)

    # Acknowledge event
    ack_res = await client.post(f"/api/v1/events/{event_id}/acknowledge")
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert "[ACKNOWLEDGED BY OFFICER]" in ack_data["summary"]
