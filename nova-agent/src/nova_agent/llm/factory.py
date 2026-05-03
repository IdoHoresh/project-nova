from nova_agent.llm.protocol import LLM
from nova_agent.llm.anthropic_client import AnthropicLLM
from nova_agent.llm.gemini_client import GeminiLLM


def build_llm(
    *,
    model: str,
    google_api_key: str,
    anthropic_api_key: str,
    daily_cap_usd: float,
    thinking_budget: int | None = None,
) -> LLM:
    """Construct the right adapter for a given model name.

    Routing:
      - gemini-* → GeminiLLM (uses GOOGLE_API_KEY)
      - claude-* → AnthropicLLM (uses ANTHROPIC_API_KEY)

    `thinking_budget` is forwarded to GeminiLLM only; AnthropicLLM ignores it.
    Pass 0 for Gemini Flash to disable internal thinking and free the full
    max_output_tokens budget for visible JSON.
    """
    if model.startswith("gemini-"):
        return GeminiLLM(
            api_key=google_api_key,
            model=model,
            daily_cap_usd=daily_cap_usd,
            thinking_budget=thinking_budget,
        )
    if model.startswith("claude-"):
        return AnthropicLLM(api_key=anthropic_api_key, model=model, daily_cap_usd=daily_cap_usd)
    raise ValueError(f"Unknown model family: {model!r}")
