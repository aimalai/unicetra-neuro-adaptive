import sys
import os
import json
import shutil
import tempfile
import traceback
from decimal import Decimal
from typing import Dict, Callable

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from code_optimizer import CodeREAParser

# ============================================================================
# ADVANCED REPOSITORY GENERATOR (ARBITRARY SEMANTIC & ADVERSARIAL SUITE)
# ============================================================================

def generate_enterprise_repository() -> Dict[str, str]:
    repo = {}

    # 1. LEGACY NOISE & LEXICAL DECOYS (Adversarial challenge: names match core modules)
    for i in range(100):
        repo[f"src/legacy/module_{i}.py"] = f'''
class LegacyProcessor{i}:
    def __init__(self):
        self.version = "1.{i}.0"
    def execute(self, payload):
        return {i}
'''

    # Lexical decoys designed to trick naive substring/name matchers
    repo["src/legacy/payment_gateway.py"] = '''
class EnterprisePaymentGateway:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("DEAD DECOY TRIGGERED: This legacy module should never be loaded!")
'''
    repo["src/payments/legacy_service.py"] = '''
from src.legacy.payment_gateway import EnterprisePaymentGateway
def dead_service():
    pass
'''

    # 2. CONFIGURATION
    repo["config/settings.py"] = '''
import os
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "enterprise_gateway")
SECURITY_POLICY = {"max_transaction": 100000, "require_idempotency": True}
'''

    # 3. SECURITY MODULE (With Exception Handlers & Context Managers)
    repo["src/security/audit.py"] = '''
import time
class AuditLogger:
    def record(self, event, metadata):
        try:
            return {"event": event, "timestamp": str(time.time()), "meta": metadata}
        except Exception as e:
            return {"error": str(e)}
'''

    repo["src/security/permissions.py"] = '''
class PermissionDenied(Exception):
    pass

def require_payment_permission(user):
    if not user.get("can_pay"):
        raise PermissionDenied("User lacks payment permission")
    return True
'''

    # 4. DOMAIN MODELS
    repo["src/domain/models.py"] = '''
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class PaymentRequest:
    amount: Decimal
    account: str
    currency: str
    user_id: str
    idempotency_key: str
'''

    # 5. ABSTRACT PAYMENT INTERFACE
    repo["src/core/interfaces.py"] = '''
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def execute(self, request):
        raise NotImplementedError
'''

    # 6. REAL PAYMENT IMPLEMENTATION
    repo["src/core/payment_gateway.py"] = '''
from decimal import Decimal
from src.core.interfaces import PaymentGateway
from src.security.audit import AuditLogger

class EnterprisePaymentGateway(PaymentGateway):
    def __init__(self, merchant_id, secret_key):
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.audit = AuditLogger()

    def execute(self, request):
        if request.amount <= Decimal("0"):
            self.audit.record("PAYMENT_REJECTED", {"reason": "invalid_amount"})
            raise ValueError("Invalid transaction amount")
        if request.amount > Decimal("100000"):
            self.audit.record("PAYMENT_REJECTED", {"reason": "limit_exceeded"})
            raise ValueError("Transaction exceeds security limit")
        return {"status": "SUCCESS", "routed_amount": request.amount, "target": request.account}
'''

    # 7. ADVANCED DECORATORS (Testing wrapper chain integrity)
    repo["src/core/decorators.py"] = '''
from functools import wraps

def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Semantic canary inside decorator execution chain
        return func(*args, **kwargs)
    return wrapper

def audited(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
'''

    # 8. FRAUD DETECTION
    repo["src/fraud/engine.py"] = '''
from decimal import Decimal

class FraudEngine:
    def __init__(self):
        self.threshold = Decimal("5000")

    def evaluate(self, request):
        if request.amount >= self.threshold:
            return {"decision": "REVIEW", "reason": "HIGH_VALUE"}
        return {"decision": "ALLOW", "reason": "NORMAL"}
'''

    # 9. IDEMPOTENCY
    repo["src/payments/idempotency.py"] = '''
class IdempotencyStore:
    def __init__(self):
        self._records = {}
    def get(self, key):
        return self._records.get(key)
    def put(self, key, result):
        self._records[key] = result
'''

    # 10. DYNAMIC PROVIDER LOADING
    repo["src/core/provider_loader.py"] = '''
import importlib

PROVIDER_REGISTRY = {
    "enterprise_gateway": "src.core.payment_gateway.EnterprisePaymentGateway"
}

def load_provider(name):
    path = PROVIDER_REGISTRY[name]
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)
'''

    # 11. PAYMENT SERVICE
    repo["src/payments/service.py"] = '''
from src.core.provider_loader import load_provider
from src.domain.models import PaymentRequest
from src.fraud.engine import FraudEngine
from src.payments.idempotency import IdempotencyStore
from src.security.permissions import require_payment_permission
from src.core.decorators import transactional, audited

class PaymentService:
    def __init__(self):
        self.provider = load_provider("enterprise_gateway")("MERCHANT_CORP", "SECRET")
        self.fraud = FraudEngine()
        self.idempotency = IdempotencyStore()

    @transactional
    @audited
    def process(self, payload, user):
        require_payment_permission(user)
        request = PaymentRequest(
            amount=payload["amount"], account=payload["account"],
            currency=payload["currency"], user_id=user["id"],
            idempotency_key=payload["idempotency_key"]
        )
        previous = self.idempotency.get(request.idempotency_key)
        if previous is not None:
            return previous
        
        fraud_result = self.fraud.evaluate(request)
        if fraud_result["decision"] == "REVIEW":
            raise ValueError("Payment requires manual review")
            
        result = self.provider.execute(request)
        self.idempotency.put(request.idempotency_key, result)
        return result
'''

    # 12. API ROUTER
    repo["src/api/router.py"] = '''
from src.payments.service import PaymentService

payment_service = PaymentService()

def handle_incoming_transaction(payload, user=None):
    if user is None:
        user = {"id": "anonymous", "can_pay": True}
    return payment_service.process(payload, user)
'''

    # 13. GENERATED NOISE MODULES
    for i in range(50):
        repo[f"generated/openapi/model_{i}.py"] = f'class GeneratedModel{i}: pass'

    return repo


# ============================================================================
# OPTIMIZER BENCHMARK & RIGOROUS SEMANTIC VALIDATION
# ============================================================================

def run_enterprise_optimizer_benchmark(optimizer_class):
    print("=" * 60)
    print(" OCCO CONTEXT PRUNING BENCHMARK (SEMANTIC HARDENED v2)")
    print("=" * 60)

    repo = generate_enterprise_repository()
    baseline_tokens = sum(len(code.split()) for code in repo.values())

    print(f"\nRepository")
    print(f"  Files:              {len(repo):,}")
    print(f"  Original tokens:    {baseline_tokens:,}")

    target_keywords = ["handle_incoming_transaction"]

    optimizer = optimizer_class(target_focus_keywords=target_keywords)
    result = optimizer.optimize_repository(repo, threshold=1.0)

    optimized_files = result["optimized_files"]
    telemetry = result["telemetry"]
    optimized_tokens = telemetry["pruned_tokens"]
    compression = telemetry["compression_ratio"]

    print(f"\nOptimization")
    print(f"  Files retained:     {telemetry['files_retained']}")
    print(f"  Files pruned:       {telemetry['files_pruned']}")
    print(f"  Output tokens:      {optimized_tokens:,}")
    print(f"  Compression:        {compression:.2f}x")
    print(f"  Tokens removed:     {telemetry['original_tokens'] - optimized_tokens:,}")
    print(f"  Retention:          {(optimized_tokens / telemetry['original_tokens']) * 100:.2f}%")

    required_files = [
        "src/api/router.py",
        "src/payments/service.py",
        "src/core/provider_loader.py",
        "src/core/payment_gateway.py",
        "src/core/interfaces.py",
        "src/domain/models.py",
        "src/security/audit.py",
        "src/security/permissions.py",
        "src/fraud/engine.py",
        "src/payments/idempotency.py",
        "src/core/decorators.py",
    ]

    missing_deps = [p for p in required_files if p not in optimized_files]

    # FALSE POSITIVE / NEGATIVE REJECTION CHECKS
    forbidden_decoys = [
        "src/legacy/payment_gateway.py",
        "src/payments/legacy_service.py"
    ]
    false_positives = [p for p in forbidden_decoys if p in optimized_files]

    print(f"\nDependency & Precision Analysis")
    print(f"  Required dep recall:  {len(required_files) - len(missing_deps)}/{len(required_files)}")
    print(f"  Forbidden decoys kept: {len(false_positives)} (Target: 0)")

    # RUNTIME MATERIALIZATION & SEMANTIC INVARIANT VERIFICATION
    runtime_tests = {
        "Normal payment": False,
        "Permission denial": False,
        "Fraud rejection": False,
        "Negative amount": False,
        "Limit rejection (Gateway)": False,
        "Idempotency": False,
        "Decorator Wrapper Chain": False,
    }
    
    temp_dir = tempfile.mkdtemp(prefix="occo_runtime_")
    
    try:
        for path, code in optimized_files.items():
            if not code.startswith("# File retained for structural path reference"):
                full_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(code)

        sys.path.insert(0, temp_dir)
        from src.api.router import handle_incoming_transaction, payment_service
        from src.core.payment_gateway import EnterprisePaymentGateway
        from src.domain.models import PaymentRequest

        # 1. Normal payment
        res1 = handle_incoming_transaction(
            {"amount": Decimal("1500"), "account": "ACC-001", "currency": "USD", "idempotency_key": "IDEMP-001"},
            {"id": "USER-001", "can_pay": True}
        )
        if res1["status"] == "SUCCESS":
            runtime_tests["Normal payment"] = True

        # 2. Permission failure
        try:
            handle_incoming_transaction(
                {"amount": Decimal("100"), "account": "ACC-004", "currency": "USD", "idempotency_key": "IDEMP-002"},
                {"id": "USER-004", "can_pay": False}
            )
        except Exception as e:
            if "permission" in str(e).lower():
                runtime_tests["Permission denial"] = True

        # 3. Fraud review path
        try:
            handle_incoming_transaction(
                {"amount": Decimal("6000"), "account": "ACC-002", "currency": "USD", "idempotency_key": "IDEMP-003"},
                {"id": "USER-002", "can_pay": True}
            )
        except Exception as e:
            if "manual review" in str(e).lower():
                runtime_tests["Fraud rejection"] = True

        # 4. Negative amount validation
        try:
            handle_incoming_transaction(
                {"amount": Decimal("-50"), "account": "ACC-003", "currency": "USD", "idempotency_key": "IDEMP-004"},
                {"id": "USER-003", "can_pay": True}
            )
        except Exception as e:
            if "invalid transaction amount" in str(e).lower():
                runtime_tests["Negative amount"] = True

        # 5. Isolated Gateway Security Limit Exceeded Test
        try:
            gateway = EnterprisePaymentGateway("MERCHANT_TEST", "SECRET")
            gateway.execute(
                PaymentRequest(
                    amount=Decimal("150000"),
                    account="ACC-LIMIT",
                    currency="USD",
                    user_id="USER-005",
                    idempotency_key="LIMIT-001"
                )
            )
        except ValueError as e:
            if "exceeds security limit" in str(e).lower():
                runtime_tests["Limit rejection (Gateway)"] = True

        # 6. Idempotency behavior preservation
        idemp_payload = {"amount": Decimal("250"), "account": "ACC-006", "currency": "USD", "idempotency_key": "IDEMP-REPEAT"}
        idemp_user = {"id": "USER-006", "can_pay": True}
        first_call = handle_incoming_transaction(idemp_payload, idemp_user)
        second_call = handle_incoming_transaction(idemp_payload, idemp_user)
        if first_call == second_call:
            runtime_tests["Idempotency"] = True

        # 7. Semantic Invariant: Verify Decorator Wrapper Chain (`@transactional` -> `@audited` -> `process`)
        proc_func = payment_service.process
        has_first_wrap = hasattr(proc_func, "__wrapped__")
        has_second_wrap = has_first_wrap and hasattr(proc_func.__wrapped__, "__wrapped__")
        if has_second_wrap:
            runtime_tests["Decorator Wrapper Chain"] = True

    except Exception as exc:
        print(f" [!] RUNTIME ERROR: {exc}")
        traceback.print_exc()
    finally:
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\nSemantic Invariant Verification")
    for test_name, passed in runtime_tests.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name:30}: {status}")

    legacy_count = sum(1 for p in optimized_files if p.startswith("src/legacy/") and p not in forbidden_decoys)
    gen_count = sum(1 for p in optimized_files if p.startswith("generated/"))

    print(f"\nNoise Elimination")
    print(f"  Legacy noise eliminated: {100 - legacy_count}/100")
    print(f"  Generated noise eliminated: {50 - gen_count}/50")
    print(f"  Lexical decoys rejected: {len(false_positives) == 0}")

    all_passed = all(runtime_tests.values()) and not missing_deps and len(false_positives) == 0

    print(f"\nRESULT")
    print(f"  Compression Ratio:       {compression:.2f}x")
    print(f"  Required Dep Recall:     {len(required_files) - len(missing_deps)}/{len(required_files)}")
    print(f"  False-Positive Rate:     {len(false_positives)}/2")
    print(f"  Behavioral Coverage:     {sum(1 for v in runtime_tests.values() if v)}/{len(runtime_tests)}")
    print(f"  Runtime Execution:       {'PASS' if all_passed else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    run_enterprise_optimizer_benchmark(CodeREAParser)