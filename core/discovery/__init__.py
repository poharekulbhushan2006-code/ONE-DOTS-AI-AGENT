"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Inspired by David Silver's Ineffable Intelligence
"""

from core.discovery.environment import VerifiableEnvironment, EvaluationResult
from core.discovery.island_pool import IslandPopulationPool, ProgramCandidate
from core.discovery.experience_store import DiscoveryExperienceStore
from core.discovery.discovery_engine import (
    DiscoverySessionRunner,
    DiscoveryEngineManager,
    discovery_manager,
)

__all__ = [
    "VerifiableEnvironment",
    "EvaluationResult",
    "IslandPopulationPool",
    "ProgramCandidate",
    "DiscoveryExperienceStore",
    "DiscoverySessionRunner",
    "DiscoveryEngineManager",
    "discovery_manager",
]
