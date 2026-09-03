from typing import List, Dict, Any, Tuple
from backend.app.engine.base import (
    EnvironmentalState,
    TerrainProfile,
    HistoricalRiskContext,
    AnomalyResult,
    TrendResult,
    TrendDirection,
    FactorScoreDetail,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class FactorScorer:
    """
    Normalizes diverse multi-source environmental, physical, and historical metrics
    into standardized 0.0 - 1.0 factor scores and computes exact mathematical contributions.
    """

    def __init__(self, weights: Dict[str, float] = settings.RISK_WEIGHTS):
        self.weights = weights
        # Normalize weights to ensure they sum to exactly 1.0
        total_w = sum(weights.values())
        self.normalized_weights = {k: v / total_w for k, v in weights.items()}

    def score_rainfall_intensity(self, env: EnvironmentalState) -> Tuple[float, str, str]:
        """
        Scores rainfall burst rate (0.0 to 1.0) based on 1h and 6h rates.
        In Himalayan / NER terrain, >35mm/h is extreme flash rainfall.
        """
        r1h = env.rainfall_1h
        r6h = env.rainfall_6h

        score_1h = min(1.0, r1h / 40.0)
        score_6h = min(1.0, r6h / 100.0)
        score = max(score_1h, score_6h * 0.9)
        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        desc = f"1h Rain: {r1h:.1f}mm, 6h Rain: {r6h:.1f}mm"
        return round(score, 3), status, desc

    def score_rainfall_anomaly(self, anomalies: List[AnomalyResult]) -> Tuple[float, str, str]:
        """
        Scores statistical departure (0.0 to 1.0) based on rolling z-scores.
        Z-score >= 3.0 represents 99.7th percentile abnormal departure.
        """
        r24_anomaly = next((a for a in anomalies if a.metric == "rainfall_24h"), None)
        score = 0.0
        desc = "Rainfall within baseline expectations"

        if r24_anomaly:
            z = r24_anomaly.anomaly_score
            if z > 0:
                score = min(1.0, (z / 3.2))
                if r24_anomaly.is_anomalous:
                    score = max(score, 0.65)
                desc = f"24h Precipitation z-score {z:.2f} (value: {r24_anomaly.value:.1f}mm)"

        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        return round(score, 3), status, desc

    def score_rainfall_persistence(
        self,
        env: EnvironmentalState,
        is_persistent: bool,
        is_increasing: bool
    ) -> Tuple[float, str, str]:
        """
        Scores continuous compounding rainfall and multi-day 72h accumulation (0.0 to 1.0).
        """
        r24h = env.rainfall_24h
        r72h = env.rainfall_72h

        # Multi-day saturation accumulation
        base_score = min(0.70, (r72h / 250.0) * 0.70)
        if is_persistent:
            base_score += 0.18
        if is_increasing:
            base_score += 0.12

        score = max(0.0, min(1.0, base_score))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        desc = f"72h Acc: {r72h:.1f}mm, 24h: {r24h:.1f}mm | Persistent: {is_persistent} | Escalating: {is_increasing}"
        return round(score, 3), status, desc

    def score_soil_moisture(self, env: EnvironmentalState) -> Tuple[float, str, str]:
        """
        Scores pore water pressure and volumetric saturation (0.0 to 1.0).
        Critical failure threshold typically exceeds 80% saturation.
        """
        if env.soil_moisture is None:
            return 0.30, "LOW", "Soil moisture telemetry unavailable (using baseline estimate)"

        sm = env.soil_moisture
        if sm <= 30.0:
            score = 0.05
        elif sm <= 55.0:
            score = 0.10 + ((sm - 30.0) / 25.0) * 0.25  # 0.10 to 0.35
        elif sm <= 80.0:
            score = 0.35 + ((sm - 55.0) / 25.0) * 0.35  # 0.35 to 0.70
        else:
            score = 0.70 + ((sm - 80.0) / 20.0) * 0.30  # 0.70 to 1.00

        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        desc = f"Pore volumetric saturation at {sm:.1f}%"
        return round(score, 3), status, desc

    def score_soil_moisture_trend(self, trends: List[TrendResult]) -> Tuple[float, str, str]:
        """
        Scores rate of pore water saturation increase (0.0 to 1.0).
        """
        sm_trend = next((t for t in trends if t.metric == "soil_moisture"), None)
        score = 0.20
        desc = "Stable soil saturation rate"

        if sm_trend:
            if sm_trend.direction == TrendDirection.INCREASING:
                score = min(1.0, 0.50 + min(0.50, sm_trend.slope * 0.30))
                desc = f"Rapid soil saturation increase (slope: {sm_trend.slope:+.2f}%/step)"
            elif sm_trend.direction == TrendDirection.DECREASING:
                score = max(0.0, 0.15 + sm_trend.slope * 0.10)
                desc = f"Soil moisture draining (slope: {sm_trend.slope:+.2f}%/step)"

        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        return round(score, 3), status, desc

    def score_terrain(self, terrain: TerrainProfile) -> Tuple[float, str, str]:
        """
        Scores topographic slope, elevation, and geomorphological susceptibility (0.0 to 1.0).
        """
        score = max(0.0, min(1.0, terrain.terrain_susceptibility))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        desc = f"Slope: {terrain.slope_angle:.1f}°, Elevation: {terrain.elevation:.0f}m, Aspect: {terrain.aspect}"
        return round(score, 3), status, desc

    def score_historical(self, historical: HistoricalRiskContext) -> Tuple[float, str, str]:
        """
        Scores baseline geological susceptibility and historical recurrence (0.0 to 1.0).
        """
        score = max(0.0, min(1.0, historical.monsoon_vulnerability_index))

        if score >= 0.75:
            status = "CRITICAL"
        elif score >= 0.50:
            status = "HIGH"
        elif score >= 0.25:
            status = "MODERATE"
        else:
            status = "LOW"

        desc = f"Historical baseline: {historical.historical_landslide_events} events over {historical.data_period_years}y"
        return round(score, 3), status, desc

    def compute_all_factor_scores(
        self,
        env: EnvironmentalState,
        terrain: TerrainProfile,
        historical: HistoricalRiskContext,
        anomalies: List[AnomalyResult],
        trends: List[TrendResult],
        is_persistent: bool,
        is_increasing: bool
    ) -> Tuple[List[FactorScoreDetail], float]:
        """
        Computes normalized factor scores, applies centralized weights,
        and produces structured factor breakdown.
        Returns: (factor_details_list, composite_risk_score_0_to_100)
        """
        s_int, stat_int, d_int = self.score_rainfall_intensity(env)
        s_ano, stat_ano, d_ano = self.score_rainfall_anomaly(anomalies)
        s_per, stat_per, d_per = self.score_rainfall_persistence(env, is_persistent, is_increasing)
        s_sm, stat_sm, d_sm = self.score_soil_moisture(env)
        s_smt, stat_smt, d_smt = self.score_soil_moisture_trend(trends)
        s_ter, stat_ter, d_ter = self.score_terrain(terrain)
        s_his, stat_his, d_his = self.score_historical(historical)

        factors_raw = [
            ("Rainfall Intensity", s_int, self.normalized_weights["rainfall_intensity"], {"rainfall_1h": env.rainfall_1h, "rainfall_6h": env.rainfall_6h}, stat_int, d_int),
            ("Rainfall Anomaly", s_ano, self.normalized_weights["rainfall_anomaly"], next((a.anomaly_score for a in anomalies if a.metric == "rainfall_24h"), 0.0), stat_ano, d_ano),
            ("Rainfall Persistence & Trend", s_per, self.normalized_weights["rainfall_persistence"], {"rainfall_72h": env.rainfall_72h, "persistent": is_persistent, "escalating": is_increasing}, stat_per, d_per),
            ("Soil Moisture Saturation", s_sm, self.normalized_weights["soil_moisture"], env.soil_moisture, stat_sm, d_sm),
            ("Soil Saturation Rate", s_smt, self.normalized_weights["soil_moisture_trend"], next((t.slope for t in trends if t.metric == "soil_moisture"), 0.0), stat_smt, d_smt),
            ("Terrain & Slope Angle", s_ter, self.normalized_weights["terrain"], {"slope_angle": terrain.slope_angle, "elevation": terrain.elevation, "aspect": terrain.aspect}, stat_ter, d_ter),
            ("Historical Susceptibility", s_his, self.normalized_weights["historical"], {"historical_events": historical.historical_landslide_events, "susceptibility": historical.susceptibility_score}, stat_his, d_his),
        ]

        factor_details: List[FactorScoreDetail] = []
        total_risk_score = 0.0

        for name, norm_score, weight, raw_val, status, desc in factors_raw:
            contribution = norm_score * weight * 100.0
            total_risk_score += contribution

            if norm_score >= 0.50:
                impact = "INCREASE_RISK"
            elif norm_score <= 0.20:
                impact = "DECREASE_RISK"
            else:
                impact = "NEUTRAL"

            factor_details.append(
                FactorScoreDetail(
                    name=name,
                    raw_value=raw_val,
                    normalized_score=norm_score,
                    weight=weight,
                    contribution=round(contribution, 2),
                    status=status,
                    impact_type=impact,
                    description=desc
                )
            )

        # Sort factors by contribution descending
        factor_details.sort(key=lambda f: f.contribution, reverse=True)
        total_risk_score = max(0.0, min(100.0, round(total_risk_score, 1)))

        return factor_details, total_risk_score


factor_scorer = FactorScorer()
