"""Single-trial integration tests for cliff_test runner."""

from __future__ import annotations

import asyncio
import csv as _csv
import tempfile
from pathlib import Path
from typing import Any

import pytest

from nova_agent.bus.recorder import RecordingEventBus
from nova_agent.lab.cliff_test import (
    BUDGET_PER_SCENARIO_ARM_USD,
    BotTrialResult,
    CarlaTrialResult,
    HARD_CAP_MULTIPLIER,
    _BudgetState,
    _CSV_COLUMNS,
    _run_bot_trial,
    _run_carla_trial,
    _worker,
)
from nova_agent.lab.scenarios import SCENARIOS
from nova_agent.llm.mock import MockLLMClient


@pytest.mark.asyncio
async def test_bot_trial_completes_happy_path(tmp_path: Path) -> None:
    """One bot trial runs to game-over OR MAX_MOVES with no abort."""
    scenario = SCENARIOS["snake-collapse-128"]
    llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        assert isinstance(result, BotTrialResult)
        assert result.cost_usd >= 0.0
        assert result.final_move_index >= 0
        assert result.abort_reason is None
        # Trial either ended in game-over or right-censored.
        if result.is_right_censored:
            assert result.t_baseline_fails == 50  # MAX_MOVES sentinel per scenarios spec §5.1
        else:
            assert result.t_baseline_fails == result.final_move_index
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_bot_trial_aborts_on_sustained_api_failure(tmp_path: Path) -> None:
    """If the LLM raises every call, BaselineDecider returns TrialAborted on the
    third retry; _run_bot_trial surfaces abort_reason='api_error', t_baseline_fails=None.
    """
    scenario = SCENARIOS["snake-collapse-128"]

    class AlwaysFailingLLM(MockLLMClient):
        def complete(  # type: ignore[override]
            self,
            *,
            system: str,
            messages: list[dict[str, Any]],
            max_tokens: int = 200,
            temperature: float = 0.7,
            response_schema: object = None,
        ) -> tuple[str, object]:
            raise RuntimeError("simulated LLM provider outage")

    llm = AlwaysFailingLLM()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        assert result.abort_reason == "api_error"
        assert result.t_baseline_fails is None
        assert result.is_right_censored is False
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_bot_trial_right_censored_when_no_game_over(tmp_path: Path) -> None:
    """If MockLLMClient drives the bot through 50 moves without game-over,
    t_baseline_fails = 50 sentinel + is_right_censored = True per scenarios
    spec §5.1.
    """
    scenario = SCENARIOS["fresh-start"]  # empty board → unlikely to hit game-over within 50 moves
    llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        # The fresh-start scenario is unlikely (but not guaranteed) to be
        # right-censored. We assert the invariant: IF right-censored, the
        # sentinel applies.
        if result.is_right_censored:
            assert result.t_baseline_fails == 50
            assert result.final_move_index == 49  # last move attempted
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_carla_trial_completes_happy_path(tmp_path: Path) -> None:
    """One Carla trial runs to game-over OR MAX_MOVES; returns a CarlaTrialResult
    with structurally valid fields.

    Note: snake-collapse-128 was re-recalibrated 2026-05-07 to a grid with 4
    empty cells. MockLLMClient always plays swipe_up; immediate game-over is
    now less likely, but anxiety_trajectory is still not guaranteed to be
    non-empty; we only assert structural invariants.
    """
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_carla_trial(
            scenario=scenario,
            trial_index=0,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bus=bus,
        )
        assert isinstance(result, CarlaTrialResult)
        assert isinstance(result.anxiety_trajectory, list)
        # t_predicts is None or an int; anxiety_threshold_met is the boolean form.
        if result.t_predicts is not None:
            assert result.anxiety_threshold_met is True
        else:
            assert result.anxiety_threshold_met is False
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_carla_trial_tempdir_is_cleaned_up(tmp_path: Path) -> None:
    """The MemoryCoordinator tempdir is removed at trial end (context-manager exit)."""
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        # Snapshot existing tempdirs that match the runner's prefix.
        tmp_root = Path(tempfile.gettempdir())
        before = {p.name for p in tmp_root.iterdir() if p.name.startswith("nova-cliff-")}
        await _run_carla_trial(
            scenario=scenario,
            trial_index=0,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bus=bus,
        )
        after = {p.name for p in tmp_root.iterdir() if p.name.startswith("nova-cliff-")}
        # No new nova-cliff- tempdirs leaked.
        assert before == after
    finally:
        await bus.stop()


# ---------------------------------------------------------------------------
# Task 8: _worker paired-trial coroutine tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paired_worker_runs_both_arms(tmp_path: Path) -> None:
    """One paired trial; both arms run; both CSV rows written."""
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bot_llm = MockLLMClient()
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()
    output_dir = tmp_path

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=output_dir,
        decision_llm=decision_llm,
        tot_llm=tot_llm,
        reflection_llm=reflection_llm,
        bot_llm=bot_llm,
    )

    # Both rows written.
    with csv_path.open() as f:
        rows = list(_csv.reader(f))
    # 1 header + 2 data rows.
    assert len(rows) == 3
    arms_written = {rows[1][2], rows[2][2]}
    assert arms_written == {"carla", "bot"}


@pytest.mark.asyncio
async def test_paired_worker_records_carla_abort_and_bot_success(tmp_path: Path) -> None:
    """If Carla aborts on api_error and Bot completes normally, both rows are
    written with the appropriate abort_reason values per Bot spec §2.6
    (paired-discard logic lives in analyze_results.py, not in the runner)."""

    scenario = SCENARIOS["snake-collapse-128"]

    class FailOnReact(MockLLMClient):
        def complete(self, *a: Any, **kw: Any) -> tuple[str, object]:  # type: ignore[override]
            raise RuntimeError("simulated provider outage on Carla path")

    decision_llm = FailOnReact()
    tot_llm = FailOnReact()
    reflection_llm = MockLLMClient()
    bot_llm = MockLLMClient()
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=tmp_path,
        decision_llm=decision_llm,
        tot_llm=tot_llm,
        reflection_llm=reflection_llm,
        bot_llm=bot_llm,
    )

    with csv_path.open() as f:
        rows = list(_csv.reader(f))
    # Both rows present.
    assert len(rows) == 3
    by_arm = {row[2]: row for row in rows[1:]}
    # Carla row: abort_reason populated; t_predicts may be None.
    idx_abort = list(_CSV_COLUMNS).index("abort_reason")
    assert by_arm["carla"][idx_abort] == "api_error"
    # Bot row: no abort_reason.
    assert by_arm["bot"][idx_abort] == ""


@pytest.mark.asyncio
async def test_paired_worker_skips_when_hard_cap_hit(tmp_path: Path) -> None:
    """If hard cap is already hit on entry, _worker returns immediately
    without invoking any LLM and writes no CSV rows."""
    scenario = SCENARIOS["snake-collapse-128"]
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()
    # Pre-load the budget past the hard cap.
    budget.add(scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD * HARD_CAP_MULTIPLIER + 0.01)

    class TripWireLLM(MockLLMClient):
        def complete(self, *a: Any, **kw: Any) -> tuple[str, object]:  # type: ignore[override]
            raise AssertionError("hard cap hit — no LLM calls should occur")

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=tmp_path,
        decision_llm=TripWireLLM(),
        tot_llm=TripWireLLM(),
        reflection_llm=TripWireLLM(),
        bot_llm=TripWireLLM(),
    )

    # No CSV rows (file may not even exist).
    if csv_path.exists():
        with csv_path.open() as f:
            rows = list(_csv.reader(f))
        # At most a header — no data rows.
        assert len(rows) <= 1
