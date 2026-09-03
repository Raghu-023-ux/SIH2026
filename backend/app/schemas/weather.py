from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WeatherObservationBase(BaseModel):
    location_id: str
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    rainfall_1h: Optional[float] = Field(default=0.0, ge=0.0)
    rainfall_6h: Optional[float] = Field(default=0.0, ge=0.0)
    rainfall_24h: Optional[float] = Field(default=0.0, ge=0.0)
    soil_moisture: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    source: str = "OPEN_METEO"
    source_version: str = "v1"
    observation_type: str = "OBSERVED"
    quality_score: float = 1.0
    freshness_status: str = "FRESH"



class WeatherObservationCreate(WeatherObservationBase):
    id: Optional[str] = None
    retrieved_at: Optional[datetime] = None


class WeatherObservationResponse(WeatherObservationBase):
    id: str
    retrieved_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
