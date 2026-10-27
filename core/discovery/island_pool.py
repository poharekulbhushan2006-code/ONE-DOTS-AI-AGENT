"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Island Model Evolutionary Program Pool (DeepMind FunSearch Architecture)
"""

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProgramCandidate:
    candidate_id: str
    code: str
    reward: float
    iteration_born: int
    island_id: int
    parent_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    mutation_type: str = "initial"


class EvolutionaryIsland:
    """An isolated evolutionary population cluster."""
    def __init__(self, island_id: int, max_capacity: int = 10):
        self.island_id = island_id
        self.max_capacity = max_capacity
        self.candidates: List[ProgramCandidate] = []

    def add(self, candidate: ProgramCandidate) -> bool:
        """Adds candidate to island, keeping only top performers up to max_capacity."""
        self.candidates.append(candidate)
        # Sort descending by reward
        self.candidates.sort(key=lambda c: c.reward, reverse=True)
        if len(self.candidates) > self.max_capacity:
            self.candidates = self.candidates[: self.max_capacity]
        return candidate in self.candidates

    def sample_elites(self, count: int = 1, temperature: float = 0.5, greedy: bool = False) -> List[ProgramCandidate]:
        """
        Samples candidates weighted by reward using Softmax temperature sampling.
        High temperature = more exploratory; low temperature / greedy = exploits highest reward.
        """
        if not self.candidates:
            return []
        if len(self.candidates) <= count:
            return list(self.candidates)
        if greedy or temperature <= 0.05:
            return list(self.candidates[:count])

        rewards = [c.reward for c in self.candidates]
        max_r = max(rewards)
        # Avoid numerical overflow
        exp_scores = [math.exp((r - max_r) / max(1e-4, temperature)) for r in rewards]
        total = sum(exp_scores)
        probs = [s / total for s in exp_scores]

        # Weighted sample without replacement
        selected = []
        indices = list(range(len(self.candidates)))
        for _ in range(min(count, len(self.candidates))):
            idx = random.choices(indices, weights=[probs[i] for i in indices], k=1)[0]
            selected.append(self.candidates[idx])
            indices.remove(idx)
        return selected

    @property
    def best_candidate(self) -> Optional[ProgramCandidate]:
        return self.candidates[0] if self.candidates else None


class IslandPopulationPool:
    """
    Manages multiple distinct islands with periodic migration,
    replicating the FunSearch distributed evolutionary discovery paradigm.
    """

    def __init__(self, num_islands: int = 3, capacity_per_island: int = 8, migration_interval: int = 10):
        self.num_islands = max(1, num_islands)
        self.capacity_per_island = capacity_per_island
        self.migration_interval = migration_interval
        self.islands: List[EvolutionaryIsland] = [
            EvolutionaryIsland(i, capacity_per_island) for i in range(self.num_islands)
        ]
        self.active_island_idx = 0
        self.total_evaluations = 0

    def seed_initial_candidate(self, code: str, reward: float = 0.1):
        """Seeds all islands with the initial baseline implementation."""
        for island in self.islands:
            candidate = ProgramCandidate(
                candidate_id="seed_baseline",
                code=code,
                reward=reward,
                iteration_born=0,
                island_id=island.island_id,
                mutation_type="baseline"
            )
            island.add(candidate)

    def select_island(self) -> EvolutionaryIsland:
        """Round-robin or stochastic island selection."""
        island = self.islands[self.active_island_idx]
        self.active_island_idx = (self.active_island_idx + 1) % self.num_islands
        return island

    def record_candidate(self, candidate: ProgramCandidate):
        """Records a new candidate in its assigned island."""
        self.total_evaluations += 1
        island = self.islands[candidate.island_id % self.num_islands]
        island.add(candidate)

        # Trigger migration between islands periodically
        if self.total_evaluations % self.migration_interval == 0:
            self.migrate_elites()

    def migrate_elites(self):
        """
        Migrates the best candidate from each island to an adjacent peer island.
        Cross-pollinates genetic breakthroughs across isolated populations.
        """
        if self.num_islands <= 1:
            return
        for i in range(self.num_islands):
            best = self.islands[i].best_candidate
            if best:
                target_island = self.islands[(i + 1) % self.num_islands]
                migrated = ProgramCandidate(
                    candidate_id=f"migrated_{best.candidate_id}",
                    code=best.code,
                    reward=best.reward,
                    iteration_born=best.iteration_born,
                    island_id=target_island.island_id,
                    parent_id=best.candidate_id,
                    metrics=dict(best.metrics),
                    mutation_type="migration"
                )
                target_island.add(migrated)

    def get_global_best(self) -> Optional[ProgramCandidate]:
        """Returns the highest-scoring candidate discovered across all islands."""
        all_bests = [i.best_candidate for i in self.islands if i.best_candidate is not None]
        if not all_bests:
            return None
        return max(all_bests, key=lambda c: c.reward)

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns summary metrics across all islands."""
        return {
            "total_islands": self.num_islands,
            "total_evaluations": self.total_evaluations,
            "global_best_reward": self.get_global_best().reward if self.get_global_best() else 0.0,
            "islands": [
                {
                    "island_id": i.island_id,
                    "population": len(i.candidates),
                    "best_reward": i.best_candidate.reward if i.best_candidate else 0.0,
                    "avg_reward": round(sum(c.reward for c in i.candidates) / len(i.candidates), 4) if i.candidates else 0.0
                }
                for i in self.islands
            ]
        }
