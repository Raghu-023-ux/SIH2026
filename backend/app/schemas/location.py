from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Gangtok Monitoring Station"})
    latitude: float = Field(..., ge=-90.0, le=90.0, json_schema_extra={"example": 27.3389})
    longitude: float = Field(..., ge=-180.0, le=180.0, json_schema_extra={"example": 88.6065})
    district: str = Field(..., json_schema_extra={"example": "East Sikkim"})
    state: str = Field(..., json_schema_extra={"example": "Sikkim"})
    elevation: float = Field(default=1650.0, description="Elevation in meters", json_schema_extra={"example": 1650.0})
    slope_angle: float = Field(default=35.0, description="Average terrain slope in degrees", json_schema_extra={"example": 35.0})
    susceptibility_score: float = Field(default=0.75, ge=0.0, le=1.0, description="Geological landslide susceptibility", json_schema_extra={"example": 0.75})


class LocationCreate(LocationBase):
    id: Optional[str] = None


class LocationResponse(LocationBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
