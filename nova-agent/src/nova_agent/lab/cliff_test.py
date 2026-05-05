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
import sys
from typing import Final

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
