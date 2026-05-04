"""Phase 0.7 cliff-test scenario library.

Each Scenario is a frozen, JSON-serializable starting condition for a
Game2048Sim run. Cliff-test scenarios per
docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md.
"""

from __future__ import annotations

from nova_agent.lab.sim import Scenario

SCENARIOS: dict[str, Scenario] = {
    "fresh-start": Scenario(
        id="fresh-start",
        initial_grid=[[0] * 4 for _ in range(4)],
        initial_score=0,
        seed_base=20260504,
        pattern_name="empty-board",
        high_tile_magnitude=0,
        expected_cliff_window=(11, 50),
        source_citation="N/A — sim-bootstrapping placeholder, not a cliff-test scenario",
    ),
    "snake-collapse-128": Scenario(
        id="snake-collapse-128",
        initial_grid=[
            [0, 0, 0, 2],
            [4, 2, 4, 8],
            [0, 4, 16, 32],
            [2, 8, 64, 128],
        ],
        initial_score=1308,
        seed_base=20260505001,
        pattern_name="snake-collapse",
        high_tile_magnitude=128,
        expected_cliff_window=(11, 16),
        source_citation=(
            "2048 strategy guides describing snake-formation collapse "
            "(e.g. Hak.is 'How to beat 2048' walkthrough; r/2048 community "
            "discussions of snake-stall failure). URL pinning deferred "
            "per scenarios spec §9."
        ),
    ),
    "512-wall": Scenario(
        id="512-wall",
        initial_grid=[
            [0, 4, 8, 2],
            [4, 8, 16, 32],
            [8, 16, 32, 128],
            [256, 64, 128, 512],
        ],
        initial_score=8152,
        seed_base=20260505002,
        pattern_name="high-tile-wall",
        high_tile_magnitude=512,
        expected_cliff_window=(12, 17),
        source_citation=(
            "2048 strategy guides describing the 1024-wall pattern "
            "(e.g. 2048 wiki, speedrun community guides on stack-blocking "
            "failures). Spec adapts the cited 1024-wall pattern to 512 "
            "for Casual-Carla persona-fidelity per scenarios spec §2.5; "
            "URL pinning deferred per scenarios spec §9."
        ),
    ),
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]
