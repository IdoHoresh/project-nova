"""Phase 0.7 cliff-test scenario library.

Each Scenario is a frozen, JSON-serializable starting condition for a
Game2048Sim run. Cliff-test scenarios per
docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md.
"""

from __future__ import annotations

from typing import Final

from nova_agent.lab.sim import Scenario

# Per cliff-test scenarios spec §2.8: hard cap of 50 moves per trial.
# Trials reaching this cap right-censor (recorded but flagged as
# scenario-invalidation evidence). snake-collapse-128 window upper
# bound (49) is one below MAX_MOVES — the strict < invariant prevents
# right-censored trials from counting as in-window. Other cliff
# scenarios have tighter windows (~3× their upper bound of 17).
MAX_MOVES: Final[int] = 50

SCENARIOS: dict[str, Scenario] = {
    "near-dead": Scenario(
        id="near-dead",
        initial_grid=[
            [512, 256, 128, 64],
            [32, 16, 8, 4],
            [2, 8, 16, 32],
            [64, 128, 0, 0],
        ],
        initial_score=8452,
        seed_base=20260508,
        pattern_name="near-dead-staircase",
        high_tile_magnitude=512,
        expected_cliff_window=(1, 30),
        source_citation=(
            "Phase 0.8 trauma-ablation game-1 trigger. Staircase layout "
            "(512→2) with no adjacent equal tiles and only 2 empty cells. "
            "Spawned 2/4 tiles cannot merge with existing ≥8 tiles; board "
            "fills to game-over within ~5–30 moves. force_trauma_on_game_over "
            "bypass ensures tag_aversive fires on any game-over regardless "
            "of is_catastrophic_loss predicate."
        ),
    ),
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
            [0, 4, 0, 0],
            [0, 32, 4, 4],
            [8, 4, 32, 4],
            [2, 8, 64, 128],
        ],
        initial_score=1396,
        seed_base=20260505001,
        pattern_name="snake-collapse",
        high_tile_magnitude=128,
        expected_cliff_window=(15, 49),
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
            [0, 4, 0, 0],
            [4, 8, 16, 32],
            [8, 16, 32, 64],
            [256, 128, 512, 0],
        ],
        initial_score=7368,
        seed_base=20260505002,
        pattern_name="high-tile-wall",
        high_tile_magnitude=512,
        expected_cliff_window=(11, 25),
        source_citation=(
            "2048 strategy guides describing the 1024-wall pattern "
            "(e.g. 2048 wiki, speedrun community guides on stack-blocking "
            "failures). Spec adapts the cited 1024-wall pattern to 512 "
            "for Casual-Carla persona-fidelity per scenarios spec §2.5; "
            "URL pinning deferred per scenarios spec §9."
        ),
    ),
    "corner-abandonment-256": Scenario(
        id="corner-abandonment-256",
        initial_grid=[
            [0, 4, 0, 0],
            [4, 8, 4, 2],
            [0, 16, 8, 128],
            [64, 256, 128, 32],
        ],
        initial_score=3868,
        seed_base=20260505003,
        pattern_name="corner-abandonment",
        high_tile_magnitude=256,
        expected_cliff_window=(18, 44),
        source_citation=(
            "r/2048 community posts on corner-abandonment failures and "
            "strategy walkthroughs describing high-tile mobility "
            "consequences (e.g. the 'never let the high tile leave the "
            "corner' rule and cascade-failure mode). URL pinning "
            "deferred per scenarios spec §9."
        ),
    ),
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]
