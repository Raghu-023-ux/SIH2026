import pytest
from backend.app.engine.confidence_calculator import confidence_calculator
from backend.app.engine.base import (
    FactorScoreDetail,
    DataQualityReport,
    QualityStatus,
)


def test_confidence_strong_signal_agreement():
    factors = [
        FactorScoreDetail("Rainfall Intensity", None, 0.85, 0.20, 17.0, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Rainfall Anomaly", None, 0.80, 0.15, 12.0, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Rainfall Persistence & Trend", None, 0.75, 0.15, 11.25, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Soil Moisture Saturation", None, 0.88, 0.15, 13.2, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Soil Saturation Rate", None, 0.70, 0.10, 7.0, "HIGH", "INCREASE_RISK"),
        FactorScoreDetail("Terrain & Slope Angle", None, 0.70, 0.15, 10.5, "HIGH", "INCREASE_RISK"),
        FactorScoreDetail("Historical Susceptibility", None, 0.75, 0.10, 7.5, "CRITICAL", "INCREASE_RISK"),
    ]

    agreement = confidence_calculator.calculate_signal_agreement(factors)
    assert agreement.agreement_level == "STRONG"
    assert agreement.agreement_score >= 0.75

    quality = DataQualityReport(status=QualityStatus.VALID, completeness_score=1.0, freshness_score=1.0)
    conf = confidence_calculator.calculate_confidence(quality, agreement, historical_points_count=24)
    assert 0.80 <= conf <= 0.98


def test_confidence_conflicting_signals_penalty():
    # Rain is extremely high but soil moisture is dry (0.05) -> conflicting
    factors = [
        FactorScoreDetail("Rainfall Intensity", None, 0.95, 0.20, 19.0, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Rainfall Anomaly", None, 0.90, 0.15, 13.5, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Rainfall Persistence & Trend", None, 0.85, 0.15, 12.75, "CRITICAL", "INCREASE_RISK"),
        FactorScoreDetail("Soil Moisture Saturation", None, 0.05, 0.15, 0.75, "LOW", "DECREASE_RISK"),
        FactorScoreDetail("Soil Saturation Rate", None, 0.05, 0.10, 0.5, "LOW", "DECREASE_RISK"),
        FactorScoreDetail("Terrain & Slope Angle", None, 0.30, 0.15, 4.5, "LOW", "NEUTRAL"),
        FactorScoreDetail("Historical Susceptibility", None, 0.30, 0.10, 3.0, "LOW", "NEUTRAL"),
    ]

    agreement = confidence_calculator.calculate_signal_agreement(factors)
    assert agreement.agreement_level in ("MODERATE", "WEAK")
    assert agreement.agreement_score < 0.75

    quality = DataQualityReport(status=QualityStatus.PARTIAL, completeness_score=0.6, freshness_score=0.7)
    conf = confidence_calculator.calculate_confidence(quality, agreement, historical_points_count=10)
    assert conf < 0.70
