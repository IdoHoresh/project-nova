"""Game2048Sim engine tests.

The 4 canonical 2048 merge edge cases are pinned here first per the
spec at docs/superpowers/specs/2026-05-04-game2048sim-design.md and
ADR-0008. Tests written FIRST per nova-agent TDD discipline.
"""

from __future__ import annotations

import pytest

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.sim import Game2048Sim, Scenario


# ---- Fresh-start invariants ----


def test_fresh_start_has_two_initial_tiles() -> None:
    sim = Game2048Sim(seed=42)
    occupied = sum(1 for row in sim.board.grid for v in row if v != 0)
    assert occupied == 2


def test_fresh_start_score_is_zero() -> None:
    sim = Game2048Sim(seed=42)
    assert sim.board.score == 0


# ---- Seed determinism ----


def test_seed_determinism_same_seed_same_first_spawn() -> None:
    sim_a = Game2048Sim(seed=42)
    sim_b = Game2048Sim(seed=42)
    assert sim_a.board.grid == sim_b.board.grid


def test_seed_determinism_different_seeds_different_first_spawn() -> None:
    sim_a = Game2048Sim(seed=42)
    sim_b = Game2048Sim(seed=43)
    assert sim_a.board.grid != sim_b.board.grid


# ---- Edge case 1: single merge per tile per move ----


def test_merge_single_per_tile_swipe_left() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 2, 4, 0], [0] * 4, [0] * 4, [0] * 4],
            initial_score=4,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=4,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.LEFT)
    assert sim.board.grid[0][:2] == [4, 4]
    assert sim.board.grid[0][2:] == [0, 0]


# ---- Edge case 2: leftmost / first-encountered priority ----


def test_merge_leftmost_priority_swipe_left() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 2, 2, 2], [0] * 4, [0] * 4, [0] * 4],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=2,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.LEFT)
    assert sim.board.grid[0][:2] == [4, 4]


def test_merge_leftmost_priority_swipe_right() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 2, 2, 2], [0] * 4, [0] * 4, [0] * 4],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=2,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.RIGHT)
    assert sim.board.grid[0][2:] == [4, 4]


def test_merge_leftmost_priority_swipe_up() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0]],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=2,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.UP)
    col_0 = [sim.board.grid[r][0] for r in range(4)]
    assert col_0[:2] == [4, 4]


def test_merge_leftmost_priority_swipe_down() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0]],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=2,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.DOWN)
    col_0 = [sim.board.grid[r][0] for r in range(4)]
    assert col_0[2:] == [4, 4]


# ---- Edge case 3: no-op swipe = no spawn ----


def test_no_op_swipe_returns_false_no_spawn() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=2,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    pre_grid = [row[:] for row in sim.board.grid]
    moved = sim.apply_move(SwipeDirection.LEFT)
    assert moved is False
    assert sim.board.grid == pre_grid  # no spawn, no merge


def test_no_op_swipe_does_not_advance_rng() -> None:
    """RNG state must be unchanged after a no-op swipe.

    Two identical sims; sim_a does (no-op then legal move), sim_b does
    (legal move alone). Boards must match — same spawn position + value,
    because no-op consumed no RNG draws.
    """
    base_grid = [
        [2, 4, 8, 16],
        [4, 8, 16, 32],
        [8, 16, 32, 64],
        [0, 0, 0, 0],
    ]
    # swipe-left = no-op (rows 0-2 already leftmost-packed, no equal adjacents)
    # swipe-down = legal (everything in rows 0-2 slides down toward row 3)

    sim_a = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=base_grid,
            initial_score=776,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=64,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim_b = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=base_grid,
            initial_score=776,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=64,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )

    moved_a_noop = sim_a.apply_move(SwipeDirection.LEFT)
    assert moved_a_noop is False, "fixture should produce a no-op on swipe-left"

    moved_a = sim_a.apply_move(SwipeDirection.DOWN)
    moved_b = sim_b.apply_move(SwipeDirection.DOWN)
    assert moved_a is True and moved_b is True

    # If the no-op consumed no RNG draws, the spawn after sim_a's
    # legal move == the spawn after sim_b's legal move.
    assert sim_a.board.grid == sim_b.board.grid


# ---- Edge case 4: spawn ratio (statistical) ----


def test_spawn_ratio_2_vs_4_distribution_over_10000_spawns() -> None:
    """Spawn 2 with probability 0.9, spawn 4 with probability 0.1.

    Statistical: over 10_000 spawns the empirical ratio should be
    within ±1.5% of the true ratio. With 10k samples the std dev is
    ~0.3% so 1.5% is ~5 sigma — extremely tight, will essentially
    never flake.
    """
    counts = {2: 0, 4: 0}
    for seed in range(10_000):
        sim = Game2048Sim(
            seed=seed,
            scenario=Scenario(
                id="t",
                initial_grid=[[2, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4],
                initial_score=0,
                seed_base=seed,
                pattern_name="test",
                high_tile_magnitude=2,
                expected_cliff_window=(1, 1),
                source_citation="test",
            ),
        )
        moved = sim.apply_move(SwipeDirection.DOWN)
        assert moved is True
        # Find the new tile (the value at the not-bottom-not-original cell)
        new_value = None
        for r in range(4):
            for c in range(4):
                if r == 3 and c == 0:
                    continue  # the slid 2
                if sim.board.grid[r][c] != 0:
                    new_value = sim.board.grid[r][c]
                    break
            if new_value is not None:
                break
        assert new_value in (2, 4), f"unexpected spawn value {new_value}"
        counts[new_value] += 1

    total = counts[2] + counts[4]
    ratio_2 = counts[2] / total
    assert 0.885 <= ratio_2 <= 0.915, f"got {ratio_2:.3f}; expected ~0.9 ±0.015"


# ---- Score accounting ----


def test_score_increments_by_merged_tile_value() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[8, 8, 0, 0], [0] * 4, [0] * 4, [0] * 4],
            initial_score=32,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=8,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.LEFT)
    # initial_score=32 (min-implied for two 8s) + 16 (8+8 merge) = 48.
    assert sim.board.score == 48


def test_score_sums_multiple_merges_in_one_move() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[2, 2, 4, 4], [0] * 4, [0] * 4, [0] * 4],
            initial_score=8,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=4,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    sim.apply_move(SwipeDirection.LEFT)
    # initial_score=8 (min-implied) + 4 (2+2 merge) + 8 (4+4 merge) = 20.
    assert sim.board.score == 20


# ---- Game-over (authoritative; sim is silent oracle) ----


def test_game_over_when_no_merges_and_no_empty_cells() -> None:
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=grid,
            initial_score=32,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=4,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    assert sim.is_game_over() is True


def test_game_over_false_when_empty_cells_exist() -> None:
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=[[0] * 4 for _ in range(4)],
            initial_score=0,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=0,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    assert sim.is_game_over() is False


def test_game_over_false_when_full_but_merges_possible() -> None:
    grid = [
        [2, 2, 4, 8],
        [4, 2, 4, 8],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    sim = Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=grid,
            initial_score=60,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=8,
            expected_cliff_window=(1, 1),
            source_citation="test",
        ),
    )
    assert sim.is_game_over() is False


# ---- Scenario library ----


def test_scenario_loading_from_library() -> None:
    from nova_agent.lab.scenarios import load

    s = load("fresh-start")
    assert s.id == "fresh-start"
    assert s.initial_score == 0
    assert s.initial_grid == [[0] * 4 for _ in range(4)]


def test_scenario_load_unknown_raises_keyerror() -> None:
    from nova_agent.lab.scenarios import load

    with pytest.raises(KeyError, match="unknown scenario"):
        load("not-a-real-scenario")


# ---- Scenario validator tests (per scenarios spec §3) ----


def _valid_scenario_kwargs() -> dict[str, object]:
    """Minimum-valid kwargs for a Scenario whose grid has one 8 tile.

    8 = 2^3, so minimum-implied-score = (3-1) * 8 = 16.
    """
    return {
        "id": "t",
        "initial_grid": [[8, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4],
        "initial_score": 16,
        "seed_base": 1,
        "pattern_name": "test-pattern",
        "high_tile_magnitude": 8,
        "expected_cliff_window": (11, 14),
        "source_citation": "test citation",
    }


def test_scenario_rejects_non_4x4_grid() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_grid"] = [[0, 0, 0]] * 4  # 4×3, not 4×4
    with pytest.raises(ValueError, match="4x4"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_out_of_palette_tile() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_grid"] = [[7, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4]
    with pytest.raises(ValueError, match="palette"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_initial_score_mismatch() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_score"] = 0  # board has an 8 (min-implied = 16), 0 is wrong
    with pytest.raises(ValueError, match="initial_score"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_accepts_initial_score_matching_min_implied() -> None:
    kwargs = _valid_scenario_kwargs()
    # Already valid (initial_score=16 for one 8-tile); should construct cleanly.
    Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_high_tile_magnitude_mismatch() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["high_tile_magnitude"] = 16  # board's max is 8, not 16
    with pytest.raises(ValueError, match="high_tile_magnitude"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_cliff_window_inverted() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["expected_cliff_window"] = (14, 11)  # hi < lo
    with pytest.raises(ValueError, match="cliff_window"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_cliff_window_zero_lower_bound() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["expected_cliff_window"] = (0, 5)  # lower must be > 0
    with pytest.raises(ValueError, match="cliff_window"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_seed_method_returns_seed_base_plus_trial_index() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["seed_base"] = 1000
    s = Scenario(**kwargs)  # type: ignore[arg-type]
    assert s.seed(0) == 1000
    assert s.seed(19) == 1019


# ---- Per-cliff-scenario sim integration ----


def test_snake_collapse_128_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS

    s = SCENARIOS["snake-collapse-128"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert (
        sim.board.score == 1396
    )  # explicit cross-check of the formula (re-recalibrated 2026-05-07)
    assert s.high_tile_magnitude == 128


def test_512_wall_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS

    s = SCENARIOS["512-wall"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert sim.board.score == 8024  # recalibrated 2026-05-07
    assert s.high_tile_magnitude == 512


def test_corner_abandonment_256_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS

    s = SCENARIOS["corner-abandonment-256"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert sim.board.score == 3868  # recalibrated 2026-05-06
    assert s.high_tile_magnitude == 256
