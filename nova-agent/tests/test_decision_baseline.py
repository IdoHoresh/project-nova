"""Tests for the Phase 0.7 Baseline Bot decider.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md
"""

from typing import Any

import pytest

from nova_agent.llm.protocol import Usage
from nova_agent.perception.types import BoardState


class _RecordingMockLLM:
    """Minimal LLM stub that records calls and returns scripted responses."""

    def __init__(self, responses: list[str], model: str = "claude-sonnet-4-6"):
        self.model = model
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> tuple[str, Usage]:
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("MockLLM ran out of scripted responses")
        text = self._responses.pop(0)
        return text, Usage(input_tokens=100, output_tokens=50, model=self.model)


@pytest.mark.asyncio
async def test_baseline_decide_returns_decision_on_valid_response() -> None:
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    valid_json = (
        '{"observation": "two corner",'
        ' "reasoning": "consolidate left",'
        ' "action": "swipe_left",'
        ' "confidence": "medium"}'
    )
    llm = _RecordingMockLLM(responses=[valid_json])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_left"
    assert result.observation == "two corner"
    assert result.confidence == "medium"
    # Verify the LLM was called with the right config
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["temperature"] == 0.0
    assert call["max_tokens"] == 500
    assert call["response_schema"].__name__ == "_ReactOutput"
    # Verify text-only message structure
    assert len(call["messages"]) == 1
    assert call["messages"][0]["role"] == "user"
    assert all(b.get("type") != "image" for b in call["messages"][0]["content"])
    # Verify the system prompt is the canonical Bot prompt
    assert "maximize score" in call["system"]


def test_baseline_module_exports_expected_symbols():
    from nova_agent.decision import baseline

    assert hasattr(baseline, "BotDecision")
    assert hasattr(baseline, "TrialAborted")
    assert hasattr(baseline, "BaselineDecider")
    assert hasattr(baseline, "BASELINE_SYSTEM_PROMPT")
    assert hasattr(baseline, "BASELINE_MAX_TOKENS")
    assert hasattr(baseline, "BASELINE_TEMPERATURE")


def test_baseline_constants_match_spec():
    from nova_agent.decision import baseline

    assert baseline.BASELINE_MAX_TOKENS == 500
    assert baseline.BASELINE_TEMPERATURE == 0.0


def test_baseline_system_prompt_matches_adr_0007_amendment_1():
    from nova_agent.decision import baseline

    text = baseline.BASELINE_SYSTEM_PROMPT
    assert "You are an AI agent playing 2048" in text
    assert "maximize score" in text
    assert '"observation"' in text
    assert '"reasoning"' in text
    assert '"action"' in text
    assert '"confidence"' in text
    assert "swipe_up" in text and "swipe_down" in text
    assert "swipe_left" in text and "swipe_right" in text


def test_bot_decision_is_immutable_and_has_required_fields():
    from nova_agent.decision.baseline import BotDecision

    d = BotDecision(
        action="swipe_up",
        observation="empty board",
        reasoning="any direction works",
        confidence="low",
    )
    assert d.action == "swipe_up"
    with pytest.raises(Exception):  # frozen dataclass
        d.action = "swipe_down"  # type: ignore[misc]


def test_trial_aborted_carries_reason():
    from nova_agent.decision.baseline import TrialAborted

    a = TrialAborted(reason="api_error", last_move_index=12)
    assert a.reason == "api_error"
    assert a.last_move_index == 12

    a2 = TrialAborted(reason="parse_failure", last_move_index=0)
    assert a2.reason == "parse_failure"


def test_trial_aborted_reason_is_constrained_to_known_values():
    """Misconfiguration guard: the only reasons are 'api_error' and
    'parse_failure'. Tie-break and right-censoring do not abort trials."""
    from nova_agent.decision.baseline import AbortReason

    # AbortReason should be a Literal type — verify the literal members are exactly these
    import typing

    args = typing.get_args(AbortReason)
    assert set(args) == {"api_error", "parse_failure"}


# ---------------------------------------------------------------------------
# Task 4 — API-error retry tests
# ---------------------------------------------------------------------------


class _RetryingMockLLM:
    """Mock that raises scripted exceptions before scripted text responses."""

    def __init__(
        self,
        scripted: list[str | BaseException],
        model: str = "claude-sonnet-4-6",
    ):
        self.model = model
        self._scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> tuple[str, Usage]:
        self.calls.append(kwargs)
        if not self._scripted:
            raise AssertionError("MockLLM ran out of scripted items")
        item = self._scripted.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item, Usage(input_tokens=100, output_tokens=50, model=self.model)


@pytest.mark.asyncio
async def test_baseline_decide_retries_on_api_error_then_succeeds() -> None:
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    valid_json = '{"observation": "x", "reasoning": "y", "action": "swipe_up", "confidence": "low"}'
    llm = _RetryingMockLLM(scripted=[RuntimeError("transient 503"), valid_json])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_up"
    assert len(llm.calls) == 2  # 1 failed + 1 succeeded


@pytest.mark.asyncio
async def test_baseline_decide_aborts_after_three_api_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nova_agent.decision.baseline import BaselineDecider, TrialAborted

    # Patch asyncio.sleep so the test doesn't actually wait the backoff intervals
    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(
        scripted=[
            RuntimeError("err 1"),
            RuntimeError("err 2"),
            RuntimeError("err 3"),
        ]
    )
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=12)

    assert isinstance(result, TrialAborted)
    assert result.reason == "api_error"
    assert result.last_move_index == 12
    assert len(llm.calls) == 3


async def _noop_sleep(_seconds: float) -> None:
    return None


# ---------------------------------------------------------------------------
# Task 5 — Parse-failure retry tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_baseline_decide_retries_once_on_parse_failure_then_succeeds(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    invalid = "not json"
    valid = '{"observation": "x", "reasoning": "y", "action": "swipe_down", "confidence": "high"}'
    llm = _RetryingMockLLM(scripted=[invalid, valid])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_down"
    assert len(llm.calls) == 2  # 1 unparseable + 1 valid


@pytest.mark.asyncio
async def test_baseline_decide_aborts_after_two_parse_failures(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider, TrialAborted

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(scripted=["bad json", "still bad"])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=8)

    assert isinstance(result, TrialAborted)
    assert result.reason == "parse_failure"
    assert result.last_move_index == 8
    assert len(llm.calls) == 2  # original + 1 retry per A1.5


# ---------------------------------------------------------------------------
# Task 6 — Telemetry event tests
# ---------------------------------------------------------------------------


class _CapturingBus:
    """Minimal stand-in for EventBus that captures published events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, event: str, data: Any) -> None:
        self.events.append((event, data))


@pytest.mark.asyncio
async def test_baseline_telemetry_events_emit_on_success() -> None:
    from nova_agent.decision.baseline import BaselineDecider

    valid = '{"observation": "x", "reasoning": "y", "action": "swipe_up", "confidence": "low"}'
    llm = _RetryingMockLLM(scripted=[valid])
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=3, move_index=7)

    event_names = [name for name, _data in bus.events]
    assert "bot_call_attempt" in event_names
    assert "bot_call_success" in event_names

    success = next(d for n, d in bus.events if n == "bot_call_success")
    assert success["trial"] == 3
    assert success["move_index"] == 7
    assert success["action"] == "swipe_up"
    assert "prompt_tokens" in success
    assert "completion_tokens" in success
    assert "latency_ms" in success


@pytest.mark.asyncio
async def test_baseline_telemetry_emits_api_error_and_trial_aborted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nova_agent.decision.baseline import BaselineDecider

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(scripted=[RuntimeError("e1"), RuntimeError("e2"), RuntimeError("e3")])
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=0, move_index=10)

    api_errors = [d for n, d in bus.events if n == "bot_call_api_error"]
    assert len(api_errors) == 3
    aborted = [d for n, d in bus.events if n == "bot_trial_aborted"]
    assert len(aborted) == 1
    assert aborted[0]["reason"] == "api_error"
    assert aborted[0]["last_move_index"] == 10


@pytest.mark.asyncio
async def test_baseline_telemetry_emits_parse_failure_and_trial_aborted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nova_agent.decision.baseline import BaselineDecider

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(scripted=["junk", "still junk"])
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=1, move_index=4)

    parse_fails = [d for n, d in bus.events if n == "bot_call_parse_failure"]
    assert len(parse_fails) == 2
    aborted = [d for n, d in bus.events if n == "bot_trial_aborted"]
    assert aborted[0]["reason"] == "parse_failure"


# ---------------------------------------------------------------------------
# Task 7 — Integration test: Bot + Game2048Sim full trial
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_baseline_runs_full_trial_against_game2048sim_with_mock_llm(monkeypatch):
    """Integration: Bot decides, runner-style loop applies the swipe to
    Game2048Sim, until game-over OR MAX_MOVES=50.

    Mock LLM cycles through valid responses. This is NOT the Test Runner
    (no scenario, no paired logic, no telemetry persistence), but it
    verifies BaselineDecider integrates with the sim contract.
    """
    from nova_agent.action.adb import SwipeDirection
    from nova_agent.decision.baseline import BaselineDecider, BotDecision
    from nova_agent.lab.scenarios import SCENARIOS
    from nova_agent.lab.sim import Game2048Sim

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    # Cycle through all four directions to avoid getting stuck on any single one.
    cycling_responses = [
        '{"observation": "x", "reasoning": "y", "action": "swipe_up", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_right", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_down", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_left", "confidence": "low"}',
    ] * 20  # max 80 calls, well above MAX_MOVES=50
    llm = _RetryingMockLLM(scripted=cycling_responses)

    scenario = SCENARIOS["fresh-start"]
    sim = Game2048Sim(seed=scenario.seed_base, scenario=scenario)
    decider = BaselineDecider(llm=llm)

    MAX_MOVES = 50
    moves_taken = 0
    while not sim.is_game_over() and moves_taken < MAX_MOVES:
        result = await decider.decide(board=sim.board, trial_index=0, move_index=moves_taken)
        assert isinstance(result, BotDecision), f"unexpected abort at move {moves_taken}"
        sim.apply_move(SwipeDirection(result.action))
        moves_taken += 1

    # Either game-over OR right-censored at MAX_MOVES. Both acceptable.
    assert sim.is_game_over() or moves_taken == MAX_MOVES
