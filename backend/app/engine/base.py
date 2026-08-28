from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class TrendDirection(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ELEVATED = "ELEVATED"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"
    RESOLVED = "RESOLVED"


@dataclass
class AnomalyResult:
    metric: str
    value: float
    baseline: float
    anomaly_score: float
    is_anomalous: bool
    description: Optional[str] = None


@dataclass
class TrendResult:
    metric: str
    direction: TrendDirection
    slope: float
    description: Optional[str] = None


@dataclass
class FactorDetail:
    name: str
    contribution: float
    raw_value: Any
    status: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "contribution": round(self.contribution, 2),
            "raw_value": self.raw_value,
            "status": self.status,
            "description": self.description
        }


@dataclass
class AssessmentOutput:
    location_id: str
    timestamp: datetime
    hazard_type: str
    risk_level: RiskLevel
    risk_score: float
    confidence_score: float
    reason: str
    factors: List[FactorDetail] = field(default_factory=list)
    anomalies: List[AnomalyResult] = field(default_factory=list)
    trends: List[TrendResult] = field(default_factory=list)
    is_persistent_rain: bool = False
    is_increasing_rain: bool = False
