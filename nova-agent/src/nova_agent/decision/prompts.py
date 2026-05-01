SYSTEM_PROMPT_V1 = """\
You are Nova, an AI playing the puzzle game 2048.
You see the board as a 4x4 grid where 0 means empty.
You decide which way to swipe and explain your reasoning briefly.

For every turn you emit Observation, Reasoning, Action as strict JSON
(no prose around it):
{
  "observation": "1 sentence about what's on the board",
  "reasoning":   "1-2 sentences on why you chose this action",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
"""


def build_user_prompt(*, grid: list[list[int]], score: int) -> str:
    grid_str = "\n".join(
        "  ".join(f"{v:>5}" if v else "    ." for v in row) for row in grid
    )
    return f"""Current board:
{grid_str}

Score: {score}

Choose the next swipe."""


def render_memories(memories: list) -> str:
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


def build_user_prompt_v2(*, grid: list[list[int]], score: int, memories: list) -> str:
    base = build_user_prompt(grid=grid, score=score)
    mem_block = render_memories(memories)
    if mem_block:
        return f"{base}\n\n{mem_block}"
    return base
