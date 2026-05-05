"""Tests for the cliff-test runner orchestrator + CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from nova_agent.lab.cliff_test import (
    BUDGET_PER_SCENARIO_ARM_USD,
    EXIT_HARD_CAP,
    EXIT_OK,
    EXIT_SOFT_CAP,
    HARD_CAP_MULTIPLIER,
    _BudgetState,
    run_cliff_test,
)
from nova_agent.lab.scenarios import SCENARIOS
from nova_agent.llm.mock import MockLLMClient


def _run_cli(
    *args: str, env_overrides: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the cliff-test CLI as a subprocess and return the result."""
    env = os.environ.copy()
    # Strip API keys to make sure tier-guard tests don't accidentally hit a real provider.
    for var in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        env.pop(var, None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "nova_agent.lab.cliff_test", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_help_runs_clean() -> None:
    """`cliff-test --help` exits 0 and prints usage."""
    result = _run_cli("--help")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "cliff-test" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_rejects_dev_tier() -> None:
    """Runner refuses NOVA_TIER=dev (per spec §6.1 + ADR-0006)."""
    result = _run_cli(
        "--scenario",
        "snake-collapse-128",
        "--n",
        "1",
        env_overrides={"NOVA_TIER": "dev"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined


def test_cli_rejects_plumbing_tier() -> None:
    """Runner refuses NOVA_TIER=plumbing (cognitive-judgment models downgraded)."""
    result = _run_cli(
        "--scenario",
        "snake-collapse-128",
        "--n",
        "1",
        env_overrides={"NOVA_TIER": "plumbing"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined


# ---------------------------------------------------------------------------
# Task 9: run_cliff_test orchestrator tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cliff_test_pilot_writes_to_pilot_subdir(tmp_path: Path) -> None:
    """--pilot routes output to pilot_results/, not results/."""
    code = await run_cliff_test(
        scenarios=[SCENARIOS["snake-collapse-128"]],
        n=1,
        output_dir=tmp_path,
        concurrency=1,
        pilot=True,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
    )
    assert code == EXIT_OK
    assert (tmp_path / "pilot_results" / "cliff_test_results.csv").exists()
    assert not (tmp_path / "results" / "cliff_test_results.csv").exists()


@pytest.mark.asyncio
async def test_run_cliff_test_real_run_writes_to_results_subdir(tmp_path: Path) -> None:
    code = await run_cliff_test(
        scenarios=[SCENARIOS["snake-collapse-128"]],
        n=1,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
    )
    assert code == EXIT_OK
    assert (tmp_path / "results" / "cliff_test_results.csv").exists()


@pytest.mark.asyncio
async def test_run_cliff_test_soft_cap_drains_in_flight(tmp_path: Path) -> None:
    """Pre-load budget near soft cap. Runner should drain at most ONE more
    pair (the in-flight one), then exit with EXIT_SOFT_CAP. Some trials
    will be skipped — verify CSV row count is < N."""
    scenario = SCENARIOS["snake-collapse-128"]
    pre_loaded_budget = _BudgetState()
    pre_loaded_budget.add(scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD - 0.001)

    code = await run_cliff_test(
        scenarios=[scenario],
        n=10,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
        _budget_for_test=pre_loaded_budget,  # test-only injection seam
    )
    assert code == EXIT_SOFT_CAP
    csv_path = tmp_path / "results" / "cliff_test_results.csv"
    if csv_path.exists():
        rows = csv_path.read_text().splitlines()
        # Header + at most a small number of data rows.
        assert len(rows) - 1 < 20  # not all 20 (10 trials × 2 arms) ran


@pytest.mark.asyncio
async def test_run_cliff_test_hard_cap_kills_pre_LLM(tmp_path: Path) -> None:
    """Pre-load budget past hard cap. Runner exits EXIT_HARD_CAP without
    invoking any LLM."""
    scenario = SCENARIOS["snake-collapse-128"]
    pre_loaded_budget = _BudgetState()
    pre_loaded_budget.add(
        scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD * HARD_CAP_MULTIPLIER + 0.01
    )

    class TripWireLLM(MockLLMClient):
        def complete(  # type: ignore[override]
            self,
            *,
            system: str,
            messages: list[dict[str, Any]],
            max_tokens: int = 200,
            temperature: float = 0.7,
            response_schema: object = None,
        ) -> tuple[str, object]:
            raise AssertionError("hard cap should prevent any LLM call")

    code = await run_cliff_test(
        scenarios=[scenario],
        n=5,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=TripWireLLM(),
        tot_llm=TripWireLLM(),
        reflection_llm=TripWireLLM(),
        bot_llm=TripWireLLM(),
        _budget_for_test=pre_loaded_budget,
    )
    assert code == EXIT_HARD_CAP


@pytest.mark.asyncio
async def test_run_cliff_test_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """A non-empty results dir without --force → runner raises FileExistsError."""
    scenario = SCENARIOS["snake-collapse-128"]
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "stale.csv").write_text("dummy")

    with pytest.raises(FileExistsError):
        await run_cliff_test(
            scenarios=[scenario],
            n=1,
            output_dir=tmp_path,
            concurrency=1,
            pilot=False,
            force=False,
            decision_llm=MockLLMClient(),
            tot_llm=MockLLMClient(),
            reflection_llm=MockLLMClient(),
            bot_llm=MockLLMClient(),
        )


# ---------------------------------------------------------------------------
# Task 10: main() e2e CLI smoke
# ---------------------------------------------------------------------------


def test_cli_e2e_pilot_smoke_via_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: run the CLI as a subprocess in pilot mode against fresh-start.

    Skipped when ANTHROPIC_API_KEY / GOOGLE_API_KEY absent (we don't want a
    test that hits real providers). For production-tier validation, this
    test runs with the real keys; for the standard pytest trio it skips.
    """
    # Truthy check, not ``in os.environ`` — CI exposes these as empty strings,
    # which the membership check accepts but pydantic-settings rejects when
    # the runner tries to load real provider credentials. Gotcha #3 in CLAUDE.md.
    if not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("e2e smoke skipped: requires populated ANTHROPIC_API_KEY + GOOGLE_API_KEY")

    output_dir = tmp_path / "runs" / "e2e-smoke"
    result = _run_cli(
        "--scenario",
        "fresh-start",
        "--n",
        "1",
        "--pilot",
        "--concurrency",
        "1",
        "--output-dir",
        str(output_dir),
        env_overrides={"NOVA_TIER": "production"},
    )
    assert result.returncode in {0, 2, 3}, f"stderr: {result.stderr}"
    csv_path = output_dir / "pilot_results" / "cliff_test_results.csv"
    assert csv_path.exists()
