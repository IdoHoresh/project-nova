from nova_agent.affect.types import AffectVector
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.perception.types import BoardState


def _board(grid: list[list[int]]) -> BoardState:
    return BoardState(grid=grid, score=0)


def test_use_tot_when_high_anxiety_and_high_max_tile() -> None:
    b = _board([[256, 0, 0, 0]] + [[0] * 4 for _ in range(3)])
    a = AffectVector(anxiety=0.8)
    assert should_use_tot(board=b, affect=a) is True


def test_use_tot_when_high_anxiety_and_tight_board() -> None:
    grid = [[2, 4, 8, 16], [4, 8, 16, 32], [8, 16, 32, 0], [16, 32, 0, 0]]
    b = _board(grid)
    a = AffectVector(anxiety=0.7)
    assert should_use_tot(board=b, affect=a) is True


def test_default_react_when_calm() -> None:
    b = _board([[2, 0, 0, 0]] + [[0] * 4 for _ in range(3)])
    a = AffectVector(anxiety=0.1)
    assert should_use_tot(board=b, affect=a) is False


def test_default_react_when_anxiety_at_threshold() -> None:
    """anxiety = 0.6 is the boundary: not strictly greater than, so ReAct."""
    b = _board([[256, 0, 0, 0]] + [[0] * 4 for _ in range(3)])
    a = AffectVector(anxiety=0.6)
    assert should_use_tot(board=b, affect=a) is False


def test_default_react_when_anxious_but_easy_board() -> None:
    """High anxiety alone does not trigger ToT — situation must be hard."""
    b = _board([[2, 4, 0, 0]] + [[0] * 4 for _ in range(3)])
    a = AffectVector(anxiety=0.9)
    assert should_use_tot(board=b, affect=a) is False
