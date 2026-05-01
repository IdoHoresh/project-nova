from datetime import datetime, timezone
from pathlib import Path
import uuid

from nova_agent.llm.embeddings import embed_board
from nova_agent.memory.episodic import EpisodicStore
from nova_agent.memory.retrieval import RetrievedMemory, retrieve_top_k
from nova_agent.memory.types import Action, AffectSnapshot, MemoryRecord
from nova_agent.memory.vector_store import VectorStore
from nova_agent.perception.types import BoardState


VECTOR_IMPORTANCE_THRESHOLD: int = 4


class MemoryCoordinator:
    def __init__(self, *, sqlite_path: Path, lancedb_path: Path):
        self.episodic = EpisodicStore(sqlite_path)
        self.vector = VectorStore(lancedb_path)
        self.vector_skip_count: int = 0

    def write_move(
        self,
        *,
        board_before: BoardState,
        board_after: BoardState,
        action: Action,
        score_delta: int,
        rpe: float,
        importance: int,
        source_reasoning: str | None = None,
        affect: AffectSnapshot | None = None,
        tags: list[str] | None = None,
    ) -> str:
        rec_id = f"ep_{uuid.uuid4().hex[:12]}"
        emb = embed_board(board_before.grid)
        rec = MemoryRecord(
            id=rec_id,
            timestamp=datetime.now(timezone.utc),
            board_before=board_before,
            board_after=board_after,
            action=action,
            score_delta=score_delta,
            rpe=rpe,
            importance=importance,
            tags=tags or [],
            embedding=emb,
            source_reasoning=source_reasoning,
            affect=affect,
        )
        self.episodic.insert(rec)

        if importance >= VECTOR_IMPORTANCE_THRESHOLD:
            self.vector.upsert(rec_id, emb)
        else:
            self.vector_skip_count += 1
        return rec_id

    def upsert_aversive_record(self, rec: MemoryRecord) -> None:
        if not rec.embedding:
            return
        self.vector.upsert(rec.id, rec.embedding)

    def retrieve_for_board(self, board: BoardState, k: int = 5) -> list[RetrievedMemory]:
        emb = embed_board(board.grid)
        candidate_ids = [id_ for id_, _ in self.vector.search(emb, k=min(50, max(k * 10, 10)))]
        candidates = [r for r in (self.episodic.get(i) for i in candidate_ids) if r]
        if not candidates:
            return []
        retrieved = retrieve_top_k(candidates=candidates, query_embedding=emb, k=k)
        if retrieved:
            self.episodic.batch_update_last_accessed(
                [m.record.id for m in retrieved],
                datetime.now(timezone.utc),
            )
        return retrieved
