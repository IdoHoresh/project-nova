"""Phase 0.7 cliff-test scenario library.

Each Scenario is a frozen, JSON-serializable starting condition for a
Game2048Sim run. The 3-5 hard cliff-test scenarios are a SEPARATE spec
under Phase 0.7 prep — this module starts with a single `fresh-start`
entry so the sim is end-to-end testable from day one.
"""

from __future__ import annotations

from nova_agent.lab.sim import Scenario

SCENARIOS: dict[str, Scenario] = {
    "fresh-start": Scenario(
        id="fresh-start",
        initial_grid=[[0] * 4 for _ in range(4)],
        initial_score=0,
        seed=20260504,
    ),
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]
