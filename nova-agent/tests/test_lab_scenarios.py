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


# ---------------------------------------------------------------------------
# Recalibration pins (2026-05-06; snake-collapse-128 re-recalibrated 2026-05-07)
#
# Per docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md §3,
# the three cliff scenarios were recalibrated after the 2026-05-06 pilot
# exposed §7.4 calibration failures. snake-collapse-128 was re-recalibrated
# 2026-05-07 after the N=5 pilot (adjudication doc 2026-05-07) showed C1
# window mismatch and fast-react failure caused by a fully-packed grid.
# These tests pin the recalibrated values so a future revert is caught.
# ---------------------------------------------------------------------------


def test_corner_abandonment_recalibrated_2026_05_06() -> None:
    s = SCENARIOS["corner-abandonment-256"]
    assert s.initial_grid == [
        [0, 4, 0, 0],
        [4, 8, 4, 2],
        [0, 16, 8, 128],
        [64, 256, 128, 32],
    ]
    assert s.initial_score == 3868
    assert s.expected_cliff_window == (12, 17)
    assert s.high_tile_magnitude == 256
    assert s.pattern_name == "corner-abandonment"


def test_snake_collapse_recalibrated_2026_05_07() -> None:
    s = SCENARIOS["snake-collapse-128"]
    assert s.initial_grid == [
        [0, 4, 0, 0],
        [0, 32, 4, 4],
        [8, 4, 32, 4],
        [2, 8, 64, 128],
    ]
    assert s.initial_score == 1396
    assert s.expected_cliff_window == (20, 45)
    assert s.high_tile_magnitude == 128
    assert s.pattern_name == "snake-collapse"


def test_512_wall_recalibrated_2026_05_06() -> None:
    s = SCENARIOS["512-wall"]
    assert s.initial_grid == [
        [0, 4, 8, 0],
        [4, 8, 16, 32],
        [8, 16, 32, 128],
        [256, 32, 128, 512],
    ]
    assert s.initial_score == 7960
    assert s.expected_cliff_window == (12, 17)
    assert s.high_tile_magnitude == 512
    assert s.pattern_name == "high-tile-wall"
