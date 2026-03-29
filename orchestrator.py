# main_orchestrator.py
import time
from datetime import datetime

import requests

from critic import critic_node, self_correction_router
from schema import GraphState, mock_retrieved_nodes
from pruning import pruning_node
from synthesis import (
    synthesis_node,
) 


class KGConnector:
    BASE_URL = "http://localhost:8001/graph"

    @staticmethod
    def search_nodes(query: str) -> list[dict]:
        """Primary Retrieval: Isolates entry points within the graph."""
        try:
            response = requests.get(f"{KGConnector.BASE_URL}/search", params={"q": query, "limit": 5})
            if response.status_code == 200:
                extracted = []
                for item in response.json():
                    payload = item["result"]
                    extracted.append(
                        {
                            "id": payload["id"],
                            "node_type": item["label"],
                            "content": payload.get("full_text") or payload.get("text") or "",
                            "regulation": payload.get("regulation"),
                            "metadata": {"score": item["score"]},
                            "entropy_score": None,
                        }
                    )
                return extracted
        except Exception as err:
            print(f"Knowledge Graph connection interrupted: {err}")
        return mock_retrieved_nodes

    @staticmethod
    def get_neighbors(node_id: str) -> list[dict]:
        """Deep Traversal: Retrieves adjacent structural elements."""
        try:
            response = requests.get(f"{KGConnector.BASE_URL}/traverse/{node_id}", params={"depth": 1})
            if response.status_code == 200:
                payload = response.json()
                adjacent_nodes = []
                for neighbor in payload.get("neighbors", []):
                    adjacent_nodes.append(
                        {
                            "id": neighbor["id"],
                            "node_type": neighbor["label"],
                            "content": neighbor.get("title") or neighbor.get("id"),
                            "regulation": neighbor.get("id", "").split("_")[0],
                            "metadata": {"parent": node_id},
                            "entropy_score": None,
                        }
                    )
                return adjacent_nodes
        except Exception as err:
            print(f"Graph expansion error: {err}")
        return []


def run_neuro_adaptive_engine(user_query: str):
    execution_start = time.time()

    # Carbon and Efficiency Metrics
    total_chars_evaluated = 0
    total_chars_retained = 0

    state: GraphState = {
        "query": user_query,
        "cypher_intent": {},
        "retrieved_nodes": KGConnector.search_nodes(user_query),
        "links_found": [],
        "pruned_context": [],
        "reasoning_trace": [f"[*] Intake processed: {user_query}"],
        "final_answer": "",
        "hops": 0,
        "is_accurate": False,
        "metrics": {
            "tokens_saved": 0,
            "entropy_reduction": 0.0,
            "nodes_pruned": 0,
            "latency_seconds": 0.0,
        },
    }

    # --- AUTONOMOUS REASONING LOOP ---
    while state["hops"] < 3:
        # Step A: Evaluate incoming volume
        cycle_raw_chars = sum(len(n.get("content", "")) for n in state["retrieved_nodes"])
        total_chars_evaluated += cycle_raw_chars
        starting_node_count = len(state["retrieved_nodes"])

        # Step B: Apply proprietary information-density filter
        state = pruning_node(state, model=None, tokenizer=None)

        # Step C: Evaluate filtered volume
        cycle_kept_chars = sum(len(n.get("content", "")) for n in state["pruned_context"])
        total_chars_retained += cycle_kept_chars

        # Step D: Log efficiency deltas
        state["metrics"]["tokens_saved"] += max(0, (cycle_raw_chars - cycle_kept_chars) // 4)
        state["metrics"]["nodes_pruned"] += starting_node_count - len(state["pruned_context"])

        # Step E: Enforce ontological integrity
        state = critic_node(state)

        if self_correction_router(state) == "generate_final_answer":
            break

        if not state["pruned_context"]:
            state["reasoning_trace"].append("[!] Execution Terminated: Context depleted below operational threshold.")
            break

        # Step F: Expand graph search dynamically
        expansion_target = state["pruned_context"][0]["id"]
        state["reasoning_trace"].append(f"[*] Expanding local subgraph centered on {expansion_target}...")

        fresh_nodes = KGConnector.get_neighbors(expansion_target)
        state["retrieved_nodes"].extend(fresh_nodes)
        state["hops"] += 1

    # --- EFFICIENCY AGGREGATION ---
    compression_rate = 0.0
    if total_chars_evaluated > 0:
        compression_rate = float(round((total_chars_evaluated - total_chars_retained) / total_chars_evaluated, 3))

    compression_rate = max(0.0, min(1.0, compression_rate))
    state["metrics"]["entropy_reduction"] = compression_rate
    state["metrics"]["latency_seconds"] = round(time.time() - execution_start, 2)

    # --- BRIEFING GENERATION ---
    state = synthesis_node(state)

    # --- API PAYLOAD CONSTRUCTION ---
    serialized_trace = []
    for index, log_entry in enumerate(state["reasoning_trace"]):
        serialized_trace.append(
            {
                "step_number": int(index + 1),
                "agent": "UnicetraCore",
                "action": str(log_entry),
                "retrieved_nodes": [str(n["id"]) for n in state["pruned_context"]],
                "entropy_reduction": 0.0,
                "timestamp": datetime.now().isoformat(),
            }
        )

    return {
        "final_answer": str(state["final_answer"]),
        "reasoning_steps": serialized_trace,
        "metrics": {
            "reasoning_steps": len(serialized_trace),
            "tokens_saved": int(state["metrics"]["tokens_saved"]),
            "nodes_pruned": int(state["metrics"]["nodes_pruned"]),
            "latency_seconds": float(state["metrics"]["latency_seconds"]),
            "entropy_reduction": float(compression_rate),
        },
    }


if __name__ == "__main__":
    test_result = run_neuro_adaptive_engine("Integration validation check")
    print(f"[SYSTEM] Operation Metrics: {test_result['metrics']}")
    print(f"[SYSTEM] Response Output: {test_result['final_answer'][:100]}...")