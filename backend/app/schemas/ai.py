from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    evidence_type: str = Field(..., description="e.g. 'ASSESSMENT', 'OBSERVATION', 'ANOMALY', 'TREND', 'TERRAIN', 'EVENT'")
    id_reference: Optional[str] = None
    metric: Optional[str] = None
    value: Optional[Any] = None
    timestamp: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class AgentFinding(BaseModel):
    type: str = Field(..., description="e.g. 'risk_driver', 'signal_change', 'environmental_anomaly', 'geological_vulnerability'")
    title: str
    description: str
    evidence: List[EvidenceReference] = Field(default_factory=list)


class AgentUncertainty(BaseModel):
    factor: str
    reason: str
    impact: str = "MODERATE"


class AgentRecommendation(BaseModel):
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    action: str
    rationale: str


class AgentAnalysis(BaseModel):
    summary: str
    risk_level: str
    risk_score: float
    confidence: float
    trajectory: str
    findings: List[AgentFinding] = Field(default_factory=list)
    uncertainties: List[AgentUncertainty] = Field(default_factory=list)
    recommendations: List[AgentRecommendation] = Field(default_factory=list)
    data_mode: str = "LIVE"
    all_evidence: List[EvidenceReference] = Field(default_factory=list)


class AIAnalysisRequest(BaseModel):
    location_id: Optional[str] = None
    event_id: Optional[str] = None
    question: Optional[str] = "Provide a comprehensive situational explanation of current landslide risk."
    agent_type: Optional[str] = "auto"  # "auto", "analyst", "investigation", "explanation"


class AIAnalysisResponse(BaseModel):
    answer: str
    analysis: AgentAnalysis
    evidence: List[EvidenceReference]
    agent: str
    data_mode: str
    model_used: str
    latency_ms: float
    timestamp: datetime


class AIAuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    agent_name: str
    request_id: str
    location_id: Optional[str] = None
    event_id: Optional[str] = None
    question: Optional[str] = None
    data_mode: str
    tool_calls_count: int
    latency_ms: float
    status: str
    error_message: Optional[str] = None
