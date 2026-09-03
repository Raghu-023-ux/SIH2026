from typing import List, Dict, Any
from backend.app.engine.base import AssessmentOutput, RiskLevel


class RiskAggregator:
    """
    Aggregates multi-factor risk assessments and calculates regional / network level statistics.
    """

    def aggregate_assessments(self, assessments: List[AssessmentOutput]) -> Dict[str, Any]:
        if not assessments:
            return {
                "total_monitored": 0,
                "highest_risk_score": 0.0,
                "highest_risk_level": RiskLevel.LOW.value,
                "critical_count": 0,
                "high_count": 0,
                "moderate_count": 0,
                "low_count": 0,
            }

        scores = [a.risk_score for a in assessments]
        highest_score = max(scores)

        # Determine highest level
        if any(a.risk_level == RiskLevel.CRITICAL for a in assessments):
            highest_level = RiskLevel.CRITICAL.value
        elif any(a.risk_level == RiskLevel.HIGH for a in assessments):
            highest_level = RiskLevel.HIGH.value
        elif any(a.risk_level == RiskLevel.MODERATE for a in assessments):
            highest_level = RiskLevel.MODERATE.value
        else:
            highest_level = RiskLevel.LOW.value

        return {
            "total_monitored": len(assessments),
            "highest_risk_score": highest_score,
            "highest_risk_level": highest_level,
            "critical_count": sum(1 for a in assessments if a.risk_level == RiskLevel.CRITICAL),
            "high_count": sum(1 for a in assessments if a.risk_level == RiskLevel.HIGH),
            "moderate_count": sum(1 for a in assessments if a.risk_level == RiskLevel.MODERATE),
            "low_count": sum(1 for a in assessments if a.risk_level == RiskLevel.LOW),
        }
