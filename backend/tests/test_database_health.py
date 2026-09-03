import pytest
from httpx import AsyncClient
from backend.app.core.config import settings
from backend.app.core.database import check_database_health


@pytest.mark.asyncio
async def test_database_health_internal():
    """Tests the internal check_database_health() utility."""
    health = await check_database_health()
    assert health["reachable"] is True
    assert health["status"] == "healthy"
    assert "latency_ms" in health
    assert isinstance(health["latency_ms"], (int, float))
    assert health["latency_ms"] >= 0.0
    assert health["engine"] in ["sqlite", "postgresql"]
    # Verify no credentials leaked
    assert "password" not in str(health).lower()
    assert "user" not in str(health).lower()


@pytest.mark.asyncio
async def test_top_level_health_endpoint(client: AsyncClient):
    """Tests GET /health returns database connectivity, mode, and service status."""
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert data["database"]["reachable"] is True
    assert data["database"]["engine"] in ["sqlite", "postgresql"]
    assert "latency_ms" in data["database"]
    assert data["application_mode"] in ["LIVE", "SIMULATION"]
    assert "password" not in str(data).lower()


@pytest.mark.asyncio
async def test_dedicated_db_health_endpoint(client: AsyncClient):
    """Tests GET /health/db dedicated endpoint."""
    res = await client.get("/health/db")
    assert res.status_code == 200
    data = res.json()
    assert data["database_reachable"] is True
    assert data["database_engine"] in ["sqlite", "postgresql"]
    assert "database_latency_ms" in data
    assert data["application_mode"] in ["LIVE", "SIMULATION"]
    # Ensure strict security - no connection strings exposed
    assert "postgresql://" not in str(data)
    assert "sqlite://" not in str(data)
    assert "password" not in str(data).lower()


@pytest.mark.asyncio
async def test_readiness_probe_with_db(client: AsyncClient):
    """Tests GET /health/ready returns connected database status and active event counts."""
    res = await client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "READY"
    assert data["database"] == "CONNECTED"
    assert "database_latency_ms" in data
    assert data["locations_monitored"] >= 0
