"""
ONE DOTS - Discovery & Empirical Intelligence Engine
Empirical Experience Store & Failure Reflection Memory (SQLite WAL Database)
"""

import json
import sqlite3
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import settings


class DiscoveryExperienceStore:
    """
    Durable, queryable persistence for all discovery attempts, stack traces,
    breakthrough candidates, and learned negative constraints.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.DATA_DIR / "discovery_experience.db")
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS discovery_sessions (
                    session_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    target_reward REAL NOT NULL DEFAULT 0.95,
                    best_reward REAL NOT NULL DEFAULT 0.0,
                    total_trials INTEGER NOT NULL DEFAULT 0,
                    baseline_code TEXT,
                    best_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS discovery_trials (
                    trial_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    island_id INTEGER NOT NULL DEFAULT 0,
                    parent_id TEXT,
                    mutation_type TEXT NOT NULL,
                    reward REAL NOT NULL,
                    is_valid INTEGER NOT NULL,
                    is_breakthrough INTEGER NOT NULL,
                    execution_time_ms REAL NOT NULL,
                    metrics_json TEXT,
                    code TEXT NOT NULL,
                    error_trace TEXT,
                    learned_reflection TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES discovery_sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS learned_negative_constraints (
                    constraint_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_trials_session ON discovery_trials(session_id, iteration);
                CREATE INDEX IF NOT EXISTS idx_trials_breakthrough ON discovery_trials(session_id, is_breakthrough);
            ''')
            conn.commit()

    def create_session(
        self,
        session_id: str,
        domain: str,
        task_name: str,
        baseline_code: str,
        target_reward: float = 0.95
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                '''
                INSERT OR REPLACE INTO discovery_sessions (
                    session_id, domain, task_name, status, target_reward, best_reward,
                    total_trials, baseline_code, best_code, created_at, updated_at
                ) VALUES (?, ?, ?, 'running', ?, 0.0, 0, ?, ?, ?, ?)
                ''',
                (session_id, domain, task_name, target_reward, baseline_code, baseline_code, now, now)
            )
            conn.commit()
        return self.get_session(session_id)

    def record_trial(
        self,
        trial_id: str,
        session_id: str,
        iteration: int,
        island_id: int,
        parent_id: Optional[str],
        mutation_type: str,
        reward: float,
        is_valid: bool,
        is_breakthrough: bool,
        execution_time_ms: float,
        metrics: Dict[str, Any],
        code: str,
        error_trace: Optional[str] = None,
        learned_reflection: Optional[str] = None
    ):
        with self._get_connection() as conn:
            conn.execute(
                '''
                INSERT OR REPLACE INTO discovery_trials (
                    trial_id, session_id, iteration, island_id, parent_id, mutation_type,
                    reward, is_valid, is_breakthrough, execution_time_ms, metrics_json,
                    code, error_trace, learned_reflection
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    trial_id, session_id, iteration, island_id, parent_id, mutation_type,
                    reward, 1 if is_valid else 0, 1 if is_breakthrough else 0,
                    execution_time_ms, json.dumps(metrics), code, error_trace, learned_reflection
                )
            )

            # Update session best reward
            now = datetime.now(timezone.utc).isoformat()
            if is_breakthrough:
                conn.execute(
                    '''
                    UPDATE discovery_sessions
                    SET best_reward = MAX(best_reward, ?),
                        best_code = ?,
                        total_trials = total_trials + 1,
                        updated_at = ?
                    WHERE session_id = ?
                    ''',
                    (reward, code, now, session_id)
                )
            else:
                conn.execute(
                    '''
                    UPDATE discovery_sessions
                    SET total_trials = total_trials + 1,
                        updated_at = ?
                    WHERE session_id = ?
                    ''',
                    (now, session_id)
                )
            conn.commit()

    def complete_session(self, session_id: str, status: str = "completed"):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE discovery_sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, datetime.now(timezone.utc).isoformat(), session_id)
            )
            conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM discovery_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not row:
                return None
            return dict(row)

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM discovery_sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_reward_progression(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns ordered trials with iteration and reward for drawing graph curves."""
        with self._get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT iteration, reward, is_breakthrough, is_valid, mutation_type
                FROM discovery_trials
                WHERE session_id = ?
                ORDER BY iteration ASC
                ''',
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_breakthroughs(self, session_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT trial_id, iteration, reward, mutation_type, metrics_json, code, created_at
                FROM discovery_trials
                WHERE session_id = ? AND is_breakthrough = 1
                ORDER BY reward DESC
                ''',
                (session_id,)
            ).fetchall()
            res = []
            for r in rows:
                item = dict(r)
                item["metrics"] = json.loads(item.pop("metrics_json", "{}"))
                res.append(item)
            return res

    def get_recent_failures(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT iteration, mutation_type, error_trace, learned_reflection, code
                FROM discovery_trials
                WHERE session_id = ? AND is_valid = 0
                ORDER BY iteration DESC LIMIT ?
                ''',
                (session_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_negative_constraint(self, session_id: str, pattern_type: str, description: str):
        cid = f"neg_{int(time.time()*1000)}"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO learned_negative_constraints (constraint_id, session_id, pattern_type, description) VALUES (?, ?, ?, ?)",
                (cid, session_id, pattern_type, description)
            )
            conn.commit()

    def get_negative_constraints(self, session_id: str) -> List[str]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT description FROM learned_negative_constraints WHERE session_id = ?",
                (session_id,)
            ).fetchall()
            return [r["description"] for r in rows]
