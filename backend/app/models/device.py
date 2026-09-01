from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy import Column, String, Float, Boolean, DateTime, Index, JSON
from backend.app.core.database import Base


class DeviceToken(Base):
    """
    Device Registration Token record for Firebase Cloud Messaging push notification delivery.
    Maintains active status, device platform, geographic location, and topic subscriptions.
    """
    __tablename__ = "device_tokens"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), nullable=True, index=True)
    fcm_token = Column(String(512), nullable=False, unique=True, index=True)
    
    # Platform: ANDROID, IOS, WEB
    platform = Column(String(32), nullable=False, default="ANDROID", index=True)
    device_name = Column(String(128), nullable=True)
    app_version = Column(String(32), nullable=True)
    
    # Optional GPS coordinates for geofenced push targeting
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # List of subscribed topics e.g. ["region:sikkim", "region:gangtok"]
    topic_subscriptions = Column(JSON, nullable=True, default=list)
    
    # Active flag (deactivated upon invalid token errors from FCM)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    deactivation_reason = Column(String(255), nullable=True)
    
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


    __table_args__ = (
        Index("idx_device_active_platform", "is_active", "platform"),
        Index("idx_device_user_active", "user_id", "is_active"),
    )
