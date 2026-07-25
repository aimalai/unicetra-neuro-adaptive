from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.graph_service import fetch_node_with_provenance
from app.models.graph import NodeProvenanceResponse
from app.services.pig_validator import evaluate_3_fan_window, IntegrityReport
from app.services.rea_auditor import execute_recursive_entropy_audit, calculate_shannon_entropy
from app.services.ontological_critic import run_recursive_contradiction_probe

from app.services.telemetry_service import TelemetryEventPayload, record_telemetry_event, export_telemetry_dataset
from app.services.schema_mapper import schema_loader
from app.services.ingestion_controller import ingestion_controller

# Import the new Neural Controller service
from app.services.neural_controller import predict_sufficient_information_point, apply_rlhf_threshold_tuning

api_router = APIRouter()

class ValidationPayload(BaseModel):
    text_content: str
    threshold: float = 0.85

class REACompressPayload(BaseModel):
    text_content: str
    node_id: str = "TargetNode"
    labels: List[str] = ["Article"]

class REAMetrics(BaseModel):
    raw_tokens: int
    pruned_tokens: int
    context_compression_ratio: float
    quadratic_compute_mitigation: float
    api_cost_saved_usd: float

class REANode(BaseModel):
    node_id: str
    text_content: str
    kl_divergence: float
    ontological_weight: float

class REACompressResult(BaseModel):
    retained_nodes: List[REANode]
    metrics: REAMetrics
    shannon_entropy: float
    original_length: int
    compressed_length: int
    c2k_ratio: float
    pruned_text: str

class CriticProbePayload(BaseModel):
    target_node_id: str
    target_text: str
    parent_node_id: Optional[str] = None
    parent_text: Optional[str] = None
    js_threshold: float = 0.6

class CriticReport(BaseModel):
    is_harmonious: bool
    d_js_score: float
    status: str
    threshold_used: float

# Payloads for the Neural Phase-Gate Controller
class NeuralSIPPayload(BaseModel):
    text_content: str
    shannon_entropy: float
    confidence_threshold: float = 0.85

class NeuralSIPReport(BaseModel):
    auto_pilot_active: bool
    predicted_sip_index: int
    original_length: int
    efficiency_gain_pct: float
    policy_status: str

@api_router.get("/status", tags=["System Health"])
async def system_status():
    return {"message": "Occo AI Semantic Firewall is online and routing correctly."}

@api_router.get("/schemas", tags=["Schema Management"])
async def get_active_schemas():
    """
    Exposes the active YAML compliance schema definitions loaded dynamically.
    """
    return {"active_schema": schema_loader.schema_definition}

@api_router.post("/ingest/document", tags=["Universal Ingestion Pipeline"])
async def ingest_enterprise_document(
    file: UploadFile = File(...),
    node_type: str = Form("Article")
):
    """
    Zero-Touch Commercial Ingestion: Accepts any enterprise document (PDF, DOCX, HTML),
    parses it via format-agnostic extraction, validates it against the active YAML schema,
    and prepares it for Neo4j structural and vector indexing.
    """
    file_path = ingestion_controller.parser.upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    result = ingestion_controller.process_and_validate_document(str(file_path), node_type)
    return result

@api_router.post("/compress", response_model=REACompressResult, tags=["Semantic Auditing"])
async def run_context_compression(payload: REACompressPayload):
    """
    Executes the full Recursive Entropy Audit (REA) incorporating Cumulative KL-Divergence
    and Ontological Document Weighting.
    """
    candidate_nodes = [{
        "node_id": payload.node_id,
        "text_content": payload.text_content,
        "labels": payload.labels
    }]
    
    rea_result = execute_recursive_entropy_audit(candidate_nodes)
    baseline_entropy = calculate_shannon_entropy(payload.text_content)
    
    metrics = rea_result["metrics"]
    retained = rea_result["retained_nodes"]
    pruned_text = " ".join([n["text_content"] for n in retained]) if retained else ""
    
    return REACompressResult(
        retained_nodes=retained,
        metrics=REAMetrics(**metrics),
        shannon_entropy=baseline_entropy,
        original_length=metrics["raw_tokens"],
        compressed_length=metrics["pruned_tokens"],
        c2k_ratio=metrics["context_compression_ratio"],
        pruned_text=pruned_text
    )

@api_router.post("/validate", response_model=IntegrityReport, tags=["Parametric Integrity"])
async def run_integrity_gate(payload: ValidationPayload):
    """
    Enforces Parametric Integrity Gating (PIG) via a 3-Fan Window.
    """
    return evaluate_3_fan_window(payload.text_content, payload.threshold)

@api_router.post("/critic/probe", response_model=CriticReport, tags=["Ontological Critic"])
async def run_critic_probe(payload: CriticProbePayload):
    """
    Executes the Recursive Contradiction Probe (RCP) using Jensen-Shannon Divergence (D_JS)
    to audit semantic consistency and catch logical friction at the middleware layer.
    """
    target_node = {"node_id": payload.target_node_id, "text_content": payload.target_text}
    parent_node = {"parent_id": payload.parent_node_id, "parent_content": payload.parent_text} if payload.parent_text else None
    
    report = run_recursive_contradiction_probe(target_node, parent_node, payload.js_threshold)
    return CriticReport(**report)

@api_router.post("/neural/sip-prediction", response_model=NeuralSIPReport, tags=["Neural Controller"])
async def run_neural_sip_prediction(payload: NeuralSIPPayload):
    """
    Executes the RL Phase-Gate controller to predict the Sufficient Information Point (SIP).
    """
    token_len = len(payload.text_content.split())
    report = predict_sufficient_information_point(token_len, payload.shannon_entropy, payload.confidence_threshold)
    return NeuralSIPReport(**report)

@api_router.get(
    "/graph/node/{node_id}", 
    response_model=NodeProvenanceResponse, 
    tags=["Graph Retrieval"]
)
async def get_node_provenance(node_id: str):
    """
    Fetches node provenance from Neo4j and dynamically validates 
    its structure against the active YAML compliance schema.
    """
    provenance_data = fetch_node_with_provenance(node_id)
    
    node_type = "Article"
    if provenance_data.labels and len(provenance_data.labels) > 0:
        node_type = provenance_data.labels[0]
        
    DynamicModel = schema_loader.generate_dynamic_model(node_type)
    
    validated_payload = {
        "node_id": provenance_data.node_id,
        "text_content": provenance_data.text_content,
        "node_type": node_type
    }
    if provenance_data.parent:
        validated_payload["parent_id"] = provenance_data.parent.parent_id
        validated_payload["parent_content"] = provenance_data.parent.parent_content

    DynamicModel(**validated_payload)
    
    return provenance_data

@api_router.post("/telemetry/log", tags=["Telemetry & Evaluation"])
async def log_hci_event(payload: TelemetryEventPayload):
    """
    Logs Human-Computer Interaction (HCI) events for DREPT empirical validation.
    """
    return record_telemetry_event(payload)

@api_router.get("/telemetry/export", tags=["Telemetry & Evaluation"])
async def get_telemetry_export():
    """
    Exports accumulated HCI telemetry logs for statistical analysis.
    """
    return export_telemetry_dataset()