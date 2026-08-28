from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    district = Column(String(128), nullable=False, index=True)
    state = Column(String(128), nullable=False, index=True)
    elevation = Column(Float, nullable=False, default=0.0)
    slope_angle = Column(Float, nullable=False, default=25.0)  # degrees
    susceptibility_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    observations = relationship("WeatherObservation", back_populates="location", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="location", cascade="all, delete-orphan")
    events = relationship("DisasterEvent", back_populates="location", cascade="all, delete-orphan")
