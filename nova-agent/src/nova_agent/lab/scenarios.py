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
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]
