from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class DisasterEvent(Base):
    __tablename__ = "disaster_events"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(64), nullable=False, default="LANDSLIDE", index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(32), nullable=False, index=True)    # WATCH, ELEVATED, HIGH_RISK, CRITICAL, RESOLVED
    severity = Column(String(32), nullable=False)              # LOW, MODERATE, HIGH, CRITICAL

    risk_score = Column(Float, nullable=False)                 # Current risk score
    confidence_score = Column(Float, nullable=False)           # Confidence score (0.0 to 1.0)

    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    expected_start = Column(DateTime, nullable=True)
    expected_peak = Column(DateTime, nullable=True)

    affected_area = Column(String(256), nullable=True)
    summary = Column(String(1024), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="events")

    __table_args__ = (
        Index("idx_event_loc_status", "location_id", "status"),
        Index("idx_event_type_status", "event_type", "status"),
    )
