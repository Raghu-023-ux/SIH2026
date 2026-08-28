from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class FactorContribution(BaseModel):
    name: str
    raw_value: Optional[Any] = None
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score 0.0 to 1.0")
    weight: float = Field(..., ge=0.0, le=1.0, description="Central factor weight")
    contribution: float = Field(..., description="Calculated point contribution to total risk score (0-100)")
    status: str = Field(..., description="'LOW', 'MODERATE', 'HIGH', or 'CRITICAL'")
    impact_type: str = Field(default="NEUTRAL", description="'INCREASE_RISK', 'DECREASE_RISK', 'NEUTRAL', 'UNAVAILABLE'")
    description: Optional[str] = None


class RiskAssessmentBase(BaseModel):
    location_id: str
    timestamp: datetime
    hazard_type: str = "LANDSLIDE"
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk score (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Assessment confidence (0-1)")
    trajectory: str = Field(default="STABLE", description="STABLE, INCREASING, DECREASING, VOLATILE, UNKNOWN")
    reason: str
    reason_codes: List[str] = Field(default_factory=list)
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    data_quality: Optional[Dict[str, Any]] = None
    signal_agreement: Optional[Dict[str, Any]] = None
    assessment_version: str = "prototype-v0.2"


class RiskAssessmentCreate(RiskAssessmentBase):
    id: Optional[str] = None


class RiskAssessmentResponse(RiskAssessmentBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
