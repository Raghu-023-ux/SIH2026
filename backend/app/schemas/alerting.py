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
