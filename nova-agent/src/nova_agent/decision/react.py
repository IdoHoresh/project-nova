from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from nova_agent.decision.prompts import (
    SYSTEM_PROMPT_V1,
    build_user_prompt_v2,
    build_user_prompt_v3,
)
from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json
from nova_agent.memory.retrieval import RetrievedMemory
from nova_agent.memory.types import Action
from nova_agent.perception.types import BoardState


class _ReactOutput(BaseModel):
    observation: str
    reasoning: str
    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    confidence: Literal["low", "medium", "high"] = Field(default="medium")


@dataclass(frozen=True)
class Decision:
    action: Action
    observation: str
    reasoning: str
    confidence: str


class ReactDecider:
    def __init__(self, *, llm: LLM):
        self.llm = llm

    def decide(self, *, board: BoardState, screenshot_b64: str) -> Decision:
        return self.decide_with_context(board=board, screenshot_b64=screenshot_b64, memories=[])

    def decide_with_context(
        self,
        *,
        board: BoardState,
        screenshot_b64: str,
        memories: list[RetrievedMemory],
        affect_text: str = "",
    ) -> Decision:
        if affect_text.strip():
            user_text = build_user_prompt_v3(
                grid=board.grid,
                score=board.score,
                memories=memories,
                affect_text=affect_text,
            )
        else:
            user_text = build_user_prompt_v2(grid=board.grid, score=board.score, memories=memories)
        messages = [
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
                    {"type": "text", "text": user_text},
                ],
            }
        ]
        # Gemini 2.5 Flash spends internal thinking tokens against this budget
        # before emitting visible JSON. Plan's 400 was too tight — model could
        # exhaust the budget thinking and return a truncated `{\n  "`. 2000 leaves
        # ~1500 for thinking + 500 for the actual JSON payload. Follow-up: add
        # thinking_budget=0 wiring in GeminiLLM so Flash can skip thinking entirely.
        text, _usage = self.llm.complete(
            system=SYSTEM_PROMPT_V1,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        parsed = parse_json(text, _ReactOutput)
        return Decision(
            action=parsed.action,
            observation=parsed.observation,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )
