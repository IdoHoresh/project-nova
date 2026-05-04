"""Game2048Sim — pure-Python in-process 2048 engine.

Implements the 4 canonical merge edge cases pinned in
docs/superpowers/specs/2026-05-04-game2048sim-design.md §Game2048Sim:

1. Single merge per tile per move (e.g. [2,2,4] swipe-left -> [4,4]).
2. Leftmost / first-encountered priority on multi-pair rows.
3. No-op swipe = no spawn AND no RNG advancement.
4. Spawn ratio: 2 with probability 0.9, 4 with probability 0.1.

is_game_over() is authoritative (no merges possible AND no empty cells)
but the cognitive layer continues to use the heuristic in
decision/heuristic.py — sim is a silent oracle, not a dictator. See
ADR-0008 for the rationale.

Determinism contract (per spec §Determinism contract):
- All randomness draws from a single random.Random(seed) instance.
- Draw order is fixed: spawn POSITION first, then spawn VALUE.
- random.Random is the stdlib Mersenne Twister — deterministic and
  byte-identical across Python 3.11+ for the same seed + draw sequence.
- Same seed != identical games once decisions diverge: spawns happen
  at random empty cells; once two arms diverge in their decisions,
  the empty-cell sets diverge -> spawn positions diverge -> games
  diverge. This is EXPECTED for the cliff test, not a bug.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import log2

from nova_agent.action.adb import SwipeDirection
from nova_agent.perception.types import BoardState

_SPAWN_FOUR_PROB = 0.1


@dataclass(frozen=True)
class Scenario:
    """Frozen, JSON-serializable starting condition for a game.

    `seed_base` is the per-scenario base seed; `seed(trial_index)` derives
    a per-trial seed for paired Carla/Bot runs per
    docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md §2.2.

    Validators (see __post_init__) enforce: 4×4 grid, in-palette tiles,
    initial_score equals the minimum-implied-score derived from the grid,
    high_tile_magnitude matches the grid max, cliff window well-formed.
    """

    id: str
    initial_grid: list[list[int]]
    initial_score: int
    seed_base: int
    pattern_name: str
    high_tile_magnitude: int
    expected_cliff_window: tuple[int, int]
    source_citation: str

    def __post_init__(self) -> None:
        # 4×4 grid shape.
        if len(self.initial_grid) != 4 or any(len(r) != 4 for r in self.initial_grid):
            raise ValueError(f"{self.id}: initial_grid must be 4x4")
        # Tile palette (canonical 2048 powers + zero).
        valid_tiles = {0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048}
        if any(v not in valid_tiles for r in self.initial_grid for v in r):
            raise ValueError(f"{self.id}: initial_grid contains out-of-palette tile")
        # initial_score equals minimum-implied-score derived from the grid.
        derived = sum(int((log2(v) - 1) * v) for r in self.initial_grid for v in r if v > 0)
        if self.initial_score != derived:
            raise ValueError(
                f"{self.id}: initial_score {self.initial_score} does not match "
                f"minimum-implied-score {derived} derived from initial_grid"
            )
        # high_tile_magnitude matches grid max.
        max_tile = max((v for r in self.initial_grid for v in r), default=0)
        if self.high_tile_magnitude != max_tile:
            raise ValueError(
                f"{self.id}: high_tile_magnitude {self.high_tile_magnitude} does not "
                f"match grid max {max_tile}"
            )
        # Cliff window well-formed: 0 < lo <= hi.
        lo, hi = self.expected_cliff_window
        if not (0 < lo <= hi):
            raise ValueError(
                f"{self.id}: expected_cliff_window {self.expected_cliff_window} ill-formed"
            )

    def seed(self, trial_index: int) -> int:
        """Derive the per-trial seed: seed_base + trial_index.

        Carla trial `i` and Bot trial `i` use the same trial seed so the
        spawn schedule is identical until their decisions diverge — see
        scenarios spec §2.2.
        """
        return self.seed_base + trial_index


class Game2048Sim:
    """Pure-Python 2048 simulator with seeded RNG."""

    def __init__(self, seed: int, scenario: Scenario | None = None) -> None:
        self._rng = random.Random(seed)
        if scenario is None:
            self._grid: list[list[int]] = [[0] * 4 for _ in range(4)]
            self._score = 0
            self._spawn_tile()
            self._spawn_tile()
        else:
            self._grid = [row[:] for row in scenario.initial_grid]
            self._score = scenario.initial_score
            # If the scenario starts with an empty grid, populate the
            # initial 2 tiles per real-2048 startup. If it starts with
            # tiles already placed (e.g. a cliff scenario), trust the
            # author and don't auto-spawn.
            if all(v == 0 for row in self._grid for v in row):
                self._spawn_tile()
                self._spawn_tile()

    @property
    def board(self) -> BoardState:
        # Construct a fresh BoardState per access so the frozen-dataclass
        # invariant stays intact even though the sim's internal grid
        # mutates.
        return BoardState(grid=[row[:] for row in self._grid], score=self._score)

    def apply_move(self, direction: SwipeDirection) -> bool:
        """Apply a move. Returns True if the board changed (legal move),
        False if no-op (no spawn, no RNG advance — matches real 2048).
        """
        before = [row[:] for row in self._grid]
        merged_score = self._slide_and_merge(direction)
        if self._grid == before:
            return False
        self._score += merged_score
        self._spawn_tile()
        return True

    def is_game_over(self) -> bool:
        """Authoritative: no empty cells AND no possible merges."""
        if any(v == 0 for row in self._grid for v in row):
            return False
        for r in range(4):
            for c in range(3):
                if self._grid[r][c] == self._grid[r][c + 1]:
                    return False
        for r in range(3):
            for c in range(4):
                if self._grid[r][c] == self._grid[r + 1][c]:
                    return False
        return True

    # ---- Internal helpers ----

    def _slide_and_merge(self, direction: SwipeDirection) -> int:
        """Slide + merge the grid in the given direction. Returns the
        score delta from merges in this step. Mutates self._grid.

        Strategy: rotate the grid so the move is always "slide LEFT",
        do the merge, then rotate back. Keeps the merge logic in one
        function regardless of direction.
        """
        # Rotate the grid so the move is always "slide LEFT". CW
        # rotation count chosen so the leading edge of the move
        # (top for UP, right for RIGHT, etc.) lands as the leftmost
        # column of the rotated frame, preserving leftmost-priority
        # merge semantics across all four directions.
        rotations = {
            SwipeDirection.LEFT: 0,
            SwipeDirection.DOWN: 1,
            SwipeDirection.RIGHT: 2,
            SwipeDirection.UP: 3,
        }[direction]
        for _ in range(rotations):
            self._grid = self._rotate_cw(self._grid)
        score_delta = 0
        for r in range(4):
            self._grid[r], row_delta = self._slide_merge_row_left(self._grid[r])
            score_delta += row_delta
        for _ in range((4 - rotations) % 4):
            self._grid = self._rotate_cw(self._grid)
        return score_delta

    @staticmethod
    def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
        return [[grid[3 - c][r] for c in range(4)] for r in range(4)]

    @staticmethod
    def _slide_merge_row_left(row: list[int]) -> tuple[list[int], int]:
        """Slide a single row LEFT applying single-merge-per-tile +
        leftmost-priority semantics. Returns (new_row, score_delta).
        """
        compact = [v for v in row if v != 0]
        merged: list[int] = []
        score_delta = 0
        i = 0
        while i < len(compact):
            if i + 1 < len(compact) and compact[i] == compact[i + 1]:
                value = compact[i] * 2
                merged.append(value)
                score_delta += value
                i += 2  # skip the consumed pair (single-merge-per-tile)
            else:
                merged.append(compact[i])
                i += 1
        merged.extend([0] * (4 - len(merged)))
        return merged, score_delta

    def _spawn_tile(self) -> None:
        """Spawn a 2 (90%) or 4 (10%) at a uniformly random empty cell.
        RNG draw order: position FIRST, then value.
        """
        empties = [(r, c) for r in range(4) for c in range(4) if self._grid[r][c] == 0]
        if not empties:
            return
        r, c = self._rng.choice(empties)
        value = 4 if self._rng.random() < _SPAWN_FOUR_PROB else 2
        self._grid[r][c] = value
