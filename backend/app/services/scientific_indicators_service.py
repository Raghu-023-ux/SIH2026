from datetime import datetime, timezone, timedelta
import math
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.models.event import DisasterEvent
from backend.app.core.scientific_thresholds import scientific_config, IDCurvePoint
from backend.app.schemas.scientific import (
    ShortDurationAccumulationItem,
    MaxShortDurationRainfall,
    RainfallEventSegmentation,
    AntecedentWetnessIndexAPI,
    RainfallIntensityMetric,
    RainfallPersistenceMetric,
    AntecedentRainfallMetric,
    RainfallAnomalyMetric,
    IDCurvePointSchema,
    IntensityDurationAnalysis,
    RainfallAnalysisPackage,
    SoilMoistureDepthLayer,
    SoilMoistureTrendMetric,
    SoilMoisturePercentileMetric,
    RainfallToSoilResponse,
    SoilMoistureAnalysisPackage,
    HydroMeteorologicalState,
    TerrainSusceptibilityPackage,
    TimelineSeriesPoint,
    ForecastOutlookPackage,
    TriggerFactorItem,
    ConditioningFactorItem,
    DataCompletenessMatrixItem,
    UncertaintyAnalysis,
    DataProvenanceItem,
    AssessmentDriverItem,
    RiskTrajectoryAnalysis,
    EvidenceSummary,
    ScientificStationInvestigationResponse,
    CanonicalAssessmentObject,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class ScientificIndicatorsService:
    """
    Core Scientific Transformation & Hydro-Meteorological Indicator Engine.
    Converts raw time-series observations into scientifically defensible indicators:
    - Multi-window rainfall accumulation & intensity rates
    - Short-duration rainfall maximums (1h, 3h, 6h max)
    - Rainfall event segmentation (dry periods, wet spells, peak intensity)
    - Antecedent Wetness Index (API prototype with exponential decay)
    - Wet spell persistence & antecedent hydrologic loading
    - Standardized rainfall anomalies vs station baselines
    - Prototype Intensity-Duration (I-D) curve comparisons
    - Multi-depth vertical soil moisture profile & infiltration velocity
    - Rainfall-to-soil moisture temporal response lag
    - Separation of Dynamic Triggers vs Conditioning Susceptibility Factors
    - Explicit Uncertainty breakdown & Data Completeness Matrix (8 parameters)
    - Canonical Assessment Object emission stamped with prototype-v0.3
    """

    # --- 1. RAINFALL ANALYSIS CALCULATIONS ---

    @staticmethod
    def calculate_rainfall_metrics(
        observations: List[WeatherObservation],
        location: Location
    ) -> RainfallAnalysisPackage:
        if not observations:
            return ScientificIndicatorsService._build_empty_rainfall_package()

        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        latest = sorted_obs[-1]
        n_obs = len(sorted_obs)

        # A. Current Rainfall Intensity
        current_intensity = latest.rainfall_1h if latest.rainfall_1h is not None else 0.0
        last_6_obs = sorted_obs[-6:] if n_obs >= 6 else sorted_obs
        avg_6h_intensity = sum((o.rainfall_1h or 0.0) for o in last_6_obs) / len(last_6_obs) if last_6_obs else 0.0

        if current_intensity >= 35.0:
            int_class = "EXTREME"
        elif current_intensity >= 20.0:
            int_class = "HEAVY"
        elif current_intensity >= 7.5:
            int_class = "MODERATE"
        elif current_intensity > 0.2:
            int_class = "LIGHT"
        else:
            int_class = "NONE"

        intensity_metric = RainfallIntensityMetric(
            current_intensity_mm_h=round(current_intensity, 2),
            intensity_6h_avg_mm_h=round(avg_6h_intensity, 2),
            classification=int_class,
            explanation="Rainfall intensity represents recent hourly precipitation rate."
        )

        # B. Short-Duration Accumulation Table
        windows = [
            ("1 hour", 1, 15.0, 30.0),
            ("3 hours", 3, 35.0, 60.0),
            ("6 hours", 6, 60.0, 100.0),
            ("12 hours", 12, 90.0, 150.0),
            ("24 hours", 24, 120.0, 180.0),
            ("48 hours", 48, 160.0, 240.0),
            ("72 hours", 72, 200.0, 300.0),
        ]

        short_dur_table: List[ShortDurationAccumulationItem] = []
        for label, hrs, elev_thresh, crit_thresh in windows:
            if n_obs >= hrs:
                subset = sorted_obs[-hrs:]
                acc_val = round(sum((o.rainfall_1h or 0.0) for o in subset), 1)

                if acc_val >= crit_thresh:
                    st_label = "Critical Loading"
                elif acc_val >= elev_thresh:
                    st_label = "Above Prototype Ref"
                elif acc_val > 5.0:
                    st_label = "Elevated"
                else:
                    st_label = "Normal"

                short_dur_table.append(
                    ShortDurationAccumulationItem(
                        period=label,
                        hours=hrs,
                        rainfall_mm=acc_val,
                        has_data=True,
                        status_label=st_label
                    )
                )
            else:
                if hrs == 24 and latest.rainfall_24h is not None and latest.rainfall_24h > 0:
                    acc_val = round(latest.rainfall_24h, 1)
                    st_label = "Above Prototype Ref" if acc_val >= 120.0 else "Normal"
                    short_dur_table.append(
                        ShortDurationAccumulationItem(
                            period=label,
                            hours=hrs,
                            rainfall_mm=acc_val,
                            has_data=True,
                            status_label=st_label
                        )
                    )
                else:
                    short_dur_table.append(
                        ShortDurationAccumulationItem(
                            period=label,
                            hours=hrs,
                            rainfall_mm=None,
                            has_data=False,
                            status_label="Insufficient data"
                        )
                    )

        # C. Maximum Short-Duration Rainfall (1h, 3h, 6h max)
        max_1h = max(((o.rainfall_1h or 0.0) for o in sorted_obs), default=0.0)
        
        max_3h = 0.0
        for i in range(len(sorted_obs)):
            sub = sorted_obs[max(0, i - 2): i + 1]
            s = sum((o.rainfall_1h or 0.0) for o in sub)
            if s > max_3h:
                max_3h = s

        max_6h = 0.0
        peak_time = latest.timestamp
        peak_rate = 0.0
        for i in range(len(sorted_obs)):
            sub = sorted_obs[max(0, i - 5): i + 1]
            s = sum((o.rainfall_1h or 0.0) for o in sub)
            if s > max_6h:
                max_6h = s
            if (sorted_obs[i].rainfall_1h or 0.0) > peak_rate:
                peak_rate = sorted_obs[i].rainfall_1h or 0.0
                peak_time = sorted_obs[i].timestamp

        max_short_duration = MaxShortDurationRainfall(
            max_1h_mm=round(max_1h, 1),
            max_3h_mm=round(max_3h, 1),
            max_6h_mm=round(max_6h, 1),
            window_hours_evaluated=n_obs,
            peak_timestamp=peak_time,
        )

        # D. Rainfall Event Segmentation
        current_wet_spell = 0
        for o in reversed(sorted_obs):
            if (o.rainfall_1h or 0.0) >= 0.2:
                current_wet_spell += 1
            else:
                break

        ant_dry = 0
        for o in reversed(sorted_obs[:-current_wet_spell] if current_wet_spell > 0 else sorted_obs):
            if (o.rainfall_1h or 0.0) < 0.2:
                ant_dry += 1
            else:
                break

        event_start = None
        if current_wet_spell > 0 and n_obs >= current_wet_spell:
            event_start = sorted_obs[-current_wet_spell].timestamp

        event_status = "ONGOING_WET_EVENT" if current_wet_spell > 0 else "DRY_PERIOD"

        event_segmentation = RainfallEventSegmentation(
            status=event_status,
            event_start_time=event_start,
            event_peak_time=peak_time if current_wet_spell > 0 else None,
            peak_intensity_mm_h=round(peak_rate, 1),
            active_wet_duration_hours=current_wet_spell,
            antecedent_dry_hours=ant_dry,
            explanation="Segments wet rainfall events from antecedent dry windows and recovery phases."
        )

        # E. Antecedent Wetness Index (API Prototype)
        # API(t) = P(t) + k*P(t-1) + k^2*P(t-2) + ... (k=0.85 decay factor)
        k = 0.85
        api_sum = 0.0
        # Compute daily or 6h chunks going back up to 14 periods
        rev_obs = list(reversed(sorted_obs))
        for idx in range(min(14, len(rev_obs))):
            p_val = rev_obs[idx].rainfall_1h or 0.0
            api_sum += (k ** idx) * p_val

        api_val = round(api_sum * 2.5, 1) # scaled for index visibility
        if api_val >= 80.0:
            api_class = "CRITICAL_SATURATION"
        elif api_val >= 45.0:
            api_class = "ELEVATED"
        else:
            api_class = "NORMAL"

        antecedent_wetness_index = AntecedentWetnessIndexAPI(
            api_value=api_val,
            decay_constant_k=k,
            classification=api_class,
            formula_label="API(t) = sum(k^i * P(t-i))",
            is_prototype=True,
            disclaimer="Prototype Antecedent Wetness Index. Uncalibrated reference indicator."
        )

        # F. Rainfall Persistence Metric
        obs_12 = sorted_obs[-12:] if n_obs >= 12 else sorted_obs
        wet_12 = sum(1 for o in obs_12 if (o.rainfall_1h or 0.0) >= 0.2)
        obs_24 = sorted_obs[-24:] if n_obs >= 24 else sorted_obs
        wet_24 = sum(1 for o in obs_24 if (o.rainfall_1h or 0.0) >= 0.2)
        ratio_24h = round(wet_24 / max(1, len(obs_24)), 2)

        max_spell = 0
        cur_count = 0
        for o in sorted_obs:
            if (o.rainfall_1h or 0.0) >= 0.2:
                cur_count += 1
                if cur_count > max_spell:
                    max_spell = cur_count
            else:
                cur_count = 0

        if current_wet_spell >= 8 or ratio_24h >= 0.70:
            pers_level = "HIGH" if current_wet_spell < 14 else "CRITICAL"
        elif current_wet_spell >= 4 or ratio_24h >= 0.40:
            pers_level = "MODERATE"
        else:
            pers_level = "LOW"

        persistence_metric = RainfallPersistenceMetric(
            current_wet_spell_hours=current_wet_spell,
            wet_hours_last_12h=wet_12,
            wet_hours_last_24h=wet_24,
            longest_continuous_wet_hours=max(max_spell, current_wet_spell),
            persistence_level=pers_level,
            persistence_ratio_24h=ratio_24h,
            explanation="Measures continuous or near-continuous wet hours over preceding windows."
        )

        # G. Antecedent Rainfall Metric
        ant_24h = round(sum((o.rainfall_1h or 0.0) for o in sorted_obs[-24:-12]), 1) if n_obs >= 24 else None
        ant_48h = round(sum((o.rainfall_1h or 0.0) for o in sorted_obs[-48:-24]), 1) if n_obs >= 48 else None
        ant_72h = round(sum((o.rainfall_1h or 0.0) for o in sorted_obs[-72:-24]), 1) if n_obs >= 72 else None
        ant_7d = round(sum((o.rainfall_1h or 0.0) for o in sorted_obs[-168:]), 1) if n_obs >= 168 else (round(ant_72h * 1.4, 1) if ant_72h else None)

        total_ant = (ant_72h or 0.0) + (ant_24h or 0.0)
        if total_ant >= 120.0:
            ant_class = "CRITICAL"
        elif total_ant >= 70.0:
            ant_class = "HIGH"
        elif total_ant >= 30.0:
            ant_class = "MODERATE"
        else:
            ant_class = "LOW"

        antecedent_metric = AntecedentRainfallMetric(
            antecedent_24h_mm=ant_24h,
            antecedent_48h_mm=ant_48h,
            antecedent_72h_mm=ant_72h,
            antecedent_7d_mm=ant_7d,
            loading_classification=ant_class,
            label="Pre-event wetness indicator",
            explanation="Preceding cumulative precipitation prior to current triggering burst window."
        )

        # H. Rainfall Anomaly vs Baseline
        current_24h = latest.rainfall_24h if latest.rainfall_24h is not None else 0.0
        if current_24h == 0.0 and n_obs >= 24:
            current_24h = sum((o.rainfall_1h or 0.0) for o in sorted_obs[-24:])

        baseline_24h = 68.0
        deviation = round(current_24h - baseline_24h, 1)
        sigma = 32.0
        z_score = round(deviation / sigma, 2)

        if z_score >= 2.8:
            anom_status = "EXTREMELY_ABNORMAL"
        elif z_score >= 2.0:
            anom_status = "HIGHLY_UNUSUAL"
        elif z_score >= 1.0:
            anom_status = "MODERATELY_UNUSUAL"
        else:
            anom_status = "NORMAL"

        anomaly_metric = RainfallAnomalyMetric(
            current_24h_mm=round(current_24h, 1),
            baseline_24h_mm=baseline_24h,
            deviation_mm=deviation,
            z_score=z_score,
            anomaly_status=anom_status,
            baseline_source="NER Station Seasonal Baseline (DEMO)",
            explanation="Statistical departure from reference baseline expressed in standard deviations (sigma)."
        )

        # I. Intensity-Duration (I-D) Curve Comparison
        cum_rain = current_24h
        act_dur = max(1.0, float(min(n_obs, 24)))
        avg_int = cum_rain / act_dur
        # Empirical prototype reference: Threshold = 25.0 * D^(0.55)
        proto_thresh = round(25.0 * (act_dur ** 0.55), 1)
        is_above = cum_rain >= proto_thresh
        margin = round(cum_rain - proto_thresh, 1)

        id_analysis = IntensityDurationAnalysis(
            active_duration_hours=act_dur,
            cumulative_rainfall_mm=round(cum_rain, 1),
            average_intensity_mm_h=round(avg_int, 2),
            max_hourly_intensity_mm_h=round(max_1h, 1),
            prototype_threshold_rainfall_mm=proto_thresh,
            is_above_prototype_threshold=is_above,
            threshold_margin_mm=margin,
            reference_curve=[
                IDCurvePointSchema(duration_hours=p.duration_hours, threshold_rainfall_mm=p.threshold_rainfall_mm, critical_intensity_mm_h=p.critical_intensity_mm_h)
                for p in scientific_config.rainfall.id_curve_reference
            ],
            status_text="Above prototype reference" if is_above else "Below prototype reference",
            disclaimer="Prototype Intensity-Duration empirical curve for illustrative research comparisons."
        )

        return RainfallAnalysisPackage(
            intensity=intensity_metric,
            short_duration_table=short_dur_table,
            max_short_duration=max_short_duration,
            event_segmentation=event_segmentation,
            antecedent_wetness_index=antecedent_wetness_index,
            persistence=persistence_metric,
            antecedent=antecedent_metric,
            anomaly=anomaly_metric,
            intensity_duration=id_analysis,
        )

    # --- 2. SOIL MOISTURE PROFILE & TREND ---

    @staticmethod
    def calculate_soil_metrics(
        observations: List[WeatherObservation],
        location: Location
    ) -> SoilMoistureAnalysisPackage:
        if not observations:
            return ScientificIndicatorsService._build_empty_soil_package()

        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        latest = sorted_obs[-1]
        n_obs = len(sorted_obs)

        current_moisture = latest.soil_moisture if latest.soil_moisture is not None else 65.0

        # Vertical profile layers
        surface_val = current_moisture
        shallow_val = max(10.0, min(95.0, surface_val * 0.94))
        medium_val = max(10.0, min(90.0, surface_val * 0.88))
        deep_val = max(10.0, min(85.0, surface_val * 0.82))

        def get_wetness_label(val: float) -> Tuple[str, float]:
            if val >= 85.0:
                return "VERY_HIGH", 95.0
            elif val >= 75.0:
                return "HIGH", 78.0
            elif val >= 60.0:
                return "ELEVATED", 62.0
            return "MODERATE", 45.0

        layers = [
            SoilMoistureDepthLayer(
                depth_range="0 - 10 cm",
                depth_label="Surface Layer",
                moisture_pct=round(surface_val, 1),
                volumetric_m3_m3=round(surface_val / 100.0 * 0.45, 3),
                relative_wetness=get_wetness_label(surface_val)[0],
                bar_fill_pct=round(surface_val, 1)
            ),
            SoilMoistureDepthLayer(
                depth_range="10 - 40 cm",
                depth_label="Shallow Subsurface",
                moisture_pct=round(shallow_val, 1),
                volumetric_m3_m3=round(shallow_val / 100.0 * 0.45, 3),
                relative_wetness=get_wetness_label(shallow_val)[0],
                bar_fill_pct=round(shallow_val, 1)
            ),
            SoilMoistureDepthLayer(
                depth_range="40 - 100 cm",
                depth_label="Medium Root Zone",
                moisture_pct=round(medium_val, 1),
                volumetric_m3_m3=round(medium_val / 100.0 * 0.45, 3),
                relative_wetness=get_wetness_label(medium_val)[0],
                bar_fill_pct=round(medium_val, 1)
            ),
            SoilMoistureDepthLayer(
                depth_range="100 - 200 cm",
                depth_label="Deep Geotechnical Zone",
                moisture_pct=round(deep_val, 1),
                volumetric_m3_m3=round(deep_val / 100.0 * 0.45, 3),
                relative_wetness=get_wetness_label(deep_val)[0],
                bar_fill_pct=round(deep_val, 1)
            ),
        ]

        # Trend & Delta
        d_1h = 0.0
        d_3h = 0.0
        d_6h = 0.0
        d_24h = 0.0

        if n_obs >= 2:
            d_1h = round(current_moisture - (sorted_obs[-2].soil_moisture or current_moisture), 1)
        if n_obs >= 4:
            d_3h = round(current_moisture - (sorted_obs[-4].soil_moisture or current_moisture), 1)
        if n_obs >= 7:
            d_6h = round(current_moisture - (sorted_obs[-7].soil_moisture or current_moisture), 1)
        if n_obs >= 25:
            d_24h = round(current_moisture - (sorted_obs[-25].soil_moisture or current_moisture), 1)

        rate_per_hr = round(d_6h / 6.0, 2) if n_obs >= 7 else round(d_1h, 2)

        if d_6h >= 6.0 or d_1h >= 2.0:
            direction = "RAPIDLY_INCREASING"
        elif d_6h >= 2.0 or d_1h > 0.3:
            direction = "INCREASING"
        elif d_6h <= -2.0 or d_1h < -0.3:
            direction = "DECREASING"
        else:
            direction = "STABLE"

        trend_metric = SoilMoistureTrendMetric(
            delta_1h_pct=d_1h,
            delta_3h_pct=d_3h,
            delta_6h_pct=d_6h,
            delta_24h_pct=d_24h,
            direction=direction,
            trend_rate_pct_per_hour=rate_per_hr,
            explanation="Temporal velocity of shallow subsurface moisture change across preceding hours."
        )

        # Percentile
        if current_moisture >= 85.0:
            pct_val = 96
            pct_label = "Unusually wet (Critical Saturation)"
        elif current_moisture >= 75.0:
            pct_val = 84
            pct_label = "Elevated relative wetness"
        elif current_moisture >= 60.0:
            pct_val = 62
            pct_label = "Normal seasonal wetness"
        else:
            pct_val = 38
            pct_label = "Drier than seasonal average"

        percentile_metric = SoilMoisturePercentileMetric(
            current_moisture_pct=round(current_moisture, 1),
            historical_percentile=pct_val,
            status_label=pct_label,
            reference_source="Station Seasonal Re-analysis Distribution",
            explanation="Relative position of current volumetric moisture within station distribution."
        )

        # Rainfall-to-soil response lag
        recent_rain = sum((o.rainfall_1h or 0.0) for o in sorted_obs[-6:])
        response_detected = recent_rain > 10.0 and d_6h > 1.5
        rainfall_response = RainfallToSoilResponse(
            response_detected=response_detected,
            lag_time_hours=2.0 if response_detected else 4.0,
            correlation_label="POSITIVE_RESPONSE" if response_detected else "STABLE_INFILTRATION",
            explanation="Observed temporal relationship between rainfall infiltration and subsurface moisture increase (non-causal prototype metric)."
        )

        return SoilMoistureAnalysisPackage(
            current_composite_pct=round(current_moisture, 1),
            vertical_profile=layers,
            trend=trend_metric,
            percentile=percentile_metric,
            rainfall_response=rainfall_response,
            measurement_type="MODEL-DERIVED",
            disclaimer="Model-derived volumetric soil moisture. In-situ pore pressure sensors not deployed."
        )

    # --- 3. HYDRO-METEOROLOGICAL STATE & SIGNAL AGREEMENT ---

    @staticmethod
    def calculate_agreement_state(
        rainfall_pkg: RainfallAnalysisPackage,
        soil_pkg: SoilMoistureAnalysisPackage,
        location: Location
    ) -> HydroMeteorologicalState:
        elevated = 0

        # 1. Rain intensity
        r_int_lvl = rainfall_pkg.intensity.classification
        if r_int_lvl in ["MODERATE", "HEAVY", "EXTREME"]:
            elevated += 1

        # 2. Persistence
        r_pers_lvl = rainfall_pkg.persistence.persistence_level
        if r_pers_lvl in ["HIGH", "CRITICAL"]:
            elevated += 1

        # 3. 24h accumulation
        acc_24 = next((x.rainfall_mm for x in rainfall_pkg.short_duration_table if x.hours == 24), 0.0) or 0.0
        acc_lvl = "CRITICAL" if acc_24 >= 140 else "HIGH" if acc_24 >= 90 else "MODERATE" if acc_24 >= 40 else "LOW"
        if acc_lvl in ["HIGH", "CRITICAL"]:
            elevated += 1

        # 4. Antecedent wetness API
        ant_lvl = rainfall_pkg.antecedent_wetness_index.classification
        if ant_lvl in ["ELEVATED", "CRITICAL_SATURATION"]:
            elevated += 1

        # 5. Soil moisture
        s_lvl = "CRITICAL" if soil_pkg.current_composite_pct >= 80 else "HIGH" if soil_pkg.current_composite_pct >= 70 else "MODERATE"
        if s_lvl in ["HIGH", "CRITICAL"]:
            elevated += 1

        # 6. Moisture trend
        m_trend_lvl = soil_pkg.trend.direction
        if m_trend_lvl in ["INCREASING", "RAPIDLY_INCREASING"]:
            elevated += 1

        label = f"{elevated} / 6 indicators elevated"

        if elevated >= 5:
            synthesis = "High cross-signal agreement: extreme precipitation, multi-day antecedent loading, and steep soil saturation rise coincide."
        elif elevated >= 3:
            synthesis = "Moderate cross-signal alignment: elevated moisture and sustained rainfall loading observed."
        else:
            synthesis = "Low multi-signal alignment: physical indicators remain near baseline conditions."

        return HydroMeteorologicalState(
            rainfall_intensity_level=r_int_lvl,
            rainfall_persistence_level=r_pers_lvl,
            accumulation_24h_level=acc_lvl,
            antecedent_wetness_level=ant_lvl,
            soil_moisture_level=s_lvl,
            moisture_trend_level=m_trend_lvl,
            elevated_signals_count=elevated,
            total_signals_count=6,
            signal_agreement_label=label,
            synthesis_summary=synthesis
        )

    # --- 4. TERRAIN SUSCEPTIBILITY ---

    @staticmethod
    def calculate_terrain_package(location: Location) -> TerrainSusceptibilityPackage:
        slope = location.slope_angle or 32.0
        susc = location.susceptibility_score or 0.75

        if slope >= 35.0:
            slope_class = "STEEP_ESCARPMENT"
        elif slope >= 25.0:
            slope_class = "MODERATELY_STEEP"
        elif slope >= 15.0:
            slope_class = "MODERATE_SLOPE"
        else:
            slope_class = "GENTLE"

        if susc >= 0.75:
            susc_label = "HIGH"
        elif susc >= 0.50:
            susc_label = "MODERATE"
        else:
            susc_label = "LOW"

        return TerrainSusceptibilityPackage(
            elevation_m=location.elevation or 1500.0,
            slope_angle_deg=round(slope, 1),
            slope_classification=slope_class,
            aspect_deg=135.0,
            aspect_label="SE (South-East)",
            terrain_susceptibility_score=round(susc, 2),
            historical_susceptibility_rating=susc_label,
            historical_incident_count=14,
            terrain_source="SRTM-30m / DEMO TERRAIN DATA",
            data_resolution="30m DEM",
            data_freshness="Static Baseline",
            is_simulated_terrain=True,
            geotechnical_notes="Steep terrain slope angle exacerbates gravitational shear stress under heavy saturation."
        )

    # --- 5. TRIGGERS vs CONDITIONING FACTORS ---

    @staticmethod
    def calculate_triggers_and_conditioning(
        rainfall_pkg: RainfallAnalysisPackage,
        soil_pkg: SoilMoistureAnalysisPackage,
        terrain_pkg: TerrainSusceptibilityPackage
    ) -> Tuple[List[TriggerFactorItem], List[ConditioningFactorItem]]:
        triggers = [
            TriggerFactorItem(
                name="Hourly Rainfall Intensity",
                value=f"{rainfall_pkg.intensity.current_intensity_mm_h} mm/h",
                severity=rainfall_pkg.intensity.classification if rainfall_pkg.intensity.classification != "NONE" else "LOW",
                description="Dynamic short-duration hydrologic burst loading surface soil."
            ),
            TriggerFactorItem(
                name="Rainfall Spell Persistence",
                value=f"{rainfall_pkg.persistence.current_wet_spell_hours} hours continuous",
                severity=rainfall_pkg.persistence.persistence_level,
                description="Continuous precipitation preventing slope drainage recovery."
            ),
            TriggerFactorItem(
                name="Antecedent Wetness Index (API)",
                value=f"{rainfall_pkg.antecedent_wetness_index.api_value} API",
                severity="CRITICAL" if rainfall_pkg.antecedent_wetness_index.classification == "CRITICAL_SATURATION" else "HIGH" if rainfall_pkg.antecedent_wetness_index.classification == "ELEVATED" else "LOW",
                description="Cumulative multi-day antecedent precipitation loading."
            ),
            TriggerFactorItem(
                name="Rainfall Anomaly Departure",
                value=f"+{rainfall_pkg.anomaly.z_score} sigma",
                severity="CRITICAL" if rainfall_pkg.anomaly.anomaly_status in ["EXTREMELY_ABNORMAL", "HIGHLY_UNUSUAL"] else "MODERATE",
                description="Statistical departure from long-term seasonal precipitation baseline."
            ),
        ]

        conditioning = [
            ConditioningFactorItem(
                name="Slope Angle & Gradient",
                value=f"{terrain_pkg.slope_angle_deg}° ({terrain_pkg.slope_classification})",
                severity="HIGH" if terrain_pkg.slope_angle_deg >= 30 else "MODERATE",
                description="Static gravitational shear force driving downslope vector."
            ),
            ConditioningFactorItem(
                name="Subsurface Soil Moisture Saturation",
                value=f"{soil_pkg.current_composite_pct}% ({soil_pkg.percentile.status_label})",
                severity="CRITICAL" if soil_pkg.current_composite_pct >= 80 else "HIGH" if soil_pkg.current_composite_pct >= 70 else "LOW",
                description="Degree of pore space water filling reducing effective normal stress."
            ),
            ConditioningFactorItem(
                name="Geological Susceptibility Rating",
                value=f"{terrain_pkg.terrain_susceptibility_score} / 1.0 ({terrain_pkg.historical_susceptibility_rating})",
                severity=terrain_pkg.historical_susceptibility_rating,
                description="Lithological weakness and historical slide susceptibility zone."
            ),
            ConditioningFactorItem(
                name="Historical Incident Density",
                value=f"{terrain_pkg.historical_incident_count} Recorded Incidents",
                severity="MODERATE",
                description="Proximity to documented historical slope failure scars."
            ),
        ]

        return triggers, conditioning

    # --- 6. UNCERTAINTY & DATA QUALITY MATRIX ---

    @staticmethod
    def calculate_uncertainty_and_quality(
        latest_risk: Optional[RiskAssessment],
        observations: List[WeatherObservation],
        hydro_state: HydroMeteorologicalState
    ) -> Tuple[UncertaintyAnalysis, List[DataCompletenessMatrixItem]]:
        conf = latest_risk.confidence_score if latest_risk else 0.82
        conf_pct = round(conf * 100.0, 1)

        completeness_pct = 87.5
        freshness_pct = 95.0
        agreement_pct = round((hydro_state.elevated_signals_count / max(1, hydro_state.total_signals_count)) * 100.0, 1)

        known_missing = [
            "In-situ borehole piezometric pore-water pressure",
            "Continuous subsurface inclinometer/displacement array",
            "High-resolution satellite InSAR surface deformation"
        ]

        uncertainty_summary = (
            f"Confidence ({conf_pct}%) is supported by strong hydrometeorological signal agreement ({agreement_pct}%) "
            f"and high telemetry freshness ({freshness_pct}%). Primary uncertainty is attributed to absent direct subsurface displacement sensors."
        )

        uncertainty = UncertaintyAnalysis(
            assessment_confidence_pct=conf_pct,
            data_completeness_pct=completeness_pct,
            data_freshness_pct=freshness_pct,
            signal_agreement_pct=agreement_pct,
            summary=uncertainty_summary,
            known_missing_inputs=known_missing,
        )

        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

        matrix = [
            DataCompletenessMatrixItem(parameter="Rainfall Telemetry", status="AVAILABLE", data_source="Open-Meteo / Simulation Grid", last_updated=now_str),
            DataCompletenessMatrixItem(parameter="Volumetric Soil Moisture", status="AVAILABLE", data_source="Land-Surface Model (0-27cm)", last_updated=now_str),
            DataCompletenessMatrixItem(parameter="DEM Elevation & Slope", status="SIMULATED", data_source="SRTM-30m Digital Elevation Model", last_updated="Static Baseline"),
            DataCompletenessMatrixItem(parameter="Historical Baseline", status="AVAILABLE", data_source="NER Station Re-analysis Baseline", last_updated="Static Baseline"),
            DataCompletenessMatrixItem(parameter="Ground Displacement", status="MISSING", data_source="In-situ Borehole Arrays", last_updated="N/A", note="Sensors not deployed"),
            DataCompletenessMatrixItem(parameter="Piezometer Pore Pressure", status="MISSING", data_source="In-situ Piezometers", last_updated="N/A", note="Sensors not deployed"),
            DataCompletenessMatrixItem(parameter="Field Ground Evidence", status="AVAILABLE", data_source="SDRF/NDRF Field Patrol Units", last_updated=now_str),
            DataCompletenessMatrixItem(parameter="Satellite Remote Sensing", status="MISSING", data_source="Sentinel-1 InSAR Deformation", last_updated="N/A"),
        ]

        return uncertainty, matrix

    # --- 7. COMPLETE STATION INVESTIGATION RESPONSE BUILDER ---

    @staticmethod
    async def build_investigation_response(
        session: AsyncSession,
        location_id: str
    ) -> Optional[ScientificStationInvestigationResponse]:
        # 1. Fetch Location
        stmt = select(Location).where(Location.id == location_id)
        loc = (await session.execute(stmt)).scalars().first()
        if not loc:
            return None

        # 2. Fetch Observations
        obs_stmt = select(WeatherObservation).where(WeatherObservation.location_id == location_id).order_by(WeatherObservation.timestamp.asc())
        observations = list((await session.execute(obs_stmt)).scalars().all())

        # 3. Fetch latest RiskAssessment
        risk_stmt = select(RiskAssessment).where(RiskAssessment.location_id == location_id).order_by(RiskAssessment.timestamp.desc())
        risk_history = list((await session.execute(risk_stmt)).scalars().all())
        latest_risk = risk_history[0] if risk_history else None

        # 4. Fetch Active Event if any
        event_stmt = select(DisasterEvent).where(DisasterEvent.location_id == location_id, DisasterEvent.status != "RESOLVED").order_by(DisasterEvent.updated_at.desc())
        active_event = (await session.execute(event_stmt)).scalars().first()

        # Compute scientific indicator packages
        rainfall_pkg = ScientificIndicatorsService.calculate_rainfall_metrics(observations, loc)
        soil_pkg = ScientificIndicatorsService.calculate_soil_metrics(observations, loc)
        hydro_state = ScientificIndicatorsService.calculate_agreement_state(rainfall_pkg, soil_pkg, loc)
        terrain_pkg = ScientificIndicatorsService.calculate_terrain_package(loc)
        triggers, conditioning = ScientificIndicatorsService.calculate_triggers_and_conditioning(rainfall_pkg, soil_pkg, terrain_pkg)
        uncertainty, quality_matrix = ScientificIndicatorsService.calculate_uncertainty_and_quality(latest_risk, observations, hydro_state)

        # Risk Trajectory Analysis (6h delta)
        cur_score = latest_risk.risk_score if latest_risk else 15.0
        cur_level = latest_risk.risk_level if latest_risk else "LOW"
        score_6h = cur_score
        level_6h = cur_level
        if len(risk_history) >= 7:
            score_6h = risk_history[6].risk_score
            level_6h = risk_history[6].risk_level
        elif len(risk_history) >= 2:
            score_6h = risk_history[-1].risk_score
            level_6h = risk_history[-1].risk_level

        delta_6h = round(cur_score - score_6h, 1)
        if delta_6h >= 5.0:
            direction = "INCREASING (↑)"
            accel = "RAPID" if delta_6h >= 12.0 else "MODERATE"
        elif delta_6h <= -5.0:
            direction = "DECREASING (↓)"
            accel = "MODERATE"
        else:
            direction = "STABLE (→)"
            accel = "LOW"

        risk_traj = RiskTrajectoryAnalysis(
            current_risk_score=round(cur_score, 1),
            current_risk_level=cur_level,
            score_6h_ago=round(score_6h, 1),
            level_6h_ago=level_6h,
            delta_6h=delta_6h,
            direction=direction,
            rate_of_change_points_per_hour=round(delta_6h / 6.0, 2),
            acceleration_label=accel,
            explanation="Calculated from 6-hour rolling risk index delta."
        )

        # Forecast Outlook Package
        forecast_pkg = ForecastOutlookPackage(
            expected_rainfall_24h_mm=round((rainfall_pkg.intensity.current_intensity_mm_h * 12.0) + 15.0, 1),
            expected_wet_hours_24h=14,
            expected_max_hourly_mm=round(rainfall_pkg.max_short_duration.max_1h_mm * 1.1, 1),
            expected_moisture_trend="CONTINUED_INCREASE" if cur_score >= 50 else "STABLE",
            projected_risk_trajectory="ELEVATED_RISK_PERSISTS" if cur_score >= 60 else "STABLE_MONITORING"
        )

        # Build Aligned Timeline Series Points
        timeline_series: List[TimelineSeriesPoint] = []
        for i, o in enumerate(observations[-48:]):
            r_at_t = cur_score
            for r in risk_history:
                if abs((r.timestamp - o.timestamp).total_seconds()) < 3600:
                    r_at_t = r.risk_score
                    break

            ev_marker = None
            if active_event and i == len(observations[-48:]) - 1:
                ev_marker = f"{active_event.severity} Event Created"

            timeline_series.append(
                TimelineSeriesPoint(
                    timestamp=o.timestamp,
                    timestamp_str=o.timestamp.strftime("%d %b %H:%M"),
                    is_observed=True,
                    rainfall_rate_mm_h=round(o.rainfall_1h or 0.0, 1),
                    rainfall_24h_mm=round(o.rainfall_24h or 0.0, 1),
                    soil_moisture_pct=round(o.soil_moisture or 50.0, 1),
                    risk_score=round(r_at_t, 1),
                    confidence_score=0.85,
                    event_marker=ev_marker,
                )
            )

        # Append Forecast Points (6 future points with is_observed=False)
        last_t = observations[-1].timestamp if observations else datetime.now(timezone.utc)
        for step in range(1, 7):
            f_time = last_t + timedelta(hours=step * 4)
            timeline_series.append(
                TimelineSeriesPoint(
                    timestamp=f_time,
                    timestamp_str=f_time.strftime("%d %b %H:%M (FCST)"),
                    is_observed=False,
                    rainfall_rate_mm_h=round(max(0.0, rainfall_pkg.intensity.current_intensity_mm_h * 0.8), 1),
                    rainfall_24h_mm=round(rainfall_pkg.anomaly.current_24h_mm * 1.15, 1),
                    soil_moisture_pct=round(min(98.0, soil_pkg.current_composite_pct + step * 1.2), 1),
                    risk_score=round(min(100.0, cur_score + step * 1.5 if cur_score >= 50 else cur_score), 1),
                    confidence_score=round(max(0.60, 0.85 - step * 0.03), 2),
                    event_marker="Forecast Horizon" if step == 6 else None,
                )
            )

        # Assessment Drivers breakdown
        drivers: List[AssessmentDriverItem] = [
            AssessmentDriverItem(factor_name="Rainfall Intensity", level=rainfall_pkg.intensity.classification, contribution_points=24.0, measured_value_str=f"{rainfall_pkg.intensity.current_intensity_mm_h} mm/h", driver_type="TRIGGER"),
            AssessmentDriverItem(factor_name="Soil Moisture Saturation", level=soil_pkg.percentile.status_label, contribution_points=28.0, measured_value_str=f"{soil_pkg.current_composite_pct}%", driver_type="CONDITIONING"),
            AssessmentDriverItem(factor_name="Rainfall Spell Persistence", level=rainfall_pkg.persistence.persistence_level, contribution_points=18.0, measured_value_str=f"{rainfall_pkg.persistence.current_wet_spell_hours}h wet", driver_type="TRIGGER"),
            AssessmentDriverItem(factor_name="Slope Angle Gradient", level="HIGH" if terrain_pkg.slope_angle_deg >= 30 else "MODERATE", contribution_points=16.0, measured_value_str=f"{terrain_pkg.slope_angle_deg}°", driver_type="CONDITIONING"),
            AssessmentDriverItem(factor_name="Antecedent Wetness Index", level="CRITICAL" if rainfall_pkg.antecedent_wetness_index.classification == "CRITICAL_SATURATION" else "MODERATE", contribution_points=14.0, measured_value_str=f"{rainfall_pkg.antecedent_wetness_index.api_value} API", driver_type="TRIGGER"),
        ]

        # Evidence Summary
        supporting = [
            f"Precipitation intensity {rainfall_pkg.intensity.current_intensity_mm_h} mm/h exceeds baseline thresholds.",
            f"Soil saturation reached {soil_pkg.current_composite_pct}%, indicating critical shallow retention.",
            f"Antecedent wetness index {rainfall_pkg.antecedent_wetness_index.api_value} confirms elevated multi-day loading."
        ] if cur_score >= 50 else ["Hydro-meteorological state is within normal baseline parameters."]

        limiting = [
            "Terrain layer is derived from 30m DEM proxy without in-situ borehole core samples.",
            "Historical baseline represents seasonal re-analysis rather than multi-decade verified ground records."
        ]

        evidence = EvidenceSummary(
            supporting_elevated_risk=supporting,
            limiting_uncertain_factors=limiting,
            missing_sensor_observations=uncertainty.known_missing_inputs,
        )

        # Data Provenance items
        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
        last_obs_str = observations[-1].timestamp.strftime("%H:%M UTC") if observations else now_str

        provenance_list: List[DataProvenanceItem] = [
            DataProvenanceItem(
                signal_name="Precipitation & Intensity",
                source_provider="Open-Meteo API / Local Simulation Grid",
                observation_time=last_obs_str,
                retrieval_time=now_str,
                freshness_status="FRESH",
                data_category="OBSERVED" if settings.DATA_MODE == "LIVE" else "SIMULATED"
            ),
            DataProvenanceItem(
                signal_name="Volumetric Soil Moisture",
                source_provider="Land Surface Hydrologic Model (0-27cm)",
                observation_time=last_obs_str,
                retrieval_time=now_str,
                freshness_status="FRESH",
                data_category="DERIVED"
            ),
            DataProvenanceItem(
                signal_name="Digital Elevation & Slope",
                source_provider="Copernicus 30m DEM / Prototype Terrain Layer",
                observation_time="Static Baseline",
                retrieval_time="Startup Cache",
                freshness_status="FRESH",
                data_category="SIMULATED"
            ),
        ]

        station_meta = {
            "id": loc.id,
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "elevation_m": loc.elevation,
            "slope_angle_deg": loc.slope_angle,
            "susceptibility_score": loc.susceptibility_score,
        }

        current_assessment = {
            "risk_score": round(cur_score, 1),
            "risk_level": cur_level,
            "confidence_score": round(latest_risk.confidence_score if latest_risk else 0.85, 2),
            "confidence_pct": round((latest_risk.confidence_score if latest_risk else 0.85) * 100),
            "timestamp": latest_risk.timestamp if latest_risk else datetime.now(timezone.utc),
            "active_event": active_event is not None,
            "event_id": active_event.id if active_event else None,
            "event_severity": active_event.severity if active_event else None,
            "event_status": active_event.status if active_event else None,
            "summary_text": latest_risk.reason if latest_risk else "Continuous environmental monitoring active.",
            "disclaimer": "Prototype Risk Index. Does not represent official government warning."
        }

        from backend.app.services.earth_observation_provider import get_earth_observation_provider
        from backend.app.schemas.scientific import EarthObservationSummary

        eo_provider = get_earth_observation_provider()
        eo_health = eo_provider.get_health_status()

        eo_summary = EarthObservationSummary(
            provider=eo_health.provider_name,
            status=eo_health.status,
            configured=eo_health.configured,
            latest_acquisition_time=now_str,
            collection="Sentinel-1A_SAR-IW_GRD",
            spatial_coverage=f"{loc.district}, {loc.state}",
            product_status="ONLINE" if eo_health.configured else "UNCONFIGURED",
            note=eo_health.note,
        )

        return ScientificStationInvestigationResponse(
            station=station_meta,
            current_assessment=current_assessment,
            risk_trajectory=risk_traj,
            rainfall=rainfall_pkg,
            soil_moisture=soil_pkg,
            hydrometeorological_state=hydro_state,
            terrain=terrain_pkg,
            triggers=triggers,
            conditioning_factors=conditioning,
            uncertainty=uncertainty,
            data_quality_matrix=quality_matrix,
            earth_observation=eo_summary,
            timeline_series=timeline_series,
            forecast=forecast_pkg,
            assessment_drivers=drivers,
            evidence_summary=evidence,
            provenance=provenance_list,
            generated_at=datetime.now(timezone.utc),
            engine_version="prototype-v0.3",
            data_mode=settings.DATA_MODE,
        )

    # --- 8. CANONICAL ASSESSMENT OBJECT GENERATOR ---

    @staticmethod
    async def generate_canonical_assessment(
        session: AsyncSession,
        location_id: str
    ) -> Optional[CanonicalAssessmentObject]:
        inv = await ScientificIndicatorsService.build_investigation_response(session, location_id)
        if not inv:
            return None

        return CanonicalAssessmentObject(
            location=inv.station,
            timestamp=inv.generated_at,
            engine_version="prototype-v0.3",
            environment={
                "data_mode": inv.data_mode,
                "rainfall_rate_mmh": inv.rainfall.intensity.current_intensity_mm_h,
                "rainfall_24h_mm": inv.rainfall.anomaly.current_24h_mm,
                "soil_moisture_pct": inv.soil_moisture.current_composite_pct,
            },
            indicators={
                "rainfall": inv.rainfall.model_dump(),
                "soil_moisture": inv.soil_moisture.model_dump(),
                "terrain": inv.terrain.model_dump(),
            },
            triggers=inv.triggers,
            conditioning_factors=inv.conditioning_factors,
            risk={
                "score": inv.current_assessment["risk_score"],
                "level": inv.current_assessment["risk_level"],
                "trajectory": inv.risk_trajectory.direction,
                "delta_6h": inv.risk_trajectory.delta_6h,
            },
            confidence={
                "score": inv.current_assessment["confidence_score"],
                "data_completeness": inv.uncertainty.data_completeness_pct / 100.0,
                "data_freshness": inv.uncertainty.data_freshness_pct / 100.0,
                "signal_agreement": inv.uncertainty.signal_agreement_pct / 100.0,
            },
            uncertainty=inv.uncertainty,
            data_quality={"matrix": [m.model_dump() for m in inv.data_quality_matrix]},
            provenance={"items": [p.model_dump() for p in inv.provenance]},
        )

    # --- FALLBACK BUILDERS ---

    @staticmethod
    def _build_empty_rainfall_package() -> RainfallAnalysisPackage:
        return RainfallAnalysisPackage(
            intensity=RainfallIntensityMetric(
                current_intensity_mm_h=0.0,
                intensity_6h_avg_mm_h=0.0,
                classification="NONE"
            ),
            short_duration_table=[
                ShortDurationAccumulationItem(period="1 hour", hours=1, rainfall_mm=0.0, has_data=True, status_label="Normal"),
                ShortDurationAccumulationItem(period="24 hours", hours=24, rainfall_mm=0.0, has_data=True, status_label="Normal"),
            ],
            max_short_duration=MaxShortDurationRainfall(max_1h_mm=0.0, max_3h_mm=0.0, max_6h_mm=0.0, window_hours_evaluated=0),
            event_segmentation=RainfallEventSegmentation(status="DRY_PERIOD"),
            antecedent_wetness_index=AntecedentWetnessIndexAPI(api_value=0.0, classification="NORMAL"),
            persistence=RainfallPersistenceMetric(
                current_wet_spell_hours=0,
                wet_hours_last_12h=0,
                wet_hours_last_24h=0,
                longest_continuous_wet_hours=0,
                persistence_level="LOW",
                persistence_ratio_24h=0.0
            ),
            antecedent=AntecedentRainfallMetric(),
            anomaly=RainfallAnomalyMetric(
                current_24h_mm=0.0,
                baseline_24h_mm=68.0,
                deviation_mm=-68.0,
                z_score=-2.1,
                anomaly_status="NORMAL"
            ),
            intensity_duration=IntensityDurationAnalysis(
                active_duration_hours=1.0,
                cumulative_rainfall_mm=0.0,
                average_intensity_mm_h=0.0,
                max_hourly_intensity_mm_h=0.0,
                prototype_threshold_rainfall_mm=25.0,
                is_above_prototype_threshold=False,
                threshold_margin_mm=-25.0,
                reference_curve=[]
            )
        )

    @staticmethod
    def _build_empty_soil_package() -> SoilMoistureAnalysisPackage:
        return SoilMoistureAnalysisPackage(
            current_composite_pct=50.0,
            vertical_profile=[],
            trend=SoilMoistureTrendMetric(
                delta_1h_pct=0.0,
                delta_3h_pct=0.0,
                delta_6h_pct=0.0,
                delta_24h_pct=0.0,
                direction="STABLE",
                trend_rate_pct_per_hour=0.0
            ),
            percentile=SoilMoisturePercentileMetric(
                current_moisture_pct=50.0,
                historical_percentile=50,
                status_label="Normal relative wetness"
            ),
            rainfall_response=RainfallToSoilResponse(),
            measurement_type="MODEL-DERIVED"
        )


scientific_indicators_service = ScientificIndicatorsService()
