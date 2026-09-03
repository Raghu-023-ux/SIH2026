import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.weather import WeatherObservation
from backend.app.engine.data_validator import data_validator
from backend.app.engine.base import QualityStatus


def test_validator_valid_observation():
    now = datetime.now(timezone.utc)
    obs = WeatherObservation(
        location_id="TEST-LOC-01",
        timestamp=now,
        temperature=21.5,
        humidity=78.0,
        pressure=1011.0,
        rainfall_1h=12.0,
        rainfall_6h=35.0,
        rainfall_24h=60.0,
        soil_moisture=65.0
    )

    report, state = data_validator.validate_observation(obs, reference_time=now)
    assert report.status == QualityStatus.VALID
    assert report.completeness_score >= 0.8
    assert report.freshness_score == 1.0
    assert state.rainfall_1h == 12.0
    assert state.soil_moisture == 65.0


def test_validator_negative_and_out_of_range_values():
    now = datetime.now(timezone.utc)
    obs = WeatherObservation(
        location_id="TEST-LOC-01",
        timestamp=now,
        temperature=150.0,  # Invalid
        humidity=150.0,    # Invalid
        pressure=400.0,    # Invalid
        rainfall_1h=-5.0,  # Negative
        rainfall_24h=-10.0,
        soil_moisture=120.0 # Out of 0-100 bounds
    )

    report, state = data_validator.validate_observation(obs, reference_time=now)
    # Should sanitize negative rainfall to 0.0
    assert state.rainfall_1h == 0.0
    assert state.rainfall_24h == 0.0
    # Should clamp soil moisture to 100.0
    assert state.soil_moisture == 100.0
    assert len(report.invalid_fields) > 0


def test_validator_stale_telemetry():
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(hours=18)
    obs = WeatherObservation(
        location_id="TEST-LOC-01",
        timestamp=stale_time,
        temperature=20.0,
        rainfall_1h=0.0,
        rainfall_24h=10.0,
        soil_moisture=35.0
    )

    report, state = data_validator.validate_observation(obs, reference_time=now)
    assert report.status in (QualityStatus.STALE, QualityStatus.PARTIAL)
    assert report.freshness_score < 0.5


def test_validator_series_72h_aggregation():
    now = datetime.now(timezone.utc)
    obs_list = []
    for i in range(30):
        t = now - timedelta(hours=29 - i)
        obs = WeatherObservation(
            location_id="TEST-LOC-01",
            timestamp=t,
            temperature=22.0,
            rainfall_1h=5.0, # 5mm every hour = 150mm over 30 hours
            rainfall_24h=120.0,
            soil_moisture=70.0
        )
        obs_list.append(obs)

    states, report = data_validator.validate_series(obs_list)
    assert len(states) == 30
    assert states[-1].rainfall_72h >= 140.0
