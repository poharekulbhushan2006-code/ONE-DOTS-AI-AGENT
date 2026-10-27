"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Benchmark: Algorithmic Optimization & Computational Speedup Discovery
"""

import json
import time
from typing import Any, Dict
from core.discovery.environment import VerifiableEnvironment, EvaluationResult
from sandbox.executor import SandboxEnvironment


class AlgorithmicOptimizationEnvironment(VerifiableEnvironment):
    """
    Evaluates automated algorithmic discovery for computational speedup.
    Challenge: Discover an optimized algorithm for Range Minimum Query (RMQ) / Segment queries
    or Fast Integer Multiplication/Search that maximizes throughput while proving 100% exact correctness.
    """

    def __init__(self):
        super().__init__(
            name="Algorithmic Optimization & Throughput Discovery",
            description="Discovers mathematically sound and asymptotic speedups for data structure queries and arithmetic pipelines.",
            domain="High-Performance Algorithmic Synthesis"
        )

    def get_initial_baseline_code(self) -> str:
        return '''class FastRangeQuery:
    """
    Baseline: Naive linear scan for Range Minimum Query (RMQ).
    Complexity: O(1) build, O(N) query.
    """
    def __init__(self, data: list[int]):
        self.data = list(data)

    def query(self, left: int, right: int) -> int:
        # Returns minimum element in range [left, right] inclusive
        sub = self.data[left : right + 1]
        return min(sub)
'''

    def get_task_specification(self) -> str:
        return (
            "You are an empirical algorithmic discovery scientist. Your task is to discover an optimal, "
            "sub-linear Range Minimum Query engine `FastRangeQuery(data: list[int])` with method `query(left: int, right: int) -> int`.\n"
            "Requirements:\n"
            "1. Given an array of integers `data` of length up to 50,000, build a data structure.\n"
            "2. The `query(left, right)` method MUST return the exact minimum element in `data[left : right + 1]` inclusive.\n"
            "3. You must maximize query throughput (e.g. Sparse Table O(1) query with O(N log N) build, or Fenwick/Segment Tree).\n"
            "4. Correctness must be 100% across all edge cases (single element ranges, negative numbers, entire array ranges).\n"
            "5. The reward scales with speedup relative to naive linear scan: 10x speedup -> 0.8 reward, 50x+ speedup -> 1.0 reward."
        )

    def evaluate(self, candidate_code: str, sandbox: SandboxEnvironment) -> EvaluationResult:
        evaluator_script = f'''import sys
import random
import time
import json

{candidate_code}

def test_correctness_and_speed():
    random.seed(1337)
    N = 25000
    Q = 20000
    test_data = [random.randint(-100000, 100000) for _ in range(N)]
    queries = []
    for _ in range(Q):
        l = random.randint(0, N - 1)
        r = random.randint(l, N - 1)
        queries.append((l, r))

    # 1. Correctness validation against ground-truth slice
    verifier_samples = queries[:200]
    try:
        solver = FastRangeQuery(test_data)
    except Exception as e:
        return {{"valid": False, "reward": 0.0, "error": f"Build crashed: {{str(e)}}"}}

    for l, r in verifier_samples:
        expected = min(test_data[l : r + 1])
        try:
            actual = solver.query(l, r)
        except Exception as e:
            return {{"valid": False, "reward": 0.0, "error": f"Query crashed at range [{{l}}, {{r}}]: {{str(e)}}"}}

        if actual != expected:
            return {{
                "valid": False,
                "reward": 0.0,
                "error": f"Incorrect answer for range [{{l}}, {{r}}]. Expected {{expected}}, got {{actual}}"
            }}

    # 2. Benchmark candidate throughput
    t0 = time.perf_counter()
    for l, r in queries:
        ans = solver.query(l, r)
    candidate_query_time = time.perf_counter() - t0

    # 3. Benchmark naive baseline throughput
    class NaiveBaseline:
        def __init__(self, d): self.d = d
        def query(self, l, r): return min(self.d[l : r + 1])
    
    nb = NaiveBaseline(test_data)
    t0 = time.perf_counter()
    # Sample a subset of baseline queries to keep eval fast
    sub_q = queries[:2000]
    for l, r in sub_q:
        ans = nb.query(l, r)
    naive_time_estimated = (time.perf_counter() - t0) * (Q / 2000.0)

    speedup = naive_time_estimated / max(1e-6, candidate_query_time)

    # Reward curve: 1x = 0.1, 5x = 0.5, 20x = 0.8, 50x+ = 1.0
    if speedup <= 1.0:
        reward = max(0.05, 0.1 * speedup)
    elif speedup < 10.0:
        reward = 0.1 + (speedup - 1.0) * (0.6 / 9.0)
    elif speedup < 50.0:
        reward = 0.7 + (speedup - 10.0) * (0.25 / 40.0)
    else:
        reward = min(1.0, 0.95 + min(0.05, (speedup - 50.0) * 0.001))

    return {{
        "valid": True,
        "reward": round(reward, 4),
        "metrics": {{
            "speedup_factor": round(speedup, 2),
            "candidate_time_sec": round(candidate_query_time, 4),
            "baseline_time_sec": round(naive_time_estimated, 4),
            "queries_executed": Q,
            "array_size": N
        }}
    }}

try:
    if "FastRangeQuery" not in globals():
        print(json.dumps({{"valid": False, "reward": 0.0, "error": "Class FastRangeQuery not found"}}))
    else:
        res = test_correctness_and_speed()
        print(json.dumps(res))
except Exception as e:
    import traceback
    print(json.dumps({{"valid": False, "reward": 0.0, "error": str(e), "traceback": traceback.format_exc()}}))
'''
        start_time = time.perf_counter()
        sandbox.write_file("eval_algo_opt.py", evaluator_script)
        exec_res = sandbox.run_command("python eval_algo_opt.py", timeout_seconds=20)
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
                    "speedup_factor": metrics.get("speedup_factor", 1.0),
                    "candidate_time": metrics.get("candidate_time_sec", 0.0),
                    "baseline_time": metrics.get("baseline_time_sec", 0.0),
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
