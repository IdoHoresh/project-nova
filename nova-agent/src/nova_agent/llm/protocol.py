from dataclasses import dataclass
from typing import Any, Protocol

import structlog
from pydantic import BaseModel

from nova_agent.budget import BudgetExceeded, SessionBudget

log = structlog.get_logger()


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


def _full_call_estimate_usd(
    *,
    model: str,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
) -> float:
    """Per-call pre-flight cost estimate per Phase 0.7a spec §5.2:

        estimated_cost = (prompt_tokens × input_rate) + (max_output_tokens × output_rate)

    ``prompt_tokens`` is approximated via a char-count heuristic
    (``char_count // 4``) because pre-tokenization would require a per-provider
    tokenizer dependency. The heuristic *under-counts* tokens vs real
    tokenizers in both directions (English ~3.5 chars/token actual; CJK ~1
    char/token actual), so the estimate generally *under-states* true cost
    relative to provider-reported usage. The abort-gate threshold is set
    conservatively low ($0.50/call default) precisely so a small
    under-estimate cannot mask a runaway request, and post-call ``true_up``
    against provider-reported usage corrects the cumulative session
    accounting. Phase 0.8 may swap this for a tokenizer-backed estimate if
    CJK or other under-counting paths emerge in production.

    Used by ``BudgetedLLM`` to enforce the per-call abort threshold separately
    from the cumulative session cap (see recalibration spec §5.0.1 precedent).
    """
    in_rate, out_rate = PRICING.get(model, (5.0, 25.0))
    char_count = len(system)
    for msg in messages:
        for value in msg.values():
            char_count += len(str(value))
    prompt_tokens = max(1, char_count // 4)
    return (prompt_tokens * in_rate / 1_000_000) + (max_tokens * out_rate / 1_000_000)


class BudgetedLLM:
    """M-07 Cost-Abort Gate: wraps any LLM, enforces a shared session spend cap.

    Satisfies the LLM Protocol (``model`` attribute + ``complete``). Multiple
    instances sharing the same ``SessionBudget`` aggregate spend across all
    LLM roles (decision, tot, reflection, bot).

    Pre-charges a pessimistic estimate (all ``max_tokens`` as output) before
    the call. On success, trues up to actual cost. On failure, refunds the
    estimate so failed calls do not consume budget.

    Per-call abort gate (Phase 0.7a spec §5.2): when ``per_call_cap_usd`` is
    set, the full pre-call estimate (input + output) is compared against the
    cap *before* session pre-charge. A single runaway call (e.g. accidental
    huge ``max_tokens`` or an oversized system prompt) is rejected without
    consuming the session budget. ``None`` or ``0`` disables the per-call gate
    while leaving the session cap intact (backward compatible).
    """

    model: str

    def __init__(
        self,
        llm: LLM,
        budget: SessionBudget,
        *,
        per_call_cap_usd: float | None = None,
    ) -> None:
        self._llm = llm
        self._budget = budget
        self._per_call_cap_usd = per_call_cap_usd
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
        if self._per_call_cap_usd is not None and self._per_call_cap_usd > 0:
            full_estimate = _full_call_estimate_usd(
                model=self._llm.model,
                system=system,
                messages=messages,
                max_tokens=max_tokens,
            )
            if full_estimate > self._per_call_cap_usd:
                # Audit trail for per-call gate trips: spec §5.2 treats
                # estimates as authoritative, so the harness needs to know
                # WHICH calls were aborted post-pilot. Never include `system`
                # or `messages` content here — those can carry retrieved
                # memories / persona context (see security.md crown-jewels).
                log.warning(
                    "per_call_cost_abort_fired",
                    model=self._llm.model,
                    max_tokens=max_tokens,
                    estimate_usd=round(full_estimate, 6),
                    cap_usd=self._per_call_cap_usd,
                )
                raise BudgetExceeded(
                    f"Pre-call estimate ${full_estimate:.4f} exceeds per-call cap "
                    f"${self._per_call_cap_usd:.2f} (model={self._llm.model}, "
                    f"max_tokens={max_tokens})."
                )

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
