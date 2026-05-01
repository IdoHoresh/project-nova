from nova_agent.perception.types import BoardState


def value_heuristic(board: BoardState) -> float:
    """Predict expected score gain from the current board.

    Cheap heuristic: count horizontally adjacent equal-value pairs and value
    them by tile. Vertical adjacency is intentionally excluded because
    column-stacked duplicates inflate the score on boards that have no real
    near-term merge opportunity.
    """
    grid = board.grid
    expected = 0.0
    for r in range(4):
        for c in range(3):
            v = grid[r][c]
            if v != 0 and grid[r][c + 1] == v:
                expected += v
    return expected


def rpe(*, actual_score_delta: int, board_before: BoardState) -> float:
    """Reward Prediction Error, normalized roughly to [-1, 1].

    δ = (actual − expected) / scale
    scale grows with board's max tile so big plays don't permanently saturate.
    """
    expected = value_heuristic(board_before)
    diff = actual_score_delta - expected
    scale = max(8, board_before.max_tile)
    return max(-1.0, min(1.0, diff / scale))
