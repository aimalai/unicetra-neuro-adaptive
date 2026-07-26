import csv
import time
import requests
from typing import List, Dict

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
OUTPUT_FILE = "occo_ai_lgm50_eval_results.csv"
CONFIDENCE_THRESHOLD = 0.85

# A representative sample of the LGM-50 Benchmark Dataset spanning 
# Biomedical, Legal, and Algorithmic domains. 
LGM_50_DATASET = [
    {
        "id": 1, 
        "domain": "Biomedical", 
        "target": "Warfarin mechanism of action (VKORC1)", 
        "payload": "Warfarin is an anticoagulant that functions by inhibiting the synthesis of vitamin K-dependent clotting factors, specifically targeting the VKORC1 enzyme complex."
    },
    {
        "id": 18, 
        "domain": "Legal", 
        "target": "Marbury v. Madison (Judicial Review)", 
        "payload": "In the landmark 1803 decision of Marbury v. Madison, the Supreme Court established the principle of judicial review under Article III of the Constitution."
    },
    {
        "id": 35, 
        "domain": "Algorithmic", 
        "target": "Dijkstra's Algorithm optimal time complexity", 
        "payload": "Using a Fibonacci heap, Dijkstra's algorithm for finding the shortest paths between nodes in a graph has an optimal time complexity of O(E + V log V)."
    },
    {
        "id": 26, 
        "domain": "Legal", 
        "target": "Gideon v. Wainwright (6th Amendment)", 
        "payload": "Gideon v. Wainwright unanimously ruled that states are required under the Sixth Amendment of the U.S. Constitution to provide an attorney to defendants in criminal cases who are unable to afford their own attorneys."
    },
    {
        "id": 50, 
        "domain": "Algorithmic", 
        "target": "Knapsack Problem (0/1) pseudo-polynomial time", 
        "payload": "The 0/1 knapsack problem can be solved in pseudo-polynomial time using dynamic programming, typically structured as a 2D array over weights and item counts."
    }
]

def run_evaluation_harness(dataset: List[Dict]):
    print(f"🚀 Initializing Occo AI LGM-50 Evaluation Harness...")
    print(f"🎯 Target Threshold: {CONFIDENCE_THRESHOLD} | Payload Count: {len(dataset)}\n")

    results_log = []
    
    for item in dataset:
        print(f"Testing [{item['domain']}] Target {item['id']}: {item['target'][:40]}...")
        
        # 1. Test the Entropy Audit (Compression) Endpoint
        compress_payload = {
            "text_content": item["payload"],
            "node_id": f"LGM_Bench_{item['id']}",
            "labels": [item["domain"]]
        }
        
        compress_metrics = {}
        try:
            start_time = time.time()
            comp_resp = requests.post(f"{API_BASE_URL}/compress", json=compress_payload)
            comp_resp.raise_for_status()
            c_data = comp_resp.json()
            
            compress_metrics = {
                "shannon_entropy": c_data.get("shannon_entropy", 0.0),
                "c2k_ratio": c_data.get("c2k_ratio", 0.0),
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }
        except Exception as e:
            print(f"  ❌ Compression API Failed: {e}")
            compress_metrics = {"shannon_entropy": 0.0, "c2k_ratio": 0.0, "latency_ms": 0.0}

        # 2. Test the Parametric Integrity Gating (PIG) Endpoint
        validate_payload = {
            "text_content": item["payload"],
            "threshold": CONFIDENCE_THRESHOLD
        }
        
        gate_metrics = {}
        try:
            val_resp = requests.post(f"{API_BASE_URL}/validate", json=validate_payload)
            val_resp.raise_for_status()
            v_data = val_resp.json()
            
            fan_scores = v_data.get("fan_scores", {})
            gate_metrics = {
                "is_valid": v_data.get("is_valid", False),
                "honest_ignorance_triggered": v_data.get("honest_ignorance_triggered", True),
                "surprisal_score": fan_scores.get("surprisal", 0.0),
                "structural_score": fan_scores.get("structural", 0.0),
                "positional_score": fan_scores.get("positional", 0.0),
                "hook_status": v_data.get("model_hook_status", "UNKNOWN")
            }
        except Exception as e:
            print(f"  ❌ Validation API Failed: {e}")
            gate_metrics = {
                "is_valid": False, 
                "honest_ignorance_triggered": True,
                "surprisal_score": 0.0, "structural_score": 0.0, "positional_score": 0.0,
                "hook_status": "API_ERROR"
            }

        # Compile row for CSV
        results_log.append({
            "Fact_ID": item["id"],
            "Domain": item["domain"],
            "Target": item["target"],
            "Shannon_Entropy": round(compress_metrics["shannon_entropy"], 4),
            "C2K_Ratio": compress_metrics["c2k_ratio"],
            "Surprisal_Fan": gate_metrics["surprisal_score"],
            "Structural_Fan": gate_metrics["structural_score"],
            "Positional_Fan": gate_metrics["positional_score"],
            "Gate_Passed": gate_metrics["is_valid"],
            "Honest_Ignorance": gate_metrics["honest_ignorance_triggered"],
            "Latency_ms": compress_metrics["latency_ms"]
        })

    # 3. Export to CSV
    export_to_csv(results_log)

def export_to_csv(results: List[Dict]):
    if not results:
        print("No results to export.")
        return
        
    keys = results[0].keys()
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
    
    print(f"\n✅ Evaluation Complete! Batch metrics successfully exported to: {OUTPUT_FILE}")
    
    # Calculate quick macro metrics for the console output
    pass_rate = sum(1 for r in results if r["Gate_Passed"]) / len(results) * 100
    avg_entropy = sum(r["Shannon_Entropy"] for r in results) / len(results)
    
    print("-" * 40)
    print(f"📊 MACRO METRICS SNAPSHOT:")
    print(f"  - Gate Pass Rate: {pass_rate:.1f}%")
    print(f"  - Avg Shannon Entropy: {avg_entropy:.4f} bits")
    print(f"  - Honest Ignorance Triggered: {100 - pass_rate:.1f}%")
    print("-" * 40)

if __name__ == "__main__":
    run_evaluation_harness(LGM_50_DATASET)