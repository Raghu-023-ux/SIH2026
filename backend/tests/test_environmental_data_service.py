import pytest
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.services.environmental_data_service import EnvironmentalDataService
from backend.app.providers.weather.mock import MockWeatherProvider
from backend.app.providers.terrain.mock import MockTerrainProvider
from backend.app.providers.historical.mock import MockHistoricalProvider


@pytest.mark.asyncio
async def test_unified_environmental_data_service(db_session):
    loc = Location(
        id="ENV-SVC-TEST-01",
        name="Service Test Node",
        district="Aizawl",
        state="Mizoram",
        latitude=23.7271,
        longitude=92.7176,
        elevation=1132.0,
        slope_angle=32.0,
        susceptibility_score=0.78
    )
    db_session.add(loc)
    await db_session.flush()

    service = EnvironmentalDataService(
        mock_weather=MockWeatherProvider(scenario="heavy_rain"),
        terrain_source=MockTerrainProvider(),
        historical_source=MockHistoricalProvider()
    )

    pkg = await service.collect_environmental_package(db_session, loc, force_fresh=True)
    assert pkg.location.id == loc.id
    assert len(pkg.observations) > 0
    assert len(pkg.env_states) > 0
    assert pkg.terrain.slope_angle == 32.0
    assert pkg.historical.historical_landslide_events > 0
    assert pkg.data_quality.completeness_score >= 0.8
    assert len(pkg.sources) == 3
