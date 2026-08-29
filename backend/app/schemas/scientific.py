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


class MaxShortDurationRainfall(BaseModel):
    max_1h_mm: float
    max_3h_mm: float
    max_6h_mm: float
    window_hours_evaluated: int
    peak_timestamp: Optional[datetime] = None


class RainfallEventSegmentation(BaseModel):
    status: str  # DRY_PERIOD, ONGOING_WET_EVENT, RECOVERY_PERIOD
    event_start_time: Optional[datetime] = None
    event_peak_time: Optional[datetime] = None
    peak_intensity_mm_h: float = 0.0
    active_wet_duration_hours: int = 0
    antecedent_dry_hours: int = 0
    explanation: str = "Segments continuous rain events from antecedent dry and recovery periods."


class AntecedentWetnessIndexAPI(BaseModel):
    api_value: float  # API(t) = P(t) + k*P(t-1) + k^2*P(t-2) + ...
    decay_constant_k: float = 0.85
    classification: str  # NORMAL, ELEVATED, CRITICAL_SATURATION
    formula_label: str = "API(t) = sum(k^i * P(t-i))"
    is_prototype: bool = True
    disclaimer: str = "Prototype Antecedent Wetness Index. Requires regional geotechnical calibration."


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
    max_short_duration: MaxShortDurationRainfall
    event_segmentation: RainfallEventSegmentation
    antecedent_wetness_index: AntecedentWetnessIndexAPI
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


class RainfallToSoilResponse(BaseModel):
    response_detected: bool = True
    lag_time_hours: float = 2.5
    correlation_label: str = "POSITIVE_RESPONSE"
    explanation: str = "Observed temporal relationship between rainfall infiltration and subsurface moisture increase (non-causal prototype metric)."


class SoilMoistureAnalysisPackage(BaseModel):
    current_composite_pct: float
    vertical_profile: List[SoilMoistureDepthLayer]
    trend: SoilMoistureTrendMetric
    percentile: SoilMoisturePercentileMetric
    rainfall_response: RainfallToSoilResponse
    measurement_type: str = "MODEL-DERIVED"
    disclaimer: str = "Model-derived volumetric soil moisture. In-situ piezometers not deployed."


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
    aspect_deg: Optional[float] = 135.0
    aspect_label: str = "SE (South-East)"
    terrain_susceptibility_score: float
    historical_susceptibility_rating: str
    historical_incident_count: int = 12
    terrain_source: str = "SRTM-30m / DEMO TERRAIN DATA"
    data_resolution: str = "30m DEM"
    data_freshness: str = "Static Geotechnical Baseline"
    is_simulated_terrain: bool = True
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


# --- Trigger vs. Conditioning Factors ---
class TriggerFactorItem(BaseModel):
    name: str
    value: str
    severity: str  # LOW, MODERATE, HIGH, CRITICAL
    type: str = "TRIGGER"
    description: str


class ConditioningFactorItem(BaseModel):
    name: str
    value: str
    severity: str  # LOW, MODERATE, HIGH, CRITICAL
    type: str = "CONDITIONING"
    description: str


# --- Data Completeness & Uncertainty Analysis ---
class DataCompletenessMatrixItem(BaseModel):
    parameter: str
    status: str  # AVAILABLE, PARTIAL, MISSING, STALE, SIMULATED
    data_source: str
    last_updated: str
    note: Optional[str] = None


class UncertaintyAnalysis(BaseModel):
    assessment_confidence_pct: float
    data_completeness_pct: float
    data_freshness_pct: float
    signal_agreement_pct: float
    summary: str
    known_missing_inputs: List[str]


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
    driver_type: str  # TRIGGER, CONDITIONING


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
    triggers: List[TriggerFactorItem] = Field(default_factory=list)
    conditioning_factors: List[ConditioningFactorItem] = Field(default_factory=list)
    uncertainty: UncertaintyAnalysis
    data_quality_matrix: List[DataCompletenessMatrixItem] = Field(default_factory=list)
    timeline_series: List[TimelineSeriesPoint]
    forecast: ForecastOutlookPackage
    assessment_drivers: List[AssessmentDriverItem]
    evidence_summary: EvidenceSummary
    provenance: List[DataProvenanceItem]
    generated_at: datetime
    engine_version: str = "prototype-v0.3"
    data_mode: str = "LIVE"


# --- Canonical Core Engine Assessment Object ---
class CanonicalAssessmentObject(BaseModel):
    location: Dict[str, Any]
    timestamp: datetime
    engine_version: str = "prototype-v0.3"
    environment: Dict[str, Any]
    indicators: Dict[str, Any]
    triggers: List[TriggerFactorItem]
    conditioning_factors: List[ConditioningFactorItem]
    risk: Dict[str, Any]
    confidence: Dict[str, Any]
    uncertainty: UncertaintyAnalysis
    data_quality: Dict[str, Any]
    provenance: Dict[str, Any]
