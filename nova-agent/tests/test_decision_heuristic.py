from nova_agent.decision.heuristic import take_the_best
from nova_agent.perception.types import BoardState


def test_prefers_obvious_merge() -> None:
    b = BoardState(grid=[[2, 2, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)
    action = take_the_best(board=b)
    assert action in ("swipe_left", "swipe_right")


def test_keeps_max_in_corner() -> None:
    b = BoardState(
        grid=[
            [64, 2, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        score=0,
    )
    action = take_the_best(board=b)
    assert action != "swipe_down"


def test_picks_higher_score_gain() -> None:
    """When two directions both yield a merge, prefer the one with higher gain."""
    b = BoardState(
        grid=[
            [4, 4, 0, 0],
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        score=0,
    )
    action = take_the_best(board=b)
    # left/right merge: 8 (4+4) + 4 (2+2) = 12 score
    # up/down: no merges, 0 score
    assert action in ("swipe_left", "swipe_right")


def test_returns_swipe_action_literal() -> None:
    b = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)
    action = take_the_best(board=b)
    assert action in ("swipe_up", "swipe_down", "swipe_left", "swipe_right")
