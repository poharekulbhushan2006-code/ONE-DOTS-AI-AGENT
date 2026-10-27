"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Benchmark: DeepMind FunSearch Online 1D Bin-Packing Heuristic Discovery
"""

import json
import time
from typing import Any, Dict
from core.discovery.environment import VerifiableEnvironment, EvaluationResult
from sandbox.executor import SandboxEnvironment


class BinPackingDiscoveryEnvironment(VerifiableEnvironment):
    """
    Evaluates online 1D bin-packing heuristics inspired by DeepMind's FunSearch paper.
    Discovers priority/selection scoring functions that maximize packing density
    across diverse probability distributions (Weibull, Uniform, Gaussian).
    """

    def __init__(self):
        super().__init__(
            name="Online 1D Bin Packing Heuristic Discovery",
            description="Discovers novel bin allocation heuristics that outperform standard Best-Fit (DeepMind FunSearch benchmark).",
            domain="Combinatorial Optimization & Algorithmic Discovery"
        )

    def get_initial_baseline_code(self) -> str:
        return '''def select_bin(item_weight: float, bin_remaining_capacities: list[float], bin_capacity: float = 1.0) -> int:
    """
    Baseline: Standard Best-Fit (BF) heuristic.
    Places item in the bin with the least remaining capacity that fits the item.
    Returns bin index (0-indexed), or -1 to open a new bin.
    """
    best_idx = -1
    min_space = float('inf')
    
    for idx, rem in enumerate(bin_remaining_capacities):
        if rem >= item_weight:
            space_left = rem - item_weight
            if space_left < min_space:
                min_space = space_left
                best_idx = idx
                
    return best_idx
'''

    def get_task_specification(self) -> str:
        return (
            "You are an empirical reinforcement learning AI scientist. Your goal is to discover a novel "
            "online 1D bin packing heuristic `select_bin(item_weight: float, bin_remaining_capacities: list[float], bin_capacity: float = 1.0) -> int`.\n"
            "Requirements:\n"
            "1. Given an incoming item weight (0 < item_weight <= bin_capacity) and the list of current remaining capacities of open bins,\n"
            "   return the index of the open bin to place it in, or -1 to open a new bin.\n"
            "2. The heuristic MUST beat or match Best-Fit by packing items more tightly across Weibull, Gaussian, and Bimodal item streams.\n"
            "3. You must not import external libraries. Keep execution fast (under 1 second).\n"
            "4. Consider scoring bins by non-linear capacity matching, gap penalties, or fractional item size affinities."
        )

    def evaluate(self, candidate_code: str, sandbox: SandboxEnvironment) -> EvaluationResult:
        """
        Executes the candidate heuristic inside the isolated sandbox against
        a multi-distribution empirical test battery.
        """
        evaluator_script = f'''import sys
import random
import math
import json
import time

{candidate_code}

def run_simulation(heuristic_fn, item_stream, bin_capacity=1.0):
    bins = []  # tracks remaining capacity in each open bin
    for item in item_stream:
        if item > bin_capacity or item <= 0:
            continue
        idx = heuristic_fn(item, list(bins), bin_capacity)
        if idx is not None and 0 <= idx < len(bins) and bins[idx] >= item - 1e-9:
            bins[idx] -= item
        else:
            # open new bin
            bins.append(bin_capacity - item)
    return len(bins)

def best_fit_baseline(item_weight, bin_capacities, bin_capacity=1.0):
    best_idx = -1
    min_space = float('inf')
    for idx, rem in enumerate(bin_capacities):
        if rem >= item_weight - 1e-9:
            space = rem - item_weight
            if space < min_space:
                min_space = space
                best_idx = idx
    return best_idx

def worst_fit_baseline(item_weight, bin_capacities, bin_capacity=1.0):
    worst_idx = -1
    max_space = -1.0
    for idx, rem in enumerate(bin_capacities):
        if rem >= item_weight - 1e-9:
            if rem > max_space:
                max_space = rem
                worst_idx = idx
    return worst_idx

def generate_test_suites():
    random.seed(42)
    suites = {{}}
    # Suite 1: Uniform distribution [0.1, 0.7]
    suites["uniform"] = [round(random.uniform(0.1, 0.7), 4) for _ in range(400)]
    # Suite 2: Weibull heavy tail (small & huge mix)
    suites["weibull"] = [min(0.95, max(0.05, round(random.weibullvariate(0.35, 1.8), 4))) for _ in range(400)]
    # Suite 3: Bimodal (clustering around 0.2 and 0.45)
    bimodal = []
    for _ in range(400):
        if random.random() < 0.5:
            bimodal.append(round(random.gauss(0.2, 0.05), 4))
        else:
            bimodal.append(round(random.gauss(0.45, 0.08), 4))
    suites["bimodal"] = [min(0.9, max(0.05, x)) for x in bimodal]
    return suites

try:
    if "select_bin" not in globals():
        print(json.dumps({{"error": "Function select_bin not defined", "valid": False, "reward": 0.0}}))
        sys.exit(0)

    # 1. Edge-case safety checks
    test_bins = [0.8, 0.4, 0.1]
    res1 = select_bin(0.35, test_bins, 1.0)
    if not (isinstance(res1, int) or res1 is None):
        print(json.dumps({{"error": "select_bin returned non-integer value", "valid": False, "reward": 0.0}}))
        sys.exit(0)

    # 2. Run benchmark across all test suites
    suites = generate_test_suites()
    candidate_bins_total = 0
    bf_bins_total = 0
    wf_bins_total = 0
    lower_bound_total = 0

    suite_results = {{}}

    for name, stream in suites.items():
        total_weight = sum(stream)
        lower_bound = math.ceil(total_weight)
        lower_bound_total += lower_bound

        c_bins = run_simulation(select_bin, stream)
        bf_bins = run_simulation(best_fit_baseline, stream)
        wf_bins = run_simulation(worst_fit_baseline, stream)

        candidate_bins_total += c_bins
        bf_bins_total += bf_bins
        wf_bins_total += wf_bins

        suite_results[name] = {{
            "candidate_bins": c_bins,
            "best_fit_bins": bf_bins,
            "worst_fit_bins": wf_bins,
            "theoretical_lower_bound": lower_bound,
            "excess_over_opt": c_bins - lower_bound
        }}

    # Objective Verifiable Reward Formula
    # Worst-fit is 0 reward baseline. Lower bound is 1.0 reward ceiling.
    span = max(1, wf_bins_total - lower_bound_total)
    saved = wf_bins_total - candidate_bins_total
    raw_reward = max(0.0, min(1.0, saved / span))

    # Bonus reward if candidate strictly outperforms or matches Best-Fit
    bf_diff = bf_bins_total - candidate_bins_total
    reward = round(raw_reward, 4)

    print(json.dumps({{
        "valid": True,
        "reward": reward,
        "metrics": {{
            "candidate_total_bins": candidate_bins_total,
            "best_fit_total_bins": bf_bins_total,
            "worst_fit_total_bins": wf_bins_total,
            "theoretical_lower_bound": lower_bound_total,
            "bins_saved_vs_worst": saved,
            "delta_vs_best_fit": bf_diff,
            "suite_breakdown": suite_results
        }}
    }}))

except Exception as e:
    import traceback
    print(json.dumps({{
        "valid": False,
        "reward": 0.0,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}))
'''
        start_time = time.perf_counter()
        sandbox.write_file("eval_bin_packing.py", evaluator_script)
        exec_res = sandbox.run_command("python eval_bin_packing.py", timeout_seconds=15)
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

        # Parse JSON output from sandbox execution
        try:
            # Find last JSON object line in stdout
            json_line = None
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    json_line = line
            
            if not json_line:
                json_data = json.loads(stdout)
            else:
                json_data = json.loads(json_line)

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
                    "best_fit_bins": metrics.get("best_fit_total_bins", 0),
                    "worst_fit_bins": metrics.get("worst_fit_total_bins", 0),
                    "candidate_bins": metrics.get("candidate_total_bins", 0),
                }
            )
        except Exception as parse_err:
            return EvaluationResult(
                reward=0.0,
                is_valid=False,
                execution_time_ms=elapsed_ms,
                stdout=stdout,
                stderr=stderr,
                error_trace=f"JSON Parse Error: {str(parse_err)}\nRaw output: {stdout}"
            )
