from fastapi import APIRouter
from pydantic import BaseModel
import math
from collections import Counter
from app.services.schema_mapper import dynamic_models
from app.services.entropy_audit import calculate_context_compression
from app.services.graph_service import fetch_node_with_provenance
from app.models.audit import AuditRequest, AuditPayload, CompressionResult
from app.models.graph import NodeProvenanceResponse

# Import the new PIG Validator
from app.services.pig_validator import evaluate_3_fan_window, IntegrityReport

api_router = APIRouter()

class ValidationPayload(BaseModel):
    text_content: str

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    probabilities = [n_x / len(text) for x, n_x in Counter(text).items()]
    return -sum(p * math.log2(p) for p in probabilities)

@api_router.get("/status", tags=["System Health"])
async def system_status():
    return {"message": "Occo AI Semantic Firewall is online and routing correctly."}

@api_router.get("/schemas", tags=["Schema Management"])
async def get_active_schemas():
    schema_definitions = {
        name: model.model_json_schema() 
        for name, model in dynamic_models.items()
    }
    return {"active_schemas": schema_definitions}

@api_router.post("/audit", tags=["Semantic Auditing"])
async def run_entropy_audit(payload: AuditRequest):
    result = calculate_context_compression(
        original_chunks=payload.chunks,
        min_entropy_threshold=payload.min_entropy_threshold
    )
    return result

@api_router.post("/compress", response_model=CompressionResult, tags=["Semantic Auditing"])
async def run_context_compression(payload: AuditPayload):
    entropy = calculate_entropy(payload.text_content)
    words = payload.text_content.split()
    pruned = " ".join([word for word in words if len(word) > 4])
    c2k = len(pruned) / len(payload.text_content) if len(payload.text_content) > 0 else 0

    return CompressionResult(
        shannon_entropy=round(entropy, 4),
        original_length=len(payload.text_content),
        compressed_length=len(pruned),
        c2k_ratio=round(c2k, 4),
        pruned_text=pruned
    )

@api_router.post("/validate", response_model=IntegrityReport, tags=["Parametric Integrity"])
async def run_integrity_gate(payload: ValidationPayload):
    """
    Enforces Parametric Integrity Gating (PIG) via a 3-Fan Window.
    """
    return evaluate_3_fan_window(payload.text_content)

@api_router.get(
    "/graph/node/{node_id}", 
    response_model=NodeProvenanceResponse, 
    tags=["Graph Retrieval"]
)
async def get_node_provenance(node_id: str):
    return fetch_node_with_provenance(node_id)