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

    status = Column(String(32), nullable=False, index=True)    # MONITORING, WATCH, ELEVATED, HIGH, CRITICAL, RESOLVING, RESOLVED
    severity = Column(String(32), nullable=False)              # LOW, MODERATE, HIGH, CRITICAL

    risk_score = Column(Float, nullable=False)                 # Current risk score
    initial_risk = Column(Float, nullable=False, default=0.0)  # Risk score at detection
    peak_risk = Column(Float, nullable=False, default=0.0)     # Peak risk score recorded
    peak_severity = Column(String(32), nullable=False, default="LOW")

    confidence_score = Column(Float, nullable=False)           # Confidence score (0.0 to 1.0)
    trajectory = Column(String(32), nullable=False, default="STABLE")  # INCREASING, DECREASING, STABLE, VOLATILE

    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    expected_start = Column(DateTime(timezone=True), nullable=True)
    expected_peak = Column(DateTime(timezone=True), nullable=True)


    affected_area = Column(String(256), nullable=True)
    summary = Column(String(1024), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="events")

    __table_args__ = (
        Index("idx_event_loc_status", "location_id", "status"),
        Index("idx_event_type_status", "event_type", "status"),
    )
