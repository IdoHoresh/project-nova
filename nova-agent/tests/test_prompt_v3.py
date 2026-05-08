from datetime import datetime, timezone

from nova_agent.decision.prompts import build_user_prompt_v2, build_user_prompt_v3
from nova_agent.memory.retrieval import RetrievedMemory
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def test_v3_appends_mood_when_text_present() -> None:
    grid = [[0] * 4 for _ in range(4)]
    text = build_user_prompt_v3(grid=grid, score=0, memories=[], affect_text="You feel anxious.")
    assert text.endswith("Mood: You feel anxious.")


def test_v3_falls_back_to_v2_for_empty_affect() -> None:
    grid = [[0] * 4 for _ in range(4)]
    v2 = build_user_prompt_v2(grid=grid, score=0, memories=[])
    v3 = build_user_prompt_v3(grid=grid, score=0, memories=[], affect_text="")
    assert v2 == v3


def test_v3_keeps_v2_body_intact() -> None:
    grid = [[0] * 4 for _ in range(4)]
    v2 = build_user_prompt_v2(grid=grid, score=42, memories=[])
    v3 = build_user_prompt_v3(grid=grid, score=42, memories=[], affect_text="You feel calm.")
    assert v3.startswith(v2)
    assert "Mood: You feel calm." in v3


def _mem(mid: str) -> RetrievedMemory:
    b = BoardState(grid=[[0] * 4 for _ in range(4)], score=0)
    return RetrievedMemory(
        record=MemoryRecord(
            id=mid,
            timestamp=datetime.now(timezone.utc),
            board_before=b,
            board_after=b,
            action="swipe_right",
            score_delta=0,
            rpe=0.0,
            importance=5,
            tags=[],
            embedding=[1.0, 0.0, 0.0, 0.0],
            source_reasoning="canary-reasoning",
        ),
        score=1.0,
        relevance=1.0,
    )


def test_memories_render_above_board_for_lost_in_middle() -> None:
    """§3.4 — memories sit at the top of the active section, not the middle."""
    grid = [[0] * 4 for _ in range(4)]
    text = build_user_prompt_v2(grid=grid, score=0, memories=[_mem("m1")])
    mem_idx = text.index("canary-reasoning")
    board_idx = text.index("Current board:")
    assert mem_idx < board_idx
