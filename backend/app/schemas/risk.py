from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class FactorContribution(BaseModel):
    name: str
    contribution: float = Field(..., description="Calculated point contribution to total risk score (0-100)")
    raw_value: Optional[Any] = Field(None, description="Raw underlying metric value")
    status: str = Field(..., description="'low', 'moderate', 'high', or 'critical'")
    description: Optional[str] = None


class RiskAssessmentBase(BaseModel):
    location_id: str
    timestamp: datetime
    hazard_type: str = "LANDSLIDE"
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk score (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Assessment confidence (0-1)")
    reason: str
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    assessment_version: str = "v1.0-prototype"


class RiskAssessmentCreate(RiskAssessmentBase):
    id: Optional[str] = None


class RiskAssessmentResponse(RiskAssessmentBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
