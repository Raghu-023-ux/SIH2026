import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dedicated_cache_health_endpoint(client: AsyncClient):
    """Tests GET /health/redis and /health/cache dedicated endpoints."""
    for endpoint in ["/health/redis", "/health/cache"]:
        res = await client.get(endpoint)
        assert res.status_code == 200
        data = res.json()
        assert data["cache_reachable"] is True
        assert "cache_backend" in data
        assert "cache_mode" in data
        assert "cache_latency_ms" in data
        assert "application_mode" in data
        # Ensure security: No URLs or tokens leaked
        assert "upstash.io" not in str(data)
        assert "bearer" not in str(data).lower()
        assert "token" not in str(data).lower()


@pytest.mark.asyncio
async def test_ready_probe_includes_cache(client: AsyncClient):
    """Tests GET /health/ready includes both database and cache subsystem statuses."""
    res = await client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "READY"
    assert data["database"] == "CONNECTED"
    assert "cache" in data
    assert data["cache"] in ["CONNECTED", "FALLBACK_MEMORY"]
    assert "cache_backend" in data
    assert "cache_latency_ms" in data


@pytest.mark.asyncio
async def test_main_health_includes_cache(client: AsyncClient):
    """Tests GET /health top-level endpoint includes cache metrics."""
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "cache" in data
    assert data["cache"]["reachable"] is True
    assert "backend" in data["cache"]
    assert "latency_ms" in data["cache"]
