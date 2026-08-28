from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WeatherObservationBase(BaseModel):
    location_id: str
    timestamp: datetime
    temperature: Optional[float] = Field(None, description="Temperature in °C")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity %")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    wind_speed: Optional[float] = Field(None, ge=0.0, description="Wind speed in km/h")
    wind_direction: Optional[float] = Field(None, ge=0.0, le=360.0, description="Wind direction in degrees")
    rainfall_1h: Optional[float] = Field(0.0, ge=0.0, description="Precipitation past 1 hour in mm")
    rainfall_6h: Optional[float] = Field(0.0, ge=0.0, description="Precipitation past 6 hours in mm")
    rainfall_24h: Optional[float] = Field(0.0, ge=0.0, description="Precipitation past 24 hours in mm")
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture volumetric %")
    source: str = Field(default="mock_sensor", description="Source provider or sensor id")


class WeatherObservationCreate(WeatherObservationBase):
    id: Optional[str] = None


class WeatherObservationResponse(WeatherObservationBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
