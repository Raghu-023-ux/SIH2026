from typing import List, Tuple
from backend.app.engine.base import (
    FactorScoreDetail,
    AnomalyResult,
    TrendResult,
    TrendDirection,
    DataQualityReport,
    QualityStatus,
    SignalAgreementReport,
    AssessmentReasonCode,
    RiskLevel,
)
from backend.app.core.logging import logger


class ReasonGenerator:
    """
    Generates standardized, machine-readable reason codes and structured
    diagnostic prose explaining risk calculations without relying on an LLM.
    """

    def generate_reasons(
        self,
        risk_level: RiskLevel,
        risk_score: float,
        factors: List[FactorScoreDetail],
        anomalies: List[AnomalyResult],
        trends: List[TrendResult],
        is_persistent: bool,
        is_increasing: bool,
        quality: DataQualityReport,
        signal_agreement: SignalAgreementReport
    ) -> Tuple[List[AssessmentReasonCode], str]:
        """
        Extracts structured reason codes and builds a human-readable diagnostic explanation.
        """
        codes: List[AssessmentReasonCode] = []
        score_dict = {f.name: f.normalized_score for f in factors}

        # Check rainfall triggers
        if score_dict.get("Rainfall Intensity", 0.0) >= 0.50:
            codes.append(AssessmentReasonCode.HEAVY_RAINFALL)

        if any(a.is_anomalous for a in anomalies if a.metric == "rainfall_24h"):
            codes.append(AssessmentReasonCode.RAINFALL_ANOMALY)

        if is_persistent or score_dict.get("Rainfall Persistence & Trend", 0.0) >= 0.50:
            codes.append(AssessmentReasonCode.PERSISTENT_RAINFALL)

        # Check hydrological triggers
        if score_dict.get("Soil Moisture Saturation", 0.0) >= 0.50:
            codes.append(AssessmentReasonCode.SOIL_MOISTURE_ELEVATED)

        sm_trend = next((t for t in trends if t.metric == "soil_moisture"), None)
        if sm_trend and sm_trend.direction == TrendDirection.INCREASING:
            codes.append(AssessmentReasonCode.SOIL_MOISTURE_RISING)

        # Check geomorphology
        if score_dict.get("Terrain & Slope Angle", 0.0) >= 0.65:
            codes.append(AssessmentReasonCode.HIGH_TERRAIN_SUSCEPTIBILITY)

        if score_dict.get("Historical Susceptibility", 0.0) >= 0.65:
            codes.append(AssessmentReasonCode.HISTORICAL_SUSCEPTIBILITY)

        # Multi-signal agreement
        if signal_agreement.agreement_level == "STRONG" and risk_score >= 40.0:
            codes.append(AssessmentReasonCode.MULTI_SIGNAL_AGREEMENT)

        # Data quality flags
        if quality.status in (QualityStatus.PARTIAL, QualityStatus.STALE, QualityStatus.INVALID):
            codes.append(AssessmentReasonCode.DATA_QUALITY_LOW)

        # Baseline / Recovery
        if risk_score < 25.0:
            if sm_trend and sm_trend.direction == TrendDirection.DECREASING:
                codes.append(AssessmentReasonCode.RECOVERY_DRAINAGE)
            else:
                codes.append(AssessmentReasonCode.BASELINE_STABLE)

        # Build diagnostic explanation prose
        top_factors = [f for f in factors if f.status in ("CRITICAL", "HIGH")]
        top_factor_names = [f.name for f in top_factors]

        if risk_level == RiskLevel.CRITICAL:
            lead = f"CRITICAL landslide hazard (Score: {risk_score:.1f}/100) triggered by compounding extreme factors."
        elif risk_level == RiskLevel.HIGH:
            lead = f"HIGH landslide risk (Score: {risk_score:.1f}/100) driven by elevated environmental indicators."
        elif risk_level == RiskLevel.MODERATE:
            lead = f"MODERATE watch state (Score: {risk_score:.1f}/100) with emerging precipitation or saturation anomalies."
        else:
            lead = f"LOW baseline risk (Score: {risk_score:.1f}/100) with monitored environmental metrics within safe tolerance."

        details: List[str] = []
        if AssessmentReasonCode.HEAVY_RAINFALL in codes:
            details.append("intense precipitation bursts")
        if AssessmentReasonCode.PERSISTENT_RAINFALL in codes:
            details.append("sustained multi-day accumulation")
        if AssessmentReasonCode.RAINFALL_ANOMALY in codes:
            details.append("abnormal statistical rainfall departure")
        if AssessmentReasonCode.SOIL_MOISTURE_ELEVATED in codes:
            details.append("critical subsurface pore saturation")
        if AssessmentReasonCode.SOIL_MOISTURE_RISING in codes:
            details.append("rapid pore pressure increase")

        if details:
            body = f"Key contributing drivers include {', '.join(details)}."
        else:
            body = "No critical atmospheric or hydrological thresholds breached."

        if signal_agreement.agreement_level == "STRONG" and risk_score >= 40.0:
            body += " Multiple independent ground and atmospheric telemetry channels exhibit strong signal coherence."

        full_reason = f"{lead} {body}"
        return codes, full_reason


reason_generator = ReasonGenerator()
