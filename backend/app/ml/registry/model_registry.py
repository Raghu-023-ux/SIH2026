from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.app.ml.types import (
    ModelTier,
    ModelMetadata,
)
from backend.app.ml.prediction.base import LandslidePredictor
from backend.app.ml.prediction.baseline import deterministic_baseline_predictor
from backend.app.ml.anomaly.base import EnvironmentalAnomalyDetector
from backend.app.ml.anomaly.statistical import statistical_anomaly_detector


class LandslideModelRegistry:
    """
    Centralized Model Registry managing model versions, manifests,
    data provenance constraints, and active inference instances.
    """

    FEATURE_NAMES = [
        "slope_angle",
        "elevation",
        "baseline_susceptibility",
        "rainfall_1h",
        "rainfall_6h",
        "rainfall_24h",
        "rainfall_72h",
        "soil_moisture_surface",
        "soil_moisture_middle",
        "soil_moisture_deep",
        "antecedent_precipitation_index",
        "consecutive_wet_hours",
        "rainfall_z_score_24h",
        "soil_moisture_trend_slope",
        "id_curve_ratio",
    ]

    def __init__(self):
        self._active_predictor: LandslidePredictor = deterministic_baseline_predictor
        self._active_anomaly_detector: EnvironmentalAnomalyDetector = statistical_anomaly_detector
        self._registered_models: Dict[str, ModelMetadata] = {
            "baseline-deterministic": ModelMetadata(
                model_id="baseline-deterministic",
                model_name="NER Deterministic Landslide Physics Baseline",
                model_tier=ModelTier.BASELINE_DETERMINISTIC,
                version="1.0.0",
                is_trained=False,
                is_active=True,
                training_dataset_name="None (Empirical Physical Formulations)",
                training_samples_count=0,
                positive_events_count=0,
                negative_samples_count=0,
                feature_names=self.FEATURE_NAMES,
                validation_roc_auc=None,
                validation_f1_score=None,
                validation_brier_score=None,
                status_note=(
                    "Operational baseline. Provides physics-grounded probability bounds "
                    "while genuine tabular ML models await curated GSI/IMD regional training data."
                ),
            ),
            "tabular-rf-ner": ModelMetadata(
                model_id="tabular-rf-ner",
                model_name="Random Forest Landslide Probability Classifier (NER)",
                model_tier=ModelTier.TABULAR_ML_RANDOM_FOREST,
                version="2.0.0-unloaded",
                is_trained=False,
                is_active=False,
                training_dataset_name="Pending GSI NLSM + NASA GLC Landslide Catalog (2014-2024)",
                feature_names=self.FEATURE_NAMES,
                status_note="Architectural slot prepared. Training pipeline pending regional historical dataset integration.",
            ),
            "tabular-gb-ner": ModelMetadata(
                model_id="tabular-gb-ner",
                model_name="HistGradientBoosting Landslide Forecaster (NER)",
                model_tier=ModelTier.TABULAR_ML_GRADIENT_BOOST,
                version="2.0.0-unloaded",
                is_trained=False,
                is_active=False,
                training_dataset_name="Pending GSI NLSM + NASA GLC Landslide Catalog (2014-2024)",
                feature_names=self.FEATURE_NAMES,
                status_note="Architectural slot prepared. Training pipeline pending regional historical dataset integration.",
            ),
        }

    def get_active_predictor(self) -> LandslidePredictor:
        return self._active_predictor

    def get_active_anomaly_detector(self) -> EnvironmentalAnomalyDetector:
        return self._active_anomaly_detector

    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        return self._registered_models.get(model_id)

    def list_models(self) -> List[ModelMetadata]:
        return list(self._registered_models.values())

    def get_registry_status(self) -> Dict[str, Any]:
        active_model = self._registered_models.get("baseline-deterministic")
        return {
            "registry_version": "1.0.0",
            "active_model_id": active_model.model_id if active_model else "none",
            "active_model_tier": active_model.model_tier.value if active_model else "none",
            "is_active_model_trained_ml": active_model.is_trained if active_model else False,
            "models_count": len(self._registered_models),
            "feature_count": len(self.FEATURE_NAMES),
            "features_monitored": self.FEATURE_NAMES,
            "registered_models": [m.model_dump() for m in self._registered_models.values()],
            "operational_status": "READY_BASELINE_OPERATIONAL",
            "training_pipeline_status": "AWAITING_LABELLED_NER_DATASET",
        }


model_registry = LandslideModelRegistry()
