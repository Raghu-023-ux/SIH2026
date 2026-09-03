from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Common Alerting Protocol (CAP v1.2) Schemas ---
class CAPParameter(BaseModel):
    valueName: str
    value: str


class CAPArea(BaseModel):
    areaDesc: str
    circle: Optional[str] = None  # "latitude,longitude radius_km"
    polygon: Optional[str] = None


class CAPInfo(BaseModel):
    language: str = "en-IN"
    category: str = "Geo"  # Geo, Met, Safety, Security, Rescue
    event: str = "Landslide Early Warning"
    responseType: str = "Evacuate"  # Shelter, Evacuate, Prepare, Execute, Avoid, Monitor
    urgency: str = "Immediate"  # Immediate, Expected, Future, Past, Unknown
    severity: str = "Severe"  # Extreme, Severe, Moderate, Minor, Unknown
    certainty: str = "Observed"  # Observed, Likely, Possible, Unlikely, Unknown
    eventCode: Optional[str] = "EQ-LS-01"
    expires: datetime
    headline: str
    description: str
    instruction: str
    web: Optional[str] = None
    contact: Optional[str] = "State Disaster Management Control Room: 1070"
    parameter: List[CAPParameter] = []
    area: List[CAPArea] = []


class CAPAlertFeedItem(BaseModel):
    identifier: str
    sender: str = "NER_DISASTER_INTELLIGENCE_ENGINE@NDMA.GOV.IN"
    sent: datetime
    status: str = "Actual"  # Actual, Exercise, System, Test, Draft
    msgType: str = "Alert"  # Alert, Update, Cancel, Ack, Error
    scope: str = "Public"  # Public, Restricted, Private
    code: Optional[List[str]] = ["IPAWS-CAP-1.2"]
    info: List[CAPInfo] = []


# --- Multi-Channel Payload Schemas ---
class SMSPayload(BaseModel):
    character_count: int
    text_en: str
    text_hi: str
    text_regional: Optional[str] = None
    is_within_160_chars: bool


class WhatsAppPayload(BaseModel):
    header: str
    body: str
    action_url: str
    contact_number: str


class EmailPayload(BaseModel):
    subject: str
    html_body: str
    priority: str


class PushPayload(BaseModel):
    title: str
    body: str
    priority: str
    tag: str


class MultiChannelPayloadPackage(BaseModel):
    event_id: str
    location_name: str
    severity: str
    sms: SMSPayload
    whatsapp: WhatsAppPayload
    email: EmailPayload
    push: PushPayload
    cap_identifier: str


# --- Broadcast Dispatches ---
class BroadcastTriggerRequest(BaseModel):
    event_id: str
    location_id: str
    channels: List[str] = Field(
        default=["CAP_FEED", "SMS_GATEWAY", "WHATSAPP_BROADCAST", "EMAIL_BULLETIN", "IN_APP_PUSH"],
        description="Target broadcast channels"
    )
    recipient_group: str = "PUBLIC_AND_OFFICIALS"
    custom_directive: Optional[str] = None


class DispatchLogResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    location_id: str
    channel: str
    recipient_group: str
    language: str
    payload_summary: str
    status: str
    latency_ms: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BroadcastTriggerResponse(BaseModel):
    broadcast_id: str
    event_id: str
    channels_dispatched: List[str]
    total_dispatched: int
    dispatch_logs: List[DispatchLogResponse]
    timestamp: datetime


# --- Situation Report (SitRep) Schemas ---
class SitRepSection(BaseModel):
    heading: str
    content: str
    key_metrics: Optional[Dict[str, Any]] = None


class SituationReportDetail(BaseModel):
    report_number: str
    incident_name: str
    location_name: str
    state: str
    reporting_officer: str
    generated_at: datetime
    operational_period: str
    executive_summary: str
    sections: List[SitRepSection]
    data_mode: str = "LIVE"


class SitRepGenerateRequest(BaseModel):
    event_id: str
    location_id: str
    reporting_officer: Optional[str] = "Command Duty Officer"


class SitRepResponse(BaseModel):
    id: str
    event_id: str
    location_id: str
    report_number: str
    incident_name: str
    reporting_officer: str
    executive_summary: str
    full_sitrep: SituationReportDetail
    created_at: datetime


# --- Core Broadcast & Multi-Provider Notification Pipeline Schemas ---
class BroadcastCreate(BaseModel):
    event_id: Optional[str] = None
    sender_id: Optional[str] = "Central Command Duty Officer"
    priority: str = Field(default="URGENT", description="ADVISORY, WARNING, URGENT, CRITICAL")
    title: str = Field(..., max_length=150, description="Broadcast header/title")
    message: str = Field(..., max_length=1000, description="Emergency alert message body")
    target_type: str = Field(default="FIELD_TEAMS", description="FIELD_TEAMS, PUBLIC_USERS, EVENT_AREA, CUSTOM_GROUP")
    target_filter: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = Field(default=["IN_APP", "SMS"], description="Channels: IN_APP, SMS")


class NotificationItemResponse(BaseModel):
    id: str
    broadcast_id: str
    recipient_id: str
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BroadcastStatusResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    sender_id: str
    priority: str
    title: str
    message: str
    target_type: str
    created_at: datetime
    total_recipients: int
    in_app_sent: int = 0
    in_app_failed: int = 0
    in_app_pending: int = 0
    sms_sent: int = 0
    sms_failed: int = 0
    sms_pending: int = 0
    fcm_sent: int = 0
    fcm_failed: int = 0
    fcm_pending: int = 0
    email_sent: int = 0
    email_failed: int = 0
    email_pending: int = 0
    notifications: List[NotificationItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)





class BroadcastCreateResponse(BaseModel):
    id: str
    status: str = "ACCEPTED"
    message: str
    recipient_count: int
    channels: List[str]
    created_at: datetime

