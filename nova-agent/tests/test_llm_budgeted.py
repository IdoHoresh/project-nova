"""Tests for BudgetedLLM (M-07 Cost-Abort Gate)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from nova_agent.budget import BudgetExceeded, SessionBudget
from nova_agent.llm.protocol import (
    PRICING,
    BudgetedLLM,
    Usage,
    _full_call_estimate_usd,
)


class _FixedLLM:
    """Minimal LLM stub: returns a fixed string and Usage."""

    model = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self.call_count = 0

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]:
        self.call_count += 1
        return "ok", Usage(input_tokens=10, output_tokens=5, model=self.model)


class _ExplodingLLM:
    """LLM stub that always raises RuntimeError."""

    model = "claude-sonnet-4-6"

    def complete(self, **_: Any) -> tuple[str, Usage]:
        raise RuntimeError("boom")


def test_budgeted_llm_passes_through_on_success() -> None:
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=1.0)
    llm = BudgetedLLM(inner, budget)
    text, usage = llm.complete(system="s", messages=[], max_tokens=100)
    assert text == "ok"
    assert inner.call_count == 1
    # spent reflects actual usage cost (trued-up from estimate)
    assert budget.spent == usage.cost_usd


def test_budgeted_llm_exposes_model() -> None:
    inner = _FixedLLM()
    llm = BudgetedLLM(inner, SessionBudget(cap_usd=1.0))
    assert llm.model == "claude-sonnet-4-6"


def test_budgeted_llm_raises_before_call_when_cap_exceeded() -> None:
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=0.0001)  # very tight cap
    llm = BudgetedLLM(inner, budget)
    with pytest.raises(BudgetExceeded):
        llm.complete(system="s", messages=[], max_tokens=10000)  # estimate >> cap
    assert inner.call_count == 0  # underlying LLM must NOT have been called


def test_budgeted_llm_refunds_on_llm_exception() -> None:
    inner = _ExplodingLLM()
    budget = SessionBudget(cap_usd=10.0)
    llm = BudgetedLLM(inner, budget)
    with pytest.raises(RuntimeError):
        llm.complete(system="s", messages=[], max_tokens=100)
    # Budget should be refunded — spent must be 0 (or very close) after a failed call
    assert budget.spent == 0.0


def test_budgeted_llm_accumulates_across_calls() -> None:
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=10.0)
    llm = BudgetedLLM(inner, budget)
    llm.complete(system="s", messages=[], max_tokens=100)
    llm.complete(system="s", messages=[], max_tokens=100)
    # spent should be 2 × actual per-call cost
    expected = 2 * Usage(input_tokens=10, output_tokens=5, model="claude-sonnet-4-6").cost_usd
    assert abs(budget.spent - expected) < 1e-9


# Phase 0.7a §5.2 — per-call cost-abort gate ---------------------------------


def test_full_call_estimate_uses_input_and_output_rates() -> None:
    """Estimate matches spec §5.2 formula:
    (prompt_tokens × input_rate) + (max_output_tokens × output_rate),
    with prompt_tokens approximated via char_count // 4.
    """
    model = "gemini-2.5-pro"  # (input=1.25, output=10.0) per Mtok
    in_rate, out_rate = PRICING[model]

    system = "x" * 4000  # 4000 chars
    messages = [{"role": "user", "content": "y" * 4000}]  # 4000 chars + role overhead
    max_tokens = 1024

    estimate = _full_call_estimate_usd(
        model=model,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    )

    # Char count ≥ 8000 chars -> ≥ 2000 prompt tokens via //4 heuristic.
    assert estimate >= (2000 * in_rate / 1_000_000) + (max_tokens * out_rate / 1_000_000)
    # Sanity upper bound (well under any plausible cap).
    assert estimate < 0.10


def test_full_call_estimate_unknown_model_uses_conservative_default() -> None:
    estimate = _full_call_estimate_usd(
        model="totally-unknown-model",
        system="hi",
        messages=[],
        max_tokens=100,
    )
    # Conservative default rates (5.0, 25.0); strictly > 0.
    assert estimate > 0.0


def test_per_call_cap_aborts_when_estimate_exceeds_cap() -> None:
    """Per-call gate fires before the inner LLM is invoked when the
    pre-call full estimate exceeds the per-call cap, even if the
    session budget would otherwise allow the call.
    """
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=100.0)  # session cap intentionally generous
    llm = BudgetedLLM(inner, budget, per_call_cap_usd=0.0001)

    with pytest.raises(BudgetExceeded):
        llm.complete(system="s", messages=[], max_tokens=10000)

    assert inner.call_count == 0  # inner LLM must NOT have been called
    assert budget.spent == 0.0  # session budget must NOT have been pre-charged


def test_per_call_cap_includes_input_token_cost() -> None:
    """Input tokens (prompt) push the estimate past the cap on their own,
    even if max_tokens × output_rate stays below the cap. Mirrors spec §5.2:
    estimated_cost = prompt_input + max_output_output.
    """
    inner = _FixedLLM()  # model = claude-sonnet-4-6, input=3.0/Mtok
    # Per-call cap chosen so that:
    #   - max_tokens=100 alone gives output cost = 100*15/1M = $0.0015 (under cap)
    #   - 1M chars of system prompt -> 250K prompt tokens -> 250K*3/1M = $0.75 (over cap)
    budget = SessionBudget(cap_usd=100.0)
    llm = BudgetedLLM(inner, budget, per_call_cap_usd=0.10)

    huge_system = "x" * 1_000_000
    with pytest.raises(BudgetExceeded):
        llm.complete(system=huge_system, messages=[], max_tokens=100)

    assert inner.call_count == 0
    assert budget.spent == 0.0


def test_per_call_cap_none_disables_gate() -> None:
    """per_call_cap_usd=None preserves prior behavior (session cap only)."""
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=100.0)
    llm = BudgetedLLM(inner, budget, per_call_cap_usd=None)
    text, _ = llm.complete(system="s" * 1_000_000, messages=[], max_tokens=10000)
    assert text == "ok"
    assert inner.call_count == 1


def test_per_call_cap_zero_disables_gate() -> None:
    """per_call_cap_usd=0 disables the gate (matches BudgetGuard's 0=unlimited convention)."""
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=100.0)
    llm = BudgetedLLM(inner, budget, per_call_cap_usd=0.0)
    text, _ = llm.complete(system="s" * 1_000_000, messages=[], max_tokens=10000)
    assert text == "ok"
    assert inner.call_count == 1


def test_per_call_cap_default_is_none_when_omitted() -> None:
    """Backward-compat: existing callsites that pass only (llm, budget) keep prior behavior."""
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=100.0)
    llm = BudgetedLLM(inner, budget)  # no per_call_cap_usd kwarg
    text, _ = llm.complete(system="s" * 1_000_000, messages=[], max_tokens=10000)
    assert text == "ok"
    assert inner.call_count == 1


def test_per_call_cap_passes_when_estimate_under_cap() -> None:
    """Calls under the per-call cap proceed normally and accumulate session spend."""
    inner = _FixedLLM()
    budget = SessionBudget(cap_usd=100.0)
    llm = BudgetedLLM(inner, budget, per_call_cap_usd=0.50)
    text, usage = llm.complete(system="hi", messages=[], max_tokens=128)
    assert text == "ok"
    assert inner.call_count == 1
    assert budget.spent == usage.cost_usd
