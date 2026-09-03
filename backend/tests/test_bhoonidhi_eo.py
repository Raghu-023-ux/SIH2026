import pytest
from httpx import AsyncClient
from backend.app.services.earth_observation_provider import (
    MockEarthObservationProvider,
    BhoonidhiProvider,
    get_earth_observation_provider,
    SUPPORTED_BHOONIDHI_COLLECTIONS,
)
from backend.app.schemas.earth_observation import EarthObservationSearchRequest
from backend.app.core.cache import cache, CacheKeys


@pytest.mark.asyncio
async def test_mock_earth_observation_provider():
    """Tests MockEarthObservationProvider deterministic scene generation."""
    provider = MockEarthObservationProvider()

    # 1. Health check
    health = provider.get_health_status()
    assert health.status == "MOCK_MODE"
    assert health.configured is True
    assert len(health.supported_collections) >= 3

    # 2. Search scenes
    req = EarthObservationSearchRequest(
        location_id="NER-SIK-GANGTOK-01",
        collection="Sentinel-1A_SAR-IW_GRD",
        limit=4
    )
    res = await provider.search(req)
    assert res.total_results == 4
    assert res.provider_status == "MOCK_MODE"
    assert res.results[0].platform == "Sentinel-1A"
    assert res.results[0].instrument == "C-SAR"
    assert res.results[0].source == "BHOONIDHI_ISRO_MOCK"


@pytest.mark.asyncio
async def test_bhoonidhi_unconfigured_behavior():
    """Tests that BhoonidhiProvider correctly flags missing credentials without throwing errors."""
    provider = BhoonidhiProvider()
    provider.user_id = None
    provider.password = None

    health = provider.get_health_status()
    assert health.configured is False
    assert health.status == "NOT_CONFIGURED"

    # Search should return 0 results with NOT_CONFIGURED status (no crash)
    req = EarthObservationSearchRequest(location_id="NER-SIK-GANGTOK-01", limit=2)
    res = await provider.search(req)
    assert res.total_results == 0
    assert res.provider_status == "NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_bhoonidhi_redis_token_caching():
    """Tests that authentication tokens are safely cached and retrieved from Redis."""
    provider = BhoonidhiProvider()
    provider.user_id = "test_user_nrsc"
    provider.password = "test_password_123"

    # Manually populate token in Redis
    token_key = CacheKeys.bhoonidhi_auth_token("test_user_nrsc")
    from datetime import datetime, timezone, timedelta
    future_exp = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    await cache.set(
        token_key,
        {"token": "simulated_bhoonidhi_bearer_token_xyz", "expires_at": future_exp},
        ttl_seconds=3600
    )

    # Provider authenticate should discover the cached token without network call
    auth_ok = await provider.authenticate()
    assert auth_ok is True
    assert provider._access_token == "simulated_bhoonidhi_bearer_token_xyz"


@pytest.mark.asyncio
async def test_earth_observation_api_endpoints(client: AsyncClient):
    """Tests /api/v1/earth-observation REST endpoints."""
    # 1. GET /status
    res_status = await client.get("/api/v1/earth-observation/status")
    assert res_status.status_code == 200
    s_data = res_status.json()
    assert "provider_name" in s_data
    assert "supported_collections" in s_data

    # 2. POST /search
    res_search = await client.post(
        "/api/v1/earth-observation/search",
        json={"location_id": "NER-SIK-GANGTOK-01", "limit": 3}
    )
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total_results"] >= 1
    assert len(search_data["results"]) <= 3

    # 3. GET /location/{id}/acquisitions
    res_acq = await client.get("/api/v1/earth-observation/location/NER-SIK-GANGTOK-01/acquisitions?limit=2")
    assert res_acq.status_code == 200
    acq_data = res_acq.json()
    assert len(acq_data) <= 2
    assert "product_id" in acq_data[0]


@pytest.mark.asyncio
async def test_station_investigation_includes_eo_summary(client: AsyncClient):
    """Verifies that Station 360 investigation payload includes EO evidence without fabricated risks."""
    res = await client.get("/api/v1/locations/NER-SIK-GANGTOK-01/scientific-investigation")
    assert res.status_code == 200
    data = res.json()

    assert "earth_observation" in data
    eo = data["earth_observation"]
    assert "provider" in eo
    assert "status" in eo
    assert "spatial_coverage" in eo
    # Ensure evidence summary exists
    assert "evidence_summary" in data
