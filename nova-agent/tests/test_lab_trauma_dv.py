import pytest

from nova_agent.lab.trauma_ablation import (
    _BASE_ANCHORS,
    compute_session_dv,
)
from nova_agent.perception.types import BoardState


def _far_board() -> BoardState:
    return BoardState(grid=[[2] * 4 for _ in range(4)], score=64)


def _anchor_board() -> BoardState:
    return BoardState(grid=_BASE_ANCHORS["corner-abandonment-256"], score=3868)


def test_zero_encounters_censored() -> None:
    boards = [_far_board()] * 10
    result = compute_session_dv(boards, T=0)
    assert result.censored_zero_encounter is True
    assert result.first_encounter_idx is None
    assert result.r_post is None


def test_all_anchors_rate_one() -> None:
    boards = [_anchor_board()] * 10
    result = compute_session_dv(boards, T=0)
    assert result.censored_zero_encounter is False
    assert result.first_encounter_idx == 0
    assert result.r_post == 1.0
    assert result.n_post_moves == 9


def test_alternating_rate_half() -> None:
    far = _far_board()
    near = _anchor_board()
    boards = [far, near, far, near, far, near]
    result = compute_session_dv(boards, T=0)
    assert result.first_encounter_idx == 1
    assert result.n_post_moves == 4
    assert result.r_post == pytest.approx(0.5)


def test_first_encounter_on_last_move_r_post_none() -> None:
    boards = [_far_board(), _far_board(), _anchor_board()]
    result = compute_session_dv(boards, T=0)
    assert result.first_encounter_idx == 2
    assert result.n_post_moves == 0
    assert result.censored_zero_encounter is False
    assert result.r_post is None


def test_threshold_widens_band() -> None:
    near_ish = BoardState(grid=_BASE_ANCHORS["corner-abandonment-256"], score=3868)
    far = _far_board()
    boards = [far, near_ish, far]
    result_T0 = compute_session_dv(boards, T=0)
    result_Twide = compute_session_dv(boards, T=176)
    assert result_T0.first_encounter_idx == 1
    assert result_Twide.first_encounter_idx == 0


def test_single_board_non_trap_censored() -> None:
    result = compute_session_dv([_far_board()], T=0)
    assert result.censored_zero_encounter is True


def test_single_board_trap_first_encounter_on_last_move() -> None:
    result = compute_session_dv([_anchor_board()], T=0)
    assert result.first_encounter_idx == 0
    assert result.n_post_moves == 0
    assert result.r_post is None
