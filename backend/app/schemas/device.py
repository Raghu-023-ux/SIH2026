from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DeviceRegisterRequest(BaseModel):
    fcm_token: str = Field(..., min_length=10, max_length=512, description="FCM registration token generated on Android/iOS/Web device")
    platform: str = Field("ANDROID", description="Device platform: ANDROID, IOS, WEB")
    user_id: Optional[str] = Field(None, description="Optional associated citizen or responder ID")
    device_name: Optional[str] = Field(None, description="e.g. Pixel 8, Samsung Galaxy S23")
    app_version: Optional[str] = Field(None, description="Client app version e.g. 1.0.0")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Current GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Current GPS longitude")
    topic_subscriptions: Optional[List[str]] = Field(default_factory=list, description="List of regional topics e.g. ['region:sikkim']")


class DeviceUpdateRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    app_version: Optional[str] = None
    topic_subscriptions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DeviceRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    fcm_token: str
    platform: str
    device_name: Optional[str] = None
    app_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    topic_subscriptions: Optional[List[str]] = None
    is_active: bool
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    message: str = "Device token registered successfully."


class FCMNotificationMessage(BaseModel):
    """Payload sent to FCM for push notification dispatch."""
    title: str = Field(..., max_length=150)
    body: str = Field(..., max_length=1000)
    priority: str = Field("HIGH", description="HIGH, NORMAL, CRITICAL")
    data: Optional[Dict[str, str]] = Field(default_factory=dict)
    topic: Optional[str] = None
    fcm_token: Optional[str] = None
