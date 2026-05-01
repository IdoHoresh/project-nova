"""End-to-end trauma test (§3.6 acceptance — Task 40).

Synthesizes a losing trajectory, runs the post-game aversive pipeline,
opens a 'second game', and verifies that a board similar to the
precondition surfaces the aversive memory through retrieval. No LLM or
emulator is involved — the test exercises the deterministic memory +
aversive + retrieval slice that backs the live demo.
"""

from nova_agent.llm.embeddings import embed_board
from nova_agent.memory.aversive import (
    AVERSIVE_TAG,
    is_catastrophic_loss,
    tag_aversive,
)
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.perception.types import BoardState


def _losing_board(idx: int) -> BoardState:
    """Five increasingly-tight precondition boards leading to a loss.

    Each board is dominated by mid-tier tiles with shrinking empty count;
    the embedding from `embed_board` therefore varies slightly across the
    five but stays similar enough that any of them is a vector-search
    candidate when querying with the final precondition.
    """
    grids = [
        [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [0, 16, 32, 64],
            [0, 0, 0, 0],
        ],
        [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 16, 32, 64],
            [0, 0, 0, 0],
        ],
        [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 16, 32, 64],
            [0, 4, 0, 0],
        ],
        [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 16, 32, 64],
            [4, 4, 0, 0],
        ],
        [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 16, 32, 64],
            [4, 4, 2, 0],
        ],
    ]
    return BoardState(grid=grids[idx], score=200 + idx * 10)


def test_trauma_persists_and_surfaces_on_similar_board(tmp_path) -> None:
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )

    # Game 1: write 5 low-importance preconditions (importance=1 means they
    # bypass the vector store on the first write — exactly the scenario
    # Task 31's retroactive upsert exists to repair).
    for i in range(5):
        b = _losing_board(i)
        coord.write_move(
            board_before=b,
            board_after=b,
            action="swipe_down",
            score_delta=0,
            rpe=-0.1,
            importance=1,
            source_reasoning=f"precondition #{i}",
        )

    # Confirm none of those records are in the vector store yet.
    final_pre = _losing_board(4)
    final_emb = embed_board(final_pre.grid)
    pre_hits = coord.vector.search(final_emb, k=10)
    pre_ids = {hit[0] for hit in pre_hits}

    # Detect catastrophic loss on the final precondition state.
    final_board = _losing_board(4)
    assert is_catastrophic_loss(
        final_score=final_board.score,
        max_tile_reached=final_board.max_tile,
        last_empty_cells=final_board.empty_cells,
    )

    # Run the post-game aversive flow: tag last 5 + retroactive upsert.
    last_5 = coord.episodic.list_recent(limit=5)
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
    for rec in tagged:
        coord.episodic.update(rec)
        coord.upsert_aversive_record(rec)

    # Game 2: query a board similar to the precondition. The aversive
    # memory must now be retrievable even though it was below the
    # importance gate at write time.
    similar_board = BoardState(
        grid=[
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 16, 32, 64],
            [4, 4, 2, 0],
        ],
        score=0,
    )
    retrieved = coord.retrieve_for_board(similar_board, k=5)

    assert retrieved, "expected at least one retrieved memory after aversive upsert"
    aversive_hits = [m for m in retrieved if AVERSIVE_TAG in m.record.tags]
    assert aversive_hits, "aversive memory did not surface on similar board"

    surfaced_ids = {m.record.id for m in retrieved}
    assert surfaced_ids - pre_ids, (
        "retroactive upsert should have introduced at least one id absent before"
    )
