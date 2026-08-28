from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DisasterEventBase(BaseModel):
    event_type: str = "LANDSLIDE"
    location_id: str
    status: str = Field(..., description="WATCH, ELEVATED, HIGH_RISK, CRITICAL, RESOLVED")
    severity: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    expected_start: Optional[datetime] = None
    expected_peak: Optional[datetime] = None
    affected_area: Optional[str] = None
    summary: str


class DisasterEventCreate(DisasterEventBase):
    id: Optional[str] = None
    detected_at: Optional[datetime] = None


class DisasterEventUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = None
    confidence_score: Optional[float] = None
    expected_start: Optional[datetime] = None
    expected_peak: Optional[datetime] = None
    affected_area: Optional[str] = None
    summary: Optional[str] = None


class DisasterEventResponse(DisasterEventBase):
    id: str
    detected_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
