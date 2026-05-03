from nova_agent.memory.retrieval import RetrievedMemory


SYSTEM_PROMPT_V1 = """\
You are Nova playing 2048. The board is a 4x4 grid; 0 means empty.

Speak in your own first-person voice — like you're thinking to yourself.
Be terse. Sentence fragments. Personal. Don't analyze; react.

Examples of the right voice:
- "16 in the corner. Going down."
- "Tight here. Try left."
- "Ugh, no good moves."
- "That worked. Push it."

Emit strict JSON only (no prose around it):
{
  "observation": "5-10 word fragment, first-person, what you see",
  "reasoning":   "5-15 word fragment, first-person, why this move",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
"""


def build_user_prompt(*, grid: list[list[int]], score: int) -> str:
    grid_str = "\n".join("  ".join(f"{v:>5}" if v else "    ." for v in row) for row in grid)
    return f"""Current board:
{grid_str}

Score: {score}

Choose the next swipe."""


def render_memories(memories: list[RetrievedMemory]) -> str:
    if not memories:
        return ""
    lines = ["Memory recalls (most relevant past situations):"]
    for m in memories:
        rec = m.record
        lines.append(
            f"- [importance {rec.importance}/10] action={rec.action} "
            f"score_delta={rec.score_delta} reasoning={rec.source_reasoning or '—'}"
        )
    return "\n".join(lines)


def build_user_prompt_v2(
    *, grid: list[list[int]], score: int, memories: list[RetrievedMemory]
) -> str:
    base = build_user_prompt(grid=grid, score=score)
    mem_block = render_memories(memories)
    if mem_block:
        return f"{mem_block}\n\n{base}"
    return base


def build_user_prompt_v3(
    *,
    grid: list[list[int]],
    score: int,
    memories: list[RetrievedMemory],
    affect_text: str,
) -> str:
    base = build_user_prompt_v2(grid=grid, score=score, memories=memories)
    if affect_text.strip():
        return f"{base}\n\nMood: {affect_text}"
    return base
