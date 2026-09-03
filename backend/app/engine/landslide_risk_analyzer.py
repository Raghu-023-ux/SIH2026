from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.engine.base import (
    RiskLevel,
    RiskTrajectory,
    FactorScoreDetail,
    AssessmentOutput,
    AnomalyResult,
    TrendResult,
    EnvironmentalState,
    TerrainProfile,
    HistoricalRiskContext,
    DataQualityReport,
    QualityStatus,
)
from backend.app.engine.data_validator import data_validator
from backend.app.engine.factor_scorer import factor_scorer
from backend.app.engine.confidence_calculator import confidence_calculator
from backend.app.engine.reason_generator import reason_generator
from backend.app.core.config import settings
from backend.app.core.logging import logger


class LandslideRiskAnalyzer:
    """
    Modular Multi-Signal Landslide Risk Analyzer.
    Combines meteorological anomalies, temporal trends, pore pressure saturation,
    topographical geometry, and historical geomorphological susceptibility into
    a normalized, explainable 0–100 risk assessment with structured reason codes.
    NOTE: Prototype analytical model for landslide early-warning demonstration.
    """

    def __init__(self):
        self.validator = data_validator
        self.factor_scorer = factor_scorer
        self.confidence_calculator = confidence_calculator
        self.reason_generator = reason_generator

    def map_score_to_risk_level(self, score: float) -> RiskLevel:
        """
        Maps normalized score (0-100) to operational risk tiers:
        0-24: LOW
        25-49: MODERATE
        50-74: HIGH
        75-100: CRITICAL
        """
        if score >= settings.THRESHOLD_CRITICAL:
            return RiskLevel.CRITICAL
        elif score >= settings.THRESHOLD_HIGH:
            return RiskLevel.HIGH
        elif score >= settings.THRESHOLD_MODERATE:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW

    def calculate_risk_trajectory(
        self,
        current_score: float,
        recent_assessments: List[RiskAssessment]
    ) -> RiskTrajectory:
        """
        Analyzes historical risk score trajectory over recent evaluations:
        INCREASING, DECREASING, STABLE, VOLATILE, UNKNOWN
        """
        if not recent_assessments:
            return RiskTrajectory.STABLE

        scores = [a.risk_score for a in recent_assessments[-5:]]
        scores.append(current_score)

        if len(scores) < 2:
            return RiskTrajectory.UNKNOWN

        deltas = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
        total_delta = scores[-1] - scores[0]

        # Check for volatility (sign reversals in consecutive deltas)
        sign_changes = sum(1 for i in range(1, len(deltas)) if (deltas[i] * deltas[i - 1]) < -4.0)
        if sign_changes >= 2:
            return RiskTrajectory.VOLATILE

        if total_delta > 4.0:
            return RiskTrajectory.INCREASING
        elif total_delta < -4.0:
            return RiskTrajectory.DECREASING
        else:
            return RiskTrajectory.STABLE

    def assess_risk(
        self,
        location: Location,
        env_state: Optional[EnvironmentalState] = None,
        current_observation: Optional[WeatherObservation] = None,
        terrain: Optional[TerrainProfile] = None,
        historical: Optional[HistoricalRiskContext] = None,
        anomalies: Optional[List[AnomalyResult]] = None,
        trends: Optional[List[TrendResult]] = None,
        is_persistent_rain: bool = False,
        is_increasing_rain: bool = False,
        recent_assessments: Optional[List[RiskAssessment]] = None,
        historical_points_count: int = 24,
        historical_count: Optional[int] = None,
    ) -> AssessmentOutput:
        """
        Executes full multi-signal assessment calculation.
        Accepts either normalized EnvironmentalState or raw WeatherObservation for backward compatibility.
        """
        anomalies = anomalies or []
        trends = trends or []
        hist_count = historical_count if historical_count is not None else historical_points_count

        # Normalize EnvironmentalState if raw observation was passed
        if env_state is None:
            if current_observation is not None:
                _, env_state = self.validator.validate_observation(current_observation)
            else:
                now = datetime.now(timezone.utc)
                env_state = EnvironmentalState(location_id=location.id, timestamp=now)

        # Build terrain profile if not passed
        if terrain is None:
            slope = location.slope_angle if location.slope_angle is not None else 30.0
            elev = location.elevation if location.elevation is not None else 1200.0
            terrain_susc = min(1.0, (slope / 45.0) * 0.7 + (elev / 2500.0) * 0.3)
            terrain = TerrainProfile(
                location_id=location.id,
                elevation=elev,
                slope_angle=slope,
                terrain_susceptibility=terrain_susc
            )

        # Build historical context if not passed
        if historical is None:
            susc = location.susceptibility_score if location.susceptibility_score is not None else 0.65
            historical = HistoricalRiskContext(
                location_id=location.id,
                historical_landslide_events=12,
                susceptibility_score=susc,
                monsoon_vulnerability_index=min(1.0, susc * 0.8 + 0.15)
            )

        # 1. Compute Factor Scores & Weighted Total Score
        factors, total_risk_score = self.factor_scorer.compute_all_factor_scores(
            env=env_state,
            terrain=terrain,
            historical=historical,
            anomalies=anomalies,
            trends=trends,
            is_persistent=is_persistent_rain,
            is_increasing=is_increasing_rain
        )

        risk_level = self.map_score_to_risk_level(total_risk_score)

        # 2. Multi-Signal Agreement & Assessment Confidence
        signal_agreement = self.confidence_calculator.calculate_signal_agreement(factors)
        confidence = self.confidence_calculator.calculate_confidence(
            quality=env_state.data_quality,
            signal_agreement=signal_agreement,
            historical_points_count=hist_count
        )

        # 3. Risk Trajectory
        trajectory = self.calculate_risk_trajectory(total_risk_score, recent_assessments or [])

        # 4. Reason Codes & Diagnostic Prose
        reason_codes, full_reason = self.reason_generator.generate_reasons(
            risk_level=risk_level,
            risk_score=total_risk_score,
            factors=factors,
            anomalies=anomalies,
            trends=trends,
            is_persistent=is_persistent_rain,
            is_increasing=is_increasing_rain,
            quality=env_state.data_quality,
            signal_agreement=signal_agreement
        )

        return AssessmentOutput(
            location_id=location.id,
            timestamp=env_state.timestamp,
            hazard_type="LANDSLIDE",
            risk_level=risk_level,
            risk_score=total_risk_score,
            confidence_score=confidence,
            trajectory=trajectory,
            reason=full_reason,
            reason_codes=reason_codes,
            factors=factors,
            anomalies=anomalies,
            trends=trends,
            data_quality=env_state.data_quality,
            signal_agreement=signal_agreement,
            is_persistent_rain=is_persistent_rain,
            is_increasing_rain=is_increasing_rain,
            engine_version=settings.ENGINE_VERSION
        )


landslide_risk_analyzer = LandslideRiskAnalyzer()
