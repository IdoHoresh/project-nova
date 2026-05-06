"""Tests for BudgetedLLM (M-07 Cost-Abort Gate)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from nova_agent.budget import BudgetExceeded, SessionBudget
from nova_agent.llm.protocol import BudgetedLLM, Usage


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
