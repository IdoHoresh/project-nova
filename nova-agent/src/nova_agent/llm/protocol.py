from dataclasses import dataclass
from typing import Any, Protocol


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
    """Provider-agnostic LLM interface used by every cognitive module."""

    model: str

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> tuple[str, Usage]: ...
