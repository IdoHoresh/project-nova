import base64
from typing import Any
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from nova_agent.budget import BudgetGuard
from nova_agent.llm.protocol import Usage

log = structlog.get_logger()


def _to_gemini_content(messages: list[dict[str, Any]]) -> list[types.Content]:
    """Convert Anthropic-style messages to Gemini Content list.

    The Anthropic shape is `[{"role": "user", "content": [{"type": "image", "source": {...}}, {"type": "text", "text": "..."}]}]`.
    Gemini accepts a flatter list of Parts.
    """
    contents: list[types.Content] = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        parts: list[types.Part] = []
        content = msg["content"]
        if isinstance(content, str):
            parts.append(types.Part.from_text(text=content))
        else:
            for item in content:
                if item.get("type") == "text":
                    parts.append(types.Part.from_text(text=item["text"]))
                elif item.get("type") == "image":
                    src = item["source"]
                    if src["type"] == "base64":
                        raw = base64.b64decode(src["data"])
                        parts.append(types.Part.from_bytes(data=raw, mime_type=src["media_type"]))
        contents.append(types.Content(role=role, parts=parts))
    return contents


_REQUEST_TIMEOUT_S = 60  # Flash averages ~2s; 60s catches silent hangs without false positives


class GeminiLLM:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        daily_cap_usd: float,
        thinking_budget: int | None = None,
    ):
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_S * 1000),
        )
        self.model = model
        self.budget = BudgetGuard(daily_cap_usd=daily_cap_usd)
        # thinking_budget=None → SDK default (model decides). thinking_budget=0
        # disables thinking entirely (Flash only — Pro rejects 0). Positive
        # values cap thinking tokens. Without this knob, Flash burns the entire
        # max_output_tokens budget on hidden reasoning and returns a truncated
        # JSON payload (latent issue #4).
        self.thinking_budget = thinking_budget

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]:
        try:
            return self._complete_inner(
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_schema=response_schema,
            )
        except Exception as exc:
            log.error(
                "llm.gemini.error",
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
        response_schema: type[BaseModel] | None = None,
    ) -> tuple[str, Usage]:
        contents = _to_gemini_content(messages)
        config_kwargs: dict[str, Any] = dict(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
            response_mime_type="application/json",  # request strict JSON
        )
        if response_schema is not None:
            # Gemini OpenAPI-3.0 schema enforcement (generation-time, not
            # post-hoc parsing). Cheaper models (flash-lite) require this to
            # avoid JSON-shape drift; flash and pro tolerate either, but
            # always passing it costs nothing and keeps the safety property
            # uniform across the tier system.
            config_kwargs["response_schema"] = response_schema
        if self.thinking_budget is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=self.thinking_budget
            )
        config = types.GenerateContentConfig(**config_kwargs)
        resp = self._client.models.generate_content(
            model=self.model,
            contents=contents,  # type: ignore[arg-type]
            config=config,
        )
        text = resp.text or ""
        meta = resp.usage_metadata
        usage = Usage(
            input_tokens=(meta.prompt_token_count or 0) if meta is not None else 0,
            output_tokens=(meta.candidates_token_count or 0) if meta is not None else 0,
            model=self.model,
        )
        self.budget.charge(usage.cost_usd)
        log.info(
            "llm.gemini",
            model=self.model,
            tokens_in=usage.input_tokens,
            tokens_out=usage.output_tokens,
            cost=usage.cost_usd,
        )
        return text, usage
