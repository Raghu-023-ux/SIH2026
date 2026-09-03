from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.services.location_service import LocationService
from backend.app.ml.features.feature_extractor import feature_extractor
from backend.app.ml.registry.model_registry import model_registry
from backend.app.schemas.ml import (
    StationFeaturesResponse,
    TaggedFeatureValueSchema,
    EnvironmentalAnomalyResponse,
    LandslidePredictionResponse,
    ModelRegistryStatusResponse,
)

router = APIRouter()


@router.get("/status", response_model=ModelRegistryStatusResponse)
async def get_ml_registry_status():
    """
    Returns the current status of the Landslide ML Model Registry,
    active models, feature definitions, and training dataset availability.
    """
    status_dict = model_registry.get_registry_status()
    return ModelRegistryStatusResponse(**status_dict)


@router.get("/features/{location_id}", response_model=StationFeaturesResponse)
async def get_station_features(
    location_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Extracts the standardized 15-dimensional ML feature vector for a station
    with explicit, 100% data provenance tagging (OBSERVED, FORECAST, SATELLITE, MODEL_DERIVED, STATIC, SIMULATED).
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored location '{location_id}' not found."
        )

    # Fetch recent observations
    stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.asc())
    )
    result = await db.execute(stmt)
    observations = list(result.scalars().all())
    latest_obs = observations[-1] if observations else None

    vector = feature_extractor.extract_features(
        location=location,
        current_obs=latest_obs,
        obs_history=observations,
    )

    feat_dict = {
        "slope_angle": TaggedFeatureValueSchema(**vector.slope_angle.model_dump()),
        "elevation": TaggedFeatureValueSchema(**vector.elevation.model_dump()),
        "baseline_susceptibility": TaggedFeatureValueSchema(**vector.baseline_susceptibility.model_dump()),
        "rainfall_1h": TaggedFeatureValueSchema(**vector.rainfall_1h.model_dump()),
        "rainfall_6h": TaggedFeatureValueSchema(**vector.rainfall_6h.model_dump()),
        "rainfall_24h": TaggedFeatureValueSchema(**vector.rainfall_24h.model_dump()),
        "rainfall_72h": TaggedFeatureValueSchema(**vector.rainfall_72h.model_dump()),
        "soil_moisture_surface": TaggedFeatureValueSchema(**vector.soil_moisture_surface.model_dump()),
        "soil_moisture_middle": TaggedFeatureValueSchema(**vector.soil_moisture_middle.model_dump()),
        "soil_moisture_deep": TaggedFeatureValueSchema(**vector.soil_moisture_deep.model_dump()),
        "antecedent_precipitation_index": TaggedFeatureValueSchema(**vector.antecedent_precipitation_index.model_dump()),
        "consecutive_wet_hours": TaggedFeatureValueSchema(**vector.consecutive_wet_hours.model_dump()),
        "rainfall_z_score_24h": TaggedFeatureValueSchema(**vector.rainfall_z_score_24h.model_dump()),
        "soil_moisture_trend_slope": TaggedFeatureValueSchema(**vector.soil_moisture_trend_slope.model_dump()),
        "id_curve_ratio": TaggedFeatureValueSchema(**vector.id_curve_ratio.model_dump()),
    }

    return StationFeaturesResponse(
        location_id=vector.location_id,
        station_name=vector.station_name,
        timestamp=vector.timestamp,
        features=feat_dict,
        provenance_summary=vector.get_provenance_summary(),
        flat_vector=vector.to_flat_dict(),
    )


@router.post("/anomaly/{location_id}", response_model=EnvironmentalAnomalyResponse)
async def evaluate_environmental_anomaly(
    location_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Task A: Environmental Anomaly Detection.
    Evaluates whether current environmental conditions are statistically abnormal.
    NOTE: Anomaly evaluates unusual rainfall/soil behaviour; it DOES NOT equal landslide occurrence probability.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored location '{location_id}' not found."
        )

    stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.asc())
    )
    result = await db.execute(stmt)
    observations = list(result.scalars().all())
    latest_obs = observations[-1] if observations else None

    vector = feature_extractor.extract_features(
        location=location,
        current_obs=latest_obs,
        obs_history=observations,
    )

    detector = model_registry.get_active_anomaly_detector()
    output = detector.detect_anomaly(vector)

    return EnvironmentalAnomalyResponse(
        location_id=output.location_id,
        timestamp=output.timestamp,
        anomaly_score=output.anomaly_score,
        anomaly_level=output.anomaly_level,
        rainfall_anomaly_score=output.rainfall_anomaly_score,
        soil_wetness_anomaly_score=output.soil_wetness_anomaly_score,
        atmospheric_anomaly_score=output.atmospheric_anomaly_score,
        primary_abnormal_factors=output.primary_abnormal_factors,
        is_statistically_anomalous=output.is_statistically_anomalous,
        summary=output.summary,
    )


@router.post("/predict/{location_id}", response_model=LandslidePredictionResponse)
async def predict_landslide_probability(
    location_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Task B: Landslide Probability Prediction Model.
    Forecasts P(landslide occurrence | features up to time T) across multiple horizons (6h, 12h, 24h).
    Returns probability bounds, contributing factors, and explicit model training disclaimers.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored location '{location_id}' not found."
        )

    stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.asc())
    )
    result = await db.execute(stmt)
    observations = list(result.scalars().all())
    latest_obs = observations[-1] if observations else None

    vector = feature_extractor.extract_features(
        location=location,
        current_obs=latest_obs,
        obs_history=observations,
    )

    predictor = model_registry.get_active_predictor()
    output = predictor.predict(vector)

    horizons_schema = {
        h.value: hp for h, hp in output.horizons.items()
    }

    return LandslidePredictionResponse(
        location_id=output.location_id,
        station_name=output.station_name,
        timestamp=output.timestamp,
        model_tier=output.model_tier,
        model_version=output.model_version,
        is_trained_ml_model=output.is_trained_ml_model,
        data_provenance_summary=output.data_provenance_summary,
        horizons=horizons_schema,
        primary_contributing_features=output.primary_contributing_features,
        confidence_score=output.confidence_score,
        disclaimer=output.disclaimer,
    )
