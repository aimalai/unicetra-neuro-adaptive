import math
from collections import Counter
from typing import List, Dict, Any

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
    Establishes the foundational knowledge state by calculating the base uncertainty.
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

    p_probs = get_token_probabilities(candidate_text) # Candidate distribution (P)
    q_probs = get_token_probabilities(baseline_text)  # Baseline distribution (Q)
    
    epsilon = 1e-10 # Smoothing to prevent division by zero
    divergence = 0.0
    
    for token, p_val in p_probs.items():
        q_val = q_probs.get(token, epsilon)
        divergence += p_val * math.log2(p_val / q_val)
        
    return round(divergence, 4)

def calculate_ontological_weight(node_labels: List[str]) -> float:
    """
    Assigns Ontological Document Weighting (w) based on structural topology.
    Primary authoritative nodes receive a higher ontological weight than subordinate nodes.
    """
    if "Article" in node_labels:
        return 0.9 # High weight: requires a lower KL-Divergence score to be retained
    elif "Recital" in node_labels:
        return 0.5 # Subordinate weight: must demonstrate significantly higher Information Gain
    return 0.3     # Generic node fallback

def execute_recursive_entropy_audit(candidate_nodes: List[Dict[str, Any]], base_threshold: float = 1.0) -> Dict[str, Any]:
    """
    Executes the full Recursive Entropy Audit (REA) to isolate high-utility informational nodes
    and physically cap the context length (L).
    """
    retained_nodes = []
    baseline_context = ""
    raw_token_count = 0
    pruned_token_count = 0
    
    for node in candidate_nodes:
        text = node.get("text_content", "")
        labels = node.get("labels", [])
        
        node_token_length = len(text.split())
        raw_token_count += node_token_length
        
        # 1. Ontological Weighting
        weight = calculate_ontological_weight(labels)
        
        # 2. Modulate Threshold
        # High weight lowers the required threshold; low weight raises it.
        dynamic_threshold = base_threshold * (1.0 - weight)
        
        # 3. Calculate Divergence from current baseline
        kl_div = calculate_kl_divergence(baseline_context, text)
        
        # 4. Weighted Recursive Information Gain Evaluation
        if kl_div >= dynamic_threshold:
            retained_nodes.append({
                "node_id": node.get("node_id"),
                "text_content": text,
                "kl_divergence": kl_div,
                "ontological_weight": weight
            })
            baseline_context += " " + text
            pruned_token_count += node_token_length

    # 5. Calculate Extended Operational Metrics
    # Context Compression Ratio (CCR) = L_raw / L_pruned
    ccr = round(raw_token_count / pruned_token_count, 2) if pruned_token_count > 0 else 0.0
    
    # Quadratic Compute Mitigation = L_raw^2 / L_pruned^2
    quadratic_mitigation = round((raw_token_count**2) / (pruned_token_count**2), 2) if pruned_token_count > 0 else 0.0
    
    # API Cost Reduction = (L_raw - L_pruned) * Cost per Token
    # Assuming a mock API cost of $0.005 per 1k tokens for the thesis demonstration
    cost_per_token = 0.005 / 1000 
    api_cost_saved = round((raw_token_count - pruned_token_count) * cost_per_token, 6)

    return {
        "retained_nodes": retained_nodes,
        "metrics": {
            "raw_tokens": raw_token_count,
            "pruned_tokens": pruned_token_count,
            "context_compression_ratio": ccr,
            "quadratic_compute_mitigation": quadratic_mitigation,
            "api_cost_saved_usd": api_cost_saved
        }
    }