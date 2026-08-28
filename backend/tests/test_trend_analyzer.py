from datetime import datetime, timezone, timedelta
import pytest
from backend.app.engine.trend_analyzer import TrendAnalyzer
from backend.app.engine.base import TrendDirection
from backend.app.models.weather import WeatherObservation


def test_linear_slope_increasing():
    analyzer = TrendAnalyzer()
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    slope = analyzer.calculate_linear_slope(vals)
    assert round(slope, 1) == 10.0
    assert analyzer.classify_direction(slope) == TrendDirection.INCREASING


def test_linear_slope_decreasing():
    analyzer = TrendAnalyzer()
    vals = [50.0, 40.0, 30.0, 20.0, 10.0]
    slope = analyzer.calculate_linear_slope(vals)
    assert round(slope, 1) == -10.0
    assert analyzer.classify_direction(slope) == TrendDirection.DECREASING


def test_linear_slope_stable():
    analyzer = TrendAnalyzer()
    vals = [15.0, 15.1, 14.9, 15.0, 15.0]
    slope = analyzer.calculate_linear_slope(vals)
    assert abs(slope) < 0.1
    assert analyzer.classify_direction(slope) == TrendDirection.STABLE


def test_analyze_trends_persistent_and_increasing():
    analyzer = TrendAnalyzer()
    now = datetime.now(timezone.utc)

    # 12 hours of increasing heavy rain
    observations = [
        WeatherObservation(
            location_id="loc-1",
            timestamp=now - timedelta(hours=12 - i),
            rainfall_1h=5.0 + (i * 3.0),
            rainfall_24h=50.0 + (i * 15.0),
            soil_moisture=60.0 + (i * 2.5),
            pressure=1010.0 - (i * 1.0)
        )
        for i in range(12)
    ]

    trends, is_persistent, is_increasing = analyzer.analyze_trends(observations)

    assert is_persistent is True
    assert is_increasing is True

    r1_trend = next((t for t in trends if t.metric == "rainfall_1h"), None)
    assert r1_trend is not None
    assert r1_trend.direction == TrendDirection.INCREASING

    sm_trend = next((t for t in trends if t.metric == "soil_moisture"), None)
    assert sm_trend is not None
    assert sm_trend.direction == TrendDirection.INCREASING
