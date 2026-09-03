from typing import List, Tuple
from backend.app.engine.base import (
    FactorScoreDetail,
    DataQualityReport,
    SignalAgreementReport,
)
from backend.app.core.logging import logger


class ConfidenceCalculator:
    """
    Computes Signal Agreement and Multi-Factor Assessment Confidence.
    Transparently evaluates telemetry completeness, freshness, signal coherence,
    and historical baseline support.
    NOTE: Assessment confidence indicates signal certainty and data density,
    NOT the probability of disaster occurrence.
    """

    def calculate_signal_agreement(
        self,
        factors: List[FactorScoreDetail]
    ) -> SignalAgreementReport:
        """
        Evaluates coherence among independent indicator groups:
        Group A: Atmospheric/Precipitation (Intensity, Anomaly, Persistence)
        Group B: Subsurface Hydrology (Soil Moisture, Saturation Trend)
        Group C: Geomorphology & Terrain (Slope Angle, Geological Susceptibility)
        """
        # Find factor normalized scores
        score_dict = {f.name: f.normalized_score for f in factors}

        precip_scores = [
            score_dict.get("Rainfall Intensity", 0.0),
            score_dict.get("Rainfall Anomaly", 0.0),
            score_dict.get("Rainfall Persistence & Trend", 0.0),
        ]
        avg_precip = sum(precip_scores) / len(precip_scores)

        hydro_scores = [
            score_dict.get("Soil Moisture Saturation", 0.3),
            score_dict.get("Soil Saturation Rate", 0.2),
        ]
        avg_hydro = sum(hydro_scores) / len(hydro_scores)

        geo_scores = [
            score_dict.get("Terrain & Slope Angle", 0.5),
            score_dict.get("Historical Susceptibility", 0.5),
        ]
        avg_geo = sum(geo_scores) / len(geo_scores)

        # Measure deviation between atmospheric triggering and subsurface response
        precip_hydro_diff = abs(avg_precip - avg_hydro)

        # High agreement occurs when signals tell a consistent story
        # e.g., both precip & hydro are high OR both are low
        coherence = 1.0 - (precip_hydro_diff * 0.7)
        coherence = max(0.2, min(1.0, coherence))

        # Check for multi-signal agreement
        coherent_count = sum(1 for s in [avg_precip, avg_hydro, avg_geo] if s >= 0.50 or s <= 0.25)
        conflicting_count = 3 - coherent_count

        if coherence >= 0.75:
            level = "STRONG"
            details = "High multi-signal coherence between atmospheric triggers and ground pore saturation."
        elif coherence >= 0.50:
            level = "MODERATE"
            details = "Moderate agreement across meteorological and hydrological signals."
        else:
            level = "WEAK"
            details = "Divergent signals: atmospheric precipitation does not align with subsurface pore saturation."

        return SignalAgreementReport(
            agreement_score=round(coherence, 2),
            coherent_signals_count=coherent_count,
            conflicting_signals_count=conflicting_count,
            agreement_level=level,
            details=details
        )

    def calculate_confidence(
        self,
        quality: DataQualityReport,
        signal_agreement: SignalAgreementReport,
        historical_points_count: int = 24
    ) -> float:
        """
        Calculates multi-factor confidence score (0.0 to 1.0):
        - Data Completeness: 35%
        - Data Freshness: 20%
        - Signal Agreement: 30%
        - Historical Time-series Density: 15%
        """
        comp_w = 0.35 * quality.completeness_score
        fresh_w = 0.20 * quality.freshness_score
        agree_w = 0.30 * signal_agreement.agreement_score
        density_w = 0.15 * min(1.0, max(0.3, historical_points_count / 24.0))

        confidence = comp_w + fresh_w + agree_w + density_w
        # Cap confidence between 0.10 and 0.98 (never claim 100% certainty in prototype model)
        confidence = max(0.10, min(0.98, round(confidence, 2)))
        return confidence


confidence_calculator = ConfidenceCalculator()
