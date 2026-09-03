import pytest
from datetime import datetime, timezone, timedelta
from typing import List

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import (
    RiskLevel,
    EnvironmentalState,
    TerrainProfile,
    HistoricalRiskContext,
    DataQualityReport,
    QualityStatus,
    AnomalyResult,
    TrendResult,
    TrendDirection,
)
from backend.app.engine.landslide_risk_analyzer import LandslideRiskAnalyzer
from backend.app.engine.factor_scorer import FactorScorer
from backend.app.engine.confidence_calculator import ConfidenceCalculator
from backend.app.services.scientific_indicators_service import ScientificIndicatorsService


@pytest.fixture
def gangtok_location():
    return Location(
        id="NER-SIK-GANGTOK-01",
        name="Gangtok Ridge Station",
        latitude=27.3389,
        longitude=88.6065,
        district="East Sikkim",
        state="Sikkim",
        elevation=1650.0,
        slope_angle=38.0,
        susceptibility_score=0.85,
    )


@pytest.fixture
def flat_location():
    return Location(
        id="NER-ASM-GUWAHATI-01",
        name="Guwahati Plain Station",
        latitude=26.1445,
        longitude=91.7362,
        district="Kamrup Metropolitan",
        state="Assam",
        elevation=55.0,
        slope_angle=4.0,
        susceptibility_score=0.15,
    )


def test_dry_baseline_risk(gangtok_location):
    """Test 1: Dry baseline condition produces LOW/MODERATE baseline risk."""
    analyzer = LandslideRiskAnalyzer()
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id=gangtok_location.id,
        timestamp=now,
        rainfall_1h=0.0,
        rainfall_6h=0.0,
        rainfall_24h=0.0,
        rainfall_72h=0.0,
        soil_moisture=25.0,
    )
    res = analyzer.assess_risk(location=gangtok_location, env_state=env)
    assert res.risk_level in [RiskLevel.LOW, RiskLevel.MODERATE]
    assert res.risk_score < 45.0


def test_extreme_compounding_disaster_risk(gangtok_location):
    """Test 2: Extreme multi-day rainfall + saturated soil + steep slope triggers elevated/critical risk."""
    analyzer = LandslideRiskAnalyzer()
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id=gangtok_location.id,
        timestamp=now,
        rainfall_1h=45.0,
        rainfall_6h=110.0,
        rainfall_24h=195.0,
        rainfall_72h=280.0,
        soil_moisture=92.5,
    )
    anomalies = [
        AnomalyResult(metric="rainfall_24h", value=195.0, baseline=45.0, anomaly_score=8.33, is_anomalous=True)
    ]
    trends = [
        TrendResult(metric="soil_moisture", direction=TrendDirection.INCREASING, slope=4.5)
    ]
    res = analyzer.assess_risk(
        location=gangtok_location,
        env_state=env,
        anomalies=anomalies,
        trends=trends,
        is_persistent_rain=True,
        is_increasing_rain=True
    )
    assert res.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert res.risk_score >= 60.0
    assert bool(res.reason) is True
    assert len(res.factors) >= 4



def test_high_slope_alone_does_not_trigger_critical(gangtok_location):
    """Test 3: Steep slope without dynamic triggers cannot create a CRITICAL alarm."""
    analyzer = LandslideRiskAnalyzer()
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id=gangtok_location.id,
        timestamp=now,
        rainfall_1h=0.0,
        rainfall_6h=0.0,
        rainfall_24h=0.0,
        rainfall_72h=0.0,
        soil_moisture=20.0,
    )
    res = analyzer.assess_risk(location=gangtok_location, env_state=env)
    assert res.risk_level != RiskLevel.CRITICAL
    assert res.risk_level != RiskLevel.HIGH


def test_confidence_reduction_when_soil_missing(gangtok_location):
    """Test 4: Missing soil moisture reduces confidence score transparently."""
    calc = ConfidenceCalculator()
    scorer = FactorScorer()
    now = datetime.now(timezone.utc)

    # Complete quality report
    q_complete = DataQualityReport(
        status=QualityStatus.VALID,
        completeness_score=1.0,
        freshness_score=1.0
    )
    # Degraded quality report (missing soil moisture)
    q_missing = DataQualityReport(
        status=QualityStatus.PARTIAL,
        completeness_score=0.65,
        freshness_score=0.85
    )

    env = EnvironmentalState(location_id=gangtok_location.id, timestamp=now, rainfall_1h=15.0, rainfall_24h=60.0)
    terrain = TerrainProfile(location_id=gangtok_location.id, elevation=1650.0, slope_angle=38.0, terrain_susceptibility=0.8)
    hist = HistoricalRiskContext(location_id=gangtok_location.id, historical_landslide_events=18, susceptibility_score=0.85)

    factors, _ = scorer.compute_all_factor_scores(env, terrain, hist, [], [], False, False)
    agree = calc.calculate_signal_agreement(factors)

    conf_complete = calc.calculate_confidence(q_complete, agree, 24)
    conf_missing = calc.calculate_confidence(q_missing, agree, 16)

    assert conf_missing < conf_complete
    assert conf_missing >= 0.10


def test_api_antecedent_decay_calculation(gangtok_location):
    """Test 5: Antecedent Precipitation Index (API) computes non-zero when recent rainfall occurs."""
    now = datetime.now(timezone.utc)
    observations: List[WeatherObservation] = []

    # Generate 14 hourly observations with rainfall in the recent window
    for i in range(14):
        t = now - timedelta(hours=(13 - i))
        r = 10.0 if i >= 8 else 0.0
        observations.append(
            WeatherObservation(
                location_id=gangtok_location.id,
                timestamp=t,
                rainfall_1h=r,
                rainfall_24h=60.0,
                soil_moisture=45.0,
                source="OPEN_METEO"
            )
        )

    pkg = ScientificIndicatorsService.calculate_rainfall_metrics(observations, gangtok_location)
    api_val = pkg.antecedent_wetness_index.api_value
    assert api_val > 0.0


def test_intensity_duration_threshold_comparison(gangtok_location):
    """Test 6: I-D curve comparison in rainfall metrics correctly identifies threshold breach."""
    now = datetime.now(timezone.utc)
    # Critical storm: 20mm/h for 6 hours (total 120mm)
    observations = [
        WeatherObservation(
            location_id=gangtok_location.id,
            timestamp=now - timedelta(hours=5 - i),
            rainfall_1h=20.0,
            rainfall_6h=20.0 * (i + 1),
            rainfall_24h=120.0,
            soil_moisture=80.0,
            source="OPEN_METEO"
        )
        for i in range(6)
    ]
    pkg = ScientificIndicatorsService.calculate_rainfall_metrics(observations, gangtok_location)
    id_analysis = pkg.intensity_duration
    assert id_analysis.cumulative_rainfall_mm >= 100.0
    assert id_analysis.is_above_prototype_threshold is True
    assert id_analysis.status_text == "Above prototype reference"
