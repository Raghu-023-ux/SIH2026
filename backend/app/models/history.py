from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class RiskAssessmentHistory(Base):
    __tablename__ = "risk_assessment_history"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(timezone.utc))

    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    trajectory = Column(String(32), nullable=False, default="STABLE")

    factors_json = Column(JSON, nullable=False, default=list)
    reasons_json = Column(JSON, nullable=False, default=list)
    quality_json = Column(JSON, nullable=True)

    engine_version = Column(String(32), nullable=False, default="1.0.0")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


    __table_args__ = (
        Index("idx_hist_loc_time", "location_id", "timestamp"),
        Index("idx_hist_event_time", "event_id", "timestamp"),
    )
