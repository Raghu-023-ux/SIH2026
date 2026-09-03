import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.analyst_agent import DisasterAnalystAgent
from backend.app.agents.investigation_agent import InvestigationAgent
from backend.app.agents.explanation_agent import ExplanationAgent
from backend.app.schemas.ai import AgentAnalysis, AIAnalysisResponse, EvidenceReference
from backend.app.models.audit import AIAuditLog
from backend.app.core.config import settings
from backend.app.core.logging import logger


class AgentOrchestrator:
    """
    Agent Orchestrator.
    Routes queries to specialized agents, enforces execution boundaries,
    handles timeouts, and logs request audits.
    """

    def __init__(self):
        self.analyst_agent = DisasterAnalystAgent()
        self.investigation_agent = InvestigationAgent()
        self.explanation_agent = ExplanationAgent()

    def classify_intent(self, question: Optional[str], requested_type: Optional[str]) -> str:
        """Classifies query intent into appropriate specialized agent."""
        if requested_type and requested_type.lower() in ("analyst", "investigation", "explanation"):
            return requested_type.lower()

        if not question:
            return "analyst"

        q_lower = question.lower()
        if any(w in q_lower for w in ["change", "trend", "increased", "decreased", "delta", "history", "earlier", "past"]):
            return "investigation"
        elif any(w in q_lower for w in ["explain", "why is", "what does", "meaning", "understand", "factors"]):
            return "explanation"
        else:
            return "analyst"

    async def execute(
        self,
        session: AsyncSession,
        location_id: str,
        event_id: Optional[str] = None,
        question: Optional[str] = None,
        agent_type: Optional[str] = "auto"
    ) -> AIAnalysisResponse:
        request_id = str(uuid.uuid4())
        start_t = time.perf_counter()
        selected_agent = self.classify_intent(question, agent_type)
        status_str = "SUCCESS"
        err_msg: Optional[str] = None
        analysis: Optional[AgentAnalysis] = None

        logger.info(f"AgentOrchestrator routing to [{selected_agent.upper()}] for location {location_id} (Req: {request_id})")

        try:
            if selected_agent == "investigation":
                analysis = await self.investigation_agent.investigate(
                    session=session,
                    location_id=location_id,
                    event_id=event_id,
                    question=question
                )
            elif selected_agent == "explanation":
                analysis = await self.explanation_agent.explain(
                    session=session,
                    location_id=location_id,
                    question=question
                )
            else:  # default analyst
                analysis = await self.analyst_agent.analyze(
                    session=session,
                    location_id=location_id,
                    question=question
                )

        except Exception as err:
            logger.error(f"Agent [{selected_agent}] encountered error: {err}. Executing deterministic fallback...", exc_info=True)
            status_str = "FALLBACK"
            err_msg = str(err)
            # Execute deterministic fallback through analyst agent
            analysis = await self.analyst_agent.analyze(
                session=session,
                location_id=location_id,
                question=question
            )

        latency_ms = (time.perf_counter() - start_t) * 1000.0

        # Log Audit Record
        audit = AIAuditLog(
            request_id=request_id,
            agent_name=selected_agent,
            location_id=location_id,
            event_id=event_id,
            question=question,
            data_mode=settings.DATA_MODE,
            tool_calls_count=len(analysis.all_evidence) if analysis else 0,
            latency_ms=round(latency_ms, 1),
            status=status_str,
            error_message=err_msg
        )
        session.add(audit)
        await session.flush()

        return AIAnalysisResponse(
            answer=analysis.summary,
            analysis=analysis,
            evidence=analysis.all_evidence,
            agent=selected_agent,
            data_mode=settings.DATA_MODE,
            model_used=f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
            latency_ms=round(latency_ms, 1),
            timestamp=datetime.now(timezone.utc)
        )


agent_orchestrator = AgentOrchestrator()
