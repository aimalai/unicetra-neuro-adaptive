import math
from collections import Counter
from typing import Dict, Any

def get_token_probabilities(text: str) -> Dict[str, float]:
    """Helper function to calculate token probability distributions."""
    tokens = text.lower().split()
    if not tokens:
        return {}
    total = len(tokens)
    counts = Counter(tokens)
    return {token: count / total for token, count in counts.items()}

def calculate_kl_divergence_for_js(p_probs: Dict[str, float], q_probs: Dict[str, float]) -> float:
    """Calculates KL divergence specifically formatted for JS divergence summation."""
    epsilon = 1e-10
    divergence = 0.0
    for token, p_val in p_probs.items():
        q_val = q_probs.get(token, epsilon)
        divergence += p_val * math.log2(p_val / q_val)
    return divergence

def calculate_jensen_shannon_divergence(text1: str, text2: str) -> float:
    """
    Calculates Jensen-Shannon Divergence (D_JS) for the Recursive Contradiction Probe.
    Measures the semantic consistency and logical friction between two text nodes.
    """
    if not text1 or not text2:
        return 0.0

    p_probs = get_token_probabilities(text1)
    q_probs = get_token_probabilities(text2)

    # Calculate M = 1/2 (P + Q)
    m_probs = {}
    all_tokens = set(p_probs.keys()).union(set(q_probs.keys()))
    for token in all_tokens:
        m_probs[token] = 0.5 * (p_probs.get(token, 0.0) + q_probs.get(token, 0.0))

    # D_JS = 1/2 D_KL(P||M) + 1/2 D_KL(Q||M)
    kl_pm = calculate_kl_divergence_for_js(p_probs, m_probs)
    kl_qm = calculate_kl_divergence_for_js(q_probs, m_probs)

    d_js = 0.5 * kl_pm + 0.5 * kl_qm
    return round(d_js, 4)

def run_recursive_contradiction_probe(target_node: Dict[str, Any], parent_node: Dict[str, Any], threshold: float = 0.6) -> Dict[str, Any]:
    """
    Executes the RCP to audit semantic harmony.
    Acts as an early-exit mechanism if logical friction exceeds the D_JS threshold.
    """
    # Self-Correction Router logic: Check for missing topological context
    if not parent_node or not parent_node.get("parent_content"):
        return {
            "is_harmonious": False,
            "d_js_score": 0.0,
            "status": "FAILED: Missing Topological Context. Self-Correction Re-traversal Triggered."
        }

    text1 = target_node.get("text_content", "")
    text2 = parent_node.get("parent_content", "")
    
    d_js_score = calculate_jensen_shannon_divergence(text1, text2)
    
    # If the divergence exceeds the threshold, a logical clash is detected
    is_harmonious = d_js_score <= threshold
    
    status = "PASSED: Semantic Harmony Verified." if is_harmonious else "FAILED: Logical Contradiction Detected. Early Exit Triggered."
    
    return {
        "is_harmonious": is_harmonious,
        "d_js_score": d_js_score,
        "status": status,
        "threshold_used": threshold
    }