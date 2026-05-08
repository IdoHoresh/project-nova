import math
from datetime import datetime, timedelta, timezone

from nova_agent.memory.aversive import AVERSIVE_TAG
from nova_agent.memory.retrieval import (
    combined_score,
    cosine,
    recency_score,
    retrieve_top_k,
)
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def test_recency_decays_power_law():
    now = datetime.now(timezone.utc)
    fresh = recency_score(last_accessed=now, now=now)
    week_old = recency_score(last_accessed=now - timedelta(days=7), now=now)
    month_old = recency_score(last_accessed=now - timedelta(days=30), now=now)
    assert fresh > week_old > month_old > 0


def test_cosine_identical_is_one():
    assert math.isclose(cosine([1, 0, 0], [1, 0, 0]), 1.0, abs_tol=1e-6)
    assert math.isclose(cosine([1, 0, 0], [-1, 0, 0]), -1.0, abs_tol=1e-6)


def test_combined_score_weights():
    s = combined_score(
        recency=0.5,
        importance_norm=0.5,
        relevance=0.5,
        w_recency=1.0,
        w_importance=1.0,
        w_relevance=1.0,
    )
    assert math.isclose(s, 1.5, abs_tol=1e-6)


# ---------- Task 32 additions ----------


def _board() -> BoardState:
    return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)


def _rec(
    rid: str,
    *,
    embedding: list[float],
    tags: list[str] | None = None,
    importance: int = 5,
    aversive_weight: float = 0.0,
    last_accessed: datetime | None = None,
) -> MemoryRecord:
    b = _board()
    return MemoryRecord(
        id=rid,
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=1),
        board_before=b,
        board_after=b,
        action="swipe_right",
        score_delta=0,
        rpe=0.0,
        importance=importance,
        tags=list(tags or []),
        embedding=embedding,
        last_accessed=last_accessed,
        aversive_weight=aversive_weight,
    )


def test_max_one_aversive_returned():
    """Defense A (§3.6) — active-tag cap."""
    q = [1.0, 0.0, 0.0, 0.0]
    aversives = [
        _rec(f"a_{i}", embedding=[1.0, 0.0, 0.0, 0.0], tags=[AVERSIVE_TAG], aversive_weight=1.0)
        for i in range(3)
    ]
    others = [_rec(f"n_{i}", embedding=[0.95, 0.05, 0.0, 0.0]) for i in range(5)]
    out = retrieve_top_k(candidates=aversives + others, query_embedding=q, k=5)
    aversive_count = sum(1 for m in out if AVERSIVE_TAG in m.record.tags)
    assert aversive_count <= 1


def test_inert_aversive_not_returned():
    """An aversive record with weight < 0.02 doesn't surface."""
    q = [1.0, 0.0, 0.0, 0.0]
    inert = _rec(
        "inert_one",
        embedding=[1.0, 0.0, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=0.01,
    )
    fillers = [_rec(f"n_{i}", embedding=[0.5, 0.5, 0.0, 0.0]) for i in range(3)]
    out = retrieve_top_k(candidates=[inert, *fillers], query_embedding=q, k=5)
    assert all(m.record.id != "inert_one" for m in out)


def test_aversive_radius_widens_low_relevance_above_floor():
    """A live aversive record at low-but-above-floor relevance gets boosted."""
    q = [1.0, 0.0, 0.0, 0.0]
    # cosine ≈ 0.555 — above 0.4 floor, below 0.7 cap → widened to 0.7
    embedding_low = [1.0, 1.5, 0.0, 0.0]
    aversive = _rec(
        "aversive_one",
        embedding=embedding_low,
        tags=[AVERSIVE_TAG],
        aversive_weight=1.0,
        importance=5,
    )
    competitor = _rec(
        "comp_one",
        embedding=embedding_low,
        importance=5,
    )
    out = retrieve_top_k(candidates=[aversive, competitor], query_embedding=q, k=2)
    a = next(m for m in out if m.record.id == "aversive_one")
    c = next(m for m in out if m.record.id == "comp_one")
    assert a.score > c.score


def test_aversive_below_floor_not_widened():
    """If raw relevance is below the aversive floor, no widening boost applies."""
    q = [1.0, 0.0, 0.0, 0.0]
    # cosine ≈ 0.0 → below 0.4 floor → no widening
    aversive = _rec(
        "aversive_low",
        embedding=[0.0, 1.0, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=1.0,
    )
    # Highly relevant non-aversive
    relevant = _rec("rel_one", embedding=[1.0, 0.0, 0.0, 0.0])
    out = retrieve_top_k(candidates=[aversive, relevant], query_embedding=q, k=2)
    rel = next(m for m in out if m.record.id == "rel_one")
    av = next(m for m in out if m.record.id == "aversive_low")
    assert rel.score > av.score


def test_decayed_aversive_surfaces_less_than_full_weight():
    """aversive_weight scales the widened relevance term."""
    q = [1.0, 0.0, 0.0, 0.0]
    full = _rec(
        "full_w",
        embedding=[1.0, 1.0, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=1.0,
    )
    decayed = _rec(
        "decayed",
        embedding=[1.0, 1.0, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=0.25,
    )
    # Run separately so the cap doesn't drop one.
    out_full = retrieve_top_k(candidates=[full], query_embedding=q, k=1)
    out_decayed = retrieve_top_k(candidates=[decayed], query_embedding=q, k=1)
    assert out_full[0].score > out_decayed[0].score


def test_retrieved_memory_exposes_raw_cosine_relevance() -> None:
    """RetrievedMemory.relevance is the raw cosine, NOT the post-boost score input.

    The graded-affect formula in ADR-0012 multiplies aversive_weight × relevance,
    where `relevance` must be the raw cosine. The aversive widen-and-multiply path
    only affects the score used for top-k ranking; the surfaced relevance stays raw.
    """
    q = [1.0, 0.0, 0.0, 0.0]
    # cosine([1,1,0,0], [1,0,0,0]) = 1 / sqrt(2) ≈ 0.7071
    aversive = _rec(
        "av_one",
        embedding=[1.0, 1.0, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=1.0,
    )
    out = retrieve_top_k(candidates=[aversive], query_embedding=q, k=1)
    assert len(out) == 1
    assert math.isclose(out[0].relevance, 1.0 / math.sqrt(2.0), abs_tol=1e-6)


def test_retrieved_memory_relevance_is_raw_even_when_boost_widens() -> None:
    """Aversive boost widens the score but leaves `relevance` at raw cosine."""
    q = [1.0, 0.0, 0.0, 0.0]
    # cosine ≈ 0.555 — above 0.4 floor, below 0.7 cap → score widened to 0.7 × weight
    aversive = _rec(
        "av_widened",
        embedding=[1.0, 1.5, 0.0, 0.0],
        tags=[AVERSIVE_TAG],
        aversive_weight=1.0,
    )
    out = retrieve_top_k(candidates=[aversive], query_embedding=q, k=1)
    assert len(out) == 1
    raw = cosine(q, [1.0, 1.5, 0.0, 0.0])
    assert math.isclose(out[0].relevance, raw, abs_tol=1e-6)


def test_retrieve_top_k_appends_per_candidate_log() -> None:
    """When `retrieval_log` is provided, retrieve_top_k records every non-inert candidate.

    Each entry: {record_id, aversive_tag_present, raw_cosine, score}. Order is
    insertion order over `candidates` (post-inert filter). Truncation to top-k
    happens AFTER logging — the log captures the full cosine distribution.
    """
    q = [1.0, 0.0, 0.0, 0.0]
    av = _rec("av", embedding=[1.0, 1.0, 0.0, 0.0], tags=[AVERSIVE_TAG], aversive_weight=1.0)
    nonav = _rec("nonav", embedding=[1.0, 0.0, 0.0, 0.0])
    inert = _rec(
        "inert", embedding=[1.0, 0.0, 0.0, 0.0], tags=[AVERSIVE_TAG], aversive_weight=0.001
    )
    log: list[dict[str, object]] = []
    retrieve_top_k(
        candidates=[av, nonav, inert],
        query_embedding=q,
        k=1,
        retrieval_log=log,
    )
    ids = [e["record_id"] for e in log]
    assert ids == ["av", "nonav"]  # inert filtered before log
    av_entry = next(e for e in log if e["record_id"] == "av")
    assert av_entry["aversive_tag_present"] is True
    assert math.isclose(float(av_entry["raw_cosine"]), 1.0 / math.sqrt(2.0), abs_tol=1e-6)
    assert "score" in av_entry


def test_retrieve_top_k_default_does_not_log() -> None:
    """Default invocation (no retrieval_log) does not allocate or write."""
    q = [1.0, 0.0, 0.0, 0.0]
    rec = _rec("r", embedding=[1.0, 0.0, 0.0, 0.0])
    out = retrieve_top_k(candidates=[rec], query_embedding=q, k=1)
    assert len(out) == 1
