"""
Scientific Threshold Configuration for Landslide Early Warning.
Defines prototype reference thresholds for Rainfall Intensity, Cumulative Accumulation,
Intensity-Duration (I-D) curves, Soil Moisture Wetness, and Anomaly Baselines for the North Eastern Region.
All prototype thresholds are explicitly tagged with metadata and marked is_prototype=True.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ThresholdMetadata(BaseModel):
    name: str
    parameter: str
    threshold_value: float
    unit: str
    region: str = "North Eastern Region (NER) - Prototype"
    source: str = "GSI / USGS / IMD Literature Empirical Adaptation"
    version: str = "v1.2-prototype"
    is_prototype: bool = True
    description: str


class IDCurvePoint(BaseModel):
    duration_hours: float
    threshold_rainfall_mm: float
    critical_intensity_mm_h: float


class RainfallThresholdConfig(BaseModel):
    intensity_extreme_mm_h: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="Extreme Rainfall Intensity",
            parameter="rainfall_1h",
            threshold_value=35.0,
            unit="mm/h",
            description="Hourly burst rate threshold associated with rapid surface runoff and shallow slip initiation."
        )
    )
    intensity_high_mm_h: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="High Rainfall Intensity",
            parameter="rainfall_1h",
            threshold_value=20.0,
            unit="mm/h",
            description="Intense precipitation rate elevating slope destabilization risk."
        )
    )
    accumulation_24h_critical_mm: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="24h Critical Cumulative Rainfall",
            parameter="rainfall_24h",
            threshold_value=140.0,
            unit="mm",
            description="24-hour cumulative precipitation threshold indicating severe hydrologic slope loading."
        )
    )
    accumulation_24h_high_mm: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="24h High Cumulative Rainfall",
            parameter="rainfall_24h",
            threshold_value=90.0,
            unit="mm",
            description="24-hour cumulative precipitation threshold indicating elevated slope wetness."
        )
    )
    accumulation_72h_critical_mm: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="72h Critical Cumulative Rainfall",
            parameter="rainfall_72h",
            threshold_value=220.0,
            unit="mm",
            description="72-hour multi-day precipitation triggering deep-seated pore pressure escalation."
        )
    )
    persistence_wet_spell_hours: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="Rainfall Persistence Spell",
            parameter="consecutive_wet_hours",
            threshold_value=6.0,
            unit="hours",
            description="Minimum consecutive hours with precipitation >0.5mm/h to establish high persistence."
        )
    )
    anomaly_z_score_threshold: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="Standardized Rainfall Anomaly Sigma",
            parameter="z_score",
            threshold_value=2.0,
            unit="sigma",
            description="Statistical departure threshold from 10-day local rolling baseline."
        )
    )
    # Prototype Empirical Intensity-Duration curve points: I = 25.0 * D^(-0.45)
    id_curve_reference: List[IDCurvePoint] = Field(
        default_factory=lambda: [
            IDCurvePoint(duration_hours=1.0, threshold_rainfall_mm=25.0, critical_intensity_mm_h=25.0),
            IDCurvePoint(duration_hours=3.0, threshold_rainfall_mm=45.0, critical_intensity_mm_h=15.0),
            IDCurvePoint(duration_hours=6.0, threshold_rainfall_mm=70.0, critical_intensity_mm_h=11.6),
            IDCurvePoint(duration_hours=12.0, threshold_rainfall_mm=105.0, critical_intensity_mm_h=8.75),
            IDCurvePoint(duration_hours=24.0, threshold_rainfall_mm=140.0, critical_intensity_mm_h=5.83),
            IDCurvePoint(duration_hours=48.0, threshold_rainfall_mm=190.0, critical_intensity_mm_h=3.95),
            IDCurvePoint(duration_hours=72.0, threshold_rainfall_mm=230.0, critical_intensity_mm_h=3.19),
        ]
    )


class SoilMoistureThresholdConfig(BaseModel):
    volumetric_elevated_pct: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="Elevated Soil Moisture",
            parameter="soil_moisture_pct",
            threshold_value=70.0,
            unit="%",
            description="Model-derived volumetric soil moisture indicating elevated shallow retention."
        )
    )
    volumetric_critical_pct: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="High Soil Moisture",
            parameter="soil_moisture_pct",
            threshold_value=85.0,
            unit="%",
            description="Model-derived volumetric soil moisture indicating near-capacity relative wetness."
        )
    )
    change_6h_rapid_pct: ThresholdMetadata = Field(
        default_factory=lambda: ThresholdMetadata(
            name="Rapid Wetting Rate (6h)",
            parameter="soil_moisture_6h_delta",
            threshold_value=6.0,
            unit="%",
            description="Rapid upward delta in soil moisture over 6 hours reflecting fast infiltration."
        )
    )


class ScientificConfig(BaseModel):
    rainfall: RainfallThresholdConfig = Field(default_factory=RainfallThresholdConfig)
    soil_moisture: SoilMoistureThresholdConfig = Field(default_factory=SoilMoistureThresholdConfig)


scientific_config = ScientificConfig()
