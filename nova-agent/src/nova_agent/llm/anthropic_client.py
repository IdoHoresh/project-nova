from typing import Any
from anthropic import Anthropic
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from nova_agent.budget import BudgetGuard
from nova_agent.llm.protocol import Usage

log = structlog.get_logger()


class AnthropicLLM:
    def __init__(self, *, api_key: str, model: str, daily_cap_usd: float):
        self._client = Anthropic(api_key=api_key)
        self.model = model
        self.budget = BudgetGuard(daily_cap_usd=daily_cap_usd)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=2, max=30))
    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]:
        # Anthropic Messages API does NOT have native generation-time schema
        # enforcement. Schema-strict callers should still pass response_schema —
        # we accept-and-ignore here so callsites can pass it unconditionally.
        # Sonnet+ have been reliable enough on JSON-mode prompts that this
        # asymmetry is acceptable for now; tool_use-based enforcement is a
        # future ADR if drift surfaces.
        del response_schema  # explicit unused-arg hint for readers

        try:
            return self._complete_inner(
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            log.error(
                "llm.anthropic.error",
                model=self.model,
                exc_type=type(exc).__name__,
                exc=str(exc),
            )
            raise

    def _complete_inner(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> tuple[str, Usage]:
        resp = self._client.messages.create(
            model=self.model,
            system=system,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = "".join(part.text for part in resp.content if part.type == "text")
        usage = Usage(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=self.model,
        )
        self.budget.charge(usage.cost_usd)
        log.info(
            "llm.anthropic",
            model=self.model,
            tokens_in=usage.input_tokens,
            tokens_out=usage.output_tokens,
            cost=usage.cost_usd,
        )
        return text, usage
