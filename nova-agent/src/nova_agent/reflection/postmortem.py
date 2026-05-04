"""Post-game reflection (CoALA §3.7, plan §3.6 defense C hook).

Runs once when game-over is detected. Reads the last-N moves and the
top-3 prior lessons; emits a JSON summary + 3-5 concrete lessons + a
short list of notable episode ids worth keeping. Output is persisted to
SemanticStore; lessons feed the next game's reflection cycle as
`prior_lessons`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json


class _ReflectionOut(BaseModel):
    summary: str
    lessons: list[str]
    notable_episodes: list[str]


_SYSTEM = """\
You are reflecting on a completed 2048 game. Be specific. Output strict JSON:
{
  "summary": "1 sentence on what happened",
  "lessons": ["concrete rule 1", "concrete rule 2", ...] (3 to 5),
  "notable_episodes": ["ep_id1", "ep_id2"] (2 to 4 memory ids worth keeping)
}
"""


def run_reflection(
    *,
    llm: LLM,
    last_30_moves_summary: str,
    prior_lessons: list[str],
) -> dict[str, Any]:
    prior = "\n".join(f"- {lesson}" for lesson in prior_lessons[-3:]) or "(none)"
    user = (
        f"Recent moves summary:\n{last_30_moves_summary}\n\n"
        f"Prior lessons (top-3):\n{prior}\n\n"
        "What worked, what failed, what should I do differently next game?"
    )
    text, _usage = llm.complete(
        system=_SYSTEM,
        messages=[{"role": "user", "content": user}],
        max_tokens=600,
        temperature=0.4,
        response_schema=_ReflectionOut,
    )
    parsed = parse_json(text, _ReflectionOut)
    return parsed.model_dump()
