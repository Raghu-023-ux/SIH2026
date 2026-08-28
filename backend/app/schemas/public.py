from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SafetyPointBase(BaseModel):
    name: str
    location_id: str
    latitude: float
    longitude: float
    point_type: str = "SAFE_ZONE"  # SAFE_ZONE, SHELTER, MEDICAL, ASSEMBLY_POINT
    capacity: Optional[int] = 200
    availability: str = "OPEN"  # OPEN, FULL, CLOSED
    source: str = "State Disaster Management Authority (SDMA)"
    contact_number: Optional[str] = "1070 / 112"
    is_simulated: bool = True


class SafetyPointCreate(SafetyPointBase):
    pass


class SafetyPointResponse(SafetyPointBase):
    id: str
    distance_km: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyGuidanceItem(BaseModel):
    category: str  # DO, DONT, NOTICE
    title: str
    instruction: str


class PublicAlertItem(BaseModel):
    alert_id: str
    event_id: str
    location_id: str
    location_name: str
    district: str
    state: str
    hazard_type: str
    public_status: str  # NO_ALERT, MONITORING, ALERT, URGENT
    message_title: str
    message_summary: str
    affected_radius_km: float
    detected_at: datetime
    updated_at: datetime
    data_mode: str = "LIVE"


class PublicAlertDetailResponse(BaseModel):
    alert: PublicAlertItem
    user_zone: str  # SAFE_ZONE, WATCH_ZONE, AFFECTED_ZONE, CRITICAL_ZONE
    user_distance_km: Optional[float] = None
    guidance: List[SafetyGuidanceItem]
    safer_reference_points: List[SafetyPointResponse]
    emergency_contacts: Dict[str, str]
    data_provenance: Dict[str, Any]


class LocationCheckRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_id: Optional[str] = None
    user_id: Optional[str] = None


class PublicRiskCheckResponse(BaseModel):
    is_affected: bool
    public_status: str  # NO_ALERT, MONITORING, ALERT, URGENT
    user_zone: str  # SAFE_ZONE, WATCH_ZONE, AFFECTED_ZONE, CRITICAL_ZONE
    location_name: str
    nearest_hazard_km: Optional[float] = None
    active_alert: Optional[PublicAlertItem] = None
    guidance: List[SafetyGuidanceItem]
    nearest_safe_point: Optional[SafetyPointResponse] = None
    data_mode: str = "LIVE"
    timestamp: datetime


class PublicPreferencesRequest(BaseModel):
    user_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_permission: bool = True
    alert_enabled: bool = True
    alert_radius_km: float = 25.0
    preferred_language: str = "en"


class PublicPreferencesResponse(BaseModel):
    user_id: str
    alert_enabled: bool
    alert_radius_km: float
    preferred_language: str
    updated_at: datetime


class PublicAlertAcknowledgeRequest(BaseModel):
    event_id: str
    location_id: str
    user_id: Optional[str] = "ANONYMOUS_PUBLIC_USER"


class PublicSystemStatusResponse(BaseModel):
    system_status: str
    active_public_alerts_count: int
    data_mode: str
    timestamp: datetime
