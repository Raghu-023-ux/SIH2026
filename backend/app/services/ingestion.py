from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
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
    Realistic multi-signal time-series simulator for meteorological, hydrological,
    and environmental conditions in the North Eastern Region.
    Supports 72-hour historical baseline evolution.
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
        Generates realistic multi-signal time-series observations leading up to end_time.
        Scenarios affect rainfall, soil moisture, atmospheric pressure, and humidity synchronously:
        - 'normal': Stable baseline, light rain, moisture 25-35%, pressure 1012 hPa
        - 'heavy_rain': Intensifying rain bursts (15-40mm/h), rising moisture (55-65%), falling pressure
        - 'persistent_rain': Multi-day sustained precipitation (>180mm cumulative), moisture 75-85%
        - 'landslide_risk_increasing': Multi-signal escalation (sustained rain + rising moisture >85% + pressure plunge)
        - 'critical': Extreme flash rain + 24h cumulative >220mm + critical soil saturation >92% + strong signal agreement
        - 'recovery': Rain ceased (0mm), moisture draining down, pressure recovering
        """
        rng = random.Random(seed if seed is not None else self.default_seed)
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        observations: List[WeatherObservation] = []
        base_temp = 22.0
        base_pressure = 1012.0
        base_humidity = 70.0

        for i in range(num_points):
            hours_ago = num_points - 1 - i
            point_time = end_time - timedelta(hours=hours_ago)
            progress = i / max(1, num_points - 1)  # 0.0 to 1.0

            if scenario == "normal":
                temp = base_temp + rng.uniform(-1.5, 1.5)
                humidity = min(90.0, max(45.0, base_humidity + rng.uniform(-4.0, 4.0)))
                pressure = base_pressure + rng.uniform(-1.0, 1.0)
                wind_speed = rng.uniform(6.0, 14.0)
                wind_direction = rng.uniform(0.0, 360.0)
                rain_1h = rng.uniform(0.0, 2.5) if rng.random() > 0.7 else 0.0
                rain_6h = rain_1h * 2.5 + rng.uniform(0.0, 3.0)
                rain_24h = rain_6h * 2.0 + rng.uniform(1.0, 8.0)
                soil_moisture = 28.0 + rng.uniform(-2.0, 3.0)

            elif scenario == "heavy_rain":
                # Intensifying rainfall bursts over recent 8 hours
                temp = base_temp - 2.5 - (progress * 2.0)
                humidity = min(98.0, 80.0 + (progress * 16.0))
                pressure = base_pressure - (progress * 5.5) + rng.uniform(-0.4, 0.4)
                wind_speed = 15.0 + (progress * 20.0)
                wind_direction = 195.0 + rng.uniform(-10.0, 10.0)
                rain_1h = 2.0 + (progress ** 2) * 35.0 + rng.uniform(-1.5, 2.5)
                rain_6h = (rain_1h * 3.5) + (progress * 45.0)
                rain_24h = (rain_6h * 1.6) + 25.0 + (progress * 35.0)
                soil_moisture = min(95.0, 42.0 + (progress * 28.0))

            elif scenario == "persistent_rain":
                # Continuous multi-day heavy rain
                temp = base_temp - 4.0 + rng.uniform(-0.8, 0.8)
                humidity = 96.0 + rng.uniform(-1.5, 3.0)
                pressure = base_pressure - 7.5 + rng.uniform(-0.8, 0.8)
                wind_speed = 22.0 + rng.uniform(-2.0, 4.0)
                wind_direction = 215.0
                rain_1h = 16.0 + rng.uniform(-2.0, 5.0)
                rain_6h = 90.0 + rng.uniform(-4.0, 10.0)
                rain_24h = 180.0 + (progress * 50.0) + rng.uniform(-4.0, 8.0)
                soil_moisture = min(97.0, 76.0 + (progress * 14.0))

            elif scenario == "abnormal_rainfall":
                # Sudden extreme spike
                is_recent = i >= (num_points - 3)
                temp = base_temp - 5.0 if is_recent else base_temp
                humidity = 98.0 if is_recent else 75.0
                pressure = base_pressure - (7.5 if is_recent else 1.0)
                wind_speed = 42.0 if is_recent else 10.0
                wind_direction = 180.0
                rain_1h = (60.0 + rng.uniform(-4.0, 8.0)) if is_recent else rng.uniform(0.0, 4.0)
                rain_6h = 115.0 if is_recent else 8.0
                rain_24h = 180.0 if is_recent else 20.0
                soil_moisture = min(99.0, 80.0 if is_recent else 38.0)

            elif scenario == "abnormal_soil_moisture":
                # Saturated pore water from prior storms
                temp = base_temp - 2.0
                humidity = 92.0
                pressure = base_pressure - 4.0
                wind_speed = 14.0
                wind_direction = 200.0
                rain_1h = 10.0 + rng.uniform(-2.0, 2.0)
                rain_6h = 50.0 + rng.uniform(-3.0, 4.0)
                rain_24h = 105.0 + rng.uniform(-4.0, 8.0)
                soil_moisture = min(99.5, 91.0 + (progress * 6.0) + rng.uniform(-0.5, 0.5))

            elif scenario in ("landslide_risk_increasing", "critical"):
                # Extreme compounding catastrophe: rain + saturation + pressure drop
                temp = base_temp - 6.0 - (progress * 3.0)
                humidity = 99.0
                pressure = base_pressure - 12.0 - (progress * 4.5)
                wind_speed = 32.0 + (progress * 22.0)
                wind_direction = 225.0
                rain_1h = 16.0 + (progress * 36.0) + rng.uniform(-2.0, 4.0)
                rain_6h = 85.0 + (progress * 80.0)
                rain_24h = 165.0 + (progress * 85.0)
                soil_moisture = min(99.9, 82.0 + (progress * 16.0))

            elif scenario == "recovery":
                # Rain completely ceases, moisture draining down
                temp = base_temp + (progress * 2.5)
                humidity = max(55.0, 85.0 - (progress * 26.0))
                pressure = base_pressure - 5.0 + (progress * 5.0)
                wind_speed = max(6.0, 18.0 - (progress * 10.0))
                wind_direction = 90.0
                rain_1h = max(0.0, 1.5 - (progress * 2.0))
                rain_6h = max(0.0, 10.0 - (progress * 10.0))
                rain_24h = max(4.0, 50.0 - (progress * 42.0))
                soil_moisture = max(32.0, 72.0 - (progress * 32.0))

            else:
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
                source="mock_multisignal_simulator"
            )
            observations.append(obs)

        return observations


mock_data_source = MockWeatherDataSource()
