from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.app.schemas.engine import EngineAssessmentResponse


class SimulationScenarioRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="Scenario type: normal, heavy_rain, persistent_rain, landslide_risk_increasing, critical, recovery",
        json_schema_extra={"example": "critical"}
    )
    location_id: Optional[str] = Field(None, description="Optional target location. If omitted, applies to default demo location.")
    seed: Optional[int] = Field(42, description="Random seed for deterministic time-series generation")


class SimulationScenarioResponse(BaseModel):
    scenario: str
    location_id: str
    location_name: str
    message: str
    observations_injected: int
    assessment: EngineAssessmentResponse
    timestamp: datetime
