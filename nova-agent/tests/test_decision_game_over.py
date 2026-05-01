from nova_agent.decision.heuristic import is_game_over
from nova_agent.perception.types import BoardState


def test_full_no_merge_board_is_game_over() -> None:
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    assert is_game_over(BoardState(grid=grid, score=0)) is True


def test_full_with_horizontal_merge_is_not_game_over() -> None:
    grid = [
        [2, 2, 4, 8],
        [4, 8, 16, 32],
        [8, 16, 32, 64],
        [16, 32, 64, 128],
    ]
    assert is_game_over(BoardState(grid=grid, score=0)) is False


def test_board_with_empty_cells_is_not_game_over() -> None:
    grid = [
        [2, 4, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    assert is_game_over(BoardState(grid=grid, score=0)) is False


def test_full_with_vertical_merge_is_not_game_over() -> None:
    grid = [
        [2, 4, 8, 16],
        [2, 8, 16, 32],
        [4, 16, 32, 64],
        [8, 32, 64, 128],
    ]
    assert is_game_over(BoardState(grid=grid, score=0)) is False
