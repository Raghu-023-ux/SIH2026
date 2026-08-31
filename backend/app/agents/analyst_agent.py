from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.tools import agent_tools
from backend.app.agents.providers import get_llm_provider
from backend.app.schemas.ai import AgentAnalysis, EvidenceReference
from backend.app.core.config import settings


class DisasterAnalystAgent:
    """
    Disaster Analyst Agent.
    Interprets current scientific engine assessments, evaluates risk drivers,
    incorporates on-ground field observations, and generates tactical monitoring recommendations.
    """

    def __init__(self, provider: Optional[Any] = None):
        self._custom_provider = provider

    async def analyze(
        self,
        session: AsyncSession,
        location_id: str,
        question: Optional[str] = None
    ) -> AgentAnalysis:
        provider = self._custom_provider or get_llm_provider()
        evidence: List[EvidenceReference] = []

        # 1. Fetch Location Profile
        loc = await agent_tools.get_location(session, location_id)
        if "error" in loc:
            raise ValueError(loc["error"])

        # 2. Fetch Authoritative Current Assessment
        assessment = await agent_tools.get_current_assessment(session, location_id)
        if "error" in assessment:
            raise ValueError(assessment["error"])

        # 3. Fetch Environmental Telemetry
        environment = await agent_tools.get_current_environment(session, location_id)

        # 4. Fetch Data Quality
        quality = await agent_tools.get_data_quality(session, location_id)

        # 5. Fetch Active Event if any
        event = await agent_tools.get_active_event(session, location_id=location_id)

        # 6. Fetch Regional Nearby Stations
        nearby = await agent_tools.get_nearby_risk(session, location_id=location_id)

        # 7. Fetch Field Reports & Assistance Requests (Prompt 6)
        field_reports = await agent_tools.get_field_reports(session, location_id=location_id)
        assistance_reqs = await agent_tools.get_assistance_requests(session, event_id=event.get("event_id")) if event.get("active_event") else {}

        # Build verified context
        context_data = {
            "location": loc,
            "assessment": assessment,
            "environment": environment,
            "quality": quality,
            "event": event,
            "nearby": nearby,
            "field_reports": field_reports,
            "assistance_requests": assistance_reqs,
        }

        # Add base assessment evidence
        evidence.append(
            EvidenceReference(
                evidence_type="ASSESSMENT_SCORE",
                id_reference=assessment.get("assessment_id"),
                metric="risk_score",
                value=f"{assessment.get('risk_score', 0):.1f}/100 ({assessment.get('risk_level')})",
                timestamp=assessment.get("timestamp"),
                notes=assessment.get("reason_summary")
            )
        )

        system_prompt = (
            "You are the Lead Disaster Analyst Agent for the North Eastern Region Landslide Early Warning System. "
            "You provide rigorous, evidence-backed situational intelligence to operational command officers. "
            "You synthesize both scientific sensor assessments and on-ground field observations. "
            "You MUST NEVER alter or question the scientific engine's mathematical risk score. "
            "All claims must cite verified sensor telemetry, factor contributions, and ground truth reports."
        )

        user_prompt = question or f"Provide a complete situational analysis of landslide risk and field observations for {loc.get('name')}."

        analysis = await provider.generate_structured_analysis(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evidence=evidence,
            context_data=context_data
        )

        return analysis
