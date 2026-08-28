from datetime import datetime, timezone
import pytest
from backend.app.engine.anomaly_detector import AnomalyDetector
from backend.app.models.weather import WeatherObservation


def test_calculate_z_score_basic():
    detector = AnomalyDetector(z_threshold=2.0)
    history = [10.0, 10.0, 10.0, 10.0, 10.0]
    mean, std, z = detector.calculate_z_score(10.0, history)
    assert mean == 10.0
    assert std == 0.0
    assert z == 0.0


def test_calculate_z_score_zero_std_with_spike():
    detector = AnomalyDetector(z_threshold=2.0)
    history = [0.0, 0.0, 0.0, 0.0, 0.0]
    # Current value spikes to 50mm when baseline is all 0
    mean, std, z = detector.calculate_z_score(50.0, history, zero_std_scale=10.0)
    assert mean == 0.0
    assert std == 0.0
    assert z == 5.0  # (50 - 0) / 10.0


def test_calculate_z_score_with_variance():
    detector = AnomalyDetector(z_threshold=2.0)
    history = [10.0, 20.0, 30.0, 40.0, 50.0]  # mean=30, std=15.81
    mean, std, z = detector.calculate_z_score(70.0, history)
    assert round(mean, 1) == 30.0
    assert z > 2.0


def test_detect_anomalies_rainfall():
    detector = AnomalyDetector(z_threshold=2.0)
    now = datetime.now(timezone.utc)

    # 10 baseline observations with low rain
    history = [
        WeatherObservation(
            location_id="test-loc",
            timestamp=now,
            rainfall_24h=15.0 + i,
            rainfall_1h=1.0,
            soil_moisture=30.0,
            pressure=1012.0,
            temperature=22.0
        )
        for i in range(10)
    ]

    # Current observation has massive rainfall burst
    current = WeatherObservation(
        location_id="test-loc",
        timestamp=now,
        rainfall_24h=180.0,
        rainfall_1h=45.0,
        soil_moisture=92.0,
        pressure=998.0,
        temperature=16.0
    )

    anomalies = detector.detect_anomalies(current, history)
    assert len(anomalies) > 0

    r24 = next((a for a in anomalies if a.metric == "rainfall_24h"), None)
    assert r24 is not None
    assert r24.is_anomalous is True
    assert r24.anomaly_score > 2.0

    sm = next((a for a in anomalies if a.metric == "soil_moisture"), None)
    assert sm is not None
    assert sm.is_anomalous is True
