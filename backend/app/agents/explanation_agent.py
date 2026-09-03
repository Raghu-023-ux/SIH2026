from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.tools import agent_tools
from backend.app.agents.providers import get_llm_provider
from backend.app.schemas.ai import AgentAnalysis, EvidenceReference
from backend.app.core.config import settings


class ExplanationAgent:
    """
    Explanation Agent.
    Translates complex multi-signal risk matrices and mathematical factor contributions
    into intuitive, high-clarity operational prose for duty officers and field commanders.
    """

    def __init__(self, provider: Optional[Any] = None):
        self._custom_provider = provider

    async def explain(
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

        # 3. Fetch Environmental Telemetry & Data Quality
        environment = await agent_tools.get_current_environment(session, location_id)
        quality = await agent_tools.get_data_quality(session, location_id)
        event = await agent_tools.get_active_event(session, location_id=location_id)

        context_data = {
            "location": loc,
            "assessment": assessment,
            "environment": environment,
            "quality": quality,
            "event": event,
        }

        # Evidence references
        evidence.append(
            EvidenceReference(
                evidence_type="ASSESSMENT_EXPLANATION",
                id_reference=assessment.get("assessment_id"),
                metric="risk_level_score",
                value=f"{assessment.get('risk_score', 0):.1f}/100 ({assessment.get('risk_level')})",
                timestamp=assessment.get("timestamp")
            )
        )

        system_prompt = (
            "You are the Lead Hazard Explanation Agent for the NER Landslide Early Warning System. "
            "Your objective is to translate complex mathematical factor scores and signal agreement metrics "
            "into clear, accessible, and actionable operational prose. "
            "Do NOT use vague jargon. Directly state the top contributing physical factors and their measured values."
        )

        user_prompt = question or f"Explain why {loc.get('name')} has been assessed at risk level {assessment.get('risk_level')}."

        analysis = await provider.generate_structured_analysis(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evidence=evidence,
            context_data=context_data
        )

        return analysis
