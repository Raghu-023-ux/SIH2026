from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.tools import agent_tools
from backend.app.agents.providers import get_llm_provider
from backend.app.schemas.ai import AgentAnalysis, EvidenceReference
from backend.app.core.config import settings


class InvestigationAgent:
    """
    Investigation Agent.
    Investigates WHY an event escalated, changed, or triggered,
    analyzing temporal factor deltas, precipitation surge times,
    pore saturation shifts, regional cluster agreement, and on-ground field observations.
    """

    def __init__(self):
        self.provider = get_llm_provider()

    async def investigate(
        self,
        session: AsyncSession,
        location_id: str,
        event_id: Optional[str] = None,
        question: Optional[str] = None
    ) -> AgentAnalysis:
        evidence: List[EvidenceReference] = []

        # 1. Fetch Location Profile
        loc = await agent_tools.get_location(session, location_id)
        if "error" in loc:
            raise ValueError(loc["error"])

        # 2. Fetch Authoritative Current Assessment
        assessment = await agent_tools.get_current_assessment(session, location_id)
        if "error" in assessment:
            raise ValueError(assessment["error"])

        # 3. Fetch Assessment History for Temporal Comparison
        history = await agent_tools.get_assessment_history(session, location_id, limit=5)

        # 4. Fetch Event & Timeline
        event = await agent_tools.get_active_event(session, location_id=location_id, event_id=event_id)
        timeline = await agent_tools.get_event_timeline(session, event["event_id"]) if event.get("active_event") else {}

        # 5. Fetch Environmental & Regional Data
        environment = await agent_tools.get_current_environment(session, location_id)
        nearby = await agent_tools.get_nearby_risk(session, location_id=location_id)
        quality = await agent_tools.get_data_quality(session, location_id)

        # 6. Fetch Field Intelligence
        field_reports = await agent_tools.get_field_reports(session, location_id=location_id, event_id=event.get("event_id"))
        assistance_reqs = await agent_tools.get_assistance_requests(session, event_id=event.get("event_id")) if event.get("active_event") else {}

        context_data = {
            "location": loc,
            "assessment": assessment,
            "history": history,
            "event": event,
            "timeline": timeline,
            "environment": environment,
            "nearby": nearby,
            "quality": quality,
            "field_reports": field_reports,
            "assistance_requests": assistance_reqs,
        }

        # Add base assessment evidence
        evidence.append(
            EvidenceReference(
                evidence_type="CURRENT_ASSESSMENT",
                id_reference=assessment.get("assessment_id"),
                metric="risk_score",
                value=f"{assessment.get('risk_score', 0):.1f} ({assessment.get('risk_level')})",
                timestamp=assessment.get("timestamp")
            )
        )

        system_prompt = (
            "You are the Lead Hazard Investigation Agent for the NER Landslide Early Warning System. "
            "Your objective is to diagnose the precise causes of hazard evolution and score changes over time. "
            "You evaluate factor deltas, precipitation surges, pore saturation transitions, and field ground observations. "
            "Every explanation must be grounded strictly in chronological data."
        )

        user_prompt = question or f"Investigate recent risk changes, triggers, and field reports at {loc.get('name')}."

        analysis = await self.provider.generate_structured_analysis(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evidence=evidence,
            context_data=context_data
        )

        return analysis
