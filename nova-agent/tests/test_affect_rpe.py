from nova_agent.affect.rpe import rpe, value_heuristic
from nova_agent.perception.types import BoardState


def _empty() -> list[list[int]]:
    return [[0] * 4 for _ in range(4)]


def test_value_heuristic_higher_for_more_pairs() -> None:
    no_pairs = BoardState(grid=[[2, 4, 8, 16]] * 4, score=0)
    with_pairs = BoardState(
        grid=[[2, 2, 4, 4], [4, 4, 8, 8], [0] * 4, [0] * 4],
        score=0,
    )
    assert value_heuristic(with_pairs) > value_heuristic(no_pairs)


def test_value_heuristic_zero_for_empty_board() -> None:
    assert value_heuristic(BoardState(grid=_empty(), score=0)) == 0.0


def test_rpe_positive_when_actual_exceeds_expected() -> None:
    b = BoardState(grid=[[2, 2, 0, 0]] + [[0] * 4] * 3, score=0)
    delta = rpe(actual_score_delta=8, board_before=b)
    assert delta > 0


def test_rpe_negative_when_actual_below_expected() -> None:
    b = BoardState(
        grid=[[8, 8, 0, 0], [4, 4, 0, 0], [0] * 4, [0] * 4],
        score=0,
    )
    delta = rpe(actual_score_delta=0, board_before=b)
    assert delta < 0


def test_rpe_clamped_to_unit_range() -> None:
    b = BoardState(grid=[[2, 2, 0, 0]] + [[0] * 4] * 3, score=0)
    high = rpe(actual_score_delta=10_000, board_before=b)
    low = rpe(actual_score_delta=-10_000, board_before=b)
    assert high == 1.0
    assert low == -1.0


def test_rpe_scales_by_max_tile() -> None:
    """Same overshoot magnitude should yield smaller |rpe| on a bigger board."""
    small = BoardState(grid=[[2, 2, 0, 0]] + [[0] * 4] * 3, score=0)
    big = BoardState(grid=[[512, 512, 0, 0]] + [[0] * 4] * 3, score=0)
    overshoot = 4
    delta_small = rpe(
        actual_score_delta=int(value_heuristic(small)) + overshoot,
        board_before=small,
    )
    delta_big = rpe(
        actual_score_delta=int(value_heuristic(big)) + overshoot,
        board_before=big,
    )
    assert abs(delta_big) < abs(delta_small)
