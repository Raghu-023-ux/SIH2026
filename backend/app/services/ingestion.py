from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
import math
import random
from typing import List, Optional
from backend.app.models.weather import WeatherObservation
from backend.app.core.logging import logger


class DataSource(ABC):
    """Abstract Base Class for environmental & weather data sources."""

    @abstractmethod
    async def fetch(
        self,
        location_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[WeatherObservation]:
        """Fetch observations for a given location within a time range."""
        pass


class MockWeatherDataSource(DataSource):
    """
    Deterministic time-series simulator for environmental and meteorological conditions.
    Provides realistic scenarios for testing and demonstration of the Disaster Intelligence Engine.
    """

    def __init__(self, default_seed: int = 42):
        self.default_seed = default_seed

    async def fetch(
        self,
        location_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 24
    ) -> List[WeatherObservation]:
        """Fetches standard simulated baseline data for a location."""
        return self.generate_series(
            location_id=location_id,
            scenario="normal",
            num_points=min(limit, 48),
            seed=self.default_seed
        )

    def generate_series(
        self,
        location_id: str,
        scenario: str = "normal",
        num_points: int = 24,
        end_time: Optional[datetime] = None,
        seed: Optional[int] = None
    ) -> List[WeatherObservation]:
        """
        Generates deterministic time-series weather observations leading up to end_time (hourly points).
        Scenarios supported:
        - 'normal': Moderate temperature, light intermittent rain (0-5mm), low soil moisture (20-35%)
        - 'heavy_rain': Rapidly intensifying rainfall over recent hours (15-40mm/h), rising soil moisture
        - 'persistent_rain': Continuous sustained rainfall over 24-48 hours (accumulated >150mm), soil saturation >75%
        - 'abnormal_rainfall': Extreme rainfall burst (z-score > 3.0), flash precipitation
        - 'abnormal_soil_moisture': Critically saturated soil moisture (>90%) with moderate rain
        - 'landslide_risk_increasing' / 'critical': High cumulative rain + high intensity + saturated soil (>85%) + pressure drop
        - 'recovery': Rain stopped, moisture draining, pressure recovering
        """
        rng = random.Random(seed if seed is not None else self.default_seed)
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        observations: List[WeatherObservation] = []
        base_temp = 22.0
        base_pressure = 1012.0
        base_humidity = 70.0

        for i in range(num_points):
            # Hours prior to end_time: i=0 is oldest (num_points-1 hours ago), i=num_points-1 is current
            hours_ago = num_points - 1 - i
            point_time = end_time - timedelta(hours=hours_ago)
            progress = i / max(1, num_points - 1)  # 0.0 at start to 1.0 at latest

            if scenario == "normal":
                temp = base_temp + rng.uniform(-2.0, 2.0)
                humidity = min(100.0, max(40.0, base_humidity + rng.uniform(-5.0, 5.0)))
                pressure = base_pressure + rng.uniform(-1.5, 1.5)
                wind_speed = rng.uniform(5.0, 15.0)
                wind_direction = rng.uniform(0.0, 360.0)
                rain_1h = rng.uniform(0.0, 3.5) if rng.random() > 0.6 else 0.0
                rain_6h = rain_1h * 3.0 + rng.uniform(0.0, 4.0)
                rain_24h = rain_6h * 2.5 + rng.uniform(2.0, 10.0)
                soil_moisture = 28.0 + rng.uniform(-3.0, 4.0)

            elif scenario == "heavy_rain":
                # Intensifying rain over the last 12 hours
                temp = base_temp - 3.0 - (progress * 2.0)
                humidity = min(100.0, 85.0 + (progress * 12.0))
                pressure = base_pressure - (progress * 6.0) + rng.uniform(-0.5, 0.5)
                wind_speed = 18.0 + (progress * 22.0)
                wind_direction = 190.0 + rng.uniform(-15.0, 15.0)
                rain_1h = 2.0 + (progress ** 2) * 38.0 + rng.uniform(-2.0, 3.0)
                rain_6h = (rain_1h * 4.0) + (progress * 50.0)
                rain_24h = (rain_6h * 1.8) + 30.0 + (progress * 40.0)
                soil_moisture = min(98.0, 45.0 + (progress * 35.0))

            elif scenario == "persistent_rain":
                # Continuous steady heavy rain over all points
                temp = base_temp - 4.0 + rng.uniform(-1.0, 1.0)
                humidity = 95.0 + rng.uniform(-2.0, 4.0)
                pressure = base_pressure - 7.0 + rng.uniform(-1.0, 1.0)
                wind_speed = 25.0 + rng.uniform(-3.0, 5.0)
                wind_direction = 210.0 + rng.uniform(-10.0, 10.0)
                rain_1h = 18.0 + rng.uniform(-3.0, 6.0)
                rain_6h = 95.0 + rng.uniform(-5.0, 15.0)
                rain_24h = 190.0 + (progress * 45.0) + rng.uniform(-5.0, 10.0)
                soil_moisture = min(98.0, 78.0 + (progress * 15.0))

            elif scenario == "abnormal_rainfall":
                # Sudden massive burst in recent 3 hours
                is_recent = i >= (num_points - 3)
                temp = base_temp - 5.0 if is_recent else base_temp
                humidity = 98.0 if is_recent else 75.0
                pressure = base_pressure - (8.0 if is_recent else 1.0)
                wind_speed = 45.0 if is_recent else 12.0
                wind_direction = 180.0
                rain_1h = (65.0 + rng.uniform(-5.0, 10.0)) if is_recent else rng.uniform(0.0, 5.0)
                rain_6h = 120.0 if is_recent else 10.0
                rain_24h = 185.0 if is_recent else 25.0
                soil_moisture = min(99.0, 82.0 if is_recent else 40.0)

            elif scenario == "abnormal_soil_moisture":
                # Saturated soil from prior days, moderate ongoing rain
                temp = base_temp - 2.0
                humidity = 90.0 + rng.uniform(-3.0, 5.0)
                pressure = base_pressure - 4.0
                wind_speed = 15.0
                wind_direction = 200.0
                rain_1h = 12.0 + rng.uniform(-2.0, 3.0)
                rain_6h = 55.0 + rng.uniform(-3.0, 5.0)
                rain_24h = 110.0 + rng.uniform(-5.0, 10.0)
                soil_moisture = min(99.5, 92.0 + (progress * 5.0) + rng.uniform(-0.5, 0.5))

            elif scenario in ("landslide_risk_increasing", "critical"):
                # Extreme combination: cumulative > 220mm, intense 1h rain > 35mm, soil moisture > 92%, dropping pressure
                temp = base_temp - 6.0 - (progress * 3.0)
                humidity = 99.0
                pressure = base_pressure - 12.0 - (progress * 4.0)
                wind_speed = 35.0 + (progress * 20.0)
                wind_direction = 225.0
                rain_1h = 15.0 + (progress * 38.0) + rng.uniform(-2.0, 4.0)
                rain_6h = 80.0 + (progress * 85.0)
                rain_24h = 160.0 + (progress * 90.0)
                soil_moisture = min(99.9, 80.0 + (progress * 18.0))

            elif scenario == "recovery":
                # Rainfall stopped, moisture draining down from saturated
                temp = base_temp + (progress * 3.0)
                humidity = max(55.0, 85.0 - (progress * 25.0))
                pressure = base_pressure - 5.0 + (progress * 5.0)
                wind_speed = max(6.0, 20.0 - (progress * 12.0))
                wind_direction = 90.0
                rain_1h = max(0.0, 2.0 - (progress * 2.0))
                rain_6h = max(0.0, 15.0 - (progress * 12.0))
                rain_24h = max(5.0, 60.0 - (progress * 45.0))
                soil_moisture = max(35.0, 75.0 - (progress * 30.0))

            else:
                # Default to normal
                temp = base_temp
                humidity = base_humidity
                pressure = base_pressure
                wind_speed = 10.0
                wind_direction = 0.0
                rain_1h = 0.0
                rain_6h = 0.0
                rain_24h = 0.0
                soil_moisture = 30.0

            obs = WeatherObservation(
                location_id=location_id,
                timestamp=point_time,
                temperature=round(temp, 1),
                humidity=round(humidity, 1),
                pressure=round(pressure, 1),
                wind_speed=round(wind_speed, 1),
                wind_direction=round(wind_direction, 1),
                rainfall_1h=round(max(0.0, rain_1h), 2),
                rainfall_6h=round(max(0.0, rain_6h), 2),
                rainfall_24h=round(max(0.0, rain_24h), 2),
                soil_moisture=round(max(0.0, min(100.0, soil_moisture)), 1),
                source="mock_simulator"
            )
            observations.append(obs)

        return observations


mock_data_source = MockWeatherDataSource()
