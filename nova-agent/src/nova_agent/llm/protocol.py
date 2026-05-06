from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from nova_agent.budget import BudgetExceeded, SessionBudget


# Per-1M-token pricing in USD. Verified against provider pricing pages May 2026.
# Update if providers change pricing — the budget guard relies on these.
PRICING: dict[str, tuple[float, float]] = {
    # (input_usd_per_mtok, output_usd_per_mtok)
    "claude-opus-4-7": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "gemini-2.5-pro": (1.25, 10.0),  # tier <=200K input tokens
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def cost_usd(self) -> float:
        in_rate, out_rate = PRICING.get(self.model, (5.0, 25.0))  # conservative default
        return self.input_tokens * in_rate / 1_000_000 + self.output_tokens * out_rate / 1_000_000


class LLM(Protocol):
    """Provider-agnostic LLM interface used by every cognitive module.

    `response_schema`: when provided, callers ask the provider to enforce
    that the response is valid JSON matching the given pydantic model.
    Providers that support native schema enforcement (Gemini's
    `response_schema` / OpenAPI 3.0 subset) MUST honor it. Providers
    that don't (Anthropic Messages API, mock) MUST accept-and-ignore so
    callsites can pass it unconditionally and benefit on Gemini routes.
    Callers should still validate via `nova_agent.llm.structured.parse_json`
    — schema enforcement is a generation-time guarantee, not a runtime
    validation; the validation step also catches cross-provider drift.
    """

    model: str

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]: ...


def _max_output_estimate(model: str, max_tokens: int) -> float:
    """Conservative pre-call cost: worst-case all max_tokens as output tokens."""
    _, out_rate = PRICING.get(model, (5.0, 25.0))
    return max_tokens * out_rate / 1_000_000


class BudgetedLLM:
    """M-07 Cost-Abort Gate: wraps any LLM, enforces a shared session spend cap.

    Satisfies the LLM Protocol (``model`` attribute + ``complete``). Multiple
    instances sharing the same ``SessionBudget`` aggregate spend across all
    LLM roles (decision, tot, reflection, bot).

    Pre-charges a pessimistic estimate (all ``max_tokens`` as output) before
    the call. On success, trues up to actual cost. On failure, refunds the
    estimate so failed calls do not consume budget.
    """

    model: str

    def __init__(self, llm: LLM, budget: SessionBudget) -> None:
        self._llm = llm
        self._budget = budget
        self.model = llm.model

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]:
        estimate = _max_output_estimate(self._llm.model, max_tokens)
        self._budget.pre_charge(estimate)  # raises BudgetExceeded if over cap
        try:
            text, usage = self._llm.complete(
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_schema=response_schema,
            )
        except BudgetExceeded:
            raise
        except Exception:
            self._budget.refund(estimate)
            raise
        self._budget.true_up(estimate, usage.cost_usd)
        return text, usage
