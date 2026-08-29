import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from backend.app.main import app
from backend.app.services.earth_observation_provider import (
    MockEarthObservationProvider,
    BhoonidhiProvider,
    get_earth_observation_provider,
)
from backend.app.schemas.earth_observation import EarthObservationSearchRequest


@pytest.mark.asyncio
async def test_mock_earth_observation_provider():
    provider = MockEarthObservationProvider()
    
    # 1. Health Status
    health = provider.get_health_status()
    assert health.status == "MOCK_MODE"
    assert health.configured is True
    assert "Sentinel-1A_SAR-IW_GRD" in health.supported_collections

    # 2. Search Catalogue
    req = EarthObservationSearchRequest(
        collection="Sentinel-1A_SAR-IW_GRD",
        location_id="NER-SIK-GANGTOK-01",
        limit=4
    )
    res = await provider.search(req)
    assert res.total_results == 4
    assert res.provider_status == "MOCK_MODE"
    assert len(res.results) == 4
    assert res.results[0].collection == "Sentinel-1A_SAR-IW_GRD"
    assert res.results[0].platform == "Sentinel-1A"
    assert res.results[0].instrument == "C-SAR"
    assert res.results[0].available_online is True

    # 3. Location Acquisitions
    acqs = await provider.get_acquisitions_for_location("NER-SIK-GANGTOK-01", limit=3)
    assert len(acqs) == 3


@pytest.mark.asyncio
async def test_bhoonidhi_provider_unconfigured_state():
    provider = BhoonidhiProvider()
    provider.user_id = None
    provider.password = None

    # When unconfigured, reports NOT_CONFIGURED without crashing
    health = provider.get_health_status()
    assert health.status == "NOT_CONFIGURED"
    assert health.configured is False
    assert "not provided" in health.note.lower()

    # Search returns empty results gracefully
    req = EarthObservationSearchRequest(collection="Sentinel-1A_SAR-IW_GRD", limit=5)
    res = await provider.search(req)
    assert res.provider_status == "NOT_CONFIGURED"
    assert res.total_results == 0
    assert len(res.results) == 0


@pytest.mark.asyncio
async def test_earth_observation_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /status
        st_res = await client.get("/api/v1/earth-observation/status")
        assert st_res.status_code == 200
        st_data = st_res.json()
        assert "provider_name" in st_data
        assert "status" in st_data
        assert "supported_collections" in st_data

        # 2. POST /search
        search_res = await client.post(
            "/api/v1/earth-observation/search",
            json={
                "collection": "CartoSat-1_PAN_CartoDEM_30m",
                "location_id": "NER-SIK-GANGTOK-01",
                "limit": 3,
            }
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["total_results"] >= 0
        assert "results" in search_data

        # 3. GET /location/{id}/acquisitions
        acq_res = await client.get("/api/v1/earth-observation/location/NER-SIK-GANGTOK-01/acquisitions?limit=2")
        assert acq_res.status_code == 200
        acq_data = acq_res.json()
        assert isinstance(acq_data, list)
        assert len(acq_data) <= 2
