import json
import sqlite3
from datetime import datetime
from pathlib import Path

from nova_agent.memory.types import AffectSnapshot, MemoryRecord
from nova_agent.perception.types import BoardState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodic (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    last_accessed TEXT,
    board_before TEXT NOT NULL,
    board_after TEXT NOT NULL,
    action TEXT NOT NULL,
    score_delta INTEGER NOT NULL,
    rpe REAL NOT NULL,
    importance INTEGER NOT NULL,
    tags TEXT NOT NULL,
    embedding TEXT NOT NULL,
    source_reasoning TEXT,
    affect TEXT,
    aversive_weight REAL NOT NULL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic(importance);
"""


def _ensure_aversive_weight_column(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(episodic)").fetchall()}
    if "aversive_weight" not in cols:
        conn.execute("ALTER TABLE episodic ADD COLUMN aversive_weight REAL NOT NULL DEFAULT 0.0")
        conn.commit()


def _board_to_json(b: BoardState) -> str:
    return json.dumps({"grid": b.grid, "score": b.score})


def _json_to_board(s: str) -> BoardState:
    d = json.loads(s)
    return BoardState(grid=d["grid"], score=d["score"])


def _record_to_row(r: MemoryRecord) -> tuple[object, ...]:
    return (
        r.id,
        r.timestamp.isoformat(),
        r.last_accessed.isoformat() if r.last_accessed else None,
        _board_to_json(r.board_before),
        _board_to_json(r.board_after),
        r.action,
        r.score_delta,
        r.rpe,
        r.importance,
        json.dumps(r.tags),
        json.dumps(r.embedding),
        r.source_reasoning,
        json.dumps(r.affect.__dict__) if r.affect else None,
        r.aversive_weight,
    )


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    affect_d = json.loads(row["affect"]) if row["affect"] else None
    return MemoryRecord(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        last_accessed=datetime.fromisoformat(row["last_accessed"])
        if row["last_accessed"]
        else None,
        board_before=_json_to_board(row["board_before"]),
        board_after=_json_to_board(row["board_after"]),
        action=row["action"],
        score_delta=row["score_delta"],
        rpe=row["rpe"],
        importance=row["importance"],
        tags=json.loads(row["tags"]),
        embedding=json.loads(row["embedding"]),
        source_reasoning=row["source_reasoning"],
        affect=AffectSnapshot(**affect_d) if affect_d else None,
        aversive_weight=row["aversive_weight"] if "aversive_weight" in row.keys() else 0.0,
    )


class EpisodicStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        _ensure_aversive_weight_column(self._conn)
        self._conn.commit()

    def insert(self, r: MemoryRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO episodic VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            _record_to_row(r),
        )
        self._conn.commit()

    def update(self, r: MemoryRecord) -> None:
        self.insert(r)

    def get(self, id: str) -> MemoryRecord | None:
        row = self._conn.execute("SELECT * FROM episodic WHERE id = ?", (id,)).fetchone()
        return _row_to_record(row) if row else None

    def list_recent(self, limit: int = 10) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT * FROM episodic ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def update_last_accessed(self, id: str, when: datetime) -> None:
        self._conn.execute(
            "UPDATE episodic SET last_accessed = ? WHERE id = ?",
            (when.isoformat(), id),
        )
        self._conn.commit()

    def all(self) -> list[MemoryRecord]:
        rows = self._conn.execute("SELECT * FROM episodic ORDER BY timestamp DESC").fetchall()
        return [_row_to_record(r) for r in rows]
