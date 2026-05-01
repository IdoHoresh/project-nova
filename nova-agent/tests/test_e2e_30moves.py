"""End-to-end loop integration test.

Exercises perception → memory.retrieve → decider → memory.write across many
ticks with the LLM, capture, and ADB layers mocked. Real components are
the OCR (one read on a fixture), the MemoryCoordinator (SQLite + LanceDB
in tmp_path), the retrieval scoring, and the prompt-building path inside
ReactDecider.

Verifies §3.4: after 30 ticks the loop should leave 29 episodic records
behind (no prev_board on tick 0) and retrieval should surface at least
one similar memory back into the prompt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from nova_agent.decision.react import ReactDecider
from nova_agent.llm.mock import MockLLMClient
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.perception.ocr import BoardOCR

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_30_move_loop_writes_memory(tmp_path: Path) -> None:
    image = Image.open(FIXTURES / "board_8.png").convert("RGB")

    ocr = BoardOCR()
    decider = ReactDecider(llm=MockLLMClient())
    memory = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )

    board = ocr.read(image)
    prev_board = None
    prev_action = ""
    prev_reasoning: str | None = None

    for _ in range(30):
        retrieved = memory.retrieve_for_board(board, k=5)
        decision = decider.decide_with_context(
            board=board, screenshot_b64="", memories=retrieved
        )
        if prev_board is not None:
            memory.write_move(
                board_before=prev_board,
                board_after=board,
                action=prev_action,
                score_delta=board.score - prev_board.score,
                rpe=0.0,
                importance=5,
                source_reasoning=prev_reasoning,
            )
        prev_board = board
        prev_action = decision.action
        prev_reasoning = decision.reasoning

    assert len(memory.episodic.all()) == 29
    assert memory.vector_skip_count == 0
    final = memory.retrieve_for_board(board, k=5)
    assert len(final) >= 1
