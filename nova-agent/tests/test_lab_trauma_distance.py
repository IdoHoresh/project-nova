import pytest

from nova_agent.lab.trauma_ablation import (
    MAX_RANK,
    _BASE_ANCHORS,
    _l1_log2,
    is_trap_proximate,
    min_orbit_distance,
    rank,
)
from nova_agent.perception.types import BoardState


def test_rank_empty_is_zero() -> None:
    assert rank(0) == 0


def test_rank_powers_of_two() -> None:
    assert rank(2) == 1
    assert rank(4) == 2
    assert rank(2048) == MAX_RANK


def test_rank_rejects_negative() -> None:
    with pytest.raises(ValueError):
        rank(-2)


def test_rank_rejects_non_power_of_two() -> None:
    with pytest.raises(ValueError):
        rank(3)


def test_rank_rejects_above_max() -> None:
    with pytest.raises(ValueError):
        rank(4096)


def test_l1_log2_zero_on_identity() -> None:
    grid = _BASE_ANCHORS["corner-abandonment-256"]
    assert _l1_log2(grid, grid) == 0


def test_l1_log2_symmetric() -> None:
    a = _BASE_ANCHORS["corner-abandonment-256"]
    b = _BASE_ANCHORS["snake-collapse-128"]
    assert _l1_log2(a, b) == _l1_log2(b, a)


def test_l1_log2_triangle_inequality_small_sample() -> None:
    a = _BASE_ANCHORS["corner-abandonment-256"]
    b = _BASE_ANCHORS["snake-collapse-128"]
    c = _BASE_ANCHORS["512-wall"]
    assert _l1_log2(a, c) <= _l1_log2(a, b) + _l1_log2(b, c)


def test_min_orbit_distance_zero_on_anchor() -> None:
    board = BoardState(grid=_BASE_ANCHORS["corner-abandonment-256"], score=3868)
    assert min_orbit_distance(board) == 0


def test_min_orbit_distance_zero_on_rotated_anchor() -> None:
    grid = _BASE_ANCHORS["corner-abandonment-256"]
    rotated = [[grid[3 - c][r] for c in range(4)] for r in range(4)]
    board = BoardState(grid=rotated, score=3868)
    assert min_orbit_distance(board) == 0


def test_min_orbit_distance_nonzero_on_far_board() -> None:
    far = [
        [2, 2, 2, 2],
        [2, 2, 2, 2],
        [2, 2, 2, 2],
        [2, 2, 2, 2],
    ]
    assert min_orbit_distance(BoardState(grid=far, score=64)) > 0


def test_is_trap_proximate_true_on_anchor() -> None:
    board = BoardState(grid=_BASE_ANCHORS["corner-abandonment-256"], score=3868)
    assert is_trap_proximate(board, T=0)


def test_is_trap_proximate_false_above_threshold() -> None:
    far = [
        [2048, 1024, 512, 256],
        [128, 64, 32, 16],
        [8, 4, 2, 0],
        [0, 0, 0, 0],
    ]
    assert not is_trap_proximate(BoardState(grid=far, score=8000), T=0)
