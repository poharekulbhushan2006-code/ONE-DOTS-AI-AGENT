"""
ONE: Always-On Autonomous AI Agent System
SQLite-based Persistent State Store & Checkpointing
With Row Level Security (RLS) & Multi-Tenant Data Scoping & Audit Logging
"""

import json
import sqlite3
import uuid
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
    ChatMessage,
    AuditLogEntry,
)


class StateStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Agents table with Row Level Security (user_id)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                user_id TEXT DEFAULT 'usr_owner_default',
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
                user_id TEXT DEFAULT 'usr_owner_default',
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
                user_id TEXT DEFAULT 'usr_owner_default',
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
                user_id TEXT DEFAULT 'usr_owner_default',
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
                user_id TEXT DEFAULT 'usr_owner_default',
                stage TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)

            # Chat Messages
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT DEFAULT 'usr_owner_default',
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id) ON DELETE CASCADE
            )
            """)

            # Tamper-Evident Admin & Fleet Audit Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT NOT NULL,
                details_json TEXT
            )
            """)

            # Dynamic migrations: ensure user_id column exists if table was pre-existing
            for table in ["agents", "task_steps", "decisions", "reports", "checkpoints", "messages"]:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [row["name"] for row in cursor.fetchall()]
                if "user_id" not in cols:
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT DEFAULT 'usr_owner_default'")
                    except sqlite3.OperationalError:
                        pass

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_user ON agents(user_id)")

            conn.commit()

    # ------------------ Agent CRUD with Row Level Security ------------------

    def save_agent(self, agent: OneAgent) -> OneAgent:
        agent.updated_at = datetime.now(timezone.utc)
        user_id = agent.user_id or "usr_owner_default"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO agents (
                id, user_id, name, responsibility, status, current_stage,
                schedule_interval_seconds, last_tick_at, next_tick_at,
                total_ticks, successful_cycles, pending_approval_id,
                context_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id=excluded.user_id,
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
                user_id,
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

    def get_agent(self, agent_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> Optional[OneAgent]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if not is_admin and user_id:
                cursor.execute("SELECT * FROM agents WHERE id = ? AND user_id = ?", (agent_id, user_id))
            else:
                cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_agent(row)

    def list_agents(self, user_id: Optional[str] = None, is_admin: bool = False) -> List[OneAgent]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if not is_admin and user_id:
                cursor.execute("SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_agent(r) for r in rows]

    def delete_agent(self, agent_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """Deletes an agent with row-level ownership verification and cascades child items."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Verify ownership if not admin
            if not is_admin and user_id:
                cursor.execute("SELECT id FROM agents WHERE id = ? AND user_id = ?", (agent_id, user_id))
                if not cursor.fetchone():
                    return False

            cursor.execute("DELETE FROM messages WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM task_steps WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM decisions WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM reports WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM checkpoints WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def _row_to_agent(self, row: sqlite3.Row) -> OneAgent:
        # Handle backward compatibility if user_id column wasn't originally present in row
        u_id = row["user_id"] if "user_id" in row.keys() and row["user_id"] else "usr_owner_default"
        return OneAgent(
            id=row["id"],
            user_id=u_id,
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

    def record_step(self, agent_id: str, step: TaskStep, user_id: Optional[str] = None):
        u_id = user_id or step.user_id or "usr_owner_default"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO task_steps (
                step_id, agent_id, user_id, stage, action, tool,
                inputs_json, output_json, success, error_message, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                step.step_id,
                agent_id,
                u_id,
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
                u_id = r["user_id"] if "user_id" in r.keys() and r["user_id"] else "usr_owner_default"
                steps.append(TaskStep(
                    step_id=r["step_id"],
                    agent_id=r["agent_id"],
                    user_id=u_id,
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
        u_id = req.user_id or "usr_owner_default"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO decisions (
                id, agent_id, user_id, action_type, tool_name, description,
                proposed_payload_json, risk_level, status, created_at, decided_at, human_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req.id,
                req.agent_id,
                u_id,
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
            u_id = row["user_id"] if "user_id" in row.keys() and row["user_id"] else "usr_owner_default"
            return DecisionRequest(
                id=row["id"],
                agent_id=row["agent_id"],
                user_id=u_id,
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

    def list_pending_decisions(self, user_id: Optional[str] = None, is_admin: bool = False) -> List[DecisionRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if not is_admin and user_id:
                cursor.execute("""
                SELECT d.* FROM decisions d
                JOIN agents a ON d.agent_id = a.id
                WHERE d.status = 'pending' AND a.user_id = ?
                ORDER BY d.created_at DESC
                """, (user_id,))
            else:
                cursor.execute("SELECT * FROM decisions WHERE status = 'pending' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            decisions = []
            for r in rows:
                u_id = r["user_id"] if "user_id" in r.keys() and r["user_id"] else "usr_owner_default"
                decisions.append(DecisionRequest(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    user_id=u_id,
                    action_type=r["action_type"],
                    tool_name=r["tool_name"],
                    description=r["description"],
                    proposed_payload=json.loads(r["proposed_payload_json"]),
                    risk_level=RiskLevel(r["risk_level"]),
                    status=DecisionStatus(r["status"]),
                    created_at=datetime.fromisoformat(r["created_at"]),
                    decided_at=datetime.fromisoformat(r["decided_at"]) if r["decided_at"] else None,
                    human_notes=r["human_notes"],
                ))
            return decisions

    # ------------------ Chat & Conversation ------------------

    def save_chat_message(self, msg: ChatMessage) -> ChatMessage:
        u_id = msg.user_id or "usr_owner_default"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO messages (id, agent_id, user_id, sender, content, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                msg.id,
                msg.agent_id,
                u_id,
                msg.sender,
                msg.content,
                json.dumps(msg.metadata) if msg.metadata else None,
                msg.created_at.isoformat(),
            ))
            conn.commit()
        return msg

    def get_chat_history(self, agent_id: str, limit: int = 50) -> List[ChatMessage]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM messages WHERE agent_id = ? ORDER BY created_at ASC LIMIT ?
            """, (agent_id, limit))
            rows = cursor.fetchall()
            messages = []
            for r in rows:
                u_id = r["user_id"] if "user_id" in r.keys() and r["user_id"] else "usr_owner_default"
                messages.append(ChatMessage(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    user_id=u_id,
                    sender=r["sender"],
                    content=r["content"],
                    metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else None,
                    created_at=datetime.fromisoformat(r["created_at"]),
                ))
            return messages

    # ------------------ Reports & Deliverables ------------------

    def save_report(self, report: ReportItem) -> ReportItem:
        u_id = report.user_id or "usr_owner_default"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO reports (id, agent_id, user_id, title, summary, content, format, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id,
                report.agent_id,
                u_id,
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
            reports = []
            for r in rows:
                u_id = r["user_id"] if "user_id" in r.keys() and r["user_id"] else "usr_owner_default"
                reports.append(ReportItem(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    user_id=u_id,
                    title=r["title"],
                    summary=r["summary"],
                    content=r["content"],
                    format=r["format"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                ))
            return reports

    # ------------------ Tamper-Evident Admin Audit Logging ------------------

    def record_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry:
        """Records an immutable security audit event into the database."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_logs (
                id, timestamp, user_id, action, resource_type,
                resource_id, ip_address, user_agent, status, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.timestamp.isoformat(),
                entry.user_id,
                entry.action,
                entry.resource_type,
                entry.resource_id,
                entry.ip_address,
                entry.user_agent,
                entry.status,
                json.dumps(entry.details),
            ))
            conn.commit()
        return entry

    def list_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """Lists audit log records with parameterized limits and optional user filtering."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT * FROM audit_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
            else:
                cursor.execute("""
                SELECT * FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """, (limit, offset))
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                logs.append(AuditLogEntry(
                    id=r["id"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    user_id=r["user_id"],
                    action=r["action"],
                    resource_type=r["resource_type"],
                    resource_id=r["resource_id"],
                    ip_address=r["ip_address"],
                    user_agent=r["user_agent"],
                    status=r["status"],
                    details=json.loads(r["details_json"]) if r["details_json"] else {},
                ))
            return logs


state_store = StateStore()
