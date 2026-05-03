"""Take-The-Best heuristic policy (Gigerenzer, 1996).

A deterministic, no-LLM fallback used when the budget guard is tripped or
the LLM repeatedly fails to produce structured output. Cues are evaluated
in priority order — the first cue that discriminates between candidates
wins, no weighting.
"""

from __future__ import annotations

from typing import Literal

from nova_agent.perception.types import BoardState

SwipeAction = Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
_DIRS: tuple[SwipeAction, ...] = ("swipe_up", "swipe_down", "swipe_left", "swipe_right")


def _shift_left(row: list[int]) -> tuple[list[int], int]:
    nz = [v for v in row if v != 0]
    out: list[int] = []
    gain = 0
    i = 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            merged = nz[i] * 2
            out.append(merged)
            gain += merged
            i += 2
        else:
            out.append(nz[i])
            i += 1
    out += [0] * (4 - len(out))
    return out, gain


def _simulate(board: BoardState, direction: SwipeAction) -> tuple[BoardState, int]:
    g = [row[:] for row in board.grid]
    gains = 0
    if direction == "swipe_left":
        for i in range(4):
            g[i], gain = _shift_left(g[i])
            gains += gain
    elif direction == "swipe_right":
        for i in range(4):
            row, gain = _shift_left(list(reversed(g[i])))
            g[i] = list(reversed(row))
            gains += gain
    elif direction == "swipe_up":
        for c in range(4):
            col = [g[r][c] for r in range(4)]
            new_col, gain = _shift_left(col)
            for r in range(4):
                g[r][c] = new_col[r]
            gains += gain
    else:  # swipe_down
        for c in range(4):
            col = [g[r][c] for r in range(4)]
            new_col, gain = _shift_left(list(reversed(col)))
            new_col = list(reversed(new_col))
            for r in range(4):
                g[r][c] = new_col[r]
            gains += gain
    return BoardState(grid=g, score=board.score + gains), gains


def is_game_over(board: BoardState) -> bool:
    """True iff no swipe direction changes the board.

    Used as the trigger for post-game reflection (Task 36) and aversive
    tagging (Task 31 game-over hook).
    """
    return all(_simulate(board, d)[0].grid == board.grid for d in _DIRS)


def take_the_best(*, board: BoardState) -> SwipeAction:
    """Take-The-Best heuristic.

    Cues, in priority order:
      1. Maximizes score gain on this move
      2. Keeps the board's max tile in the top-left corner
      3. Maximizes empty cells after the move
    """
    sims = [(d, *_simulate(board, d)) for d in _DIRS]
    best = max(
        sims,
        key=lambda t: (
            t[2],
            t[1].grid[0][0] == board.max_tile,
            sum(1 for r in t[1].grid for v in r if v == 0),
        ),
    )
    return best[0]
