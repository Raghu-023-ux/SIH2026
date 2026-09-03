import pytest
from datetime import datetime, timezone
from backend.app.engine.factor_scorer import factor_scorer
from backend.app.engine.base import (
    EnvironmentalState,
    TerrainProfile,
    HistoricalRiskContext,
    AnomalyResult,
    TrendResult,
    TrendDirection,
)


def test_factor_scorer_normalization_bounds():
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id="TEST",
        timestamp=now,
        rainfall_1h=50.0,
        rainfall_6h=120.0,
        rainfall_24h=200.0,
        rainfall_72h=280.0,
        soil_moisture=95.0
    )

    s_int, stat_int, _ = factor_scorer.score_rainfall_intensity(env)
    assert 0.0 <= s_int <= 1.0
    assert stat_int == "CRITICAL"

    s_sm, stat_sm, _ = factor_scorer.score_soil_moisture(env)
    assert 0.0 <= s_sm <= 1.0
    assert stat_sm == "CRITICAL"


def test_factor_scorer_zero_rainfall():
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id="TEST",
        timestamp=now,
        rainfall_1h=0.0,
        rainfall_6h=0.0,
        rainfall_24h=0.0,
        rainfall_72h=0.0,
        soil_moisture=25.0
    )

    s_int, stat_int, _ = factor_scorer.score_rainfall_intensity(env)
    assert s_int == 0.0
    assert stat_int == "LOW"

    s_sm, stat_sm, _ = factor_scorer.score_soil_moisture(env)
    assert s_sm <= 0.10
    assert stat_sm == "LOW"


def test_factor_scorer_weighted_contributions_sum():
    now = datetime.now(timezone.utc)
    env = EnvironmentalState(
        location_id="TEST",
        timestamp=now,
        rainfall_1h=10.0,
        rainfall_6h=30.0,
        rainfall_24h=50.0,
        rainfall_72h=70.0,
        soil_moisture=50.0
    )
    terrain = TerrainProfile(location_id="TEST", elevation=1500.0, slope_angle=32.0, terrain_susceptibility=0.6)
    historical = HistoricalRiskContext(location_id="TEST", historical_landslide_events=10, susceptibility_score=0.7)
    anomalies = [AnomalyResult("rainfall_24h", 50.0, 20.0, 1.5, False, "test")]
    trends = [TrendResult("soil_moisture", TrendDirection.STABLE, 0.0)]

    factors, total_score = factor_scorer.compute_all_factor_scores(
        env=env,
        terrain=terrain,
        historical=historical,
        anomalies=anomalies,
        trends=trends,
        is_persistent=False,
        is_increasing=False
    )

    assert len(factors) == 7
    # Sum of factor contributions should equal total_score within rounding tolerance
    sum_contrib = sum(f.contribution for f in factors)
    assert abs(sum_contrib - total_score) < 0.5
    assert 0.0 <= total_score <= 100.0
