from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class NotificationDispatchLog(Base):
    """
    Audit log of outgoing emergency notifications dispatched across public and official channels.
    """
    __tablename__ = "notification_dispatch_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="CASCADE"), nullable=True, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Channel: CAP_FEED, SMS_GATEWAY, WHATSAPP_BROADCAST, EMAIL_BULLETIN, IN_APP_PUSH
    channel = Column(String(32), nullable=False, index=True)
    
    # Recipient: PUBLIC_CITIZENS, RESCUE_TEAMS, DISTRICT_MAGISTRATE, SDMA_OFFICERS, ALL
    recipient_group = Column(String(64), nullable=False, default="PUBLIC_CITIZENS")
    
    language = Column(String(16), nullable=False, default="en")
    payload_summary = Column(String(256), nullable=False)
    full_payload_json = Column(JSON, nullable=True)
    
    # Status: DISPATCHED, QUEUED, FAILED
    status = Column(String(32), nullable=False, default="DISPATCHED", index=True)
    latency_ms = Column(Float, nullable=True, default=12.5)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    event = relationship("DisasterEvent")
    location = relationship("Location")


class SituationReport(Base):
    """
    Formal operational Situation Report (SitRep) archived for civil administration and disaster authorities.
    """
    __tablename__ = "situation_reports"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(String(64), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    report_number = Column(String(64), nullable=False, unique=True, index=True)
    incident_name = Column(String(128), nullable=False)
    reporting_officer = Column(String(128), nullable=False, default="Command Duty Officer")
    
    executive_summary = Column(Text, nullable=False)
    full_sitrep_json = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    event = relationship("DisasterEvent")
    location = relationship("Location")


class Broadcast(Base):
    """
    Authorized central emergency broadcast dispatch to field teams and/or public.
    """
    __tablename__ = "broadcasts"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_id = Column(String(128), nullable=False, default="Central Command Duty Officer")
    priority = Column(String(32), nullable=False, default="URGENT", index=True)  # ADVISORY, WARNING, URGENT, CRITICAL
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    target_type = Column(String(64), nullable=False, default="FIELD_TEAMS", index=True)  # FIELD_TEAMS, PUBLIC_USERS, EVENT_AREA, CUSTOM_GROUP
    target_filter = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    event = relationship("DisasterEvent")
    notifications = relationship("Notification", back_populates="broadcast", cascade="all, delete-orphan", lazy="selectin")


class Notification(Base):
    """
    Individual delivery record for an emergency broadcast channel (IN_APP, SMS).
    """
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    broadcast_id = Column(String(64), ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(String(128), nullable=False, index=True)
    channel = Column(String(32), nullable=False, index=True)  # IN_APP, SMS
    status = Column(String(32), nullable=False, default="QUEUED", index=True)  # QUEUED, SENT, FAILED, DELIVERED
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


    # Relationships
    broadcast = relationship("Broadcast", back_populates="notifications")

