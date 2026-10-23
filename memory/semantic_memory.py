"""
ONE: Always-On Autonomous AI Agent System
Semantic & Episodic Memory Subsystem
"""

import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from config.settings import settings


class SemanticMemoryStore:
    """
    Episodic memory store supporting persistent embedding/keyword retrieval,
    knowledge retention across ticks, and domain indexing.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DATA_DIR / "episodic_memory.db"
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
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL, -- 'observation', 'finding', 'summary', 'rule'
                source TEXT,           -- URL or file path
                tokens_json TEXT,      -- Token bag for TF-IDF / BM25 style similarity
                created_at TEXT NOT NULL
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_agent ON memories (agent_id)")
            conn.commit()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower())
        # Filter basic stop words
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
            "is", "was", "are", "were", "it", "this", "that", "be", "as", "by", "from"
        }
        return [w for w in words if len(w) > 2 and w not in stopwords]

    def remember(
        self,
        agent_id: str,
        content: str,
        category: str = "finding",
        source: Optional[str] = None
    ) -> int:
        """Stores a persistent memory record."""
        tokens = self._tokenize(content)
        import json
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO memories (agent_id, content, category, source, tokens_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                content,
                category,
                source,
                json.dumps(tokens),
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def recall(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant memories using token-overlap BM25-normalized scoring.
        """
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            query_tokens = set(self._tokenize(query.lower()))

        with self._get_conn() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM memories WHERE agent_id = ? AND category = ? ORDER BY id DESC LIMIT 200",
                    (agent_id, category),
                )
            else:
                cursor.execute(
                    "SELECT * FROM memories WHERE agent_id = ? ORDER BY id DESC LIMIT 200",
                    (agent_id,),
                )
            rows = cursor.fetchall()

        import json
        scored_memories = []
        for r in rows:
            tokens = set(json.loads(r["tokens_json"])) if r["tokens_json"] else set()
            overlap = query_tokens.intersection(tokens)
            if not overlap and len(rows) > limit:
                continue

            # Simple TF-IDF score approximation
            score = len(overlap) / (math.log(len(tokens) + 2) + 0.1)
            scored_memories.append({
                "id": r["id"],
                "content": r["content"],
                "category": r["category"],
                "source": r["source"],
                "created_at": r["created_at"],
                "score": score
            })

        # Sort descending by relevance score
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:limit]

    def get_recent(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM memories WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
                (agent_id, limit),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "category": r["category"],
                    "source": r["source"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]


semantic_memory = SemanticMemoryStore()
