import time
import pandas as pd
import re
import os
import sys
import numpy as np
from typing import List, Dict, Any, Set, Tuple
from sentence_transformers import SentenceTransformer, CrossEncoder
from langdetect import detect, DetectorFactory

# Fallback wrapper for rank_bm25 if not installed in the local environment
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    print("Notice: 'rank_bm25' package not found. Using native term-frequency fallback for sparse retrieval.")

# Set seed for deterministic language detection
DetectorFactory.seed = 0

# Ensure the script can find your 'app' modules for Neo4j
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.neo4j import neo4j_connector

print("Loading embedding models & cross-encoders (this may take a moment)...")
# Base embedding model used by both pipelines for initial recall, Dense REA, and Semantic Fidelity
dense_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# Industry standard heavy Re-Ranker for the Baseline Pipeline
reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Warm up PyTorch engine
print("Warming up inference engine...")
_ = dense_model.encode("warmup query")

# Structured Enterprise Evaluation Dataset across 4 Commercial Stress-Test Categories
TEST_DATASET = [
    # 1. Exact Match Queries
    {
        "query": "What are the specific data retention requirements for high-risk AI system logs?",
        "category": "Exact Match"
    },
    {
        "query": "What is the maximum administrative fine for using prohibited AI systems under Article 5?",
        "category": "Exact Match"
    },
    # 2. Verbose / Padded Queries
    {
        "query": "Could you please tell me all the various multifaceted approaches and definitions regarding biometric categorization systems?",
        "category": "Verbose Padded"
    },
    {
        "query": "I am looking for a detailed synthesis explaining the responsibilities of a notified body under the new European AI regulation.",
        "category": "Verbose Padded"
    },
    # 3. Adversarial / Out-of-Domain Queries (Tests Adaptive Floor Rejection)
    {
        "query": "What are the tax filing deadlines and income deduction brackets for corporate entities in Switzerland?",
        "category": "Out-of-Domain Adversarial"
    },
    {
        "query": "How do I optimize a Python script using multithreading and GPU CUDA drivers?",
        "category": "Out-of-Domain Adversarial"
    },
    # 4. Contradictory / Friction Queries (Tests D_JS Ontological Critic Probe)
    {
        "query": "Do general-purpose AI models have the exact same administrative fine thresholds as prohibited AI practices?",
        "category": "Contradictory Friction"
    },
    {
        "query": "How does the framework handle fundamental rights impact assessments when data protection impact assessments are already complete?",
        "category": "Contradictory Friction"
    }
]

# ---------------------------------------------------------------------------
# RECALL & HYBRID SEARCH ENGINE (BM25 + Dense + RRF)
# ---------------------------------------------------------------------------

def fetch_raw_candidates(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches candidate document chunks from Neo4j vector index."""
    query_vector = dense_model.encode(query).tolist()
    driver = neo4j_connector.get_driver()
    
    cypher = """
    CALL db.index.vector.queryNodes('chunkEmbedding', $limit, $query_vector)
    YIELD node AS c, score
    OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(c)
    RETURN c.node_id AS node_id,
           c.text_content AS text_content,
           labels(c) AS labels,
           score
    """
    candidates = []
    try:
        with driver.session() as session:
            records = session.run(cypher, query_vector=query_vector, limit=limit)
            for r in records:
                candidates.append({
                    "node_id": r["node_id"],
                    "text_content": r["text_content"],
                    "labels": r["labels"],
                    "vector_score": float(r["score"])
                })
    except Exception as e:
        print(f"Database error during candidate recall: {e}")
    return candidates

def compute_rrf_hybrid_recall(query: str, candidates: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
    """
    ITEM 1: Hybrid Search (BM25 + Dense Vectors) with Reciprocal Rank Fusion (RRF).
    Calculates RRF Score = 1/(k + Rank_dense) + 1/(k + Rank_bm25).
    """
    if not candidates:
        return []

    # 1. Rank by Dense Vector Similarity
    dense_sorted = sorted(candidates, key=lambda x: x.get("vector_score", 0.0), reverse=True)
    dense_ranks = {c["node_id"]: idx + 1 for idx, c in enumerate(dense_sorted)}

    # 2. Rank by BM25 Lexical Matching
    corpus = [c["text_content"] for c in candidates]
    tokenized_corpus = [re.findall(r'\w+', doc.lower()) for doc in corpus]
    tokenized_query = re.findall(r'\w+', query.lower())

    if HAS_BM25:
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(tokenized_query)
    else:
        # Fallback term frequency scorer if rank_bm25 is missing
        bm25_scores = []
        query_set = set(tokenized_query)
        for doc_tokens in tokenized_corpus:
            score = sum(1 for t in doc_tokens if t in query_set)
            bm25_scores.append(score)

    bm25_tuples = [(candidates[i]["node_id"], bm25_scores[i]) for i in range(len(candidates))]
    bm25_sorted = sorted(bm25_tuples, key=lambda x: x[1], reverse=True)
    bm25_ranks = {node_id: idx + 1 for idx, (node_id, _) in enumerate(bm25_sorted)}

    # 3. Compute Reciprocal Rank Fusion (RRF)
    for c in candidates:
        nid = c["node_id"]
        r_dense = dense_ranks.get(nid, len(candidates))
        r_bm25 = bm25_ranks.get(nid, len(candidates))
        c["rrf_score"] = (1.0 / (k + r_dense)) + (1.0 / (k + r_bm25))

    # Sort candidates by combined RRF score
    hybrid_candidates = sorted(candidates, key=lambda x: x["rrf_score"], reverse=True)
    return hybrid_candidates

def filter_chunks_by_language(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filters candidate chunks to match the language of the query."""
    try:
        query_lang = detect(query)
    except Exception:
        query_lang = 'en'  
        
    filtered = []
    for c in candidates:
        text = c.get("text_content", "")
        if not text.strip():
            continue
        try:
            chunk_lang = detect(text)
            if chunk_lang == query_lang:
                filtered.append(c)
        except Exception:
            filtered.append(c) 
            
    return filtered if filtered else candidates 

def decompose_chunks_to_sentences(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Decomposes coarse-grained document chunks into sentence-level atomic nodes."""
    sentence_nodes = []
    for c in candidates:
        text = c.get("text_content", "")
        labels = c.get("labels", ["Article"])
        chunk_id = c.get("node_id", "node")
        
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
        
        for idx, s in enumerate(sentences):
            sentence_nodes.append({
                "node_id": f"{chunk_id}_s{idx}",
                "text_content": s,
                "labels": labels
            })
            
    return sentence_nodes if sentence_nodes else candidates

# ---------------------------------------------------------------------------
# MATHEMATICAL IP & ACCURACY EVALUATORS
# ---------------------------------------------------------------------------

def calculate_ontological_weight(node_labels: List[str], structural_depth: int = -1) -> float:
    """
    Document-Agnostic Ontological Weighting.
    Uses universal hierarchy tags (H1, H2, Title) or explicit tree depth, 
    making the algorithm blind to the specific domain (Legal, Medical, Technical).
    """
    # 1. Explicit Depth Evaluation (0 = Root, 1 = Section, 2 = Subsection, 3+ = Body)
    if structural_depth == 0:
        return 0.9
    elif structural_depth == 1:
        return 0.7
    elif structural_depth == 2:
        return 0.5
    elif structural_depth >= 3:
        return 0.3
        
    # 2. Fallback to universal label matching if depth isn't explicitly passed
    labels_upper = [str(l).upper() for l in node_labels]
    
    # Depth 0/1 Equivalents (Major Headers)
    if any(l in labels_upper for l in ["H1", "TITLE", "ARTICLE", "CHAPTER", "ROOT", "ABSTRACT"]):
        return 0.9
    # Depth 2 Equivalents (Sub-headers)
    elif any(l in labels_upper for l in ["H2", "SECTION", "RECITAL", "SUBHEADER", "METHODOLOGY"]):
        return 0.5
        
    # Depth 3+ Equivalents
    return 0.3 # Default leaf node / Standard paragraph

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates cosine similarity between two dense vectors."""
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm > 0 else 0.0

def calculate_jensen_shannon_divergence(p_vec: np.ndarray, q_vec: np.ndarray) -> float:
    """
    ITEM 4: Jensen-Shannon Divergence Probe (D_JS).
    Measures semantic conflict/friction between two retained nodes in vector space.
    D_JS = 0.5 * D_KL(P||M) + 0.5 * D_KL(Q||M)
    In normalized dense vector space, JS divergence correlates to angular divergence.
    """
    p_norm = p_vec / (np.linalg.norm(p_vec) + 1e-10)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-10)
    m_vec = 0.5 * (p_norm + q_norm)
    
    # Angular divergence mapping for continuous dense distributions
    cos_pm = cosine_similarity(p_norm, m_vec)
    cos_qm = cosine_similarity(q_norm, m_vec)
    
    d_kl_pm = float(np.abs(1.0 - cos_pm))
    d_kl_qm = float(np.abs(1.0 - cos_qm))
    
    d_js = 0.5 * d_kl_pm + 0.5 * d_kl_qm
    return round(d_js, 4)

def calculate_semantic_fidelity(baseline_payload: str, occo_payload: str) -> float:
    """Calculates vector similarity between full Baseline context and Occo's pruned context."""
    if not baseline_payload.strip() or not occo_payload.strip():
        return 0.0
    v_base = dense_model.encode(baseline_payload)
    v_occo = dense_model.encode(occo_payload)
    sim = cosine_similarity(v_base, v_occo)
    return round(sim * 100.0, 2)

def extract_critical_entities(text: str) -> Set[str]:
    """Extracts high-stakes legal entities: fines, citations, percentages, durations, and dates."""
    patterns = [
        r'EUR\s+\d+(?:\s+\d+)*',                                    # Fines (e.g., EUR 35 000 000)
        r'\d+\s*%',                                                 # Percentages (e.g., 7 %)
        r'\b(?:six|twelve|\d+)\s+(?:months|years|days|weeks)\b',    # Durations (e.g., six months)
        r'\b(?:Article|Recital|Section|Chapter)\s+\d+(?:\(\d+\))*', # Citations (e.g., Article 12(1))
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b' # Dates
    ]
    
    entities = set()
    for p in patterns:
        matches = re.findall(p, text, flags=re.IGNORECASE)
        for m in matches:
            entities.add(m.strip().lower())
    return entities

def calculate_entity_retention(baseline_payload: str, occo_payload: str) -> float:
    """Verifies what percentage of key baseline citations, fines, and dates survived REA pruning."""
    baseline_entities = extract_critical_entities(baseline_payload)
    if not baseline_entities:
        return 100.0  
        
    occo_payload_lower = occo_payload.lower()
    retained_count = sum(1 for e in baseline_entities if e in occo_payload_lower)
    return round((retained_count / len(baseline_entities)) * 100.0, 2)

# ---------------------------------------------------------------------------
# PIPELINE A: ENTERPRISE HYBRID BASELINE
# ---------------------------------------------------------------------------

def pipeline_baseline(query: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ENTERPRISE GOLD STANDARD:
    Hybrid Search (BM25 + Dense RRF) + Cross-Encoder Re-Ranking (Top 3 full chunks).
    """
    start_time = time.perf_counter()
    
    if not candidates:
        return {"latency_ms": 0, "tokens": 0, "payload": ""}

    # 1. Apply Hybrid RRF Ranking
    hybrid_candidates = compute_rrf_hybrid_recall(query, candidates)

    # 2. Pair query with each hybrid candidate text for Cross-Encoder re-ranking
    pairs = [[query, c["text_content"]] for c in hybrid_candidates]
    scores = reranker_model.predict(pairs)
    
    for i, c in enumerate(hybrid_candidates):
        c["rerank_score"] = scores[i]
        
    ranked_candidates = sorted(hybrid_candidates, key=lambda x: x["rerank_score"], reverse=True)
    
    # Return top 3 full unpruned chunks
    top_3 = ranked_candidates[:3]
    payload = " ".join([c["text_content"] for c in top_3])
    tokens = len(payload.split())
    
    latency = (time.perf_counter() - start_time) * 1000
    
    return {
        "latency_ms": round(latency, 2),
        "tokens": tokens,
        "payload": payload
    }

# ---------------------------------------------------------------------------
# PIPELINE B: OCCO IP (ADAPTIVE FLOOR + DENSE REA + D_JS CRITIC PROBE)
# ---------------------------------------------------------------------------

def execute_query_guided_dense_rea(
    query: str,
    candidate_nodes: List[Dict[str, Any]],
    base_query_threshold: float = 0.50,
    base_novelty_threshold: float = 0.75,
    adaptive_floor: float = 0.45,
    js_friction_threshold: float = 0.18
) -> Dict[str, Any]:
    """
    OCCO IP CORE:
    1. Adaptive Floor Gating (Out-of-Domain Interception)
    2. Query-Guided Dense REA (Dual-Gate Information Density Pruning)
    3. D_JS Ontological Critic Probe (Contradiction Friction Detection)
    """
    retained_nodes = []
    retained_embeddings = []
    raw_token_count = 0
    pruned_token_count = 0
    friction_events = 0
    
    texts = [node.get("text_content", "") for node in candidate_nodes]
    if not texts:
        return {
            "retained_nodes": [],
            "status": "EMPTY",
            "friction_events": 0,
            "metrics": {"raw_tokens": 0, "pruned_tokens": 0, "context_compression_ratio": 0.0}
        }
        
    query_emb = dense_model.encode(query)
    embeddings = dense_model.encode(texts)
    
    # ITEM 3: ADAPTIVE SIMILARITY FLOOR CHECK (Out-of-Domain Interception)
    all_query_sims = [cosine_similarity(emb, query_emb) for emb in embeddings]
    max_query_sim = max(all_query_sims) if all_query_sims else 0.0
    
    if max_query_sim < adaptive_floor:
        # Intercept garbage/out-of-domain query immediately ("Honest Ignorance")
        return {
            "retained_nodes": [],
            "status": "REJECTED_OUT_OF_DOMAIN",
            "friction_events": 0,
            "metrics": {"raw_tokens": sum(len(t.split()) for t in texts), "pruned_tokens": 0, "context_compression_ratio": 0.0}
        }
    
    for idx, node in enumerate(candidate_nodes):
        text = texts[idx]
        labels = node.get("labels", ["Article"])
        emb = embeddings[idx]
        
        node_token_length = len(text.split())
        raw_token_count += node_token_length
        
        weight = calculate_ontological_weight(labels)
        
        # GATE 1: Query Relevance Gating
        query_sim = all_query_sims[idx]
        min_required_relevance = base_query_threshold * (1.5 - weight)
        
        if query_sim < min_required_relevance:
            continue 
            
        # GATE 2: Semantic Novelty Gating
        if not retained_embeddings:
            novelty = 1.0
        else:
            max_sim = max([cosine_similarity(emb, r_emb) for r_emb in retained_embeddings])
            novelty = 1.0 - max_sim
            
        required_novelty = base_novelty_threshold * (1.5 - weight)
        
        if novelty >= required_novelty:
            # ITEM 4: Jensen-Shannon Divergence Probe (D_JS Contradiction Check)
            if retained_embeddings:
                for r_emb in retained_embeddings:
                    d_js = calculate_jensen_shannon_divergence(emb, r_emb)
                    if d_js >= js_friction_threshold:
                        friction_events += 1 # Flag logical friction point between retrieved clauses
            
            retained_nodes.append({
                "node_id": node.get("node_id"),
                "text_content": text,
                "query_relevance": round(query_sim, 4),
                "semantic_novelty": round(novelty, 4),
                "ontological_weight": weight
            })
            retained_embeddings.append(emb)
            pruned_token_count += node_token_length

    ccr = round(raw_token_count / max(1, pruned_token_count), 2)

    return {
        "retained_nodes": retained_nodes,
        "status": "PASSED",
        "friction_events": friction_events,
        "metrics": {
            "raw_tokens": raw_token_count,
            "pruned_tokens": pruned_token_count,
            "context_compression_ratio": ccr
        }
    }

def pipeline_occo(query: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """OCCO IP Pipeline Execution Wrapper"""
    start_time = time.perf_counter()
    
    if not candidates:
        return {"latency_ms": 0, "tokens": 0, "payload": "", "status": "EMPTY", "friction_events": 0}

    aligned_candidates = filter_chunks_by_language(query, candidates)
    sentence_candidates = decompose_chunks_to_sentences(aligned_candidates)
    
    # Run Query-Guided Dense REA with Adaptive Floor & D_JS Critic Probe
    rea_result = execute_query_guided_dense_rea(
        query=query,
        candidate_nodes=sentence_candidates,
        base_query_threshold=0.50,
        base_novelty_threshold=0.75,
        adaptive_floor=0.45,
        js_friction_threshold=0.18
    )
    
    if rea_result["status"] == "REJECTED_OUT_OF_DOMAIN":
        payload = "[REJECTED: Out-of-Domain Query Intercepted by Adaptive Floor]"
        tokens = 0
    else:
        payload = " ".join([n["text_content"] for n in rea_result["retained_nodes"]])
        tokens = len(payload.split()) if payload.strip() else 0
    
    latency = (time.perf_counter() - start_time) * 1000
    
    return {
        "latency_ms": round(latency, 2),
        "tokens": tokens,
        "payload": payload,
        "status": rea_result["status"],
        "friction_events": rea_result.get("friction_events", 0)
    }

# ---------------------------------------------------------------------------
# BENCHMARK RUNNER & COMPARATOR
# ---------------------------------------------------------------------------

def run_study():
    results = []
    
    print("\nStarting Commercial Benchmark Study (Enterprise Hybrid vs. Occo IP)...")
    print("=" * 70)
    
    for i, item in enumerate(TEST_DATASET):
        query = item["query"]
        category = item["category"]
        print(f"\nEvaluating Query {i+1}/{len(TEST_DATASET)} [{category}]:")
        print(f"  '{query[:65]}...'")
        
        # 1. Fetch Raw Recall Set from Neo4j Vector Index
        candidates = fetch_raw_candidates(query, limit=15)
        
        # 2. Run Pipeline A: Enterprise Hybrid Baseline (BM25 + Dense RRF + Cross-Encoder)
        baseline_metrics = pipeline_baseline(query, candidates)
        
        # 3. Run Pipeline B: Occo IP (Adaptive Floor + Dense REA + D_JS Critic Probe)
        occo_metrics = pipeline_occo(query, candidates)
        
        # 4. Calculate Efficiency Gains & Accuracy Metrics
        if occo_metrics["status"] == "REJECTED_OUT_OF_DOMAIN":
            c2k_ratio = round(baseline_metrics["tokens"] / 1.0, 2)  # Avoid division by 0 on rejection
            fidelity_score = 0.0
            entity_retention = 0.0
        else:
            c2k_ratio = round(baseline_metrics["tokens"] / max(1, occo_metrics["tokens"]), 2)
            fidelity_score = calculate_semantic_fidelity(baseline_metrics["payload"], occo_metrics["payload"])
            entity_retention = calculate_entity_retention(baseline_metrics["payload"], occo_metrics["payload"])
            
        latency_diff = round(baseline_metrics["latency_ms"] - occo_metrics["latency_ms"], 2)
        
        results.append({
            "Query": query,
            "Category": category,
            "Status": occo_metrics["status"],
            "Baseline_Tokens": baseline_metrics["tokens"],
            "Occo_Tokens": occo_metrics["tokens"],
            "C2K_Ratio": c2k_ratio,
            "Semantic_Fidelity_Pct": fidelity_score,
            "Entity_Retention_Pct": entity_retention,
            "Friction_Events_Flagged": occo_metrics["friction_events"],
            "Baseline_Latency_ms": baseline_metrics["latency_ms"],
            "Occo_Latency_ms": occo_metrics["latency_ms"],
            "Latency_Saved_ms": latency_diff,
            "Baseline_Payload": baseline_metrics["payload"],
            "Occo_Payload": occo_metrics["payload"]
        })
        
        print(f"  -> Baseline Tokens: {baseline_metrics['tokens']} | Occo Tokens: {occo_metrics['tokens']} | C2K: {c2k_ratio}x")
        print(f"  -> Fidelity: {fidelity_score}% | Entity Retention: {entity_retention}% | Status: {occo_metrics['status']}")

    df = pd.DataFrame(results)
    
    # 5. Export Detailed CSV
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    export_path = os.path.join(results_dir, "benchmark_metrics_dense.csv")
    export_path_standard = os.path.join(results_dir, "benchmark_metrics.csv")
    
    df.to_csv(export_path, index=False)
    df.to_csv(export_path_standard, index=False)
    
    # Filter passed in-domain queries for clean aggregate statistics
    passed_df = df[df["Status"] == "PASSED"]
    rejected_count = len(df[df["Status"] == "REJECTED_OUT_OF_DOMAIN"])
    
    print("\n" + "=" * 70)
    print("COMMERCIAL BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Total Queries Evaluated:               {len(df)}")
    print(f"Out-of-Domain Queries Intercepted:     {rejected_count} / {len(df[df['Category'] == 'Out-of-Domain Adversarial'])}")
    print(f"Contradiction Friction Events Flagged: {df['Friction_Events_Flagged'].sum()}")
    print("-" * 70)
    if not passed_df.empty:
        print(f"Average C2K Efficiency Ratio:          {passed_df['C2K_Ratio'].mean():.2f}x")
        print(f"Average Semantic Fidelity:             {passed_df['Semantic_Fidelity_Pct'].mean():.2f}%")
        print(f"Average Entity Retention:              {passed_df['Entity_Retention_Pct'].mean():.2f}%")
        print(f"Average Latency Saved:                  {passed_df['Latency_Saved_ms'].mean():.2f} ms")
    print(f"Detailed CSV exported to:              {export_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_study()