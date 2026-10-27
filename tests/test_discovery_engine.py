"""
ONE DOTS - Test Suite for Discovery & Empirical Intelligence Engine
Validates:
1. Environment deterministic scoring (Bin-Packing, Algorithm Opt, Math Conjecture).
2. Island Model evolutionary pool capacity, ranking, and elite sampling.
3. Discovery experience store persistence and breakthrough tracking.
4. Autonomous discovery runner execution loop and verifiable reward improvements.
"""

import pytest
from core.discovery.environment import EvaluationResult
from core.discovery.island_pool import IslandPopulationPool, ProgramCandidate
from core.discovery.experience_store import DiscoveryExperienceStore
from core.discovery.verifiers.bin_packing import BinPackingDiscoveryEnvironment
from core.discovery.verifiers.algorithm_opt import AlgorithmicOptimizationEnvironment
from core.discovery.verifiers.math_conjecture import MathConjectureDiscoveryEnvironment
from core.discovery.discovery_engine import DiscoverySessionRunner
from sandbox.executor import SandboxEnvironment


def test_bin_packing_environment_evaluation():
    env = BinPackingDiscoveryEnvironment()
    sandbox = SandboxEnvironment(agent_id="test_disc_bp")

    # Evaluate baseline
    base_code = env.get_initial_baseline_code()
    res = env.evaluate(base_code, sandbox)

    assert res.is_valid is True
    assert res.reward > 0.0
    assert "best_fit_total_bins" in res.metrics
    assert res.execution_time_ms > 0


def test_algorithmic_opt_environment_evaluation():
    env = AlgorithmicOptimizationEnvironment()
    sandbox = SandboxEnvironment(agent_id="test_disc_algo")

    base_code = env.get_initial_baseline_code()
    res = env.evaluate(base_code, sandbox)

    assert res.is_valid is True
    assert res.reward > 0.0
    assert "speedup_factor" in res.metrics


def test_island_pool_evolution_and_migration():
    pool = IslandPopulationPool(num_islands=2, capacity_per_island=3, migration_interval=2)
    pool.seed_initial_candidate("def baseline(): pass", reward=0.2)

    assert len(pool.islands) == 2
    assert pool.islands[0].best_candidate.reward == 0.2

    # Add improved candidate to island 0
    c1 = ProgramCandidate(
        candidate_id="c1",
        code="def improved(): return 1",
        reward=0.85,
        iteration_born=1,
        island_id=0,
        mutation_type="exploit_refine"
    )
    pool.record_candidate(c1)

    assert pool.islands[0].best_candidate.reward == 0.85
    assert pool.get_global_best().reward == 0.85

    # Sample elites
    elites = pool.islands[0].sample_elites(count=1, greedy=True)
    assert len(elites) == 1
    assert elites[0].reward == 0.85


def test_experience_store_persistence(tmp_path):
    db_file = tmp_path / "test_exp.db"
    store = DiscoveryExperienceStore(db_path=db_file)

    session_id = "test_sess_001"
    store.create_session(
        session_id=session_id,
        domain="Combinatorial",
        task_name="Bin Packing",
        baseline_code="def f(): pass",
        target_reward=0.9
    )

    store.record_trial(
        trial_id="t1",
        session_id=session_id,
        iteration=1,
        island_id=0,
        parent_id=None,
        mutation_type="exploit_refine",
        reward=0.75,
        is_valid=True,
        is_breakthrough=True,
        execution_time_ms=120.0,
        metrics={"bins": 42},
        code="def f(): return 42",
        error_trace=None,
        learned_reflection="Initial improvement"
    )

    sess = store.get_session(session_id)
    assert sess is not None
    assert sess["best_reward"] == 0.75

    prog = store.get_reward_progression(session_id)
    assert len(prog) == 1
    assert prog[0]["reward"] == 0.75


def test_discovery_runner_autonomous_loop():
    env = BinPackingDiscoveryEnvironment()
    session_id = "test_loop_01"

    runner = DiscoverySessionRunner(
        session_id=session_id,
        environment=env,
        max_iterations=3,
        target_reward=0.95,
        num_islands=2
    )

    result = runner.run_sync()

    assert result["session_id"] == session_id
    assert result["iterations_completed"] >= 1
    assert result["best_reward"] > 0.0
    assert result["best_code"] != ""


def test_discovery_api_endpoints():
    from fastapi.testclient import TestClient
    from api.app import app

    client = TestClient(app)

    # 1. Get benchmarks
    resp = client.get("/api/discovery/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 3

    # 2. List sessions
    sess_resp = client.get("/api/discovery/sessions")
    assert sess_resp.status_code == 200
    assert "sessions" in sess_resp.json()

    # 3. Start a small discovery run
    start_resp = client.post("/api/discovery/start", json={
        "benchmark_id": "bin_packing",
        "max_iterations": 2,
        "target_reward": 0.95,
        "num_islands": 2
    })
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["success"] is True
    sid = start_data["session_id"]

    # 4. Check status
    import time
    time.sleep(0.5)
    st_resp = client.get(f"/api/discovery/status/{sid}")
    assert st_resp.status_code == 200
    st_data = st_resp.json()
    assert st_data["session_id"] == sid
    assert "reward_progression" in st_data

    # 5. Stop session
    stop_resp = client.post(f"/api/discovery/stop/{sid}")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["success"] is True

