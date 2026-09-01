from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class SafetyPoint(Base):
    """
    Configured safer reference points, shelter facilities, or medical aid posts.
    Clearly indicates verified vs demo/simulated status.
    """
    __tablename__ = "safety_points"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Coordinates of safe zone
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Type: SAFE_ZONE, SHELTER, MEDICAL, ASSEMBLY_POINT
    point_type = Column(String(32), nullable=False, default="SAFE_ZONE", index=True)
    
    capacity = Column(Integer, nullable=True, default=200)
    
    # Availability: OPEN, FULL, CLOSED
    availability = Column(String(32), nullable=False, default="OPEN")
    
    source = Column(String(128), nullable=False, default="State Disaster Management Authority (SDMA)")
    contact_number = Column(String(64), nullable=True, default="1070 / 112")
    is_simulated = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    location = relationship("Location")

    __table_args__ = (
        Index("idx_safepoint_loc_type", "location_id", "point_type"),
    )


class PublicUser(Base):
    """
    Lightweight anonymous or registered public profile for localized emergency alerts.
    """
    __tablename__ = "public_users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_permission = Column(Boolean, default=False, nullable=False)
    alert_enabled = Column(Boolean, default=True, nullable=False)
    alert_radius_km = Column(Float, default=25.0, nullable=False)
    preferred_language = Column(String(16), default="en", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class PublicAlertAcknowledgment(Base):
    """
    Audit log recording that a citizen reviewed/acknowledged a safety alert.
    """
    __tablename__ = "public_alert_acknowledgments"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


    # Relationships
    event = relationship("DisasterEvent")
    location = relationship("Location")
