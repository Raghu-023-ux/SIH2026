from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class HistoricalDisasterIncident(Base):
    """
    Catalog of historical major landslide disasters across the North Eastern Region
    used for post-disaster forensic timeline reconstruction and model validation.
    """
    __tablename__ = "historical_disaster_incidents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False, unique=True, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    state = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    incident_type = Column(String(64), nullable=False, default="RAINFALL_TRIGGERED_LANDSLIDE")
    
    actual_impact_summary = Column(Text, nullable=False)
    casualties = Column(Integer, nullable=False, default=0)
    infrastructure_loss = Column(String(256), nullable=True)
    
    # Validation ground-truth metrics
    recorded_lead_time_hours = Column(Float, nullable=False, default=16.5)
    peak_rainfall_mm = Column(Float, nullable=False, default=185.0)
    
    # 72-Hour Timeline telemetry frames array
    timeline_data_json = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    location = relationship("Location")


class ModelEvaluationRun(Base):
    """
    Archived model calibration runs, parameter weight backtests, and statistical validation metrics.
    """
    __tablename__ = "model_evaluation_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String(128), nullable=False, index=True)
    dataset_name = Column(String(128), nullable=False, default="NER_HISTORICAL_2018_2024")
    
    weights_json = Column(JSON, nullable=False)
    
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    brier_score = Column(Float, nullable=False, default=0.12)
    mean_lead_time_hours = Column(Float, nullable=False)
    
    total_samples = Column(Integer, nullable=False, default=100)
    true_positives = Column(Integer, nullable=False)
    false_positives = Column(Integer, nullable=False)
    false_negatives = Column(Integer, nullable=False)
    true_negatives = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

