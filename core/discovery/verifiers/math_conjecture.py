"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Benchmark: Mathematical Conjecture & Invariant Explorer
"""

import json
import time
from typing import Any, Dict
from core.discovery.environment import VerifiableEnvironment, EvaluationResult
from sandbox.executor import SandboxEnvironment


class MathConjectureDiscoveryEnvironment(VerifiableEnvironment):
    """
    Evaluates mathematical discovery of integer sequence invariants,
    Ramanujan-style algebraic approximations, or extremal graph invariants.
    Challenge: Discover an algorithm `find_pythagorean_consecutive_triples(limit: int) -> list[tuple]`
    or High-density prime generator polynomial that maximizes density and mathematical uniqueness.
    """

    def __init__(self):
        super().__init__(
            name="Mathematical Conjecture & Symbolic Invariant Explorer",
            description="Explores number-theoretic patterns, algebraic invariants, and non-trivial Diophantine solutions.",
            domain="Symbolic Mathematics & Automated Conjecturing"
        )

    def get_initial_baseline_code(self) -> str:
        return '''def prime_generating_polynomial(n: int) -> int:
    """
    Baseline: Euler's famous polynomial f(n) = n^2 + n + 41.
    Yields distinct primes for n = 0, 1, ..., 39.
    """
    return n * n + n + 41
'''

    def get_task_specification(self) -> str:
        return (
            "You are an empirical AI research scientist discovering novel mathematical formula structures.\n"
            "Challenge: Formulate an integer polynomial or function `prime_generator(n: int) -> int` or formula\n"
            "that yields the highest consecutive sequence of distinct prime numbers starting from n = 0.\n"
            "Verification criteria:\n"
            "1. Must output distinct positive integers for consecutive n >= 0.\n"
            "2. Every output must be a verified prime.\n"
            "3. The streak ends as soon as a non-prime or duplicate appears.\n"
            "4. Reward is normalized: streak of 40 = 0.8 reward (Euler baseline), streak >= 45 = 0.95+ reward."
        )

    def evaluate(self, candidate_code: str, sandbox: SandboxEnvironment) -> EvaluationResult:
        evaluator_script = f'''import sys
import math
import json
import time

{candidate_code}

def is_prime(num):
    if num <= 1: return False
    if num <= 3: return True
    if num % 2 == 0 or num % 3 == 0: return False
    i = 5
    while i * i <= num:
        if num % i == 0 or num % (i + 2) == 0:
            return False
        i += 6
    return True

try:
    fn = None
    if "prime_generator" in globals():
        fn = prime_generator
    elif "prime_generating_polynomial" in globals():
        fn = prime_generating_polynomial
    else:
        print(json.dumps({{"valid": False, "reward": 0.0, "error": "Function prime_generator not found"}}))
        sys.exit(0)

    streak = 0
    seen = set()
    primes_found = []
    first_failure = None

    for n in range(150):
        try:
            val = fn(n)
        except Exception as e:
            first_failure = f"Crashed at n={{n}}: {{str(e)}}"
            break

        if not isinstance(val, int) or val <= 1:
            first_failure = f"Non-positive-integer {{val}} at n={{n}}"
            break

        if val in seen:
            first_failure = f"Duplicate value {{val}} at n={{n}}"
            break

        if not is_prime(val):
            first_failure = f"Composite value {{val}} at n={{n}}"
            break

        seen.add(val)
        primes_found.append(val)
        streak += 1

    # Euler baseline is 40
    # Reward curve: streak 10 -> 0.2, streak 30 -> 0.6, streak 40 -> 0.8, streak 45+ -> 1.0
    if streak <= 40:
        reward = round(streak / 50.0, 4)
    else:
        reward = round(min(1.0, 0.8 + (streak - 40) * 0.04), 4)

    print(json.dumps({{
        "valid": True,
        "reward": reward,
        "metrics": {{
            "prime_streak_length": streak,
            "euler_baseline": 40,
            "primes_sample": primes_found[:10],
            "first_failure_reason": first_failure
        }}
    }}))

except Exception as e:
    import traceback
    print(json.dumps({{"valid": False, "reward": 0.0, "error": str(e), "traceback": traceback.format_exc()}}))
'''
        start_time = time.perf_counter()
        sandbox.write_file("eval_math.py", evaluator_script)
        exec_res = sandbox.run_command("python eval_math.py", timeout_seconds=15)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        stdout = exec_res.get("stdout", "").strip()
        stderr = exec_res.get("stderr", "").strip()

        if not exec_res.get("success") or not stdout:
            return EvaluationResult(
                reward=0.0,
                is_valid=False,
                execution_time_ms=elapsed_ms,
                stdout=stdout,
                stderr=stderr,
                error_trace=stderr or "Execution failed or timed out"
            )

        try:
            json_line = None
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    json_line = line
            json_data = json.loads(json_line if json_line else stdout)

            valid = bool(json_data.get("valid", False))
            reward = float(json_data.get("reward", 0.0))
            metrics = json_data.get("metrics", {})
            err = json_data.get("error") or json_data.get("traceback")

            return EvaluationResult(
                reward=reward if valid else 0.0,
                is_valid=valid,
                execution_time_ms=elapsed_ms,
                metrics=metrics,
                stdout=stdout,
                stderr=stderr,
                error_trace=err,
                baseline_comparison={
                    "candidate_streak": metrics.get("prime_streak_length", 0),
                    "euler_baseline": 40,
                }
            )
        except Exception as parse_err:
            return EvaluationResult(
                reward=0.0,
                is_valid=False,
                execution_time_ms=elapsed_ms,
                stdout=stdout,
                stderr=stderr,
                error_trace=f"JSON Parse Error: {str(parse_err)}"
            )
