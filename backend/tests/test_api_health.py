import pytest


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Disaster Intelligence Engine" in data["service"]
    assert "version" in data


@pytest.mark.asyncio
async def test_list_locations_endpoint(client):
    response = await client.get("/api/v1/locations")
    assert response.status_code == 200
    locations = response.json()
    assert isinstance(locations, list)
    assert len(locations) >= 1
    assert "name" in locations[0]
    assert "state" in locations[0]
