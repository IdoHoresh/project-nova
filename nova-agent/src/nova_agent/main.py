import asyncio
import base64
import sys

import structlog

from nova_agent.action.adb import ADB, SwipeDirection
from nova_agent.affect.rpe import rpe as compute_rpe
from nova_agent.affect.state import AffectState
from nova_agent.affect.verbalize import describe as describe_affect
from nova_agent.bus.websocket import EventBus
from nova_agent.config import get_settings
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.decision.heuristic import is_game_over
from nova_agent.decision.react import Decision, ReactDecider
from nova_agent.decision.tot import ToTDecider
from nova_agent.llm.factory import build_llm
from nova_agent.memory.aversive import is_catastrophic_loss, tag_aversive
from nova_agent.llm.protocol import LLM
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.memory.semantic import SemanticStore
from nova_agent.memory.types import AffectSnapshot, MemoryRecord
from nova_agent.reflection import run_reflection
from nova_agent.perception.capture import Capture
from nova_agent.perception.ocr import BoardOCR, CalibrationError
from nova_agent.perception.types import BoardState

log = structlog.get_logger()


def _empty_board() -> BoardState:
    return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)


def _summarize_moves(records: list[MemoryRecord], *, limit: int = 30) -> str:
    """Compact text summary of the most recent N episodic records.

    Reflection LLM reads this verbatim, so keep one line per move and lead
    with the action+delta — that's the signal that drives lesson extraction.
    """
    lines: list[str] = []
    for rec in records[:limit]:
        score_part = f"{rec.score_delta:+d}" if rec.score_delta else "0"
        reasoning = (rec.source_reasoning or "—").replace("\n", " ")[:80]
        lines.append(f"[{rec.id}] {rec.action} delta={score_part} | {reasoning}")
    return "\n".join(lines) or "(no moves recorded)"


async def _run_post_game(
    *,
    bus: EventBus,
    memory: MemoryCoordinator,
    semantic: SemanticStore,
    affect: AffectState,
    reflection_llm: LLM,
    final_board: BoardState,
) -> None:
    """Game-over hook: aversive-tag preconditions, run reflection, persist
    semantic rules, reset affect (defense D), publish events.
    """
    last_30 = memory.episodic.list_recent(limit=30)
    catastrophic = is_catastrophic_loss(
        final_score=final_board.score,
        max_tile_reached=final_board.max_tile,
        last_empty_cells=final_board.empty_cells,
    )
    if catastrophic and last_30:
        last_5 = last_30[:5]
        tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
        for rec in tagged:
            memory.episodic.update(rec)
            memory.upsert_aversive_record(rec)

    prior_lessons = [r["rule"] for r in semantic.all_rules()]
    summary = _summarize_moves(last_30)
    try:
        reflection = run_reflection(
            llm=reflection_llm,
            last_30_moves_summary=summary,
            prior_lessons=prior_lessons,
        )
    except Exception as exc:  # reflection is best-effort; never block restart
        log.warning("reflection.failed", error=str(exc))
        reflection = {"summary": "", "lessons": [], "notable_episodes": []}

    notable = reflection.get("notable_episodes") or []
    for lesson in reflection.get("lessons") or []:
        semantic.add_rule(rule=lesson, citations=list(notable))

    await bus.publish(
        "game_over",
        {
            "final_score": final_board.score,
            "max_tile": final_board.max_tile,
            "catastrophic": catastrophic,
            "summary": reflection.get("summary", ""),
            "lessons": reflection.get("lessons", []),
        },
    )
    affect.reset_for_new_game()


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
    deliberation_llm = build_llm(
        model=s.deliberation_model,
        google_api_key=s.google_api_key,
        anthropic_api_key=s.anthropic_api_key,
        daily_cap_usd=s.daily_budget_usd,
    )
    reflection_llm = build_llm(
        model=s.reflection_model,
        google_api_key=s.google_api_key,
        anthropic_api_key=s.anthropic_api_key,
        daily_cap_usd=s.daily_budget_usd,
    )
    decider = ReactDecider(llm=decision_llm)
    tot_decider = ToTDecider(llm=deliberation_llm, bus=bus)
    ocr = BoardOCR()
    memory = MemoryCoordinator(sqlite_path=s.sqlite_path, lancedb_path=s.lancedb_path)
    semantic = SemanticStore(s.sqlite_path.parent / "semantic.db")
    affect = AffectState()

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

            if is_game_over(board):
                await _run_post_game(
                    bus=bus,
                    memory=memory,
                    semantic=semantic,
                    affect=affect,
                    reflection_llm=reflection_llm,
                    final_board=board,
                )
                break

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

            affect_text = describe_affect(affect.vector)
            mode = "tot" if should_use_tot(board=board, affect=affect.vector) else "react"
            await bus.publish("mode", {"mode": mode, "step": step})
            if mode == "tot":
                decision = await tot_decider.decide(
                    board=board,
                    screenshot_b64=b64,
                    move_idx=step,
                )
            else:
                decision = decider.decide_with_context(
                    board=board,
                    screenshot_b64=b64,
                    memories=retrieved,
                    affect_text=affect_text,
                )
            await bus.publish(
                "decision",
                {
                    "action": decision.action,
                    "observation": decision.observation,
                    "reasoning": decision.reasoning,
                    "confidence": decision.confidence,
                    "affect_text": affect_text,
                    "mode": mode,
                },
            )
            adb.swipe(SwipeDirection(decision.action))

            if prev_board is not None and prev_decision is not None:
                score_delta = board.score - prev_board.score
                delta_rpe = compute_rpe(actual_score_delta=score_delta, board_before=prev_board)
                trauma_triggered = any("trauma" in m.record.tags for m in retrieved)
                v = affect.update(
                    rpe=delta_rpe,
                    empty_cells=board.empty_cells,
                    terminal=False,
                    trauma_triggered=trauma_triggered,
                )
                snapshot = AffectSnapshot(
                    valence=v.valence,
                    arousal=v.arousal,
                    dopamine=v.dopamine,
                    frustration=v.frustration,
                    anxiety=v.anxiety,
                    confidence=v.confidence,
                )
                await bus.publish(
                    "affect",
                    {
                        "valence": v.valence,
                        "arousal": v.arousal,
                        "dopamine": v.dopamine,
                        "frustration": v.frustration,
                        "anxiety": v.anxiety,
                        "confidence": v.confidence,
                        "rpe": delta_rpe,
                        "trauma_triggered": trauma_triggered,
                    },
                )
                rec_id = memory.write_move(
                    board_before=prev_board,
                    board_after=board,
                    action=prev_decision.action,
                    score_delta=score_delta,
                    rpe=delta_rpe,
                    importance=1,
                    source_reasoning=prev_decision.reasoning,
                    affect=snapshot,
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
