import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import httpx

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.providers.base import WeatherDataSource
from backend.app.providers.health import provider_health_registry
from backend.app.core.config import settings
from backend.app.core.logging import logger


class OpenMeteoWeatherProvider(WeatherDataSource):
    """
    Live Weather Data Adapter for Open-Meteo free public API.
    Retrieves hourly precipitation, multi-depth soil moisture, pressure,
    temperature, humidity, and wind telemetry for geographical coordinates.
    Includes timeout handling, exponential backoff retries, and telemetry latency tracking.
    """

    def __init__(
        self,
        api_url: str = settings.OPEN_METEO_API_URL,
        timeout_seconds: float = settings.WEATHER_REQUEST_TIMEOUT_SECONDS,
        max_retries: int = settings.WEATHER_MAX_RETRIES,
        backoff_factor: float = settings.WEATHER_BACKOFF_FACTOR
    ):
        self._api_url = api_url
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._backoff = backoff_factor

    @property
    def provider_name(self) -> str:
        return "OPEN_METEO"

    @property
    def provider_version(self) -> str:
        return "open-meteo-v1"

    def validate_coordinates(self, lat: float, lon: float):
        if lat < -90.0 or lat > 90.0:
            raise ValueError(f"Invalid latitude {lat}. Must be between -90 and 90.")
        if lon < -180.0 or lon > 180.0:
            raise ValueError(f"Invalid longitude {lon}. Must be between -180 and 180.")

    async def get_observations(
        self,
        location: Location,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 24
    ) -> List[WeatherObservation]:
        """
        Queries Open-Meteo with retry and exponential backoff,
        parses hourly response, and returns chronological WeatherObservation models.
        """
        lat = location.latitude
        lon = location.longitude
        self.validate_coordinates(lat, lon)

        params: Dict[str, Any] = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "hourly": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "surface_pressure,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "precipitation,"
                "rain,"
                "soil_moisture_0_to_1cm,"
                "soil_moisture_1_to_3cm,"
                "soil_moisture_3_to_9cm,"
                "soil_moisture_9_to_27cm"
            ),
            "past_days": 2,
            "forecast_days": 1,
            "timezone": "UTC"
        }

        last_err: Optional[Exception] = None
        start_t = time.perf_counter()

        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.get(self._api_url, params=params)
                    if resp.status_code != 200:
                        raise httpx.HTTPStatusError(
                            f"Open-Meteo returned HTTP {resp.status_code}: {resp.text[:120]}",
                            request=resp.request,
                            response=resp
                        )

                    data = resp.json()
                    latency = (time.perf_counter() - start_t) * 1000.0
                    provider_health_registry.record_success("open-meteo", latency)
                    return self._parse_open_meteo_response(location.id, data, limit=limit)

            except (httpx.RequestError, httpx.HTTPStatusError, Exception) as err:
                last_err = err
                if attempt < self._max_retries:
                    delay = self._backoff * (2 ** attempt)
                    logger.warning(
                        f"Open-Meteo request attempt {attempt + 1} failed for {location.name} ({err}). Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        # Record provider failure if all retries exhausted
        err_msg = str(last_err) or "Max retries exceeded"
        provider_health_registry.record_failure("open-meteo", err_msg)
        raise RuntimeError(f"Open-Meteo weather provider failed for {location.name}: {err_msg}") from last_err

    def _parse_open_meteo_response(
        self,
        location_id: str,
        data: Dict[str, Any],
        limit: int = 24
    ) -> List[WeatherObservation]:
        """
        Transforms Open-Meteo hourly dictionary into list of WeatherObservation objects.
        """
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            return []

        temps = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        pressures = hourly.get("surface_pressure", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        wind_dirs = hourly.get("wind_direction_10m", [])
        precips = hourly.get("precipitation", [])
        rains = hourly.get("rain", [])
        sm_0_1 = hourly.get("soil_moisture_0_to_1cm", [])
        sm_1_3 = hourly.get("soil_moisture_1_to_3cm", [])
        sm_3_9 = hourly.get("soil_moisture_3_to_9cm", [])
        sm_9_27 = hourly.get("soil_moisture_9_to_27cm", [])

        observations: List[WeatherObservation] = []
        now_retrieved = datetime.now(timezone.utc)

        # Iterate over all hourly points
        for i in range(len(times)):
            time_str = times[i]
            # Parse ISO string (e.g. "2026-08-28T14:00")
            dt = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)

            # Skip points further than 1 hour into future
            if dt > now_retrieved + timedelta(hours=1):
                continue

            r1h = precips[i] if i < len(precips) and precips[i] is not None else 0.0

            # Calculate rolling 6h and 24h rainfall
            window_6h = precips[max(0, i - 5):i + 1]
            r6h = sum(p for p in window_6h if p is not None)

            window_24h = precips[max(0, i - 23):i + 1]
            r24h = sum(p for p in window_24h if p is not None)

            # Calculate composite volumetric soil moisture % (0-100%)
            # Open-Meteo gives m3/m3 (e.g. 0.35 = 35% volumetric saturation)
            sm_layers: List[float] = []
            for sm_arr in [sm_0_1, sm_1_3, sm_3_9, sm_9_27]:
                if i < len(sm_arr) and sm_arr[i] is not None:
                    sm_layers.append(float(sm_arr[i]) * 100.0)

            sm_composite = (sum(sm_layers) / len(sm_layers)) if sm_layers else None
            if sm_composite is not None:
                sm_composite = round(max(0.0, min(100.0, sm_composite)), 1)

            obs = WeatherObservation(
                location_id=location_id,
                timestamp=dt,
                temperature=round(float(temps[i]), 1) if i < len(temps) and temps[i] is not None else None,
                humidity=round(float(humidities[i]), 1) if i < len(humidities) and humidities[i] is not None else None,
                pressure=round(float(pressures[i]), 1) if i < len(pressures) and pressures[i] is not None else None,
                wind_speed=round(float(wind_speeds[i]), 1) if i < len(wind_speeds) and wind_speeds[i] is not None else None,
                wind_direction=round(float(wind_dirs[i]), 1) if i < len(wind_dirs) and wind_dirs[i] is not None else None,
                rainfall_1h=round(float(r1h), 2),
                rainfall_6h=round(float(r6h), 2),
                rainfall_24h=round(float(r24h), 2),
                soil_moisture=sm_composite,
                source="OPEN_METEO"
            )
            observations.append(obs)

        # Slice to requested limit of most recent points
        return observations[-limit:] if limit > 0 else observations


open_meteo_provider = OpenMeteoWeatherProvider()
