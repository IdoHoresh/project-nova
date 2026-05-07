"""Tests for multi-session aggregator and halt criteria (Task 7)."""

import dataclasses

from nova_agent.lab.trauma_ablation import (
    SOFT_WARNING_D_FLOOR,
    STAGE_BUDGET_USD,
    STAGE_DEFAULT_N,
    SessionResult,
    _check_halt_criteria,
)


def _ok_result(seed: int, delta: float = 0.3) -> SessionResult:
    """Factory: create a passing SessionResult with optional delta override."""
    return SessionResult(
        seed_base=seed,
        r_post_y_on=0.10,
        r_post_y_off=0.10 + delta,
        n_post_moves_y_on=10,
        n_post_moves_y_off=10,
        censored_cap_y_on=False,
        censored_cap_y_off=False,
        censored_zero_encounter_y_on=False,
        censored_zero_encounter_y_off=False,
        delta_i=delta,
        anxiety_lift_y_on=0.4,
        anxiety_lift_y_off=0.6,
        aversive_tag_count_y_on=5,
        aversive_tag_count_y_off=0,
        would_predicate_have_fired_y_on=True,
        reached_game_over_y_on=True,
        reached_game_over_y_off=True,
    )


def test_smoke_pass_returns_none() -> None:
    """Smoke stage with all constraints met should pass (return None)."""
    results = [_ok_result(i) for i in range(3)]
    assert _check_halt_criteria("smoke", results, pilot_censoring_rate=None) is None


def test_smoke_low_reach_gameover_aborts() -> None:
    """Smoke stage with <80% reach_game_over should abort."""
    results = [_ok_result(i) for i in range(2)]
    # Mutate: set reached_game_over_y_on = False for first result
    results = [
        dataclasses.replace(r, reached_game_over_y_on=False) if i == 0 else r
        for i, r in enumerate(results)
    ]
    halt = _check_halt_criteria("smoke", results, pilot_censoring_rate=None)
    assert halt is not None and "reach_game_over" in halt


def test_surrogate_direction_flip_aborts() -> None:
    """Surrogate stage with mean_delta <= 0 should abort."""
    # Create results with negative delta (direction flip)
    results = [_ok_result(i, delta=-0.2) for i in range(20)]
    halt = _check_halt_criteria("surrogate", results, pilot_censoring_rate=0.0)
    assert halt is not None and "direction" in halt


def test_surrogate_zero_variance_aborts() -> None:
    """Surrogate stage with all identical deltas should abort (variance=0)."""
    results = [_ok_result(i, delta=0.30) for i in range(20)]
    halt = _check_halt_criteria("surrogate", results, pilot_censoring_rate=0.0)
    assert halt is not None and "variance" in halt


def test_surrogate_high_censoring_aborts() -> None:
    """Surrogate stage with high censoring rate should abort."""
    results = [
        dataclasses.replace(
            _ok_result(i, delta=0.30),
            delta_i=None,
            censored_zero_encounter_y_on=True,
        )
        for i in range(20)
    ]
    halt = _check_halt_criteria("surrogate", results, pilot_censoring_rate=0.0)
    assert halt is not None and "censor" in halt


def test_main_no_halt_in_progress() -> None:
    """Main stage with N=70 and valid variance should pass (not halt)."""
    results = [_ok_result(i, delta=0.30 + 0.01 * (i % 3)) for i in range(70)]
    assert _check_halt_criteria("main", results, pilot_censoring_rate=0.0) is None


def test_constants_exist() -> None:
    """Constants should be available at module scope."""
    assert isinstance(STAGE_BUDGET_USD, dict)
    assert isinstance(STAGE_DEFAULT_N, dict)
    assert isinstance(SOFT_WARNING_D_FLOOR, float)
