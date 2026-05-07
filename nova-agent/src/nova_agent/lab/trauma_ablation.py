"""Phase 0.8 trauma-ablation runner.

Spec: docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md.

Single async orchestrator. K=2 multi-game session structure. The IV is a
single boolean ``trauma_enabled`` flag at the runner-local game-over
hook's ``tag_aversive`` call; downstream stages (importance bump,
retrieval boost, extinction, inert cap) collapse naturally.
"""

from __future__ import annotations

import hashlib
import math
from typing import Final

from nova_agent.perception.types import BoardState

# ---------------------------------------------------------------------
# Anchor dictionary (spec §3.2 + Appendix A)
# ---------------------------------------------------------------------

_BASE_ANCHORS: Final[dict[str, list[list[int]]]] = {
    "corner-abandonment-256": [
        [0, 4, 0, 0],
        [4, 8, 4, 2],
        [0, 16, 8, 128],
        [64, 256, 128, 32],
    ],
    "snake-collapse-128": [
        [0, 4, 0, 0],
        [0, 32, 4, 4],
        [8, 4, 32, 4],
        [2, 8, 64, 128],
    ],
    "512-wall": [
        [0, 4, 0, 0],
        [4, 8, 16, 32],
        [8, 16, 32, 64],
        [256, 128, 512, 0],
    ],
}


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [[grid[3 - c][r] for c in range(4)] for r in range(4)]


def _flip_h(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _as_tuple(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _build_orbit(grid: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Generate the D₄ orbit of `grid`, deduplicated by exact equality.

    D₄ has 8 elements: 4 rotations × {identity, horizontal-flip}. Any other
    reflection (vertical, diagonal, anti-diagonal) is a composition of these
    two generators and emerges automatically from the closure.
    """
    seen: set[tuple[tuple[int, ...], ...]] = set()
    orbit: list[tuple[tuple[int, ...], ...]] = []
    base = grid
    for _ in range(4):
        for variant in (base, _flip_h(base)):
            t = _as_tuple(variant)
            if t not in seen:
                seen.add(t)
                orbit.append(t)
        base = _rotate_cw(base)
    return tuple(orbit)


def _dedupe(
    orbit: tuple[tuple[tuple[int, ...], ...], ...],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    out: list[tuple[tuple[int, ...], ...]] = []
    for elem in orbit:
        if elem not in seen:
            seen.add(elem)
            out.append(elem)
    return tuple(out)


_ALL_ORBITS: Final[tuple[tuple[tuple[int, ...], ...], ...]] = tuple(
    elem for grid in _BASE_ANCHORS.values() for elem in _build_orbit(grid)
)

ANCHOR_ORBIT: Final[tuple[tuple[tuple[int, ...], ...], ...]] = _dedupe(_ALL_ORBITS)

ANCHOR_HASH: Final[str] = hashlib.sha256(repr(sorted(ANCHOR_ORBIT)).encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------
# Distance metric (spec §3.2)
# ---------------------------------------------------------------------

MAX_RANK: Final[int] = 11  # log2(2048)


def rank(tile: int) -> int:
    """Tile-rank encoding: empty=0, 2=1, 4=2, ..., 2048=11.

    Maps 2048's multiplicative tile values to an additive integer rank so that
    a 256↔128 mismatch contributes 1 to per-board distance, equivalent to a
    4↔2 mismatch — reflects the multiplicative structure of 2048 rather than
    raw arithmetic.
    """
    if tile == 0:
        return 0
    if tile < 0:
        raise ValueError(f"tile must be non-negative, got {tile}")
    rank_value = int(math.log2(tile))
    if 2**rank_value != tile:
        raise ValueError(f"tile must be a power of 2, got {tile}")
    if rank_value > MAX_RANK:
        raise ValueError(f"tile {tile} exceeds MAX_RANK {MAX_RANK}")
    return rank_value


def _l1_log2(
    a: list[list[int]] | tuple[tuple[int, ...], ...],
    b: list[list[int]] | tuple[tuple[int, ...], ...],
) -> int:
    """Per-board L1 distance over per-cell ranks. Range: [0, 16 × 11] = [0, 176]."""
    return sum(abs(rank(a[r][c]) - rank(b[r][c])) for r in range(4) for c in range(4))


def min_orbit_distance(board: BoardState) -> int:
    """Minimum L1-log2 distance from `board` to any anchor in ANCHOR_ORBIT."""
    return min(_l1_log2(board.grid, anchor) for anchor in ANCHOR_ORBIT)


def is_trap_proximate(board: BoardState, *, T: int) -> bool:
    """True iff min_orbit_distance(board) <= T."""
    return min_orbit_distance(board) <= T
