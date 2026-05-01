"""Semantic memory — durable rules learned across games (post-reflection).

Distinct from `episodic.py` (per-move records) and the LanceDB vector store
(retrieval index). Reflection writes here; future game starts read here as
'prior_lessons' input to the next reflection cycle, and (future) the
decision prompt may surface the top-N rules as a system-level prefix.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS semantic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    rule TEXT NOT NULL,
    citations TEXT NOT NULL DEFAULT '[]',
    confidence INTEGER NOT NULL DEFAULT 5
);
"""


class SemanticStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def add_rule(self, *, rule: str, citations: list[str], confidence: int = 5) -> int:
        cur = self._conn.execute(
            "INSERT INTO semantic(created_at, rule, citations, confidence) VALUES (?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(),
                rule,
                json.dumps(citations),
                confidence,
            ),
        )
        self._conn.commit()
        rid = cur.lastrowid
        if rid is None:
            raise RuntimeError("SemanticStore.add_rule: SQLite returned no lastrowid")
        return rid

    def all_rules(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, rule, citations, confidence FROM semantic ORDER BY id DESC"
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            d["citations"] = json.loads(d["citations"])
            out.append(d)
        return out
