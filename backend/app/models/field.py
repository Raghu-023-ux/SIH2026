from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class FieldTeam(Base):
    __tablename__ = "field_teams"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_name = Column(String(128), nullable=False, index=True)
    callsign = Column(String(64), nullable=False, unique=True, index=True)
    assigned_location_id = Column(String(64), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status: AVAILABLE, DEPLOYED, ON_SCENE, ASSISTING, EVACUATING, NEED_ASSISTANCE, OFFLINE
    status = Column(String(32), nullable=False, default="AVAILABLE", index=True)
    
    # Coordinates of last known team location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    contact_channel = Column(String(64), nullable=True, default="VHF Ch 4 / Satellite")
    
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    assigned_location = relationship("Location")
    assigned_event = relationship("DisasterEvent")
    reports = relationship("FieldReport", back_populates="team", cascade="all, delete-orphan")
    assistance_requests = relationship("AssistanceRequest", back_populates="team", cascade="all, delete-orphan")


class FieldReport(Base):
    __tablename__ = "field_reports"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(String(64), ForeignKey("field_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    reported_by = Column(String(128), nullable=False, default="Rescue Unit Alpha")

    # Type: ROAD_BLOCKED, LANDSLIDE_OBSERVED, WATER_MUD_FLOW, INFRASTRUCTURE_DAMAGE, PEOPLE_TRAPPED, INJURIES, VISIBILITY_ISSUE, COMMUNICATION_FAILURE, OTHER
    report_type = Column(String(64), nullable=False, index=True)
    
    # Severity: LOW, MODERATE, HIGH, CRITICAL
    severity = Column(String(32), nullable=False, default="MODERATE", index=True)
    
    description = Column(Text, nullable=False)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_accuracy = Column(Float, nullable=True) # in meters
    location_source = Column(String(32), nullable=False, default="UNKNOWN") # GPS, MANUAL, UNKNOWN
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Status: SUBMITTED, ACKNOWLEDGED, UNDER_REVIEW, REVIEWED, INCORPORATED, DISMISSED
    status = Column(String(32), nullable=False, default="SUBMITTED", index=True)
    reviewed_by = Column(String(128), nullable=True)
    review_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    team = relationship("FieldTeam", back_populates="reports")
    location = relationship("Location")
    event = relationship("DisasterEvent")
    images = relationship("FieldReportImage", back_populates="report", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_field_rep_loc_time", "location_id", "timestamp"),
        Index("idx_field_rep_event_status", "event_id", "status"),
    )


class FieldReportImage(Base):
    __tablename__ = "field_report_images"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(64), ForeignKey("field_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key = Column(String(255), nullable=False)
    mime_type = Column(String(64), nullable=False, default="image/jpeg")
    file_size = Column(Float, nullable=False, default=0.0) # size in bytes
    uploaded_by = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    report = relationship("FieldReport", back_populates="images")


class AssistanceRequest(Base):
    __tablename__ = "assistance_requests"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(String(64), ForeignKey("field_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Type: MEDICAL, PERSONNEL, EQUIPMENT, TRANSPORT, COMMUNICATION, OTHER
    request_type = Column(String(64), nullable=False, index=True)
    
    # Priority: HIGH, CRITICAL
    priority = Column(String(32), nullable=False, default="HIGH", index=True)
    
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Status: REQUESTED, ACKNOWLEDGED, ASSIGNED, RESOLVED
    status = Column(String(32), nullable=False, default="REQUESTED", index=True)
    assigned_unit = Column(String(128), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    team = relationship("FieldTeam", back_populates="assistance_requests")
    event = relationship("DisasterEvent")


class OperationalMessage(Base):
    __tablename__ = "operational_messages"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_id = Column(String(128), nullable=False, default="Central Command Officer")
    recipient_team = Column(String(128), nullable=False, default="ALL_FIELD_TEAMS", index=True)
    
    # Priority: NORMAL, IMPORTANT, URGENT
    priority = Column(String(32), nullable=False, default="NORMAL", index=True)
    
    message = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(128), nullable=True)


    # Relationships
    event = relationship("DisasterEvent")
