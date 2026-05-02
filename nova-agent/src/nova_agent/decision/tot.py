"""Tree-of-Thoughts deliberation (System 2, §3.8).

Branch evaluators run in parallel via asyncio.gather, stream results to the
event bus as they complete (so the brain panel renders thinking, not a
4-second freeze), and are READ-ONLY with respect to long-term memory —
branches may QUERY but must never WRITE. Writes happen on the single
decision-loop thread after the chosen branch is committed (§3.4
concurrency rule).
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from pydantic import BaseModel, Field

from nova_agent.bus import EventBus
from nova_agent.decision.react import Decision
from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import StructuredOutputError, parse_json
from nova_agent.perception.types import BoardState

_BranchAction = Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]


class _ToTBranch(BaseModel):
    action: _BranchAction
    reasoning: str
    value: float = Field(ge=0.0, le=1.0)


_TOT_SYSTEM = """\
You are evaluating ONE candidate move for a 2048 game. Imagine the board after
swiping in the proposed direction; rate the resulting position from 0 (terrible,
near-loss) to 1 (excellent, opens many merges). Be honest. You are not selecting
the move — you are scoring this single candidate.

Respond as strict JSON:
{"action": "swipe_up|swipe_down|swipe_left|swipe_right",
 "reasoning": "1-2 sentences",
 "value": 0.0..1.0}
"""

_DIRECTIONS: tuple[_BranchAction, ...] = (
    "swipe_up",
    "swipe_down",
    "swipe_left",
    "swipe_right",
)


class ToTDecider:
    def __init__(self, *, llm: LLM, bus: EventBus, branch_temperature: float = 0.3):
        self.llm = llm
        self.bus = bus
        self.branch_temperature = branch_temperature

    async def decide(
        self,
        *,
        board: BoardState,
        screenshot_b64: str,
        num_branches: int = 4,
        game_id: str | None = None,
        move_idx: int | None = None,
    ) -> Decision:
        directions = _DIRECTIONS[:num_branches]
        tasks = [
            self._evaluate_one(board, screenshot_b64, d, game_id, move_idx) for d in directions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates = [r for r in results if isinstance(r, _ToTBranch)]
        if not candidates:
            # Surface the underlying per-branch failures so the caller (and
            # future debugging) can see WHY all branches failed instead of
            # just "no valid candidates". `_evaluate_one` returns either a
            # `_ToTBranch` on success or the original exception on failure;
            # `gather(return_exceptions=True)` may also wrap unforeseen
            # errors that `_evaluate_one` didn't catch.
            failure_summaries = [
                f"{type(r).__name__}: {r}" for r in results if isinstance(r, BaseException)
            ]
            detail = (
                "; ".join(failure_summaries)
                if failure_summaries
                else "all branches returned non-_ToTBranch values"
            )
            raise RuntimeError(f"ToT produced no valid candidates ({detail})")

        best = max(candidates, key=lambda c: c.value)
        await self.bus.publish(
            "tot_selected",
            {
                "game_id": game_id,
                "move_idx": move_idx,
                "chosen_action": best.action,
                "chosen_value": best.value,
                "branch_values": {c.action: c.value for c in candidates},
            },
        )
        return Decision(
            action=best.action,
            observation=f"ToT considered {len(candidates)} candidates",
            reasoning=best.reasoning,
            confidence="medium",
        )

    async def _evaluate_one(
        self,
        board: BoardState,
        screenshot_b64: str,
        direction: _BranchAction,
        game_id: str | None,
        move_idx: int | None,
    ) -> _ToTBranch | Exception:
        """Evaluate ONE branch. READ-ONLY: must never call memory.write_*.

        On completion, publish `tot_branch` so the brain panel can render
        the branch card incrementally.
        """
        user = f"Board:\n{board.grid}\nScore: {board.score}\n\nEvaluate the move: {direction}"
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64,
                        },
                    },
                    {"type": "text", "text": user},
                ],
            }
        ]
        # Gemini 2.5 Pro spends a large hidden thinking budget against
        # max_output_tokens. Plan's 200 only left room for thinking; visible
        # JSON came back truncated/empty, every branch failed to parse, and
        # ToTDecider raised "no valid candidates". 3000 leaves Pro ~2500
        # for thinking + 500 for the small JSON payload (action + reasoning
        # + value). Pro disallows thinking_budget=0 so we can't fully disable
        # it the way ReactDecider on Flash does — see GeminiLLM constructor
        # for the per-llm thinking_budget knob (set to 1024 for the
        # deliberation_llm in main.py).
        try:
            text, _usage = await asyncio.to_thread(
                self.llm.complete,
                system=_TOT_SYSTEM,
                messages=messages,
                max_tokens=3000,
                temperature=self.branch_temperature,
            )
        except Exception as exc:
            # Catch ANY failure from the LLM call — quota errors (429),
            # network failures, tenacity RetryError, etc. Without this catch,
            # the exception propagates to gather(return_exceptions=True) and
            # the user sees only the generic "no valid candidates" downstream
            # error with no clue what actually broke. Publish a descriptive
            # tot_branch with the underlying exception type + message so the
            # brain panel and logs both see it.
            await self.bus.publish(
                "tot_branch",
                {
                    "game_id": game_id,
                    "move_idx": move_idx,
                    "direction": direction,
                    "status": "api_error",
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            return exc
        try:
            branch = parse_json(text, _ToTBranch)
        except StructuredOutputError as exc:
            await self.bus.publish(
                "tot_branch",
                {
                    "game_id": game_id,
                    "move_idx": move_idx,
                    "direction": direction,
                    "status": "parse_error",
                    "error": str(exc),
                },
            )
            return exc
        await self.bus.publish(
            "tot_branch",
            {
                "game_id": game_id,
                "move_idx": move_idx,
                "direction": branch.action,
                "value": branch.value,
                "reasoning": branch.reasoning,
                "status": "complete",
            },
        )
        return branch
