# engine_schema.py
from typing import Any, TypedDict


class LegalNode(TypedDict):
    id: str  # Example: "dsa_art_14"
    node_type: str  # Classification: "Article", "Recital", "Definition", "Section"
    content: str  # Extracts from 'full_text' or 'text' properties
    regulation: str  # Identifier: "eu_ai_act" or "dsa"
    metadata: dict[str, Any]  # Key-value pairs like {"chapter": "IV", "section": "2", "score": 0.88}
    entropy_score: float | None
    kl_score: float | None  # Proprietary Field: Tracks Information Gain via Recursive Audit


class GraphState(TypedDict):
    query: str
    cypher_intent: dict[str, Any]
    retrieved_nodes: list[LegalNode]
    links_found: list[dict[str, Any]]
    pruned_context: list[LegalNode]
    reasoning_trace: list[str]
    final_answer: str
    hops: int
    is_accurate: bool
    # Metrics preserved for scientific reporting and token reduction tracking
    metrics: dict[str, Any]


mock_retrieved_nodes = []  # Fallback payload