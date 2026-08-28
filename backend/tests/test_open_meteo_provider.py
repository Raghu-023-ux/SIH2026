import pytest
from datetime import datetime, timezone
from backend.app.providers.weather.open_meteo import OpenMeteoWeatherProvider
from backend.app.models.location import Location


def test_open_meteo_coordinate_validation():
    provider = OpenMeteoWeatherProvider()
    # Valid coordinates
    provider.validate_coordinates(27.3389, 88.6065)

    # Invalid latitude
    with pytest.raises(ValueError):
        provider.validate_coordinates(95.0, 88.0)

    # Invalid longitude
    with pytest.raises(ValueError):
        provider.validate_coordinates(25.0, 195.0)


def test_open_meteo_response_parsing():
    provider = OpenMeteoWeatherProvider()
    mock_payload = {
        "latitude": 27.3389,
        "longitude": 88.6065,
        "hourly": {
            "time": ["2026-08-28T10:00", "2026-08-28T11:00", "2026-08-28T12:00"],
            "temperature_2m": [22.4, 21.8, 20.5],
            "relative_humidity_2m": [82.0, 85.0, 89.0],
            "surface_pressure": [1011.5, 1010.8, 1009.2],
            "wind_speed_10m": [12.5, 15.0, 18.2],
            "wind_direction_10m": [190.0, 205.0, 210.0],
            "precipitation": [5.2, 12.0, 24.5],
            "rain": [5.2, 12.0, 24.5],
            "soil_moisture_0_to_1cm": [0.45, 0.52, 0.65],
            "soil_moisture_1_to_3cm": [0.42, 0.48, 0.60],
            "soil_moisture_3_to_9cm": [0.38, 0.44, 0.55],
            "soil_moisture_9_to_27cm": [0.35, 0.40, 0.50],
        }
    }

    obs = provider._parse_open_meteo_response("NER-SIK-GANGTOK-01", mock_payload, limit=3)
    assert len(obs) == 3
    assert obs[-1].rainfall_1h == 24.5
    # 24h rolling precipitation
    assert obs[-1].rainfall_24h == round(5.2 + 12.0 + 24.5, 2)
    # Soil moisture average of 4 layers scaled to percentage
    expected_sm = round(((0.65 + 0.60 + 0.55 + 0.50) / 4.0) * 100.0, 1)
    assert obs[-1].soil_moisture == expected_sm
    assert obs[-1].source == "OPEN_METEO"
