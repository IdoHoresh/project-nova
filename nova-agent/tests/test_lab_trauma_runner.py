"""Tests for multi-session aggregator and halt criteria (Task 7)."""

import dataclasses
import json
import math
import statistics
from pathlib import Path

import pytest

from nova_agent.lab.trauma_ablation import (
    SOFT_WARNING_D_FLOOR,
    STAGE_BUDGET_USD,
    STAGE_DEFAULT_N,
    T_CALIBRATION_BAND,
    T_CANDIDATES_INITIAL,
    SessionResult,
    _check_halt_criteria,
    _lock_golden_thresholds,
    _select_T_from_sweep,
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


# --- T-selection tests (Part A) ---


def test_select_T_smallest_qualifying_when_unique() -> None:
    rates = {2: 0.10, 4: 0.30, 6: 0.40}
    assert _select_T_from_sweep(rates, band=T_CALIBRATION_BAND) == 4


def test_select_T_lower_median_when_multiple_qualify() -> None:
    rates = {2: 0.10, 4: 0.27, 6: 0.30, 8: 0.33, 10: 0.50}
    assert _select_T_from_sweep(rates, band=T_CALIBRATION_BAND) == 6


def test_select_T_lower_of_two_medians_when_even() -> None:
    rates = {2: 0.10, 4: 0.26, 6: 0.27, 8: 0.30, 10: 0.34, 12: 0.50}
    assert _select_T_from_sweep(rates, band=T_CALIBRATION_BAND) == 6


def test_select_T_returns_none_when_no_band_match() -> None:
    rates = {t: 0.50 for t in T_CANDIDATES_INITIAL}
    assert _select_T_from_sweep(rates, band=T_CALIBRATION_BAND) is None


# --- Golden-scenario calibration threshold tests (Part B) ---


def test_lock_golden_thresholds_computes_correctly() -> None:
    # 5 sessions: moves_to_merge=[2, 4, 6, 8, 10], mean_anxiety=[0.1]*5
    sessions = [{"moves_to_merge": m, "mean_anxiety": 0.1} for m in [2, 4, 6, 8, 10]]
    thresholds = _lock_golden_thresholds(sessions)
    mu = 6.0  # mean of [2,4,6,8,10]
    sigma = statistics.stdev([2, 4, 6, 8, 10])
    assert thresholds["move_threshold"] == math.ceil(mu + sigma)
    assert thresholds["anxiety_threshold"] == pytest.approx(0.1 + 2 * 0.0, abs=1e-9)


def test_lock_golden_thresholds_uses_only_merge_successful_for_moves() -> None:
    # 8 sessions merge-successful (moves=[5]*8), 2 cap-reached (moves_to_merge=None)
    sessions = [{"moves_to_merge": 5, "mean_anxiety": 0.2}] * 8 + [
        {"moves_to_merge": None, "mean_anxiety": 0.5}
    ] * 2
    thresholds = _lock_golden_thresholds(sessions)
    # μ_moves = 5.0, σ_moves = 0.0 → move_threshold = ceil(5.0) = 5
    assert thresholds["move_threshold"] == 5
    # anxiety from ALL 10: μ=0.26, σ computed from [0.2]*8+[0.5]*2
    all_anx = [0.2] * 8 + [0.5] * 2
    mu_a = statistics.mean(all_anx)
    sigma_a = statistics.stdev(all_anx)
    assert thresholds["anxiety_threshold"] == pytest.approx(mu_a + 2 * sigma_a)


def test_pilot_budget_cap_is_35() -> None:
    assert STAGE_BUDGET_USD["pilot"] == 35.0


@pytest.mark.asyncio
async def test_run_smoke_returns_integer_exit_code(tmp_path: Path) -> None:
    """run_smoke completes without exception and returns an int exit code."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from test_lab_trauma_session import _FixedActionLLM

    llm = _FixedActionLLM(action="swipe_up")
    from nova_agent.lab.trauma_ablation import EXIT_OK, EXIT_SMOKE_HALT, run_smoke

    rc = await run_smoke(
        run_dir=tmp_path,
        n=1,  # 1 session to keep test fast
        seed_base_start=20260507,
        decision_llm=llm,
        deliberation_llm=llm,
        reflection_llm=llm,
        T_placeholder=16,
        max_moves=200,
    )
    assert rc in (EXIT_OK, EXIT_SMOKE_HALT)


def test_surrogate_reads_locked_t(tmp_path: Path) -> None:
    pilot_dir = tmp_path / "pilot"
    pilot_dir.mkdir(parents=True)
    (pilot_dir / "locked_T.json").write_text(
        json.dumps(
            {
                "locked_T": 8,
                "pilot_censoring_rate": 0.05,
                "calibration_failure": False,
            }
        )
    )
    from nova_agent.lab.trauma_ablation import _read_locked_t

    T, censoring_rate = _read_locked_t(pilot_dir / "locked_T.json")
    assert T == 8
    assert censoring_rate == pytest.approx(0.05)


def test_surrogate_aborts_when_pilot_failure(tmp_path: Path) -> None:
    pilot_dir = tmp_path / "pilot"
    pilot_dir.mkdir(parents=True)
    (pilot_dir / "locked_T.json").write_text(
        json.dumps(
            {
                "locked_T": None,
                "calibration_failure": True,
            }
        )
    )
    from nova_agent.lab.trauma_ablation import _read_locked_t

    with pytest.raises(RuntimeError, match="calibration_failure"):
        _read_locked_t(pilot_dir / "locked_T.json")


def test_surrogate_blocks_without_golden_gate(tmp_path: Path) -> None:
    """run_surrogate must raise before running sessions if golden not passed."""
    from nova_agent.lab.trauma_ablation import _check_golden_gate_passed

    with pytest.raises((FileNotFoundError, RuntimeError)):
        _check_golden_gate_passed(tmp_path)


# --- Task 12: Output writers (CSV + JSONL) ---


def test_summary_csv_has_expected_columns(tmp_path: Path) -> None:
    from nova_agent.lab.trauma_ablation import _write_summary_csv

    results = [_ok_result(0), _ok_result(1)]
    out = tmp_path / "summary.csv"
    _write_summary_csv(out, results)
    text = out.read_text().splitlines()
    header = text[0].split(",")
    assert "seed_base" in header
    assert "delta_i" in header
    assert "r_post_y_on" in header
    assert "r_post_y_off" in header
    assert len(text) == 3  # header + 2 rows


def test_append_session_jsonl_accumulates(tmp_path: Path) -> None:
    from nova_agent.lab.trauma_ablation import _append_session_jsonl

    path = tmp_path / "sessions.jsonl"
    _append_session_jsonl(path, _ok_result(0))
    _append_session_jsonl(path, _ok_result(1))
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["seed_base"] == 0


# --- Task 11: Main run + adjudication ---


def test_adjudication_md_contains_required_sections(tmp_path: Path) -> None:
    from nova_agent.lab.trauma_ablation import (
        AdjudicationResult,
        _write_adjudication_md,
    )

    adj = AdjudicationResult(
        d=0.32,
        ci_lo=0.05,
        ci_hi=0.6,
        p_value_one_sided=0.01,
        n_used=68,
        n_censored_cap=1,
        n_censored_zero_encounter=1,
        primary_pass=True,
        secondary_d=0.20,
        r_off_mean=0.30,
        r_on_mean=0.18,
        anxiety_lift_off=0.55,
        anxiety_lift_on=0.40,
        sensitivity_predicate_firing_d=0.34,
        sensitivity_cap_exhaustion_count=1,
    )
    out_path = tmp_path / "adjudication.md"
    _write_adjudication_md(out_path, adj)
    text = out_path.read_text()
    assert "Primary DV" in text
    assert "Secondary DV" in text
    assert "PASS" in text
    assert "Sensitivity" in text
    assert "0.32" in text
    assert "Three-branch" in text


# --- Task 13: CLI entry point ---


def test_cli_help_runs() -> None:
    import subprocess
    import os

    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(Path.home() / ".cache/uv-envs/nova-agent")}
    result = subprocess.run(
        ["python", "-m", "nova_agent.lab.trauma_ablation", "--help"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path("/Users/idohoresh/Desktop/a/.claude/worktrees/phase-08-impl/nova-agent")),
    )
    assert result.returncode == 0
    assert "--stage" in result.stdout


@pytest.mark.asyncio
async def test_e2e_smoke_with_mock_stack(tmp_path: Path) -> None:
    """End-to-end: run_smoke with mock LLM, verify summary.csv written."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from test_lab_trauma_session import _FixedActionLLM
    from nova_agent.lab.trauma_ablation import EXIT_OK, EXIT_SMOKE_HALT, run_smoke

    llm = _FixedActionLLM(action="swipe_up")
    rc = await run_smoke(
        run_dir=tmp_path,
        n=1,
        seed_base_start=20260507,
        decision_llm=llm,
        deliberation_llm=llm,
        reflection_llm=llm,
        T_placeholder=16,
        max_moves=200,
    )
    assert rc in (EXIT_OK, EXIT_SMOKE_HALT)
    assert (tmp_path / "smoke" / "summary.csv").exists()
