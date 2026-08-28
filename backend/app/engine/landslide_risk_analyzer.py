from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import (
    RiskLevel,
    FactorDetail,
    AssessmentOutput,
    AnomalyResult,
    TrendResult,
    TrendDirection,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class LandslideRiskAnalyzer:
    """
    Explainable scientific/rule-based Landslide Risk Analyzer.
    Combines environmental indicators, anomaly statistics, temporal trends,
    and terrain susceptibility using weighted factors.
    NOTE: Prototype analytical model for landslide early-warning demonstration.
    """

    def __init__(
        self,
        weight_intensity: float = settings.WEIGHT_RAINFALL_INTENSITY,
        weight_anomaly: float = settings.WEIGHT_RAINFALL_ANOMALY,
        weight_persistence: float = settings.WEIGHT_RAINFALL_PERSISTENCE,
        weight_soil_moisture: float = settings.WEIGHT_SOIL_MOISTURE,
        weight_soil_trend: float = settings.WEIGHT_SOIL_MOISTURE_TREND,
        weight_slope: float = settings.WEIGHT_SLOPE_ELEVATION,
        weight_susceptibility: float = settings.WEIGHT_HISTORICAL_SUSCEPTIBILITY,
    ):
        self.w_intensity = weight_intensity
        self.w_anomaly = weight_anomaly
        self.w_persistence = weight_persistence
        self.w_soil_moisture = weight_soil_moisture
        self.w_soil_trend = weight_soil_trend
        self.w_slope = weight_slope
        self.w_susceptibility = weight_susceptibility

        # Total weights sum for normalization
        self.total_weights = (
            self.w_intensity
            + self.w_anomaly
            + self.w_persistence
            + self.w_soil_moisture
            + self.w_soil_trend
            + self.w_slope
            + self.w_susceptibility
        )

    def calculate_intensity_subscore(self, current: WeatherObservation) -> Tuple[float, str, str]:
        """Scores 0-100 based on 1h and 6h rainfall intensity."""
        r1 = current.rainfall_1h or 0.0
        r6 = current.rainfall_6h or 0.0

        # Subscore mapping based on Himalayan / NER rainfall thresholds
        # Flash rain: >40mm/h is extreme; >20mm/h is heavy; >10mm/h moderate
        score_1h = min(100.0, (r1 / 40.0) * 100.0)
        score_6h = min(100.0, (r6 / 100.0) * 100.0)
        score = max(score_1h, score_6h * 0.9)

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        desc = f"1h Rain: {r1:.1f}mm, 6h Rain: {r6:.1f}mm"
        return score, status, desc

    def calculate_anomaly_subscore(self, anomalies: List[AnomalyResult]) -> Tuple[float, str, str]:
        """Scores 0-100 based on rainfall and pressure anomalies."""
        r24_anomaly = next((a for a in anomalies if a.metric == "rainfall_24h"), None)
        score = 0.0
        desc = "No abnormal departure detected"

        if r24_anomaly:
            if r24_anomaly.anomaly_score > 0:
                # Z-score of 3.0 maps to ~90-100
                score = min(100.0, max(0.0, (r24_anomaly.anomaly_score / 3.0) * 85.0))
                if r24_anomaly.is_anomalous:
                    score = max(score, 65.0)
                desc = f"24h Rainfall z-score {r24_anomaly.anomaly_score:.2f} (value: {r24_anomaly.value}mm)"

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        return score, status, desc

    def calculate_persistence_subscore(
        self,
        current: WeatherObservation,
        is_persistent: bool,
        is_increasing: bool
    ) -> Tuple[float, str, str]:
        """Scores 0-100 based on persistent rainfall and compounding trend."""
        r24 = current.rainfall_24h or 0.0
        score = min(100.0, (r24 / 200.0) * 80.0)

        if is_persistent:
            score += 20.0
        if is_increasing:
            score += 15.0

        score = min(100.0, max(0.0, score))

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        desc = f"24h Acc: {r24:.1f}mm | Persistent: {is_persistent} | Escalating: {is_increasing}"
        return score, status, desc

    def calculate_soil_moisture_subscore(self, current: WeatherObservation) -> Tuple[float, str, str]:
        """Scores 0-100 based on soil saturation level (volumetric moisture %)."""
        sm = current.soil_moisture if current.soil_moisture is not None else 30.0

        # Critical pore water pressure threshold typically above 75-80% in NER soils
        if sm <= 30.0:
            score = 5.0
        elif sm <= 55.0:
            score = 10.0 + ((sm - 30.0) / 25.0) * 25.0  # 10 to 35
        elif sm <= 80.0:
            score = 35.0 + ((sm - 55.0) / 25.0) * 35.0  # 35 to 70
        else:
            score = 70.0 + ((sm - 80.0) / 20.0) * 30.0  # 70 to 100

        score = min(100.0, max(0.0, score))

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        desc = f"Soil moisture saturation at {sm:.1f}%"
        return score, status, desc

    def calculate_soil_trend_subscore(self, trends: List[TrendResult]) -> Tuple[float, str, str]:
        """Scores 0-100 based on rate of soil moisture increase."""
        sm_trend = next((t for t in trends if t.metric == "soil_moisture"), None)
        score = 20.0
        desc = "Stable soil saturation rate"

        if sm_trend:
            if sm_trend.direction == TrendDirection.INCREASING:
                # Slope > 1.0%/hr is fast saturation
                score = min(100.0, 50.0 + min(50.0, sm_trend.slope * 30.0))
                desc = f"Rapid soil saturation increase (slope: {sm_trend.slope:+.2f}%/step)"
            elif sm_trend.direction == TrendDirection.DECREASING:
                score = max(0.0, 15.0 + sm_trend.slope * 10.0)
                desc = f"Soil moisture draining (slope: {sm_trend.slope:+.2f}%/step)"

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        return score, status, desc

    def calculate_terrain_subscore(self, location: Location) -> Tuple[float, str, str]:
        """Scores 0-100 based on slope angle and mountain elevation."""
        slope = location.slope_angle if location.slope_angle is not None else 25.0
        elev = location.elevation if location.elevation is not None else 1000.0

        # Slopes > 35° are high risk in Himalayas/NER
        slope_score = min(100.0, (slope / 45.0) * 85.0)
        elev_score = min(100.0, (elev / 2500.0) * 50.0)

        score = (slope_score * 0.7) + (elev_score * 0.3)
        score = min(100.0, max(0.0, score))

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        desc = f"Terrain slope: {slope:.1f}°, Elevation: {elev:.0f}m"
        return score, status, desc

    def calculate_susceptibility_subscore(self, location: Location) -> Tuple[float, str, str]:
        """Scores 0-100 based on baseline geological susceptibility (0.0 to 1.0)."""
        susc = location.susceptibility_score if location.susceptibility_score is not None else 0.5
        score = min(100.0, max(0.0, susc * 100.0))

        if score >= 75.0:
            status = "critical"
        elif score >= 50.0:
            status = "high"
        elif score >= 25.0:
            status = "moderate"
        else:
            status = "low"

        desc = f"Baseline Geological Susceptibility Index: {susc:.2f}"
        return score, status, desc

    def map_score_to_risk_level(self, score: float) -> RiskLevel:
        """
        Maps normalized score 0-100 to risk level:
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

    def assess_risk(
        self,
        location: Location,
        current_observation: WeatherObservation,
        anomalies: List[AnomalyResult],
        trends: List[TrendResult],
        is_persistent_rain: bool,
        is_increasing_rain: bool,
        historical_count: int = 24
    ) -> AssessmentOutput:
        """
        Calculates explainable composite risk score, contributing factor weights,
        and builds structured assessment output.
        """
        # Calculate subscores (0-100) for each factor
        s_int, stat_int, d_int = self.calculate_intensity_subscore(current_observation)
        s_ano, stat_ano, d_ano = self.calculate_anomaly_subscore(anomalies)
        s_per, stat_per, d_per = self.calculate_persistence_subscore(current_observation, is_persistent_rain, is_increasing_rain)
        s_sm, stat_sm, d_sm = self.calculate_soil_moisture_subscore(current_observation)
        s_smt, stat_smt, d_smt = self.calculate_soil_trend_subscore(trends)
        s_ter, stat_ter, d_ter = self.calculate_terrain_subscore(location)
        s_sus, stat_sus, d_sus = self.calculate_susceptibility_subscore(location)

        # Weighted contributions to 0-100 score
        c_int = (s_int * self.w_intensity) / self.total_weights
        c_ano = (s_ano * self.w_anomaly) / self.total_weights
        c_per = (s_per * self.w_persistence) / self.total_weights
        c_sm = (s_sm * self.w_soil_moisture) / self.total_weights
        c_smt = (s_smt * self.w_soil_trend) / self.total_weights
        c_ter = (s_ter * self.w_slope) / self.total_weights
        c_sus = (s_sus * self.w_susceptibility) / self.total_weights

        total_risk_score = round(c_int + c_ano + c_per + c_sm + c_smt + c_ter + c_sus, 1)
        total_risk_score = min(100.0, max(0.0, total_risk_score))

        risk_level = self.map_score_to_risk_level(total_risk_score)

        # Factors list for transparency
        factors: List[FactorDetail] = [
            FactorDetail(
                name="Rainfall Intensity",
                contribution=c_int,
                raw_value={"rainfall_1h": current_observation.rainfall_1h, "rainfall_6h": current_observation.rainfall_6h},
                status=stat_int,
                description=d_int
            ),
            FactorDetail(
                name="Rainfall Anomaly",
                contribution=c_ano,
                raw_value=next((a.anomaly_score for a in anomalies if a.metric == "rainfall_24h"), 0.0),
                status=stat_ano,
                description=d_ano
            ),
            FactorDetail(
                name="Rainfall Persistence & Trend",
                contribution=c_per,
                raw_value={"rainfall_24h": current_observation.rainfall_24h, "persistent": is_persistent_rain, "escalating": is_increasing_rain},
                status=stat_per,
                description=d_per
            ),
            FactorDetail(
                name="Soil Moisture Saturation",
                contribution=c_sm,
                raw_value=current_observation.soil_moisture,
                status=stat_sm,
                description=d_sm
            ),
            FactorDetail(
                name="Soil Saturation Rate",
                contribution=c_smt,
                raw_value=next((t.slope for t in trends if t.metric == "soil_moisture"), 0.0),
                status=stat_smt,
                description=d_smt
            ),
            FactorDetail(
                name="Terrain & Slope Angle",
                contribution=c_ter,
                raw_value={"slope_angle": location.slope_angle, "elevation": location.elevation},
                status=stat_ter,
                description=d_ter
            ),
            FactorDetail(
                name="Geological Susceptibility",
                contribution=c_sus,
                raw_value=location.susceptibility_score,
                status=stat_sus,
                description=d_sus
            ),
        ]

        # Sort factors by contribution descending so highest impact items appear first
        factors.sort(key=lambda f: f.contribution, reverse=True)

        # Confidence calculation based on data availability
        # Baseline density: full 24 hours gives high confidence; missing points reduce confidence
        obs_density_factor = min(1.0, max(0.4, historical_count / 24.0))
        sensor_completeness = 1.0 if current_observation.soil_moisture is not None and current_observation.rainfall_24h is not None else 0.75
        confidence_score = round(obs_density_factor * sensor_completeness * 0.95, 2)

        # Generate clear reason summary
        top_factors = [f.name for f in factors if f.status in ("critical", "high")]
        if top_factors:
            reason = f"{risk_level.value} landslide risk driven primarily by elevated {', '.join(top_factors[:3])}."
        else:
            reason = f"{risk_level.value} landslide risk with baseline environmental parameters within safe ranges."

        return AssessmentOutput(
            location_id=location.id,
            timestamp=current_observation.timestamp,
            hazard_type="LANDSLIDE",
            risk_level=risk_level,
            risk_score=total_risk_score,
            confidence_score=confidence_score,
            reason=reason,
            factors=factors,
            anomalies=anomalies,
            trends=trends,
            is_persistent_rain=is_persistent_rain,
            is_increasing_rain=is_increasing_rain
        )
