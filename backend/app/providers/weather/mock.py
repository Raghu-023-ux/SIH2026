from datetime import datetime, timezone
from typing import List, Optional
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.providers.base import WeatherDataSource
from backend.app.providers.health import provider_health_registry
from backend.app.services.ingestion import mock_data_source


class MockWeatherProvider(WeatherDataSource):
    """
    Deterministic simulation weather provider.
    Used for simulation mode and fallback during offline or air-gapped runs.
    """

    def __init__(self, scenario: str = "normal", seed: int = 42):
        self.scenario = scenario
        self.seed = seed

    @property
    def provider_name(self) -> str:
        return "MOCK"

    @property
    def provider_version(self) -> str:
        return "mock-v2"

    async def get_observations(
        self,
        location: Location,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 24
    ) -> List[WeatherObservation]:
        obs = mock_data_source.generate_series(
            location_id=location.id,
            scenario=self.scenario,
            num_points=limit,
            end_time=end_time or datetime.now(timezone.utc),
            seed=self.seed
        )
        provider_health_registry.record_success("mock-weather", 1.0)
        return obs


mock_weather_provider = MockWeatherProvider()
