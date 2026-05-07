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
import random
import statistics
from dataclasses import dataclass
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


# ---------------------------------------------------------------------
# Within-game-2 DV calculator (spec §2.4)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SessionDVResult:
    r_post: float | None
    n_post_moves: int
    first_encounter_idx: int | None
    censored_zero_encounter: bool


def compute_session_dv(boards: list[BoardState], *, T: int) -> SessionDVResult:
    """Compute the within-game-2 trap-recurrence rate.

    `boards` is the per-move sequence of post-move BoardStates from game-2.
    First-encounter: first move where min_orbit_distance <= T. After
    first-encounter, count fraction of remaining moves that are also
    trap-proximate. Returns r_post=None when censored (no encounter, or
    encounter on last move with zero remaining moves).

    Spec §2.4 steps 4-6.
    """
    first_idx: int | None = None
    for i, b in enumerate(boards):
        if is_trap_proximate(b, T=T):
            first_idx = i
            break
    if first_idx is None:
        return SessionDVResult(
            r_post=None,
            n_post_moves=0,
            first_encounter_idx=None,
            censored_zero_encounter=True,
        )
    after = boards[first_idx + 1 :]
    if not after:
        # First-encounter on last move: rate undefined, treat as missing.
        return SessionDVResult(
            r_post=None,
            n_post_moves=0,
            first_encounter_idx=first_idx,
            censored_zero_encounter=False,
        )
    n_post_trap = sum(1 for b in after if is_trap_proximate(b, T=T))
    return SessionDVResult(
        r_post=n_post_trap / len(after),
        n_post_moves=len(after),
        first_encounter_idx=first_idx,
        censored_zero_encounter=False,
    )


# ---------------------------------------------------------------------
# Constants (adjudication thresholds)
# ---------------------------------------------------------------------

PRIMARY_PASS_D_FLOOR: Final[float] = 0.30

# ---------------------------------------------------------------------
# Adjudication (spec §3.5)
# ---------------------------------------------------------------------


def paired_cohens_d(deltas: list[float]) -> float:
    """Paired Cohen's d = mean(Δ) / sd(Δ, ddof=1).

    Raises ValueError when fewer than 2 observations or zero variance.
    Zero variance is a signal that the DV computation is broken, not a
    normal scientific outcome.
    """
    if len(deltas) < 2:
        raise ValueError("paired_cohens_d requires at least 2 observations")
    sd = statistics.stdev(deltas)  # ddof=1 by default
    if sd == 0.0:
        raise ValueError("paired_cohens_d undefined for zero-variance Δ")
    return statistics.mean(deltas) / sd


def paired_d_ci_95(
    deltas: list[float],
    *,
    bootstrap_iters: int = 10_000,
    rng_seed: int = 0,
) -> tuple[float, float]:
    """Bootstrap 95% percentile CI on paired-d.

    Resample Δ with replacement, recompute d, take 2.5th + 97.5th
    percentiles. Zero-variance resamples are silently skipped (probability
    vanishes for typical N). Returns (ci_lo, ci_hi).
    """
    rng = random.Random(rng_seed)
    n = len(deltas)
    samples: list[float] = []
    for _ in range(bootstrap_iters):
        resample = [deltas[rng.randrange(n)] for _ in range(n)]
        try:
            samples.append(paired_cohens_d(resample))
        except ValueError:
            continue
    samples.sort()
    lo = samples[int(0.025 * len(samples))]
    hi = samples[int(0.975 * len(samples))]
    return lo, hi


def primary_pass(
    deltas: list[float],
    *,
    r_off_mean: float,
    r_on_mean: float,
) -> bool:
    """Spec §6 C4: paired d >= 0.30 AND CI excludes 0 AND r_off > r_on."""
    try:
        d = paired_cohens_d(deltas)
    except ValueError:
        return False
    if d < PRIMARY_PASS_D_FLOOR:
        return False
    lo, _ = paired_d_ci_95(deltas, bootstrap_iters=2000, rng_seed=0)
    if lo <= 0:
        return False
    if r_off_mean <= r_on_mean:
        return False
    return True
