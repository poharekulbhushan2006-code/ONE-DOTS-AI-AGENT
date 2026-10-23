"""
ONE: Always-On Autonomous AI Agent System
Heartbeat & Continuous Background Scheduler
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
from config.settings import settings
from memory.state_store import state_store
from core.models import AgentStatus
from core.orchestrator import AgentOrchestrator


class HeartbeatScheduler:
    """
    Continuous background loop that monitors all registered ONE agents,
    evaluates scheduled cadences, and triggers autonomous execution ticks.
    """

    def __init__(self, check_interval_seconds: int = 5):
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the continuous heartbeat worker."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        print(f"[Heartbeat] ONE Scheduler active (polling every {self.check_interval_seconds}s)")

    async def stop(self):
        """Stops the heartbeat worker cleanly."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[Heartbeat] ONE Scheduler stopped")

    async def _loop(self):
        while self.is_running:
            try:
                await self._evaluate_agents()
            except Exception as e:
                print(f"[Heartbeat] Error during agent evaluation: {e}")
            await asyncio.sleep(self.check_interval_seconds)

    async def _evaluate_agents(self):
        agents = state_store.list_agents()
        now = datetime.now(timezone.utc)

        for agent in agents:
            # Skip agents that are paused or waiting for human approval
            if agent.status in [AgentStatus.PAUSED, AgentStatus.WAITING_APPROVAL, AgentStatus.RUNNING]:
                continue

            should_tick = False

            # Check if agent is due for a tick
            if agent.next_tick_at is None:
                should_tick = True
            elif agent.next_tick_at <= now:
                should_tick = True

            if should_tick:
                # Trigger tick asynchronously
                asyncio.create_task(self._run_agent_tick(agent.id))

    async def _run_agent_tick(self, agent_id: str):
        try:
            orchestrator = AgentOrchestrator(agent_id)
            await orchestrator.execute_tick()
        except Exception as e:
            print(f"[Heartbeat] Failed execution tick for agent {agent_id}: {e}")


heartbeat = HeartbeatScheduler()
