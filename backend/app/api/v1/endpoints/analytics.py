from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.services.disaster_playback_service import disaster_playback_service
from backend.app.services.model_calibration_service import model_calibration_service
from backend.app.schemas.analytics import (
    HistoricalIncidentSummary,
    DisasterPlaybackResponse,
    CalibrationMetricsResponse,
    BacktestRequest,
    BacktestResponse,
)
from backend.app.models.analytics import ModelEvaluationRun

router = APIRouter()


@router.get("/incidents", response_model=List[HistoricalIncidentSummary])
async def list_historical_incidents(db: AsyncSession = Depends(get_db)):
    """Lists all archived North Eastern Region disaster benchmarks for timeline playback."""
    incidents = await disaster_playback_service.get_all_incidents(db)
    await db.commit()
    return [HistoricalIncidentSummary.model_validate(i) for i in incidents]


@router.get("/incidents/{incident_id}/playback", response_model=DisasterPlaybackResponse)
async def get_incident_playback(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves 72-hour frame-by-frame disaster reconstruction and engine lead-time validation."""
    playback = await disaster_playback_service.get_playback_for_incident(db, incident_id)
    if not playback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical incident '{incident_id}' not found."
        )
    await db.commit()
    return playback


@router.get("/metrics", response_model=CalibrationMetricsResponse)
async def get_calibration_metrics():
    """Retrieves statistical model calibration metrics, confusion matrix, and lead-time distributions."""
    return model_calibration_service.get_baseline_calibration_metrics()


@router.post("/backtest", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def run_weight_backtest(
    req: BacktestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Executes a backtesting experiment on historical re-analysis data using custom factor weights."""
    result = await model_calibration_service.run_backtest(db, req)
    await db.commit()
    return result


@router.get("/history")
async def get_evaluation_run_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological archived model evaluation and backtest runs."""
    runs = await model_calibration_service.get_evaluation_history(db, limit)
    return runs
