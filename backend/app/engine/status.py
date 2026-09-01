from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.core.config import settings


class EngineStatusTracker:
    """
    Centralized runtime status tracker for the Disaster Intelligence Assessment Engine.
    Tracks live execution status, last successful run, execution duration, and errors.
    """

    def __init__(self):
        self._status: str = "ONLINE"  # "ONLINE", "RUNNING", "IDLE", "ERROR", "OFFLINE"
        self._last_run_at: Optional[datetime] = None
        self._last_success_at: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._locations_evaluated: int = 0
        self._active_events_count: int = 0
        self._highest_risk_score: float = 0.0
        self._highest_risk_level: str = "LOW"
        self._execution_duration_ms: float = 0.0
        self._total_runs_count: int = 0
        self._scheduler_enabled: bool = True
        self._scheduler_interval_seconds: int = 30

    def mark_running(self):
        self._status = "RUNNING"
        self._last_run_at = datetime.now(timezone.utc)

    def record_success(
        self,
        locations_count: int,
        active_events: int,
        highest_score: float,
        highest_level: str,
        duration_ms: float
    ):
        now = datetime.now(timezone.utc)
        self._status = "ONLINE"
        self._last_run_at = now
        self._last_success_at = now
        self._last_error = None
        self._locations_evaluated = locations_count
        self._active_events_count = active_events
        self._highest_risk_score = highest_score
        self._highest_risk_level = highest_level
        self._execution_duration_ms = round(duration_ms, 2)
        self._total_runs_count += 1

    def record_error(self, error_message: str, duration_ms: float = 0.0):
        self._status = "ERROR"
        self._last_run_at = datetime.now(timezone.utc)
        self._last_error = error_message
        self._execution_duration_ms = round(duration_ms, 2)

    def get_status_payload(self) -> Dict[str, Any]:
        return {
            "engine_status": self._status,
            "engine_version": settings.ENGINE_VERSION,
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "data_mode": settings.DATA_MODE,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "last_success_at": self._last_success_at.isoformat() if self._last_success_at else None,
            "last_error": self._last_error,
            "locations_evaluated": self._locations_evaluated,
            "active_events_count": self._active_events_count,
            "highest_risk_score": self._highest_risk_score,
            "highest_risk_level": self._highest_risk_level,
            "execution_duration_ms": self._execution_duration_ms,
            "total_runs_count": self._total_runs_count,
            "scheduler": {
                "enabled": self._scheduler_enabled,
                "interval_seconds": self._scheduler_interval_seconds,
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


engine_status_tracker = EngineStatusTracker()
