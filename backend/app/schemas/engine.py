from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnomalyReport(BaseModel):
    metric: str
    value: float
    baseline: float
    anomaly_score: float
    is_anomalous: bool
    description: Optional[str] = None


class TrendReport(BaseModel):
    metric: str
    direction: str  # INCREASING, DECREASING, STABLE, UNKNOWN
    slope: float
    description: Optional[str] = None


class EngineRunRequest(BaseModel):
    location_id: Optional[str] = Field(None, description="Optional target location ID. If omitted, runs for all locations.")
    force_fresh_fetch: bool = Field(False, description="Whether to trigger fresh ingestion before assessment")


class EngineAssessmentResponse(BaseModel):
    location_id: str
    location: str
    state: str
    hazard: str = "LANDSLIDE"
    risk_level: str
    risk_score: float
    confidence: float
    trend: str
    active_event: bool
    event_id: Optional[str] = None
    event_status: Optional[str] = None
    anomalies: List[AnomalyReport] = Field(default_factory=list)
    trends: List[TrendReport] = Field(default_factory=list)
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str
    timestamp: datetime


class MultiLocationEngineResponse(BaseModel):
    executed_at: datetime
    locations_evaluated: int
    active_events_count: int
    highest_risk_score: float
    highest_risk_level: str
    assessments: List[EngineAssessmentResponse]
