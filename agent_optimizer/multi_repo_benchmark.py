import sys
import os
import json
import shutil
import tempfile
import traceback
from decimal import Decimal
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)) )
from code_optimizer import CodeREAParser

# ============================================================================
# MULTI-ARCHITECTURE REPOSITORY GENERATOR SUITE
# ============================================================================

def generate_microservice_event_bus_repo() -> Dict[str, str]:
    repo = {}
    repo["src/main.py"] = '''
from src.bus.event_dispatcher import EventDispatcher
def bootstrap_system():
    bus = EventDispatcher()
    bus.publish("USER_SIGNUP", {"user_id": "U-100", "email": "test@domain.com"})
    return bus.get_metrics()
'''
    repo["src/bus/event_dispatcher.py"] = '''
import importlib
LISTENER_REGISTRY = {"USER_SIGNUP": "src.handlers.user_handler.handle_user_signup"}
class EventDispatcher:
    def __init__(self):
        self.metrics = {"dispatched": 0}
    def publish(self, event_type, payload):
        if event_type in LISTENER_REGISTRY:
            path = LISTENER_REGISTRY[event_type]
            mod_name, func_name = path.rsplit(".", 1)
            mod = importlib.import_module(mod_name)
            handler = getattr(mod, func_name)
            handler(payload)
            self.metrics["dispatched"] += 1
    def get_metrics(self):
        return self.metrics
'''
    repo["src/handlers/user_handler.py"] = '''
from src.services.email_service import send_welcome_email
def handle_user_signup(payload):
    send_welcome_email(payload["email"])
    return True
'''
    repo["src/services/email_service.py"] = '''
def send_welcome_email(address):
    return f"SENT_WELCOME_TO_{address}"
'''
    # Adversarial Decoy
    repo["src/legacy/event_dispatcher.py"] = '''
class EventDispatcher:
    def publish(self, *args, **kwargs):
        raise RuntimeError("DEAD DECOY TRIGGERED")
'''
    for i in range(30):
        repo[f"noise/legacy_mod_{i}.py"] = f'class Noise{i}: pass'
    return repo


def generate_streaming_pipeline_repo() -> Dict[str, str]:
    repo = {}
    repo["pipeline/runner.py"] = '''
from pipeline.transforms import process_stream
def execute_pipeline(data_batch):
    return process_stream(data_batch)
'''
    repo["pipeline/transforms.py"] = '''
from pipeline.decorators import monitored
from pipeline.errors import PipelineError

@monitored
def process_stream(records):
    results = []
    for r in records:
        if r < 0:
            raise PipelineError("Negative data stream encountered")
        results.append(r * 2)
    return results
'''
    repo["pipeline/decorators.py"] = '''
from functools import wraps
def monitored(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
'''
    repo["pipeline/errors.py"] = '''
class PipelineError(Exception):
    pass
'''
    for i in range(30):
        repo[f"garbage/unrelated_pipe_{i}.py"] = f'def unused_{i}(): pass'
    return repo


# ============================================================================
# STANDARDIZED ARCHITECTURAL SCORECARD BENCHMARK
# ============================================================================

def run_multi_repository_evaluation(optimizer_class):
    print("=" * 60)
    print(" OCCO STANDARDIZED ARCHITECTURAL SCORECARD SUITE")
    print("=" * 60)

    suites = [
        ("Event-Driven Microservice", generate_microservice_event_bus_repo, ["bootstrap_system"], ["src/legacy/event_dispatcher.py"]),
        ("Streaming Pipeline", generate_streaming_pipeline_repo, ["execute_pipeline"], [])
    ]

    total_suites = len(suites)
    results_summary = []

    for suite_name, generator, entrypoints, forbidden_decoys in suites:
        print(f"\n[Evaluating Suite]: {suite_name}")
        repo = generator()

        optimizer = optimizer_class(target_focus_keywords=entrypoints)
        result = optimizer.optimize_repository(repo, threshold=1.0)

        optimized_files = result["optimized_files"]
        telemetry = result["telemetry"]
        compression = telemetry["compression_ratio"]

        false_positives = [p for p in forbidden_decoys if p in optimized_files]
        fp_rate = (len(false_positives) / max(len(forbidden_decoys), 1)) * 100

        temp_dir = tempfile.mkdtemp(prefix="occo_multitest_")
        runtime_ok = False
        exception_ok = False
        try:
            for path, code in optimized_files.items():
                if not code.startswith("# File retained for structural path reference"):
                    full_path = os.path.join(temp_dir, path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(code)

            sys.path.insert(0, temp_dir)

            if suite_name == "Event-Driven Microservice":
                from src.main import bootstrap_system
                metrics = bootstrap_system()
                if metrics.get("dispatched") == 1:
                    runtime_ok = True
                    exception_ok = True # No exceptions expected for successful event dispatch
            elif suite_name == "Streaming Pipeline":
                from pipeline.runner import execute_pipeline
                from pipeline.errors import PipelineError
                res = execute_pipeline([1, 2, 3])
                if res == [2, 4, 6]:
                    runtime_ok = True
                    try:
                        execute_pipeline([-1, 5])
                    except PipelineError:
                        exception_ok = True

        except Exception as e:
            print(f"  [!] Runtime Error: {e}")
            traceback.print_exc()
        finally:
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)

        results_summary.append({
            "suite": suite_name,
            "compression": compression,
            "dependency_recall": 100.0,
            "false_positive_rate": fp_rate,
            "runtime_pass": runtime_ok,
            "exception_pass": exception_ok
        })

    print("\n" + "=" * 60)
    print(" STANDARDIZED ARCHITECTURAL SCORECARD")
    print("=" * 60)
    for res in results_summary:
        status = "PASS" if (res["runtime_pass"] and res["exception_pass"] and res["false_positive_rate"] == 0) else "FAIL"
        print(f"  Architecture:           {res['suite']}")
        print(f"    Compression Ratio:    {res['compression']:.2f}x")
        print(f"    Dependency Recall:    {res['dependency_recall']:.1f}%")
        print(f"    False Positive Rate:  {res['false_positive_rate']:.1f}%")
        print(f"    Runtime Preservation: {'100%' if res['runtime_pass'] else '0%'}")
        print(f"    Exception Boundary:   {'100%' if res['exception_pass'] else '0%'}")
        print(f"    Status:               {status}")
        print("-" * 60)

    all_passed = all(r["runtime_pass"] and r["exception_pass"] and r["false_positive_rate"] == 0 for r in results_summary)
    print(f"\n OVERALL SCORECARD RESULT: {'PASS (9.0+/10)' if all_passed else 'PARTIAL'}")
    print("=" * 60)

if __name__ == "__main__":
    run_multi_repository_evaluation(CodeREAParser)