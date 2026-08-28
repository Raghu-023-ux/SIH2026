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
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

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
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    event = relationship("DisasterEvent")
    location = relationship("Location")
