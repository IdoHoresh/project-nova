"""Phase 0.7 cliff-test runner.

Single async orchestrator that runs paired Carla/Bot trials across the
configured scenarios and writes per-trial CSV + per-trial JSONL artifacts.

This module is a DATA COLLECTOR only. Aggregate statistics, mean-Δ
computation, and the cliff-test pass/fail verdict are explicitly
out-of-scope and live in a separate ``analyze_results.py`` per the spec
§2.7 / §8.

Spec: ``docs/superpowers/specs/2026-05-05-test-runner-design.md``.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Final

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.io import SimGameIO
from nova_agent.perception.types import BoardState

# Per spec §2.6 + ADR-0006: cognitive-judgment models must run at production tier.
_ALLOWED_TIERS: Final[frozenset[str]] = frozenset({"production", "demo"})

EXIT_OK: Final[int] = 0
EXIT_SOFT_CAP: Final[int] = 2
EXIT_HARD_CAP: Final[int] = 3
EXIT_TIER_REFUSED: Final[int] = 4  # USAGE error; not the methodology >2-aborts-per-scenario flag


# Per spec §2.7 / scenarios spec §2.7: Carla "predicts the cliff" iff
# anxiety > 0.6 for >= 2 consecutive moves. Strict greater-than.
ANXIETY_THRESHOLD: Final[float] = 0.6
ANXIETY_CONSECUTIVE: Final[int] = 2


def _first_threshold_index(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> int | None:
    """Return the index of the first move that begins a run of ``consecutive``
    moves with anxiety strictly greater than ``threshold``. Return None if no
    such run exists.

    Spec §2.7: ``t_predicts`` for Carla = this index, or null if no breach.
    """
    if consecutive <= 0 or len(trajectory) < consecutive:
        return None
    run = 0
    for i, v in enumerate(trajectory):
        if v > threshold:
            run += 1
            if run >= consecutive:
                return i - consecutive + 1
        else:
            run = 0
    return None


def _check_anxiety_threshold(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> bool:
    """True iff the trajectory contains >= ``consecutive`` consecutive values
    strictly greater than ``threshold``.
    """
    return (
        _first_threshold_index(trajectory, threshold=threshold, consecutive=consecutive) is not None
    )


# Per spec §2.3 + §2.6: cost-cap envelope.
BUDGET_PER_SCENARIO_ARM_USD: Final[float] = 5.00
HARD_CAP_MULTIPLIER: Final[float] = 1.3


class _BudgetState:
    """Per-(scenario_id, arm) running spend, with soft- and hard-cap checks.

    Used by the worker (hard-cap pre-LLM gate) and the orchestrator
    (soft-cap drain-in-flight halt). asyncio coroutines do not race on a
    single-threaded event loop, so no lock is needed; ``add`` is a single
    arithmetic update.
    """

    def __init__(
        self,
        *,
        soft_cap_usd: float = BUDGET_PER_SCENARIO_ARM_USD,
        hard_cap_multiplier: float = HARD_CAP_MULTIPLIER,
    ) -> None:
        self._soft_cap = soft_cap_usd
        self._hard_cap = soft_cap_usd * hard_cap_multiplier
        self._spent: dict[tuple[str, str], float] = {}

    def add(self, scenario_id: str, arm: str, cost_usd: float) -> None:
        key = (scenario_id, arm)
        self._spent[key] = self._spent.get(key, 0.0) + cost_usd

    def spent(self, scenario_id: str, arm: str) -> float:
        return self._spent.get((scenario_id, arm), 0.0)

    def soft_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._soft_cap

    def hard_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._hard_cap


# Per spec §2.7. Order is contract — analyze_results.py reads by name,
# not position, but appending new columns at the end is the ratchet.
_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "scenario_id",
    "trial_index",
    "arm",
    "t_predicts",
    "t_baseline_fails",
    "cost_usd",
    "abort_reason",
    "anxiety_threshold_met",
    "final_move_index",
    "is_right_censored",
)


def _append_csv_row(csv_path: Path | str, **fields: Any) -> None:
    """Append a single trial row to ``csv_path``. Creates the file (and parent
    dirs) if missing; writes the header iff the file does not exist or is empty.

    None values serialize as empty strings (CSV null convention). Raises
    KeyError if any expected column is missing from ``fields``.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    row = []
    for col in _CSV_COLUMNS:
        if col not in fields:
            raise KeyError(f"missing column {col!r} in CSV row append")
        v = fields[col]
        row.append("" if v is None else str(v))

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(list(_CSV_COLUMNS))
        writer.writerow(row)


# Tie-break order per scenarios spec §2.3 + Bot spec §2.3.
_TIEBREAK_ORDER: Final[tuple[SwipeDirection, ...]] = (
    SwipeDirection.UP,
    SwipeDirection.RIGHT,
    SwipeDirection.DOWN,
    SwipeDirection.LEFT,
)


def _try_apply(
    io: SimGameIO,
    direction: SwipeDirection,
    board_before: BoardState,
) -> SwipeDirection | None:
    """Apply ``direction`` via ``io``. Return the direction iff the board
    changed, else None (the move was a no-op).

    Relies on Game2048Sim's no-op contract (edge case #3 in sim.py): a no-op
    swipe does not advance RNG and does not spawn a tile, so calling
    apply_move on a no-op direction is safe and leaves the sim state unchanged.
    """
    io.apply_move(direction)
    if io.read_board().grid == board_before.grid:
        return None
    return direction


def _apply_with_tiebreak(
    io: SimGameIO,
    chosen: str,
    board: BoardState,
) -> SwipeDirection:
    """Apply ``chosen`` (e.g. ``"swipe_up"``) via ``io``. If the move is a
    no-op (board unchanged), fall through the tie-break order UP > RIGHT >
    DOWN > LEFT and apply the first direction that changes the board.

    Returns the SwipeDirection that was actually applied.
    Raises ValueError if no direction changes the board (defensive; the
    per-move loop should check ``is_game_over()`` before invoking the decider,
    making this branch unreachable in normal operation).
    """
    chosen_direction = SwipeDirection(chosen)
    applied = _try_apply(io, chosen_direction, board)
    if applied is not None:
        return applied

    for direction in _TIEBREAK_ORDER:
        if direction == chosen_direction:
            continue
        applied = _try_apply(io, direction, board)
        if applied is not None:
            return applied

    raise ValueError("no legal move on this board (game-over should have caught this)")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cliff-test",
        description=(
            "Phase 0.7 cliff-test runner: paired Carla/Bot trials per scenario. "
            "Data collector only — does not compute pass/fail verdicts."
        ),
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario id (e.g. 'snake-collapse-128') or 'all' for every cliff-test scenario.",
    )
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        help="Number of paired trials per scenario.",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Pilot mode — output to pilot_results/ subdirectory instead of results/.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Max in-flight paired trials. Default 8.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory root. Default runs/<UTC-iso-timestamp>/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty output directory.",
    )
    return parser


def _check_tier() -> str | None:
    """Validate NOVA_TIER env var. Returns the tier string if OK, else None."""
    import os

    tier = os.environ.get("NOVA_TIER", "").strip()
    if tier not in _ALLOWED_TIERS:
        return None
    return tier


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    tier = _check_tier()
    if tier is None:
        print(
            f"error: NOVA_TIER must be one of {sorted(_ALLOWED_TIERS)} "
            "(dev/plumbing tiers downgrade cognitive-judgment models — see ADR-0006).",
            file=sys.stderr,
        )
        sys.exit(EXIT_TIER_REFUSED)

    # Dispatch shell — Tasks 9-10 fill this in.
    print(f"cliff-test placeholder: scenario={args.scenario}, n={args.n}, tier={tier}")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
