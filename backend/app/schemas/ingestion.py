from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.engine import EngineAssessmentResponse


class IngestionResponse(BaseModel):
    location_id: str
    location_name: str
    status: str = Field(..., description="'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED'")
    data_mode: str = Field(..., description="'LIVE' or 'SIMULATION'")
    source: str
    freshness: str
    assessment: EngineAssessmentResponse
    timestamp: datetime
    message: str


class BatchIngestionResponse(BaseModel):
    executed_at: datetime
    data_mode: str
    locations_processed: int
    successful_count: int
    failed_count: int
    active_events_count: int
    highest_risk_score: float
    highest_risk_level: str
    assessments: List[EngineAssessmentResponse]


class IngestionStatusResponse(BaseModel):
    data_mode: str
    engine_version: str
    last_ingestion: datetime
    total_locations: int
    providers: List[Dict[str, Any]]
    cache_status: str


class DataModeToggleRequest(BaseModel):
    mode: str = Field(..., description="'LIVE' or 'SIMULATION'")


class DataModeResponse(BaseModel):
    current_mode: str
    message: str
    timestamp: datetime
