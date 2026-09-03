import pytest
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.services.environmental_data_service import EnvironmentalDataService
from backend.app.providers.weather.mock import MockWeatherProvider
from backend.app.providers.base import WeatherDataSource


class FailingWeatherProvider(WeatherDataSource):
    @property
    def provider_name(self) -> str:
        return "FAILING_PROVIDER"

    @property
    def provider_version(self) -> str:
        return "v1"

    async def get_observations(self, location: Location, **kwargs):
        raise RuntimeError("External network connection timeout")


@pytest.mark.asyncio
async def test_provider_fallback_to_simulation(db_session):
    loc = Location(
        id="FALLBACK-TEST-01",
        name="Fallback Test Station",
        district="East Sikkim",
        state="Sikkim",
        latitude=27.3,
        longitude=88.6,
        elevation=1600.0,
        slope_angle=35.0,
        susceptibility_score=0.75
    )
    db_session.add(loc)
    await db_session.flush()

    # Create service with intentionally failing live provider
    service = EnvironmentalDataService(
        live_weather=FailingWeatherProvider(),
        mock_weather=MockWeatherProvider(scenario="normal")
    )

    # Should gracefully catch failure and fall back to mock simulation
    obs, source, is_live = await service.collect_weather_observations(db_session, loc, force_fresh=True)
    assert len(obs) > 0
    assert source == "MOCK"
    assert is_live is False
