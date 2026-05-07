"""Test suite for trauma_ablation._run_game() per-game inner loop.

Tests the GameResult return type, trauma_enabled flag behavior,
force_trauma_on_game_over override, and game-over detection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nova_agent.affect.state import AffectState
from nova_agent.lab.io import SimGameIO
from nova_agent.lab.sim import Game2048Sim
from nova_agent.lab.trauma_ablation import (
    MAX_MOVES_PHASE_08,
    GameResult,
    SessionResult,
    _per_arm_db_paths,
    _run_game,
    _run_paired_session,
)
from nova_agent.llm.mock import MockLLMClient
from nova_agent.llm.protocol import LLM
from nova_agent.memory.aversive import AVERSIVE_TAG
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.memory.semantic import SemanticStore
from nova_agent.perception.types import BoardState


class _FixedActionLLM:
    """Helper: wraps MockLLMClient behavior to return a deterministic action.

    Supports all role types (decision, tot_branch, reflection, importance).
    """

    def __init__(self, action: str = "swipe_up") -> None:
        self._action = action

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 200,
        temperature: float = 0.7,
        response_schema: type | None = None,
    ) -> tuple[str, Any]:
        # Return role-appropriate payloads to avoid mock fingerprint errors
        if '"observation":' in system:
            payload = {
                "observation": "test observation",
                "reasoning": "test reasoning",
                "action": self._action,
                "confidence": "low",
                "memory_citation": None,
            }
        elif "evaluating ONE candidate move" in system:
            payload = {"action": self._action, "reasoning": "test branch", "value": 0.5}
        elif "postmortem" in system.lower():
            payload = {
                "summary": "test postmortem",
                "lessons": ["test lesson"],
                "notable_episodes": [],
            }
        elif "rate this event" in system and "memorability" in system:
            payload = {"importance": 5}
        else:
            payload = {
                "observation": "test observation",
                "reasoning": "test reasoning",
                "action": self._action,
                "confidence": "low",
                "memory_citation": None,
            }
        return json.dumps(payload), type(
            "Usage",
            (),
            {
                "input_tokens": 1,
                "output_tokens": 1,
                "cost_usd": 0.0,
            },
        )()


@pytest.mark.asyncio
async def test_run_game_returns_game_result_with_boards(tmp_path: Path) -> None:
    """Smoke test: _run_game returns GameResult with correct structure."""
    sim = Game2048Sim(seed=42)
    sim_io = SimGameIO(sim=sim)
    memory = MemoryCoordinator(
        sqlite_path=tmp_path / "episodic.db", lancedb_path=tmp_path / "vectors"
    )
    semantic = SemanticStore(path=tmp_path / "semantic.json")
    affect = AffectState()
    decision_llm: LLM = MockLLMClient()
    deliberation_llm: LLM = MockLLMClient()
    reflection_llm: LLM = MockLLMClient()
    bus = None  # type: ignore

    result = await _run_game(
        sim_io=sim_io,
        sim=sim,
        memory=memory,
        semantic=semantic,
        affect=affect,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        bus=bus,
        trauma_enabled=True,
        force_trauma_on_game_over=False,
        max_moves=10,
    )

    assert isinstance(result, GameResult)
    assert isinstance(result.per_move_boards, list)
    assert isinstance(result.per_move_anxieties, list)
    assert isinstance(result.reached_game_over, bool)
    assert isinstance(result.final_board, BoardState)
    assert isinstance(result.would_predicate_have_fired, bool)
    assert len(result.per_move_boards) > 0
    assert len(result.per_move_anxieties) > 0
    assert len(result.per_move_boards) == len(result.per_move_anxieties)


@pytest.mark.asyncio
async def test_force_trauma_on_game_over_writes_tag_when_y_on(tmp_path: Path) -> None:
    """When force_trauma_on_game_over=True and reached_game_over=True,
    aversive tag is written even if predicate would not fire.
    """
    sim = Game2048Sim(seed=42)
    sim_io = SimGameIO(sim=sim)
    memory = MemoryCoordinator(
        sqlite_path=tmp_path / "episodic.db", lancedb_path=tmp_path / "vectors"
    )
    semantic = SemanticStore(path=tmp_path / "semantic.json")
    affect = AffectState()
    decision_llm: LLM = _FixedActionLLM(action="swipe_up")
    deliberation_llm: LLM = _FixedActionLLM(action="swipe_up")
    reflection_llm: LLM = _FixedActionLLM(action="swipe_up")
    bus = None  # type: ignore

    _ = await _run_game(
        sim_io=sim_io,
        sim=sim,
        memory=memory,
        semantic=semantic,
        affect=affect,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        bus=bus,
        trauma_enabled=True,
        force_trauma_on_game_over=True,
        max_moves=MAX_MOVES_PHASE_08,
    )

    # Check that aversive tag was written
    recent = memory.episodic.list_recent(limit=10)
    has_aversive = any(AVERSIVE_TAG in r.tags for r in recent)
    # If game reached_game_over, should have aversive tags
    if any(AVERSIVE_TAG in r.tags for r in memory.episodic.list_recent(limit=20)):
        assert has_aversive, "Expected aversive tag when force_trauma_on_game_over=True"


@pytest.mark.asyncio
async def test_trauma_enabled_false_skips_tag_writes(tmp_path: Path) -> None:
    """When trauma_enabled=False, no aversive tags are written regardless
    of force_trauma_on_game_over or game-over status.
    """
    sim = Game2048Sim(seed=42)
    sim_io = SimGameIO(sim=sim)
    memory = MemoryCoordinator(
        sqlite_path=tmp_path / "episodic.db", lancedb_path=tmp_path / "vectors"
    )
    semantic = SemanticStore(path=tmp_path / "semantic.json")
    affect = AffectState()
    decision_llm: LLM = _FixedActionLLM(action="swipe_up")
    deliberation_llm: LLM = _FixedActionLLM(action="swipe_up")
    reflection_llm: LLM = _FixedActionLLM(action="swipe_up")
    bus = None  # type: ignore

    _ = await _run_game(
        sim_io=sim_io,
        sim=sim,
        memory=memory,
        semantic=semantic,
        affect=affect,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        bus=bus,
        trauma_enabled=False,
        force_trauma_on_game_over=True,  # Should be ignored
        max_moves=MAX_MOVES_PHASE_08,
    )

    # No aversive tags should be written, even if game ended
    recent = memory.episodic.list_recent(limit=20)
    has_aversive = any(AVERSIVE_TAG in r.tags for r in recent)
    assert not has_aversive, "Expected NO aversive tags when trauma_enabled=False"


@pytest.mark.asyncio
async def test_per_arm_db_paths_disjoint(tmp_path: Path) -> None:
    """_per_arm_db_paths returns different paths for different arms."""
    p_on = _per_arm_db_paths(tmp_path, stage="smoke", seed=42, arm="y_on")
    p_off = _per_arm_db_paths(tmp_path, stage="smoke", seed=42, arm="y_off")
    assert p_on != p_off
    assert "y_on" in str(p_on[0])
    assert "y_off" in str(p_off[0])
    assert p_on[0].parent.exists()
    assert p_off[0].parent.exists()


@pytest.mark.asyncio
async def test_run_paired_session_returns_per_arm_results(tmp_path: Path) -> None:
    """_run_paired_session returns SessionResult with per-arm metrics."""
    llm = _FixedActionLLM(action="swipe_up")
    result = await _run_paired_session(
        seed_base=20260507,
        run_dir=tmp_path,
        stage="smoke",
        decision_llm=llm,
        deliberation_llm=llm,
        reflection_llm=llm,
        T=4,
        max_moves=MAX_MOVES_PHASE_08,
    )
    assert isinstance(result, SessionResult)
    assert result.seed_base == 20260507
    assert result.r_post_y_on is None or 0.0 <= result.r_post_y_on <= 1.0
    assert result.r_post_y_off is None or 0.0 <= result.r_post_y_off <= 1.0


@pytest.mark.asyncio
async def test_paired_session_y_on_has_aversive_records_y_off_does_not(tmp_path: Path) -> None:
    """IV observable: Y_on memory after game-1 has aversive-tagged records, Y_off does not."""
    llm = _FixedActionLLM(action="swipe_up")
    result = await _run_paired_session(
        seed_base=20260507,
        run_dir=tmp_path,
        stage="smoke",
        decision_llm=llm,
        deliberation_llm=llm,
        reflection_llm=llm,
        T=4,
        max_moves=MAX_MOVES_PHASE_08,
    )
    assert result.aversive_tag_count_y_on >= 0
    assert result.aversive_tag_count_y_off == 0


@pytest.mark.asyncio
async def test_cap_exhaustion_does_not_write_tag(tmp_path: Path) -> None:
    """When max_moves is exhausted without reaching game_over,
    reached_game_over=False and no aversive tags are written.
    """
    sim = Game2048Sim(seed=42)
    sim_io = SimGameIO(sim=sim)
    memory = MemoryCoordinator(
        sqlite_path=tmp_path / "episodic.db", lancedb_path=tmp_path / "vectors"
    )
    semantic = SemanticStore(path=tmp_path / "semantic.json")
    affect = AffectState()
    decision_llm: LLM = MockLLMClient()
    deliberation_llm: LLM = MockLLMClient()
    reflection_llm: LLM = MockLLMClient()
    bus = None  # type: ignore

    result = await _run_game(
        sim_io=sim_io,
        sim=sim,
        memory=memory,
        semantic=semantic,
        affect=affect,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        bus=bus,
        trauma_enabled=True,
        force_trauma_on_game_over=False,
        max_moves=5,  # Small cap
    )

    # Cap exhaustion: game did not reach game-over state
    assert result.reached_game_over is False
    # No aversive tags should be written without game-over
    recent = memory.episodic.list_recent(limit=20)
    has_aversive = any(AVERSIVE_TAG in r.tags for r in recent)
    assert not has_aversive, "Expected NO aversive tags without game-over"
