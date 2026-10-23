"""
ONE: Always-On Autonomous AI Agent System
SQLite-based Persistent State Store & Checkpointing
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

from config.settings import settings
from core.models import (
    OneAgent,
    AgentStatus,
    LifecycleStage,
    DecisionRequest,
    DecisionStatus,
    RiskLevel,
    TaskStep,
    ReportItem,
)


class StateStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                responsibility TEXT NOT NULL,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                schedule_interval_seconds INTEGER NOT NULL,
                last_tick_at TEXT,
                next_tick_at TEXT,
                total_ticks INTEGER DEFAULT 0,
                successful_cycles INTEGER DEFAULT 0,
                pending_approval_id TEXT,
                context_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # Task Steps (Action History)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_steps (
                step_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                action TEXT NOT NULL,
                tool TEXT,
                inputs_json TEXT,
                output_json TEXT,
                success INTEGER NOT NULL,
                error_message TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)

            # Decision Requests (Escalations)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                description TEXT NOT NULL,
                proposed_payload_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                human_notes TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)

            # Reports & Deliverables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                format TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)

            # Checkpoints (State Snapshots)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)
            conn.commit()

    # ------------------ Agent CRUD ------------------

    def save_agent(self, agent: OneAgent) -> OneAgent:
        agent.updated_at = datetime.now(timezone.utc)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO agents (
                id, name, responsibility, status, current_stage,
                schedule_interval_seconds, last_tick_at, next_tick_at,
                total_ticks, successful_cycles, pending_approval_id,
                context_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                responsibility=excluded.responsibility,
                status=excluded.status,
                current_stage=excluded.current_stage,
                schedule_interval_seconds=excluded.schedule_interval_seconds,
                last_tick_at=excluded.last_tick_at,
                next_tick_at=excluded.next_tick_at,
                total_ticks=excluded.total_ticks,
                successful_cycles=excluded.successful_cycles,
                pending_approval_id=excluded.pending_approval_id,
                context_json=excluded.context_json,
                updated_at=excluded.updated_at
            """, (
                agent.id,
                agent.name,
                agent.responsibility,
                agent.status.value,
                agent.current_stage.value,
                agent.schedule_interval_seconds,
                agent.last_tick_at.isoformat() if agent.last_tick_at else None,
                agent.next_tick_at.isoformat() if agent.next_tick_at else None,
                agent.total_ticks,
                agent.successful_cycles,
                agent.pending_approval_id,
                json.dumps(agent.context),
                agent.created_at.isoformat(),
                agent.updated_at.isoformat(),
            ))
            conn.commit()
        return agent

    def get_agent(self, agent_id: str) -> Optional[OneAgent]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_agent(row)

    def list_agents(self) -> List[OneAgent]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_agent(r) for r in rows]

    def _row_to_agent(self, row: sqlite3.Row) -> OneAgent:
        return OneAgent(
            id=row["id"],
            name=row["name"],
            responsibility=row["responsibility"],
            status=AgentStatus(row["status"]),
            current_stage=LifecycleStage(row["current_stage"]),
            schedule_interval_seconds=row["schedule_interval_seconds"],
            last_tick_at=datetime.fromisoformat(row["last_tick_at"]) if row["last_tick_at"] else None,
            next_tick_at=datetime.fromisoformat(row["next_tick_at"]) if row["next_tick_at"] else None,
            total_ticks=row["total_ticks"],
            successful_cycles=row["successful_cycles"],
            pending_approval_id=row["pending_approval_id"],
            context=json.loads(row["context_json"]) if row["context_json"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------ Steps & History ------------------

    def record_step(self, agent_id: str, step: TaskStep):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO task_steps (
                step_id, agent_id, stage, action, tool,
                inputs_json, output_json, success, error_message, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                step.step_id,
                agent_id,
                step.stage.value,
                step.action,
                step.tool,
                json.dumps(step.inputs) if step.inputs else None,
                json.dumps(step.output, default=str) if step.output is not None else None,
                1 if step.success else 0,
                step.error_message,
                step.timestamp.isoformat(),
            ))
            conn.commit()

    def get_agent_steps(self, agent_id: str, limit: int = 50) -> List[TaskStep]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM task_steps WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (agent_id, limit))
            rows = cursor.fetchall()
            steps = []
            for r in rows:
                steps.append(TaskStep(
                    step_id=r["step_id"],
                    stage=LifecycleStage(r["stage"]),
                    action=r["action"],
                    tool=r["tool"],
                    inputs=json.loads(r["inputs_json"]) if r["inputs_json"] else None,
                    output=json.loads(r["output_json"]) if r["output_json"] else None,
                    success=bool(r["success"]),
                    error_message=r["error_message"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                ))
            return steps

    # ------------------ Decision Requests ------------------

    def create_decision_request(self, req: DecisionRequest) -> DecisionRequest:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO decisions (
                id, agent_id, action_type, tool_name, description,
                proposed_payload_json, risk_level, status, created_at, decided_at, human_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req.id,
                req.agent_id,
                req.action_type,
                req.tool_name,
                req.description,
                json.dumps(req.proposed_payload),
                req.risk_level.value,
                req.status.value,
                req.created_at.isoformat(),
                req.decided_at.isoformat() if req.decided_at else None,
                req.human_notes,
            ))
            # update agent pending_approval_id and status
            cursor.execute("""
            UPDATE agents SET status = ?, pending_approval_id = ?, updated_at = ?
            WHERE id = ?
            """, (
                AgentStatus.WAITING_APPROVAL.value,
                req.id,
                datetime.now(timezone.utc).isoformat(),
                req.agent_id,
            ))
            conn.commit()
        return req

    def resolve_decision(self, decision_id: str, status: DecisionStatus, human_notes: Optional[str] = None) -> Optional[DecisionRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            agent_id = row["agent_id"]
            now_iso = datetime.now(timezone.utc).isoformat()
            
            cursor.execute("""
            UPDATE decisions SET status = ?, decided_at = ?, human_notes = ?
            WHERE id = ?
            """, (status.value, now_iso, human_notes, decision_id))
            
            # Free the agent to resume or sleep
            cursor.execute("""
            UPDATE agents SET status = ?, pending_approval_id = NULL, updated_at = ?
            WHERE id = ?
            """, (
                AgentStatus.RUNNING.value if status == DecisionStatus.APPROVED else AgentStatus.IDLE.value,
                now_iso,
                agent_id,
            ))
            conn.commit()
            
            return self.get_decision(decision_id)

    def get_decision(self, decision_id: str) -> Optional[DecisionRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DecisionRequest(
                id=row["id"],
                agent_id=row["agent_id"],
                action_type=row["action_type"],
                tool_name=row["tool_name"],
                description=row["description"],
                proposed_payload=json.loads(row["proposed_payload_json"]),
                risk_level=RiskLevel(row["risk_level"]),
                status=DecisionStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                decided_at=datetime.fromisoformat(row["decided_at"]) if row["decided_at"] else None,
                human_notes=row["human_notes"],
            )

    def list_pending_decisions(self) -> List[DecisionRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE status = 'pending' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                DecisionRequest(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    action_type=r["action_type"],
                    tool_name=r["tool_name"],
                    description=r["description"],
                    proposed_payload=json.loads(r["proposed_payload_json"]),
                    risk_level=RiskLevel(r["risk_level"]),
                    status=DecisionStatus(r["status"]),
                    created_at=datetime.fromisoformat(r["created_at"]),
                    decided_at=datetime.fromisoformat(r["decided_at"]) if r["decided_at"] else None,
                    human_notes=r["human_notes"],
                )
                for r in rows
            ]

    # ------------------ Reports ------------------

    def save_report(self, report: ReportItem) -> ReportItem:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO reports (id, agent_id, title, summary, content, format, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id,
                report.agent_id,
                report.title,
                report.summary,
                report.content,
                report.format,
                report.created_at.isoformat(),
            ))
            conn.commit()
        return report

    def get_agent_reports(self, agent_id: str, limit: int = 20) -> List[ReportItem]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?", (agent_id, limit))
            rows = cursor.fetchall()
            return [
                ReportItem(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    title=r["title"],
                    summary=r["summary"],
                    content=r["content"],
                    format=r["format"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]


state_store = StateStore()
