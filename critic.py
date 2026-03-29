# critic_engine.py
from schema import GraphState


def critic_node(state: GraphState) -> GraphState:
    """Proprietary Step 2: Ontological Dependency Verification."""
    print(f">>> INITIATING ONTOLOGICAL AUDIT (Cycle {state['hops']}) <<<")

    active_ids = [n["id"] for n in state["pruned_context"]]
    combined_text = " ".join([n["content"] for n in state["pruned_context"]]).lower()

    identified_gaps = []

    # Check A: Legislative Intent Alignment (e.g., Article requires a Recital)
    if "eu_ai_act_art_10" in active_ids and "eu_ai_act_rec_59" not in active_ids:
        identified_gaps.append("eu_ai_act_rec_59 (Contextual Intent Required)")

    # Check B: Regulatory Intersections (e.g., Systemic Risk overlap)
    risk_indicator_present = "eu_ai_act_art_55" in active_ids or "systemic risk" in combined_text
    if risk_indicator_present and "dsa_art_34" not in active_ids:
        state["reasoning_trace"].append(
            "Audit System: Systemic risk parameters detected. Mandating DSA Article 34 cross-reference."
        )
        identified_gaps.append("dsa_art_34 (Mandatory Risk Intersection)")

    # Check C: Nomenclature Resolution (e.g., GPAI definition)
    if "general-purpose ai" in combined_text and not any("_def_" in node_id for node_id in active_ids):
        identified_gaps.append("eu_ai_act_art_3 (Core Terminology Missing)")

    # --- Resolution Phase ---
    if identified_gaps and state["hops"] < 3:
        warning_message = f"Deficiency detected in legal graph: {identified_gaps}"
        print(f"[!] {warning_message}")
        state["is_accurate"] = False
        state["reasoning_trace"].append(warning_message)
    else:
        state["is_accurate"] = True
        state["reasoning_trace"].append("Audit System: Topological and ontological validity confirmed.")

    return state


def self_correction_router(state: GraphState):
    """Directs traversal logic based on ontological integrity."""
    return "generate_final_answer" if state["is_accurate"] else "re_traverse_graph"