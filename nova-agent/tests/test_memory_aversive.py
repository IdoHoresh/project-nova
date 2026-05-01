from datetime import datetime, timedelta, timezone

from nova_agent.memory.aversive import (
    AVERSIVE_TAG,
    exposure_extinction_halve,
    is_catastrophic_loss,
    is_inert,
    tag_aversive,
)
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def _rec(i: int = 0, *, importance: int = 3, aversive_weight: float | None = None) -> MemoryRecord:
    b = BoardState(grid=[[0] * 4] * 4, score=0)
    extras: dict[str, float] = {}
    if aversive_weight is not None:
        extras["aversive_weight"] = aversive_weight
    return MemoryRecord(
        id=f"r_{i}",
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=10 - i),
        board_before=b,
        board_after=b,
        action="swipe_right",
        score_delta=0,
        rpe=0.0,
        importance=importance,
        tags=[],
        embedding=[0.0] * 8,
        **extras,
    )


def test_tag_aversive_after_catastrophic_loss() -> None:
    last_5 = [_rec(i) for i in range(5)]
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
    assert all(AVERSIVE_TAG in r.tags for r in tagged)
    assert all(r.importance >= 7 for r in tagged)
    assert all(r.aversive_weight == 1.0 for r in tagged)


def test_tag_aversive_noop_when_not_catastrophic() -> None:
    last_5 = [_rec(i) for i in range(5)]
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=False)
    assert tagged is last_5


def test_tag_aversive_caps_importance_at_10() -> None:
    last_5 = [_rec(i, importance=9) for i in range(5)]
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
    assert all(r.importance == 10 for r in tagged)


def test_tag_aversive_adds_loss_precondition_tag() -> None:
    last_5 = [_rec(i) for i in range(5)]
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
    assert all("loss_precondition" in r.tags for r in tagged)


def test_exposure_extinction_halves_weight() -> None:
    """§3.6 defense B — primary deterministic spiral guarantee."""
    r = _rec(0, importance=8, aversive_weight=1.0)
    r.tags.append(AVERSIVE_TAG)
    after_one = exposure_extinction_halve(r)
    assert after_one.aversive_weight == 0.5
    after_two = exposure_extinction_halve(after_one)
    assert after_two.aversive_weight == 0.25
    weights = [r.aversive_weight]
    cur = r
    for _ in range(6):
        cur = exposure_extinction_halve(cur)
        weights.append(cur.aversive_weight)
    assert weights[-1] < 0.02


def test_extinction_noop_on_non_aversive() -> None:
    r = _rec(0)
    out = exposure_extinction_halve(r)
    assert out is r


def test_aversive_weight_decays_continuously_not_in_integer_steps() -> None:
    """R3 — aversive_weight is float, not int-truncated.

    A previous draft had `int(importance * 0.95)` which truncated 7→6 on the
    first decay because `int(6.65) == 6`. Whole-integer steps would burn
    aversive memories ~5× faster than intended. The current implementation
    must keep aversive_weight as a continuous float. The integer
    `importance` field stays for retrieval-scoring; aversive_weight is the
    decay channel.
    """
    r = _rec(0, importance=8, aversive_weight=1.0)
    r.tags.append(AVERSIVE_TAG)
    cur = r
    weights: list[float] = [cur.aversive_weight]
    for _ in range(3):
        cur = exposure_extinction_halve(cur)
        weights.append(cur.aversive_weight)
    assert weights == [1.0, 0.5, 0.25, 0.125]
    assert isinstance(cur.aversive_weight, float)
    assert isinstance(cur.importance, int)


def test_is_catastrophic_loss_requires_contested_board() -> None:
    assert is_catastrophic_loss(final_score=200, max_tile_reached=64, last_empty_cells=1)
    assert not is_catastrophic_loss(final_score=200, max_tile_reached=64, last_empty_cells=8)


def test_is_catastrophic_loss_requires_decent_max_tile() -> None:
    assert not is_catastrophic_loss(final_score=20, max_tile_reached=32, last_empty_cells=1)


def test_is_catastrophic_loss_false_when_score_matches_max_tile() -> None:
    assert not is_catastrophic_loss(final_score=2000, max_tile_reached=128, last_empty_cells=1)


def test_is_inert_below_threshold() -> None:
    r = _rec(0, importance=8, aversive_weight=0.01)
    r.tags.append(AVERSIVE_TAG)
    assert is_inert(r)


def test_is_inert_false_above_threshold() -> None:
    r = _rec(0, importance=8, aversive_weight=0.5)
    r.tags.append(AVERSIVE_TAG)
    assert not is_inert(r)


def test_is_inert_false_for_non_aversive() -> None:
    r = _rec(0, aversive_weight=0.0)
    assert not is_inert(r)
