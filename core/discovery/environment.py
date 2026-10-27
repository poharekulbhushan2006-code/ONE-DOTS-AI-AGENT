"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Inspired by David Silver's Ineffable Intelligence (Reinforcement Learning from Experience & Verifiable Simulators)
Base Environment Protocol & Verifier Interfaces
"""

import abc
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from sandbox.executor import SandboxEnvironment


@dataclass
class EvaluationResult:
    """Deterministic, objective verification result returned by the environment."""
    reward: float  # Objective scalar score in [0.0, 1.0]
    is_valid: bool  # Passed all verification unit tests
    execution_time_ms: float  # Wall-clock runtime in milliseconds
    metrics: Dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    error_trace: Optional[str] = None
    baseline_comparison: Optional[Dict[str, float]] = None


class VerifiableEnvironment(abc.ABC):
    """
    Abstract base class for a zero-trust simulation environment.
    Evaluates candidate code or hypotheses through objective sandbox execution.
    Never relies on human subjective ratings; relies strictly on verifiable ground truth.
    """

    def __init__(self, name: str, description: str, domain: str):
        self.name = name
        self.description = description
        self.domain = domain

    @abc.abstractmethod
    def get_initial_baseline_code(self) -> str:
        """Returns standard textbook or naive baseline implementation."""
        pass

    @abc.abstractmethod
    def get_task_specification(self) -> str:
        """Returns the scientific or algorithmic challenge prompt for the proposer model."""
        pass

    @abc.abstractmethod
    def evaluate(self, candidate_code: str, sandbox: SandboxEnvironment) -> EvaluationResult:
        """
        Executes candidate code inside the isolated sandbox, tests against
        unseen test harnesses, and calculates the verifiable reward.
        """
        pass
