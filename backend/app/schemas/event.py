from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DisasterEventBase(BaseModel):
    event_type: str = "LANDSLIDE"
    location_id: str
    status: str = Field(..., description="MONITORING, WATCH, ELEVATED, HIGH, CRITICAL, RESOLVING, RESOLVED")
    severity: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    risk_score: float = Field(..., ge=0.0, le=100.0)
    initial_risk: float = Field(default=0.0, ge=0.0, le=100.0)
    peak_risk: float = Field(default=0.0, ge=0.0, le=100.0)
    peak_severity: str = Field(default="LOW")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    trajectory: str = Field(default="STABLE")
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
    peak_risk: Optional[float] = None
    peak_severity: Optional[str] = None
    confidence_score: Optional[float] = None
    trajectory: Optional[str] = None
    expected_start: Optional[datetime] = None
    expected_peak: Optional[datetime] = None
    affected_area: Optional[str] = None
    summary: Optional[str] = None


class DisasterEventResponse(DisasterEventBase):
    id: str
    detected_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
