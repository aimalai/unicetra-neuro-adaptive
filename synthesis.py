# synthesis_engine.py
from schema import GraphState


def synthesis_node(state: GraphState) -> GraphState:
    """Proprietary Step 3: Contextual Generation Pipeline.
    Local Execution: Aggregates verified text segments.
    Remote Execution (Nuvlos): Synthesizes comprehensive legal briefings.
    """
    print(">>> COMPILING VERIFIED LEGAL BRIEFING <<<")

    if not state["pruned_context"]:
        state["final_answer"] = (
            "Insufficient validated context retrieved to formulate a legally robust response."
        )
        return state

    # Extract the apex nodes post-entropy filtration
    apex_nodes = state["pruned_context"][:3]

    header = f"Diagnostic review based on filtered {state['retrieved_nodes'][0]['regulation'].upper()} statutes:\n\n"

    compiled_segments = []
    for node in apex_nodes:
        preview = node["content"][:200].strip() + "..."
        compiled_segments.append(f"-> REFERENCE {node['id'].upper()}: {preview}")

    footer = f"\n\nOutput refined via Recursive Entropy Audit. Redundant data suppressed by {state['metrics']['entropy_reduction'] * 100:.1f}%."

    # Finalize state payload
    state["final_answer"] = header + "\n".join(compiled_segments) + footer
    state["reasoning_trace"].append(
        "Generator: Final briefing assembled from isolated high-utility nodes."
    )

    return state