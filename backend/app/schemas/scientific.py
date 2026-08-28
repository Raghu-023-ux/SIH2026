from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Rainfall Schemas ---
class ShortDurationAccumulationItem(BaseModel):
    period: str
    hours: int
    rainfall_mm: Optional[float] = None
    has_data: bool = True
    status_label: str = "Normal"


class RainfallIntensityMetric(BaseModel):
    current_intensity_mm_h: float
    intensity_6h_avg_mm_h: float
    classification: str  # NONE, LIGHT, MODERATE, HEAVY, EXTREME
    explanation: str = "Rainfall intensity represents the recent rate of precipitation rather than accumulated rainfall."


class RainfallPersistenceMetric(BaseModel):
    current_wet_spell_hours: int
    wet_hours_last_12h: int
    wet_hours_last_24h: int
    longest_continuous_wet_hours: int
    persistence_level: str  # LOW, MODERATE, HIGH, CRITICAL
    persistence_ratio_24h: float
    explanation: str = "Measures continuous or near-continuous wet hours over recent temporal windows."


class AntecedentRainfallMetric(BaseModel):
    antecedent_24h_mm: Optional[float] = None
    antecedent_48h_mm: Optional[float] = None
    antecedent_72h_mm: Optional[float] = None
    antecedent_7d_mm: Optional[float] = None
    loading_classification: str = "MODERATE"
    label: str = "Pre-event wetness indicator"
    explanation: str = "Preceding cumulative precipitation prior to the current triggering burst window."


class RainfallAnomalyMetric(BaseModel):
    current_24h_mm: float
    baseline_24h_mm: float
    deviation_mm: float
    z_score: float
    anomaly_status: str  # NORMAL, MODERATELY_UNUSUAL, HIGHLY_UNUSUAL, EXTREMELY_ABNORMAL
    baseline_source: str = "DEMO REFERENCE DATA"
    explanation: str = "Statistical departure from the station reference baseline expressed in standard deviations (sigma)."


class IDCurvePointSchema(BaseModel):
    duration_hours: float
    threshold_rainfall_mm: float
    critical_intensity_mm_h: float


class IntensityDurationAnalysis(BaseModel):
    active_duration_hours: float
    cumulative_rainfall_mm: float
    average_intensity_mm_h: float
    max_hourly_intensity_mm_h: float
    prototype_threshold_rainfall_mm: float
    is_above_prototype_threshold: bool
    threshold_margin_mm: float
    reference_curve: List[IDCurvePointSchema] = []
    status_text: str = "Above prototype reference"
    disclaimer: str = "Prototype Intensity-Duration empirical curve for illustrative research comparisons."


class RainfallAnalysisPackage(BaseModel):
    intensity: RainfallIntensityMetric
    short_duration_table: List[ShortDurationAccumulationItem]
    persistence: RainfallPersistenceMetric
    antecedent: AntecedentRainfallMetric
    anomaly: RainfallAnomalyMetric
    intensity_duration: IntensityDurationAnalysis


# --- Soil Moisture Schemas ---
class SoilMoistureDepthLayer(BaseModel):
    depth_range: str
    depth_label: str
    moisture_pct: float
    volumetric_m3_m3: float
    relative_wetness: str  # MODERATE, ELEVATED, HIGH, VERY_HIGH
    bar_fill_pct: float


class SoilMoistureTrendMetric(BaseModel):
    delta_1h_pct: float
    delta_3h_pct: float
    delta_6h_pct: float
    delta_24h_pct: float
    direction: str  # STABLE, INCREASING, RAPIDLY_INCREASING, DECREASING
    trend_rate_pct_per_hour: float
    explanation: str = "Temporal velocity of shallow subsurface moisture change across preceding hours."


class SoilMoisturePercentileMetric(BaseModel):
    current_moisture_pct: float
    historical_percentile: int  # e.g. 91
    status_label: str = "Unusually wet"  # Normal relative wetness, Elevated wetness, Unusually wet
    reference_source: str = "Historical seasonal distribution"
    explanation: str = "Relative position of current volumetric moisture within the station seasonal re-analysis distribution."


class SoilMoistureAnalysisPackage(BaseModel):
    current_composite_pct: float
    vertical_profile: List[SoilMoistureDepthLayer]
    trend: SoilMoistureTrendMetric
    percentile: SoilMoisturePercentileMetric
    measurement_type: str = "MODEL-DERIVED"
    disclaimer: str = "Model-derived volumetric soil moisture. In-situ pore pressure sensors not deployed."


# --- Hydro-Meteorological & Terrain Schemas ---
class HydroMeteorologicalState(BaseModel):
    rainfall_intensity_level: str
    rainfall_persistence_level: str
    accumulation_24h_level: str
    antecedent_wetness_level: str
    soil_moisture_level: str
    moisture_trend_level: str
    elevated_signals_count: int
    total_signals_count: int = 6
    signal_agreement_label: str = "5 / 6 indicators elevated"
    synthesis_summary: str


class TerrainSusceptibilityPackage(BaseModel):
    elevation_m: float
    slope_angle_deg: float
    slope_classification: str
    terrain_susceptibility_score: float
    historical_susceptibility_rating: str
    terrain_source: str = "DEM / simulated terrain"
    geotechnical_notes: str = "Steep terrain slope angle exacerbates shear stress under heavy hydrologic loading."


# --- Timeline & Forecast Schemas ---
class TimelineSeriesPoint(BaseModel):
    timestamp: datetime
    timestamp_str: str
    is_observed: bool = True
    rainfall_rate_mm_h: float
    rainfall_24h_mm: float
    soil_moisture_pct: float
    risk_score: float
    confidence_score: float
    event_marker: Optional[str] = None


class ForecastOutlookPackage(BaseModel):
    expected_rainfall_24h_mm: float
    expected_wet_hours_24h: int
    expected_max_hourly_mm: float
    expected_moisture_trend: str
    projected_risk_trajectory: str
    forecast_period_label: str = "Next 24 Hours (Model Forecast)"
    provenance_note: str = "Open-Meteo GFS/ECMWF Numerical Forecast Model"


# --- Provenance, Drivers & Evidence Summary ---
class DataProvenanceItem(BaseModel):
    signal_name: str
    source_provider: str
    observation_time: str
    retrieval_time: str
    freshness_status: str  # FRESH, AGING, STALE
    data_category: str  # OBSERVED, FORECAST, SIMULATED, DERIVED, MISSING


class AssessmentDriverItem(BaseModel):
    factor_name: str
    level: str  # Low, Mod, High, Critical
    contribution_points: float
    measured_value_str: str
    driver_type: str


class RiskTrajectoryAnalysis(BaseModel):
    current_risk_score: float
    current_risk_level: str
    score_6h_ago: float
    level_6h_ago: str
    delta_6h: float
    direction: str  # ↑ INCREASING, ↓ DECREASING, → STABLE
    rate_of_change_points_per_hour: float
    acceleration_label: str = "MODERATE"
    explanation: str


class EvidenceSummary(BaseModel):
    supporting_elevated_risk: List[str]
    limiting_uncertain_factors: List[str]
    missing_sensor_observations: List[str]


# --- Consolidated Station Investigation Payload ---
class ScientificStationInvestigationResponse(BaseModel):
    station: Dict[str, Any]
    current_assessment: Dict[str, Any]
    risk_trajectory: RiskTrajectoryAnalysis
    rainfall: RainfallAnalysisPackage
    soil_moisture: SoilMoistureAnalysisPackage
    hydrometeorological_state: HydroMeteorologicalState
    terrain: TerrainSusceptibilityPackage
    timeline_series: List[TimelineSeriesPoint]
    forecast: ForecastOutlookPackage
    assessment_drivers: List[AssessmentDriverItem]
    evidence_summary: EvidenceSummary
    provenance: List[DataProvenanceItem]
    generated_at: datetime
    data_mode: str = "LIVE"
