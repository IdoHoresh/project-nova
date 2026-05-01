def score_programmatic(
    *,
    rpe: float,
    terminal: bool,
    max_tile: int,
    empty_cells: int,
    milestone: bool,
) -> int:
    """Importance 1..10 derived without an LLM call.

    Components (each 0..3):
      surprise:    |rpe| spike
      jeopardy:    near-loss (low empty cells)
      grandeur:    big-tile achievement (max_tile)
      finality:    game-over event
      milestone:   first-time tile achievements
    Sum, clamp to 1..10.
    """
    surprise = min(3, int(abs(rpe) * 6))
    jeopardy = min(3, max(0, 4 - empty_cells))
    grandeur = 0 if max_tile < 128 else 1 if max_tile < 512 else 2 if max_tile < 2048 else 3
    finality = 3 if terminal else 0
    milestone_score = 2 if milestone else 0
    raw = surprise + jeopardy + grandeur + finality + milestone_score
    return max(1, min(10, raw))


def llm_rated_importance_prompt() -> str:
    """The prompt fragment to ask the VLM for a 1..10 importance rating."""
    return (
        "Rate the memorability of this 2048 game event from 1 to 10. "
        "1 = utterly mundane (e.g., merging two 2s in an empty corner). "
        "10 = extremely memorable (e.g., near-game-over save, hitting 2048 "
        "for the first time). Reply with only the integer."
    )


def combined_importance(programmatic: int, llm_rated: int | None) -> int:
    if llm_rated is None:
        return programmatic
    return max(1, min(10, round((programmatic + llm_rated) / 2)))
