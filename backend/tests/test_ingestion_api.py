import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_data_mode_toggle_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Toggle to SIMULATION
        res = await client.post("/api/v1/ingestion/mode", json={"mode": "SIMULATION"})
        assert res.status_code == 200
        assert res.json()["current_mode"] == "SIMULATION"

        # Toggle back to LIVE
        res2 = await client.post("/api/v1/ingestion/mode", json={"mode": "LIVE"})
        assert res2.status_code == 200
        assert res2.json()["current_mode"] == "LIVE"


@pytest.mark.asyncio
async def test_ingestion_status_and_data_sources_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingestion status
        res = await client.get("/api/v1/ingestion/status")
        assert res.status_code == 200
        data = res.json()
        assert "data_mode" in data
        assert "providers" in data
        assert len(data["providers"]) > 0

        # 2. System data sources health
        res_sys = await client.get("/api/v1/system/data-sources")
        assert res_sys.status_code == 200
        sys_data = res_sys.json()
        assert "providers" in sys_data
        assert sys_data["caching"]["status"] == "OPERATIONAL"
