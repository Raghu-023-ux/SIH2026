from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.models.audit import AIAuditLog
from backend.app.services.location_service import LocationService
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.schemas.ai import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIAuditLogResponse,
)
from backend.app.core.logging import logger

router = APIRouter()


@router.post("/analyze", response_model=AIAnalysisResponse)
async def run_ai_analysis(
    request: AIAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes specialized Agentic AI analysis.
    Interprets scientific risk metrics, evaluates risk drivers, and cites verified telemetry evidence.
    """
    # 1. Resolve Location ID
    loc_id = request.location_id
    if not loc_id:
        # Default to first monitored station if not specified
        locations = await LocationService.get_all_locations(db)
        if not locations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No locations available for analysis."
            )
        loc_id = locations[0].id

    # 2. Validate Location exists
    loc = await LocationService.get_location_by_id(db, loc_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{loc_id}' not found."
        )

    try:
        response = await agent_orchestrator.execute(
            session=db,
            location_id=loc.id,
            event_id=request.event_id,
            question=request.question,
            agent_type=request.agent_type
        )
        await db.commit()
        return response

    except Exception as err:
        logger.error(f"AI Analysis failed: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Analysis execution failed: {str(err)}"
        )


@router.post("/explain-assessment", response_model=AIAnalysisResponse)
async def explain_assessment(
    request: AIAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Convenience endpoint for Explanation Agent.
    Translates mathematical risk matrices into actionable operational prose.
    """
    request.agent_type = "explanation"
    if not request.question:
        request.question = "Explain the primary physical and terrain factors determining this risk score."
    return await run_ai_analysis(request, db)


@router.post("/investigate-change", response_model=AIAnalysisResponse)
async def investigate_change(
    request: AIAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Convenience endpoint for Investigation Agent.
    Diagnoses temporal deltas, precipitation surges, and factor evolution.
    """
    request.agent_type = "investigation"
    if not request.question:
        request.question = "Investigate what factors changed to cause this hazard trajectory."
    return await run_ai_analysis(request, db)


@router.get("/audit-logs", response_model=List[AIAuditLogResponse])
async def get_ai_audit_logs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves chronological audit trail of agent executions and tool call counts.
    """
    stmt = select(AIAuditLog).order_by(AIAuditLog.timestamp.desc()).limit(limit)
    res = await db.execute(stmt)
    logs = list(res.scalars().all())

    return [
        AIAuditLogResponse(
            id=l.id,
            timestamp=l.timestamp,
            agent_name=l.agent_name,
            request_id=l.request_id,
            location_id=l.location_id,
            event_id=l.event_id,
            question=l.question,
            data_mode=l.data_mode,
            tool_calls_count=l.tool_calls_count,
            latency_ms=l.latency_ms,
            status=l.status,
            error_message=l.error_message
        )
        for l in logs
    ]
