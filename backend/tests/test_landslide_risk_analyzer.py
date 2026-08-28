from datetime import datetime, timezone
import pytest
from backend.app.engine.landslide_risk_analyzer import LandslideRiskAnalyzer
from backend.app.engine.base import RiskLevel, AnomalyResult, TrendResult, TrendDirection
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation


def test_landslide_risk_analyzer_normal_conditions():
    analyzer = LandslideRiskAnalyzer()
    now = datetime.now(timezone.utc)

    location = Location(
        id="test-loc",
        name="Test Hill",
        latitude=27.0,
        longitude=88.0,
        district="District A",
        state="Sikkim",
        elevation=1200.0,
        slope_angle=25.0,
        susceptibility_score=0.4
    )

    current = WeatherObservation(
        location_id="test-loc",
        timestamp=now,
        rainfall_1h=0.0,
        rainfall_6h=2.0,
        rainfall_24h=5.0,
        soil_moisture=25.0,
        pressure=1012.0
    )

    anomalies = [
        AnomalyResult(metric="rainfall_24h", value=5.0, baseline=5.0, anomaly_score=0.0, is_anomalous=False)
    ]
    trends = [
        TrendResult(metric="soil_moisture", direction=TrendDirection.STABLE, slope=0.0)
    ]

    output = analyzer.assess_risk(
        location=location,
        current_observation=current,
        anomalies=anomalies,
        trends=trends,
        is_persistent_rain=False,
        is_increasing_rain=False,
        historical_count=24
    )

    assert output.risk_score < 25.0
    assert output.risk_level == RiskLevel.LOW
    assert len(output.factors) == 7
    # Verify factor sum matches total risk score approximately
    sum_contributions = sum(f.contribution for f in output.factors)
    assert abs(sum_contributions - output.risk_score) < 0.5


def test_landslide_risk_analyzer_critical_conditions():
    analyzer = LandslideRiskAnalyzer()
    now = datetime.now(timezone.utc)

    location = Location(
        id="test-loc-crit",
        name="Steep Ridge",
        latitude=27.3,
        longitude=88.6,
        district="East Sikkim",
        state="Sikkim",
        elevation=1800.0,
        slope_angle=40.0,
        susceptibility_score=0.85
    )

    current = WeatherObservation(
        location_id="test-loc-crit",
        timestamp=now,
        rainfall_1h=45.0,
        rainfall_6h=110.0,
        rainfall_24h=210.0,
        soil_moisture=96.0,
        pressure=992.0
    )

    anomalies = [
        AnomalyResult(metric="rainfall_24h", value=210.0, baseline=40.0, anomaly_score=3.5, is_anomalous=True)
    ]
    trends = [
        TrendResult(metric="soil_moisture", direction=TrendDirection.INCREASING, slope=1.5)
    ]

    output = analyzer.assess_risk(
        location=location,
        current_observation=current,
        anomalies=anomalies,
        trends=trends,
        is_persistent_rain=True,
        is_increasing_rain=True,
        historical_count=24
    )

    assert output.risk_score >= 75.0
    assert output.risk_level == RiskLevel.CRITICAL
    assert "CRITICAL" in output.reason
