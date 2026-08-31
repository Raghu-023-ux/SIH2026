import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.event import DisasterEvent
from backend.app.models.risk import RiskAssessment
from backend.app.models.field import FieldTeam, FieldReport
from backend.app.repositories.location_repository import location_repository
from backend.app.repositories.weather_repository import weather_repository
from backend.app.repositories.event_repository import event_repository
from backend.app.repositories.risk_repository import risk_repository
from backend.app.repositories.field_repository import field_repository


@pytest.mark.asyncio
async def test_location_repository_crud(db_session: AsyncSession):
    """Tests LocationRepository data access operations."""
    loc = Location(
        id="TEST-LOC-REPO-01",
        name="Test Location Repository Station",
        latitude=27.5,
        longitude=88.5,
        district="Test District",
        state="Sikkim",
        elevation=1200.0,
        slope_angle=30.0,
        susceptibility_score=0.7,
    )
    saved = await location_repository.save(db_session, loc)
    assert saved.id == "TEST-LOC-REPO-01"

    fetched = await location_repository.get_by_id(db_session, "TEST-LOC-REPO-01")
    assert fetched is not None
    assert fetched.name == "Test Location Repository Station"

    all_locs = await location_repository.list_all(db_session)
    assert len(all_locs) >= 1
    assert any(l.id == "TEST-LOC-REPO-01" for l in all_locs)


@pytest.mark.asyncio
async def test_weather_repository_timeseries(db_session: AsyncSession):
    """Tests WeatherRepository time-series queries."""
    obs1 = WeatherObservation(
        id="TEST-OBS-01",
        location_id="TEST-LOC-REPO-01",
        timestamp=datetime.now(timezone.utc),
        rainfall_1h=12.5,
        rainfall_24h=45.0,
        soil_moisture=72.0,
        source="unit_test",
        source_version="v1",
        freshness_status="FRESH",
    )
    await weather_repository.save(db_session, obs1)

    latest = await weather_repository.get_latest_for_location(db_session, "TEST-LOC-REPO-01")
    assert latest is not None
    assert latest.id == "TEST-OBS-01"
    assert latest.rainfall_1h == 12.5

    history = await weather_repository.get_history_for_location(db_session, "TEST-LOC-REPO-01", limit=10)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_event_repository_active_lifecycle(db_session: AsyncSession):
    """Tests EventRepository queries for active vs resolved disaster incidents."""
    event = DisasterEvent(
        id="TEST-EV-REPO-01",
        event_type="LANDSLIDE",
        location_id="TEST-LOC-REPO-01",
        status="HIGH",
        severity="HIGH",
        risk_score=72.0,
        confidence_score=0.85,
        trajectory="INCREASING",
        summary="Test active event lifecycle repository query.",
    )
    await event_repository.save(db_session, event)

    active_ev = await event_repository.get_active_for_location(db_session, "TEST-LOC-REPO-01")
    assert active_ev is not None
    assert active_ev.id == "TEST-EV-REPO-01"
    assert active_ev.status == "HIGH"

    active_list = await event_repository.list_active_events(db_session)
    assert len(active_list) >= 1
    assert any(e.id == "TEST-EV-REPO-01" for e in active_list)


@pytest.mark.asyncio
async def test_field_repository_team_lookup(db_session: AsyncSession):
    """Tests FieldRepository lookup by identifier or callsign."""
    team = FieldTeam(
        id="TEST-TEAM-01",
        team_name="Unit Test Alpha",
        callsign="TEST-ALPHA-99",
        assigned_location_id="TEST-LOC-REPO-01",
        status="DEPLOYED",
    )
    await field_repository.save(db_session, team)

    fetched_by_callsign = await field_repository.get_by_callsign_or_id(db_session, "TEST-ALPHA-99")
    assert fetched_by_callsign is not None
    assert fetched_by_callsign.id == "TEST-TEAM-01"
