"""Tests for the Phase 0.7 Baseline Bot decider.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md
"""

import pytest


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
