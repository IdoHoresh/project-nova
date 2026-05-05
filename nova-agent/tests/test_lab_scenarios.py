"""Cliff-test scenario corpus invariants.

Validates the SCENARIOS dict against the cross-scenario invariants
documented in docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md
§7.2 and §7.3.
"""

from __future__ import annotations

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.scenarios import MAX_MOVES, SCENARIOS
from nova_agent.lab.sim import Game2048Sim

# Scenarios that are NOT cliff-test scenarios and skip cliff-specific
# invariants (the illusion-of-hope lower bound + max-moves upper bound).
_NON_CLIFF_SCENARIOS: frozenset[str] = frozenset({"fresh-start"})

_CLIFF_SCENARIO_IDS: tuple[str, ...] = (
    "snake-collapse-128",
    "512-wall",
    "corner-abandonment-256",
)


def test_max_moves_is_50() -> None:
    assert MAX_MOVES == 50


def test_all_cliff_scenarios_present() -> None:
    for sid in _CLIFF_SCENARIO_IDS:
        assert sid in SCENARIOS, f"missing cliff scenario {sid!r}"


def test_all_scenarios_have_distinct_seed_base() -> None:
    seed_bases = [s.seed_base for s in SCENARIOS.values()]
    assert len(seed_bases) == len(set(seed_bases)), (
        f"duplicate seed_base in SCENARIOS: {seed_bases}"
    )


def test_cliff_scenarios_satisfy_illusion_of_hope_lower_bound() -> None:
    # Per spec §2.1: 10-15 prior-move buffer before gridlock means
    # cliff manifests no earlier than move 11.
    for sid in _CLIFF_SCENARIO_IDS:
        s = SCENARIOS[sid]
        lo, _hi = s.expected_cliff_window
        assert lo >= 11, (
            f"{sid}: expected_cliff_window lower bound {lo} violates "
            f"illusion-of-hope (must be >= 11)"
        )


def test_cliff_scenarios_satisfy_max_moves_upper_bound() -> None:
    for sid in _CLIFF_SCENARIO_IDS:
        s = SCENARIOS[sid]
        _lo, hi = s.expected_cliff_window
        assert hi < MAX_MOVES, (
            f"{sid}: expected_cliff_window upper bound {hi} violates "
            f"max_moves cap (must be < {MAX_MOVES})"
        )


def test_every_scenario_admits_at_least_one_legal_move() -> None:
    for sid, s in SCENARIOS.items():
        sim = Game2048Sim(seed=s.seed(0), scenario=s)
        before = [row[:] for row in sim.board.grid]
        legal_directions = []
        for direction in (
            SwipeDirection.UP,
            SwipeDirection.DOWN,
            SwipeDirection.LEFT,
            SwipeDirection.RIGHT,
        ):
            test_sim = Game2048Sim(seed=s.seed(0), scenario=s)
            if test_sim.apply_move(direction):
                legal_directions.append(direction)
        assert legal_directions, f"{sid}: initial state admits no legal move; before={before}"


def test_non_cliff_scenarios_documented() -> None:
    """Catch authoring errors where a cliff scenario gets misclassified."""
    documented = _NON_CLIFF_SCENARIOS | set(_CLIFF_SCENARIO_IDS)
    actual = set(SCENARIOS.keys())
    assert actual == documented, (
        f"SCENARIOS contains {actual - documented} not in either "
        f"_NON_CLIFF_SCENARIOS or _CLIFF_SCENARIO_IDS — classify it "
        f"in this test file"
    )
