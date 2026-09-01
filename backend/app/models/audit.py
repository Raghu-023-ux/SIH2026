from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from backend.app.core.database import Base


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False, index=True)
    location_id = Column(String(64), nullable=True, index=True)
    event_id = Column(String(64), nullable=True, index=True)
    question = Column(Text, nullable=True)
    data_mode = Column(String(32), nullable=False, default="LIVE")
    tool_calls_count = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, FAILED, FALLBACK
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

