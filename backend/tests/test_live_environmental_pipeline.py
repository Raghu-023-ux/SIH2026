import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.providers.weather.open_meteo import OpenMeteoWeatherProvider
from backend.app.services.environmental_data_service import EnvironmentalDataService, FreshnessStatus
from backend.app.providers.base import ProviderStatus
from backend.app.core.cache import cache


@pytest.fixture
def sample_location():
    return Location(
        id="NER-SIK-GANGTOK-01",
        name="Gangtok Ridge Station",
        latitude=27.3389,
        longitude=88.6065,
        district="East Sikkim",
        state="Sikkim",
        elevation=1650.0,
        slope_angle=38.0,
        susceptibility_score=0.85
    )


@pytest.mark.asyncio
async def test_open_meteo_coordinate_validation():
    """Tests that Open-Meteo provider strictly validates geographical coordinate boundaries."""
    provider = OpenMeteoWeatherProvider()
    
    # Valid
    provider.validate_coordinates(27.3389, 88.6065)
    
    # Invalid lat
    with pytest.raises(ValueError, match="Invalid latitude"):
        provider.validate_coordinates(95.0, 88.6065)
        
    # Invalid lon
    with pytest.raises(ValueError, match="Invalid longitude"):
        provider.validate_coordinates(27.3389, -190.0)


@pytest.mark.asyncio
async def test_open_meteo_response_parsing(sample_location):
    """Tests transformation of Open-Meteo hourly dictionary into canonical WeatherObservation objects."""
    provider = OpenMeteoWeatherProvider()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    
    raw_payload = {
        "hourly": {
            "time": ["2026-08-30T10:00", "2026-08-30T11:00", now_str],
            "temperature_2m": [21.5, 22.0, 20.8],
            "relative_humidity_2m": [82.0, 85.0, 89.0],
            "surface_pressure": [1010.5, 1009.2, 1008.1],
            "wind_speed_10m": [12.0, 14.5, 16.0],
            "wind_direction_10m": [180.0, 190.0, 210.0],
            "precipitation": [5.2, 12.4, 18.0],
            "rain": [5.2, 12.4, 18.0],
            "soil_moisture_0_to_1cm": [0.45, 0.48, 0.52],
            "soil_moisture_1_to_3cm": [0.42, 0.44, 0.48],
            "soil_moisture_3_to_9cm": [0.40, 0.41, 0.44],
            "soil_moisture_9_to_27cm": [0.38, 0.39, 0.40],
        }
    }
    
    obs_list = provider._parse_open_meteo_response(sample_location.id, raw_payload, limit=3)
    assert len(obs_list) == 3
    
    latest = obs_list[-1]
    assert latest.location_id == sample_location.id
    assert latest.rainfall_1h == 18.0
    # 24h sum should be 5.2 + 12.4 + 18.0 = 35.6
    assert latest.rainfall_24h == 35.6
    # Soil moisture composite: (52 + 48 + 44 + 40) / 4 = 46.0%
    assert latest.soil_moisture == 46.0
    assert latest.source == "OPEN_METEO"
    assert latest.observation_type in ["OBSERVED", "FORECAST"]
    assert latest.quality_score == 1.0


@pytest.mark.asyncio
async def test_data_freshness_evaluation():
    """Tests explicit data freshness boundaries (FRESH, AGING, STALE)."""
    service = EnvironmentalDataService()
    now = datetime.now(timezone.utc)
    
    # 10 minutes ago -> FRESH (<= 60 mins)
    fresh_time = now - timedelta(minutes=10)
    assert service.evaluate_freshness(fresh_time) == FreshnessStatus.FRESH

    # 100 minutes ago -> AGING (> 60 mins and <= 180 mins)
    aging_time = now - timedelta(minutes=100)
    assert service.evaluate_freshness(aging_time) == FreshnessStatus.AGING

    # 240 minutes ago -> STALE (> 180 mins)
    stale_time = now - timedelta(minutes=240)
    assert service.evaluate_freshness(stale_time) == FreshnessStatus.STALE



@pytest.mark.asyncio
async def test_elevation_lookup_caching():
    """Tests Open-Meteo elevation lookup and Redis caching behavior."""
    provider = OpenMeteoWeatherProvider()
    lat, lon = 27.3389, 88.6065
    cache_key = f"terrain:elevation:{lat:.4f}:{lon:.4f}"
    
    # Set simulated cached elevation
    await cache.set(cache_key, 1650.0, ttl_seconds=3600)
    
    elev = await provider.get_elevation(lat, lon)
    assert elev == 1650.0
