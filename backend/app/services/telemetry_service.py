from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TelemetryEventPayload(BaseModel):
    session_id: str
    event_type: str  # e.g., "slider_adjustment", "provenance_click", "ab_mode_switch", "likert_rating", "graph_search"
    mode: str = "Visual_Trust_Mode"  # "Opaque_RAG_Mode" or "Visual_Trust_Mode"
    metadata: Dict[str, Any] = {}
    timestamp: Optional[str] = None

# In-memory evaluation event store for academic reporting / telemetry export
TELEMETRY_LOGS = []

# Account-Level Aggregation State
ACCOUNT_STATE = {
    "total_queries": 0,
    "total_tokens_averted": 0,
    "total_cost_saved": 0.0
}

def record_telemetry_event(payload: TelemetryEventPayload) -> Dict[str, Any]:
    """
    Logs granular HCI metrics and updates Account-Level cumulative economic state.
    """
    event_record = {
        "session_id": payload.session_id,
        "event_type": payload.event_type,
        "mode": payload.mode,
        "metadata": payload.metadata,
        "timestamp": payload.timestamp or datetime.utcnow().isoformat()
    }
    TELEMETRY_LOGS.append(event_record)
    
    # Update Account Aggregates if this was a search/audit event
    if payload.event_type == "graph_search" and "economics" in payload.metadata:
        ACCOUNT_STATE["total_queries"] += 1
        ACCOUNT_STATE["total_tokens_averted"] += payload.metadata["economics"].get("tokens_averted", 0)
        ACCOUNT_STATE["total_cost_saved"] += payload.metadata["economics"].get("api_cost_saved_usd", 0.0)

    return {
        "status": "SUCCESS",
        "recorded_events_count": len(TELEMETRY_LOGS),
        "account_aggregate": ACCOUNT_STATE,
        "event": event_record
    }

def export_telemetry_dataset() -> Dict[str, Any]:
    """
    Exports all logged telemetry events and the cumulative account savings.
    """
    return {
        "account_aggregate": ACCOUNT_STATE,
        "total_records": len(TELEMETRY_LOGS),
        "logs": TELEMETRY_LOGS
    }