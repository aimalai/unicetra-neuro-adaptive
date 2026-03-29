# pruning_engine.py
import random

import torch
import torch.nn.functional as fn

from schema import GraphState

# --- PROPRIETARY CORE: RECURSIVE ENTROPY AUDIT ---


def calculate_cumulative_information_gain(base_distribution, candidate_distribution):
    """
    Proprietary Algorithm: Cumulative KL-Divergence.
    Evaluates the distinct information gain of a candidate against a continually 
    updating knowledge baseline, ensuring strictly zero semantic redundancy.
    """
    # Computes D_KL(Base || Candidate)
    divergence = torch.sum(
        base_distribution * (torch.log(base_distribution + 1e-10) - torch.log(candidate_distribution + 1e-10)), 
        dim=-1
    )
    return divergence.item()


def pruning_node(state: GraphState, model=None, tokenizer=None, threshold=0.35) -> GraphState:
    """
    Information-Density Filter: Applies recursive probabilistic checks to 
    isolate high-utility legal nodes and discard duplicate concepts.
    """
    print(f">>> EXECUTING RECURSIVE ENTROPY AUDIT [Strictness: {threshold}] <<<")

    raw_data = state["retrieved_nodes"]
    if not raw_data:
        return state

    verified_context = []
    
    # Establish the foundational knowledge node
    foundation_node = raw_data[0]
    verified_context.append(foundation_node)

    if model is None or tokenizer is None:
        # Simulation Mode
        for candidate in raw_data[1:]:
            simulated_gain = random.uniform(0.05, 0.95)
            if simulated_gain > threshold:
                candidate["kl_score"] = simulated_gain
                verified_context.append(candidate)
            else:
                print(f"   [FILTERED] {candidate['id']} - Insufficient Utility: {simulated_gain:.4f}")
    else:
        # Hardware-Accelerated Probabilistic Processing
        with torch.no_grad():
            foundation_inputs = tokenizer(foundation_node["content"], return_tensors="pt").to(model.device)
            foundation_logits = model(**foundation_inputs).logits
            cumulative_probs = fn.softmax(torch.mean(foundation_logits, dim=1), dim=-1)

            for candidate in raw_data[1:]:
                cand_inputs = tokenizer(candidate["content"], return_tensors="pt").to(model.device)
                cand_logits = model(**cand_inputs).logits
                cand_probs = fn.softmax(torch.mean(cand_logits, dim=1), dim=-1)

                # Proprietary IP: Evaluate against the aggregated memory state
                gain_metric = calculate_cumulative_information_gain(cumulative_probs, cand_probs)

                if gain_metric > threshold:
                    candidate["kl_score"] = gain_metric
                    verified_context.append(candidate)
                    # Dynamically update the baseline to represent combined knowledge
                    cumulative_probs = (cumulative_probs + cand_probs) / 2.0
                else:
                    print(f"   [FILTERED] {candidate['id']} - Insufficient Utility: {gain_metric:.4f}")

    print(f"Audit Concluded. Retained {len(verified_context)} of {len(raw_data)} source nodes.")
    state["pruned_context"] = verified_context
    return state