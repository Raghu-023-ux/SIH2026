from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(timezone.utc))

    hazard_type = Column(String(64), nullable=False, default="LANDSLIDE", index=True)
    risk_level = Column(String(32), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    risk_score = Column(Float, nullable=False)                   # 0.0 to 100.0
    confidence_score = Column(Float, nullable=False)             # 0.0 to 1.0

    reason = Column(String(512), nullable=False)
    factors = Column(JSON, nullable=False, default=list)         # List of contributing factor details

    assessment_version = Column(String(32), nullable=False, default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


    # Relationships
    location = relationship("Location", back_populates="risk_assessments")

    __table_args__ = (
        Index("idx_risk_loc_time_hazard", "location_id", "timestamp", "hazard_type"),
    )
