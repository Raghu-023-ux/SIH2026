import pytest
from httpx import AsyncClient
from backend.app.engine.status import engine_status_tracker
from backend.app.engine.pipeline import disaster_engine
from backend.app.services.location_service import LocationService


@pytest.mark.asyncio
async def test_engine_status_endpoint(client: AsyncClient):
    """Verify GET /api/v1/engine/status returns real engine metrics and version."""
    response = await client.get("/api/v1/engine/status")
    assert response.status_code == 200
    data = response.json()
    assert "engine_status" in data
    assert data["engine_version"] == "1.0.0"
    assert "scheduler" in data
    assert data["scheduler"]["enabled"] is True


@pytest.mark.asyncio
async def test_engine_run_telemetry_recording(client: AsyncClient):
    """Verify POST /api/v1/engine/run updates the engine status tracker upon success."""
    response = await client.post("/api/v1/engine/run", json={"force_fresh_fetch": False})
    assert response.status_code == 200
    data = response.json()
    assert data["engine_version"] == "1.0.0"
    assert data["locations_evaluated"] > 0

    # Check that tracker recorded success
    status_payload = engine_status_tracker.get_status_payload()
    assert status_payload["engine_status"] == "ONLINE"
    assert status_payload["locations_evaluated"] == data["locations_evaluated"]
    assert status_payload["last_success_at"] is not None


@pytest.mark.asyncio
async def test_engine_pipeline_evaluation_cycle(db_session):
    """Verify single cycle pipeline execution records on engine status tracker."""
    await LocationService.seed_initial_locations(db_session)
    result = await disaster_engine.run_pipeline(session=db_session, force_fresh=False)
    await db_session.commit()

    engine_status_tracker.record_success(
        locations_count=result.locations_evaluated,
        active_events=result.active_events_count,
        highest_score=result.highest_risk_score,
        highest_level=result.highest_risk_level,
        duration_ms=45.2
    )

    status_payload = engine_status_tracker.get_status_payload()
    assert status_payload["engine_status"] == "ONLINE"
    assert status_payload["locations_evaluated"] == result.locations_evaluated
    assert status_payload["total_runs_count"] >= 1
