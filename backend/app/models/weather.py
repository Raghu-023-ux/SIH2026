from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=lambda: datetime.now(timezone.utc))

    temperature = Column(Float, nullable=True)  # °C
    humidity = Column(Float, nullable=True)     # %
    pressure = Column(Float, nullable=True)     # hPa
    wind_speed = Column(Float, nullable=True)   # km/h
    wind_direction = Column(Float, nullable=True) # degrees

    rainfall_1h = Column(Float, nullable=True, default=0.0)   # mm
    rainfall_6h = Column(Float, nullable=True, default=0.0)   # mm
    rainfall_24h = Column(Float, nullable=True, default=0.0)  # mm

    soil_moisture = Column(Float, nullable=True)  # % volumetric water content (0-100%)

    source = Column(String(64), nullable=False, default="mock_sensor")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="observations")

    __table_args__ = (
        Index("idx_weather_loc_time", "location_id", "timestamp"),
    )
