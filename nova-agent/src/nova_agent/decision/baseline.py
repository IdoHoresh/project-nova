"""Phase 0.7 Baseline Bot — purely-logical score-maximizer (ADR-0007).

The Baseline Bot is the control arm of the cliff test. It calls the LLM
once per move with no affect, no memory, no Tree-of-Thoughts, no
reflection. Its only job is to commit a move that maximizes score from
the current grid + score.

Per-call protocol:
  - 3x exponential-backoff retry on API errors → trial abort
  - 1x retry on parse failures → trial abort
  - Invalid-move handling lives in the Test Runner (UP > RIGHT > DOWN >
    LEFT tie-break per scenarios spec §2.3); the Bot does not see
    post-swipe state.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md
ADR:  docs/decisions/0007-blind-control-group-for-cliff-test.md (Amendment 1)
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Literal

from nova_agent.bus.websocket import EventBus
from nova_agent.decision.prompts import build_user_prompt
from nova_agent.decision.react import _ReactOutput  # noqa: PLC2701
from nova_agent.llm.protocol import LLM, Usage
from nova_agent.llm.structured import StructuredOutputError, parse_json
from nova_agent.perception.types import BoardState


# ADR-0007 prompt (verbatim) extended with JSON-output instructions matching
# the shared schema (Q4 / A1.3). Schema is _ReactOutput from decision/react.py.
BASELINE_SYSTEM_PROMPT = """\
You are an AI agent playing 2048. Your only goal is to maximize score.
Compute the next move. Emit strict JSON only (no prose around it):
{
  "observation": "5-10 word fragment, what you see on the board",
  "reasoning":   "5-15 word fragment, why this move maximizes score",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
"""

# Per Q4 / A1.3 — Bot temp=0 (greedy max-prob), max_tokens=500 (Bot needs
# no thinking budget; 500 leaves room for short reasoning + small JSON
# payload).
BASELINE_TEMPERATURE: float = 0.0
BASELINE_MAX_TOKENS: int = 500


AbortReason = Literal["api_error", "parse_failure"]

# Retry budget for parse failures.  At temp=0 with the same prompt the retry
# is deterministic, but cheap insurance against transient model-version-routing
# variance (spec §3.3).
_PARSE_RETRY_LIMIT: int = 2  # 1 original attempt + 1 retry per A1.5

# Retry budget for transient API failures.  _RETRYABLE_API_EXCEPTIONS is
# deliberately broad (Exception) for now — the LLM provider exception
# hierarchy has not yet been audited across Anthropic, Gemini, and Mock
# adapters.  Narrow in a follow-up commit once the audit is complete.
_API_RETRY_LIMIT: int = 3
_RETRYABLE_API_EXCEPTIONS: tuple[type[BaseException], ...] = (Exception,)


@dataclass(frozen=True)
class BotDecision:
    """Successful per-call output from BaselineDecider."""

    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    observation: str
    reasoning: str
    confidence: Literal["low", "medium", "high"]


@dataclass(frozen=True)
class TrialAborted:
    """Returned by BaselineDecider.decide when retries exhaust.

    Per A1.5: aborted trials are not re-run (Bot at temp=0 + fixed seed
    reproduces the same failure deterministically). The Test Runner
    records the abort and applies paired-discard logic (A1.6) for test 2.
    """

    reason: AbortReason
    last_move_index: int


class BaselineDecider:
    """LLM-based one-shot per-move decider for the Phase 0.7 control arm.

    Call signature mirrors ReactDecider's text-only mode (no screenshot).
    Implementation in subsequent tasks: Task 3 (happy path), Task 4
    (API error retry), Task 5 (parse failure retry), Task 6 (telemetry).
    """

    def __init__(self, *, llm: LLM, bus: EventBus | None = None) -> None:
        self.llm = llm
        self.bus = bus

    async def decide(
        self,
        *,
        board: BoardState,
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]

        for parse_attempt in range(_PARSE_RETRY_LIMIT):
            call_result = await self._call_with_api_retry(
                messages=messages,
                trial_index=trial_index,
                move_index=move_index,
            )
            if call_result is None:
                await self._emit(
                    "bot_trial_aborted",
                    {
                        "trial": trial_index,
                        "reason": "api_error",
                        "last_move_index": move_index,
                    },
                )
                return TrialAborted(reason="api_error", last_move_index=move_index)

            text, usage, latency_ms = call_result
            try:
                parsed = parse_json(text, _ReactOutput)
                await self._emit(
                    "bot_call_success",
                    {
                        "trial": trial_index,
                        "move_index": move_index,
                        "action": parsed.action,
                        "latency_ms": latency_ms,
                        "prompt_tokens": usage.input_tokens,
                        "completion_tokens": usage.output_tokens,
                    },
                )
                return BotDecision(
                    action=parsed.action,
                    observation=parsed.observation,
                    reasoning=parsed.reasoning,
                    confidence=parsed.confidence,
                )
            except StructuredOutputError:
                # Excerpt narrowed from 200 to 40 chars per security-reviewer
                # MEDIUM finding on commit 0bfcca3: 200-char window comfortably
                # fits Anthropic (~108) and Google (~39) API keys; if a
                # prompt-injection or confused-model response echoes a key,
                # the excerpt persists via RecordingEventBus → JSONL on disk.
                # 40 chars preserves debugging value (parse-failure shape) and
                # forces any current-format key into a truncated state.
                # excerpt_length surfaces full size for diagnostics.
                await self._emit(
                    "bot_call_parse_failure",
                    {
                        "trial": trial_index,
                        "move_index": move_index,
                        "raw_response_excerpt": text[:40],
                        "excerpt_length": len(text),
                        "attempt_n": parse_attempt + 1,
                    },
                )
                continue  # try once more with same prompt (A1.5)

        await self._emit(
            "bot_trial_aborted",
            {
                "trial": trial_index,
                "reason": "parse_failure",
                "last_move_index": move_index,
            },
        )
        return TrialAborted(reason="parse_failure", last_move_index=move_index)

    async def _call_with_api_retry(
        self,
        *,
        messages: list[dict[str, Any]],
        trial_index: int,
        move_index: int,
    ) -> tuple[str, Usage, float] | None:
        """Call LLM with up to _API_RETRY_LIMIT attempts and exponential backoff.

        Returns (text, usage, latency_ms) on success, None on retry exhaustion.
        Backoff: 2s, 4s, 8s after attempts 1, 2, 3 respectively (matches
        spec §3.3 pseudocode).
        """
        for attempt in range(_API_RETRY_LIMIT):
            await self._emit(
                "bot_call_attempt",
                {
                    "trial": trial_index,
                    "move_index": move_index,
                    "attempt_n": attempt + 1,
                },
            )
            t0 = time.monotonic()
            try:
                text, usage = self.llm.complete(
                    system=BASELINE_SYSTEM_PROMPT,
                    messages=messages,
                    max_tokens=BASELINE_MAX_TOKENS,
                    temperature=BASELINE_TEMPERATURE,
                    response_schema=_ReactOutput,
                )
                latency_ms = (time.monotonic() - t0) * 1000
                return text, usage, latency_ms
            except _RETRYABLE_API_EXCEPTIONS as exc:
                await self._emit(
                    "bot_call_api_error",
                    {
                        "trial": trial_index,
                        "move_index": move_index,
                        "error_type": type(exc).__name__,
                        "attempt_n": attempt + 1,
                    },
                )
                if attempt + 1 < _API_RETRY_LIMIT:
                    await asyncio.sleep(2 ** (attempt + 1))
                # else: fall through; loop ends; return None below
        return None

    async def _emit(self, event: str, data: dict[str, Any]) -> None:
        """Publish a telemetry event to the bus if one is wired in.

        Security contract: callers must pass ONLY safe fields — indices,
        action enum, token counts, latency, error class name, bounded
        raw-response excerpt (≤200 chars). No API keys, env values, full
        LLM responses, prompts, or memory contents.
        """
        if self.bus is not None:
            await self.bus.publish(event, data)
