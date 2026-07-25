from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TelemetryEventPayload(BaseModel):
    session_id: str
    event_type: str  # e.g., "slider_adjustment", "provenance_click", "ab_mode_switch", "likert_rating"
    mode: str = "Visual_Trust_Mode"  # "Opaque_RAG_Mode" or "Visual_Trust_Mode"
    metadata: Dict[str, Any] = {}
    timestamp: Optional[str] = None

# In-memory evaluation event store for academic reporting / telemetry export
TELEMETRY_LOGS = []

def record_telemetry_event(payload: TelemetryEventPayload) -> Dict[str, Any]:
    """
    Logs granular HCI metrics and experimental states to support Hevner's DSRM evaluation framework.
    """
    event_record = {
        "session_id": payload.session_id,
        "event_type": payload.event_type,
        "mode": payload.mode,
        "metadata": payload.metadata,
        "timestamp": payload.timestamp or datetime.utcnow().isoformat()
    }
    TELEMETRY_LOGS.append(event_record)
    return {
        "status": "SUCCESS",
        "recorded_events_count": len(TELEMETRY_LOGS),
        "event": event_record
    }

def export_telemetry_dataset() -> Dict[str, Any]:
    """
    Exports all logged telemetry events for statistical analysis (ANOVA, t-tests, effect sizes).
    """
    return {
        "total_records": len(TELEMETRY_LOGS),
        "logs": TELEMETRY_LOGS
    }