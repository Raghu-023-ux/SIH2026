from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Field Team Schemas ---
class FieldTeamBase(BaseModel):
    team_name: str
    callsign: str
    assigned_location_id: Optional[str] = None
    assigned_event_id: Optional[str] = None
    status: str = "AVAILABLE"  # AVAILABLE, DEPLOYED, ON_SCENE, ASSISTING, EVACUATING, NEED_ASSISTANCE, OFFLINE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_channel: Optional[str] = "VHF Ch 4 / Satellite"


class FieldTeamCreate(FieldTeamBase):
    pass


class FieldTeamResponse(FieldTeamBase):
    id: str
    last_active_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="AVAILABLE, DEPLOYED, ON_SCENE, ASSISTING, EVACUATING, NEED_ASSISTANCE, OFFLINE")
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# --- Field Report Schemas ---
class FieldReportImageResponse(BaseModel):
    id: str
    report_id: str
    storage_key: str
    mime_type: str
    file_size: float
    url: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FieldReportCreate(BaseModel):
    event_id: Optional[str] = None
    location_id: str
    team_id: Optional[str] = None
    reported_by: str = "Rescue Unit Alpha"
    report_type: str = Field(..., description="ROAD_BLOCKED, LANDSLIDE_OBSERVED, WATER_MUD_FLOW, INFRASTRUCTURE_DAMAGE, PEOPLE_TRAPPED, INJURIES, VISIBILITY_ISSUE, COMMUNICATION_FAILURE, OTHER")
    severity: str = Field(default="MODERATE", description="LOW, MODERATE, HIGH, CRITICAL")
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    location_source: Optional[str] = "UNKNOWN" # GPS, MANUAL, UNKNOWN
    image_storage_keys: Optional[List[str]] = Field(default_factory=list)


class FieldReportUpdate(BaseModel):
    status: str = Field(..., description="SUBMITTED, ACKNOWLEDGED, UNDER_REVIEW, REVIEWED, INCORPORATED, DISMISSED")
    reviewed_by: Optional[str] = "Command Duty Officer"
    review_notes: Optional[str] = None


class FieldReportResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    location_id: str
    team_id: Optional[str] = None
    reported_by: str
    report_type: str
    severity: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    location_source: Optional[str] = "UNKNOWN"
    timestamp: datetime
    status: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    images: List[FieldReportImageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Assistance Request Schemas ---
class AssistanceRequestCreate(BaseModel):
    event_id: Optional[str] = None
    team_id: str
    request_type: str = Field(..., description="MEDICAL, PERSONNEL, EQUIPMENT, TRANSPORT, COMMUNICATION, OTHER")
    priority: str = Field(default="HIGH", description="HIGH, CRITICAL")
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AssistanceRequestUpdate(BaseModel):
    status: str = Field(..., description="REQUESTED, ACKNOWLEDGED, ASSIGNED, RESOLVED")
    assigned_unit: Optional[str] = None
    resolution_notes: Optional[str] = None


class AssistanceRequestResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    team_id: str
    request_type: str
    priority: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    assigned_unit: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Operational Message Schemas ---
class OperationalMessageCreate(BaseModel):
    event_id: Optional[str] = None
    sender_id: str = "Central Command Officer"
    recipient_team: str = "ALL_FIELD_TEAMS"
    priority: str = Field(default="NORMAL", description="NORMAL, IMPORTANT, URGENT")
    message: str


class OperationalMessageResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    sender_id: str
    recipient_team: str
    priority: str
    message: str
    created_at: datetime
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- High-level Field Operations Summaries ---
class NearbyIncidentItem(BaseModel):
    event_id: Optional[str] = None
    location_id: str
    location_name: str
    hazard_type: str
    severity: str
    risk_score: float
    distance_km: float
    updated_at: datetime


class ImmediateConditionsSummary(BaseModel):
    slope_risk: str
    rainfall_state: str
    soil_saturation_state: str
    road_status: str
    nearest_hazard_km: Optional[float] = None


class FieldAssignmentResponse(BaseModel):
    team: FieldTeamResponse
    assigned_location: Optional[Dict[str, Any]] = None
    assigned_event: Optional[Dict[str, Any]] = None
    immediate_conditions: ImmediateConditionsSummary
    nearby_incidents: List[NearbyIncidentItem]
    recent_messages: List[OperationalMessageResponse]
    recent_reports: List[FieldReportResponse]


class FieldOperationsSummary(BaseModel):
    total_teams: int
    teams_deployed: int
    teams_on_scene: int
    teams_need_assistance: int
    unacknowledged_reports_count: int
    active_assistance_requests_count: int
    teams: List[FieldTeamResponse]
    recent_reports: List[FieldReportResponse]
    assistance_requests: List[AssistanceRequestResponse]
