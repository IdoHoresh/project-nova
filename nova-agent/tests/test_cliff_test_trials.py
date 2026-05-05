"""Single-trial integration tests for cliff_test runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nova_agent.bus.recorder import RecordingEventBus
from nova_agent.lab.cliff_test import BotTrialResult, _run_bot_trial
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
