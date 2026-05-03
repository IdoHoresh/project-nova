from dataclasses import replace
from datetime import datetime, timedelta, timezone

from nova_agent.llm.embeddings import embed_board
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.perception.types import BoardState


def test_coordinator_writes_and_retrieves(tmp_path):
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )
    b = BoardState(grid=[[0, 2, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)
    coord.write_move(
        board_before=b,
        board_after=b,
        action="swipe_right",
        score_delta=4,
        rpe=0.1,
        source_reasoning="merge",
        importance=5,
    )
    retrieved = coord.retrieve_for_board(b, k=3)
    assert len(retrieved) >= 1


def test_low_importance_skips_vector_store(tmp_path):
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )
    b = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)
    rec_id = coord.write_move(
        board_before=b,
        board_after=b,
        action="swipe_right",
        score_delta=4,
        rpe=0.05,
        importance=2,
        source_reasoning="trivial",
    )
    assert coord.episodic.get(rec_id) is not None
    assert coord.vector_skip_count == 1
    hits = coord.vector.search(embed_board(b.grid), k=5)
    assert all(h[0] != rec_id for h in hits)


def test_aversive_record_upserted_retroactively(tmp_path):
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )
    b = BoardState(grid=[[2, 4, 8, 16]] + [[0] * 4 for _ in range(3)], score=0)
    rec_id = coord.write_move(
        board_before=b,
        board_after=b,
        action="swipe_left",
        score_delta=0,
        rpe=-0.2,
        importance=2,
        source_reasoning="bad move",
    )
    assert all(h[0] != rec_id for h in coord.vector.search(embed_board(b.grid), k=5))
    rec = coord.episodic.get(rec_id)
    assert rec is not None
    rec_promoted = replace(rec, importance=8, tags=[*rec.tags, "aversive"])
    coord.upsert_aversive_record(rec_promoted)
    hits = coord.vector.search(embed_board(b.grid), k=5)
    assert any(h[0] == rec_id for h in hits)


def test_retrieve_writes_back_last_accessed(tmp_path):
    """§3.4 — recency decay requires last_accessed to be refreshed on retrieval."""
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )
    b = BoardState(grid=[[0, 2, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)
    rec_id = coord.write_move(
        board_before=b,
        board_after=b,
        action="swipe_right",
        score_delta=4,
        rpe=0.1,
        importance=6,
        source_reasoning="merge",
    )
    # Force last_accessed to a stale value.
    stale = datetime.now(timezone.utc) - timedelta(hours=1)
    coord.episodic.update_last_accessed(rec_id, stale)
    pre = coord.episodic.get(rec_id)
    assert pre is not None and pre.last_accessed == stale

    retrieved = coord.retrieve_for_board(b, k=3)
    assert any(m.record.id == rec_id for m in retrieved)

    post = coord.episodic.get(rec_id)
    assert post is not None and post.last_accessed is not None
    assert post.last_accessed > stale
