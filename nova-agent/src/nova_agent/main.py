import asyncio
import base64
import sys

import structlog

from nova_agent.action.adb import ADB, SwipeDirection
from nova_agent.bus.websocket import EventBus
from nova_agent.config import get_settings
from nova_agent.decision.react import Decision, ReactDecider
from nova_agent.llm.factory import build_llm
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.perception.capture import Capture
from nova_agent.perception.ocr import BoardOCR, CalibrationError
from nova_agent.perception.types import BoardState

log = structlog.get_logger()


def _empty_board() -> BoardState:
    return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)


async def run() -> None:
    s = get_settings()
    bus = EventBus(host=s.ws_host, port=s.ws_port)
    await bus.start()

    capture = Capture(adb_path=s.adb_path, device_id=s.adb_device_id)
    adb = ADB(
        adb_path=s.adb_path,
        device_id=s.adb_device_id,
        screen_w=1080,
        screen_h=2400,
    )
    decision_llm = build_llm(
        model=s.decision_model,
        google_api_key=s.google_api_key,
        anthropic_api_key=s.anthropic_api_key,
        daily_cap_usd=s.daily_budget_usd,
    )
    decider = ReactDecider(llm=decision_llm)
    ocr = BoardOCR()
    memory = MemoryCoordinator(sqlite_path=s.sqlite_path, lancedb_path=s.lancedb_path)

    log.info("nova.started", model=s.decision_model, device=s.adb_device_id)
    try:
        prev_board: BoardState | None = None
        prev_decision: Decision | None = None
        for step in range(50):
            image = capture.grab_stable()
            try:
                board = ocr.read(image)
            except CalibrationError as exc:
                log.warning("perception.calibration_failed", error=str(exc))
                board = _empty_board()
            log.info("perception.read", step=step, grid=board.grid, score=board.score)
            png_bytes = Capture.to_vlm_bytes(image)
            b64 = base64.b64encode(png_bytes).decode("ascii")
            await bus.publish("perception", {"score": board.score, "step": step})

            retrieved = memory.retrieve_for_board(board, k=5)
            await bus.publish(
                "memory_retrieved",
                {
                    "items": [
                        {
                            "id": m.record.id,
                            "importance": m.record.importance,
                            "action": m.record.action,
                            "score_delta": m.record.score_delta,
                            "reasoning": m.record.source_reasoning,
                            "tags": m.record.tags,
                            "preview_grid": m.record.board_before.grid,
                        }
                        for m in retrieved
                    ]
                },
            )

            decision = decider.decide_with_context(
                board=board, screenshot_b64=b64, memories=retrieved
            )
            await bus.publish(
                "decision",
                {
                    "action": decision.action,
                    "observation": decision.observation,
                    "reasoning": decision.reasoning,
                    "confidence": decision.confidence,
                },
            )
            adb.swipe(SwipeDirection(decision.action))

            if prev_board is not None and prev_decision is not None:
                rec_id = memory.write_move(
                    board_before=prev_board,
                    board_after=board,
                    action=prev_decision.action,
                    score_delta=board.score - prev_board.score,
                    rpe=0.0,
                    importance=1,
                    source_reasoning=prev_decision.reasoning,
                )
                await bus.publish(
                    "memory_write",
                    {"id": rec_id, "importance": 1, "tags": []},
                )

            prev_board = board
            prev_decision = decision
            await asyncio.sleep(0.5)
    finally:
        await bus.stop()


def cli() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    cli()
