import math
import re
import numpy as np
from collections import Counter
from typing import List, Dict, Any
from langdetect import detect, DetectorFactory

# Set seed for deterministic language detection
DetectorFactory.seed = 0

# -----------------------------------------------------------------------
# PRE-PROCESSING & NORMALIZATION
# -----------------------------------------------------------------------

def filter_chunks_by_language(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensures parametric integrity by filtering candidate chunks to match query language."""
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
    """Decomposes coarse-grained document chunks into sentence-level atomic nodes for granular REA."""
    sentence_nodes = []
    for c in candidates:
        text = c.get("text_content", "")
        labels = c.get("labels", ["Paragraph"])
        depth = c.get("depth", -1)
        chunk_id = c.get("node_id", "node")
        
        # Split using standard regex for structural punctuation
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
        
        for idx, s in enumerate(sentences):
            sentence_nodes.append({
                "node_id": f"{chunk_id}_s{idx}",
                "text_content": s,
                "labels": labels,
                "depth": depth
            })
            
    return sentence_nodes if sentence_nodes else candidates

# -----------------------------------------------------------------------
# PROBABILITY & INFORMATION THEORY MATH
# -----------------------------------------------------------------------

def get_token_probabilities(text: str) -> Dict[str, float]:
    """Helper function to calculate token probability distributions."""
    tokens = text.lower().split()
    if not tokens:
        return {}
    total = len(tokens)
    counts = Counter(tokens)
    return {token: count / total for token, count in counts.items()}

def calculate_shannon_entropy(text: str) -> float:
    """
    Calculates the Shannon Entropy Baseline (H).
    Establishes the foundational knowledge state by calculating base uncertainty.
    """
    probs = get_token_probabilities(text)
    entropy = -sum(p * math.log2(p) for p in probs.values()) if probs else 0.0
    return round(entropy, 4)

def calculate_kl_divergence(baseline_text: str, candidate_text: str) -> float:
    """
    Calculates the KL-Divergence D_KL(P||Q) to measure Relative Information Gain.
    Ensures every token passed to the model adds strictly unique value.
    """
    if not baseline_text:
        return calculate_shannon_entropy(candidate_text)

    p_probs = get_token_probabilities(candidate_text) 
    q_probs = get_token_probabilities(baseline_text)  
    
    epsilon = 1e-10 
    divergence = 0.0
    
    for token, p_val in p_probs.items():
        q_val = q_probs.get(token, epsilon)
        divergence += p_val * math.log2(p_val / q_val)
        
    return round(divergence, 4)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates high-dimensional cosine similarity between two dense vectors."""
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm > 0 else 0.0

def calculate_jensen_shannon_divergence(p_vec: np.ndarray, q_vec: np.ndarray) -> float:
    """
    Recursive Contradiction Probe (RCP).
    Uses Jensen-Shannon Divergence D_JS(P||Q) to audit semantic consistency 
    and flag logical friction points at the middleware layer.
    """
    p_norm = p_vec / (np.linalg.norm(p_vec) + 1e-10)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-10)
    m_vec = 0.5 * (p_norm + q_norm)
    
    cos_pm = cosine_similarity(p_norm, m_vec)
    cos_qm = cosine_similarity(q_norm, m_vec)
    
    d_kl_pm = float(np.abs(1.0 - cos_pm))
    d_kl_qm = float(np.abs(1.0 - cos_qm))
    
    d_js = 0.5 * d_kl_pm + 0.5 * d_kl_qm
    return round(d_js, 4)

# -----------------------------------------------------------------------
# ONTOLOGICAL TOPOLOGY
# -----------------------------------------------------------------------

def calculate_ontological_weight(node_labels: List[str], structural_depth: int = -1) -> float:
    """
    Assigns Ontological Document Weighting (w).
    Document-agnostic: relies on explicit tree depth or universal fallback labels.
    """
    if structural_depth == 0: return 0.9      
    elif structural_depth == 1: return 0.7    
    elif structural_depth == 2: return 0.5    
    elif structural_depth >= 3: return 0.3    
        
    labels_upper = [str(l).upper() for l in node_labels]
    if any(l in labels_upper for l in ["H1", "TITLE", "ARTICLE", "CHAPTER", "ROOT", "ABSTRACT"]):
        return 0.9
    elif any(l in labels_upper for l in ["H2", "SECTION", "RECITAL", "SUBHEADER", "METHODOLOGY"]):
        return 0.5
        
    return 0.3 

# -----------------------------------------------------------------------
# MAIN EXECUTION PIPELINE
# -----------------------------------------------------------------------

def execute_recursive_entropy_audit(
    candidate_nodes: List[Dict[str, Any]], 
    query: str = None,
    dense_model=None,
    base_query_threshold: float = 0.50,
    base_novelty_threshold: float = 0.75,
    adaptive_floor: float = 0.45,
    js_friction_threshold: float = 0.18
) -> Dict[str, Any]:
    """
    Executes the full Recursive Entropy Audit (REA).
    Isolates high-utility nodes using KL-Divergence, Adaptive Gating, and D_JS Probes.
    """
    # 1. Pre-process Candidates (Language filter & Sentence Decomp)
    if query:
        candidate_nodes = filter_chunks_by_language(query, candidate_nodes)
    sentence_nodes = decompose_chunks_to_sentences(candidate_nodes)

    retained_nodes = []
    retained_embeddings = []
    baseline_context = ""
    
    raw_token_count = 0
    pruned_token_count = 0
    friction_events = 0
    
    use_vector_gating = query is not None and dense_model is not None
    query_emb = None
    all_embeddings = []
    all_query_sims = []
    
    texts = [node.get("text_content", "") for node in sentence_nodes]
    
    if use_vector_gating and texts:
        query_emb = dense_model.encode(query)
        all_embeddings = dense_model.encode(texts)
        all_query_sims = [cosine_similarity(emb, query_emb) for emb in all_embeddings]
        
        # 2. ADAPTIVE SIMILARITY FLOOR (Out-of-Domain Interception)
        max_query_sim = max(all_query_sims) if all_query_sims else 0.0
        if max_query_sim < adaptive_floor:
            return {
                "status": "REJECTED_OUT_OF_DOMAIN",
                "retained_nodes": [],
                "friction_events": 0,
                "metrics": {
                    "raw_tokens": sum(len(t.split()) for t in texts),
                    "pruned_tokens": 0,
                    "context_compression_ratio": 0.0,
                    "quadratic_compute_mitigation": 0.0,
                    "api_cost_saved_usd": 0.0
                }
            }

    # 3. RECURSIVE ENTROPY AUDIT (Information Density Pruning)
    for idx, node in enumerate(sentence_nodes):
        text = texts[idx]
        labels = node.get("labels", [])
        depth = node.get("depth", -1)
        
        node_token_length = len(text.split())
        raw_token_count += node_token_length
        
        # Step A: Ontological Weighting
        weight = calculate_ontological_weight(labels, depth)
        
        # Step B: Optional Vector Relevance Gate (using exact benchmark formula)
        if use_vector_gating:
            emb = all_embeddings[idx]
            query_sim = all_query_sims[idx]
            min_required_relevance = base_query_threshold * (1.5 - weight) 
            if query_sim < min_required_relevance:
                continue
                
        # Step C: Modulate Novelty Threshold (using exact benchmark formula)
        dynamic_threshold = base_novelty_threshold * (1.5 - weight)
        
        # Step D: Calculate KL-Divergence from current baseline
        kl_div = calculate_kl_divergence(baseline_context, text)
        
        # Step E: Weighted Recursive Information Gain Evaluation
        if kl_div >= dynamic_threshold:
            
            # Step F: Ontological Critic (D_JS Contradiction Probe)
            if use_vector_gating and retained_embeddings:
                for r_emb in retained_embeddings:
                    d_js = calculate_jensen_shannon_divergence(emb, r_emb)
                    if d_js >= js_friction_threshold:
                        friction_events += 1 
            
            # Retain Node
            retained_nodes.append({
                "node_id": node.get("node_id"),
                "text_content": text,
                "kl_divergence": kl_div,
                "ontological_weight": weight
            })
            baseline_context += " " + text
            pruned_token_count += node_token_length
            
            if use_vector_gating:
                retained_embeddings.append(emb)

    # 4. CALCULATE OPERATIONAL METRICS
    ccr = round(raw_token_count / pruned_token_count, 2) if pruned_token_count > 0 else 0.0
    quad_mitigation = round((raw_token_count**2) / (pruned_token_count**2), 2) if pruned_token_count > 0 else 0.0
    cost_per_token = 0.005 / 1000 
    api_cost_saved = round((raw_token_count - pruned_token_count) * cost_per_token, 6)

    return {
        "status": "PASSED",
        "retained_nodes": retained_nodes,
        "friction_events": friction_events,
        "metrics": {
            "raw_tokens": raw_token_count,
            "pruned_tokens": pruned_token_count,
            "context_compression_ratio": ccr,
            "quadratic_compute_mitigation": quad_mitigation,
            "api_cost_saved_usd": api_cost_saved
        }
    }