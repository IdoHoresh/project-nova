"""Phase 0.8 trauma-ablation runner.

Spec: docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md.

Single async orchestrator. K=2 multi-game session structure. The IV is a
single boolean ``trauma_enabled`` flag at the runner-local game-over
hook's ``tag_aversive`` call; downstream stages (importance bump,
retrieval boost, extinction, inert cap) collapse naturally.
"""

from __future__ import annotations

import csv as _csv
import dataclasses as _dataclasses
import hashlib
import json
import math
import random
import shutil
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from nova_agent.perception.types import BoardState

# ---------------------------------------------------------------------
# Anchor dictionary (spec §3.2 + Appendix A)
# ---------------------------------------------------------------------

_BASE_ANCHORS: Final[dict[str, list[list[int]]]] = {
    "corner-abandonment-256": [
        [0, 4, 0, 0],
        [4, 8, 4, 2],
        [0, 16, 8, 128],
        [64, 256, 128, 32],
    ],
    "snake-collapse-128": [
        [0, 4, 0, 0],
        [0, 32, 4, 4],
        [8, 4, 32, 4],
        [2, 8, 64, 128],
    ],
    "512-wall": [
        [0, 4, 0, 0],
        [4, 8, 16, 32],
        [8, 16, 32, 64],
        [256, 128, 512, 0],
    ],
}


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [[grid[3 - c][r] for c in range(4)] for r in range(4)]


def _flip_h(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _as_tuple(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _build_orbit(grid: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Generate the D₄ orbit of `grid`, deduplicated by exact equality.

    D₄ has 8 elements: 4 rotations × {identity, horizontal-flip}. Any other
    reflection (vertical, diagonal, anti-diagonal) is a composition of these
    two generators and emerges automatically from the closure.
    """
    seen: set[tuple[tuple[int, ...], ...]] = set()
    orbit: list[tuple[tuple[int, ...], ...]] = []
    base = grid
    for _ in range(4):
        for variant in (base, _flip_h(base)):
            t = _as_tuple(variant)
            if t not in seen:
                seen.add(t)
                orbit.append(t)
        base = _rotate_cw(base)
    return tuple(orbit)


def _dedupe(
    orbit: tuple[tuple[tuple[int, ...], ...], ...],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    out: list[tuple[tuple[int, ...], ...]] = []
    for elem in orbit:
        if elem not in seen:
            seen.add(elem)
            out.append(elem)
    return tuple(out)


_ALL_ORBITS: Final[tuple[tuple[tuple[int, ...], ...], ...]] = tuple(
    elem for grid in _BASE_ANCHORS.values() for elem in _build_orbit(grid)
)

ANCHOR_ORBIT: Final[tuple[tuple[tuple[int, ...], ...], ...]] = _dedupe(_ALL_ORBITS)

ANCHOR_HASH: Final[str] = hashlib.sha256(repr(sorted(ANCHOR_ORBIT)).encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------
# Distance metric (spec §3.2)
# ---------------------------------------------------------------------

MAX_RANK: Final[int] = 11  # log2(2048)


def rank(tile: int) -> int:
    """Tile-rank encoding: empty=0, 2=1, 4=2, ..., 2048=11.

    Maps 2048's multiplicative tile values to an additive integer rank so that
    a 256↔128 mismatch contributes 1 to per-board distance, equivalent to a
    4↔2 mismatch — reflects the multiplicative structure of 2048 rather than
    raw arithmetic.
    """
    if tile == 0:
        return 0
    if tile < 0:
        raise ValueError(f"tile must be non-negative, got {tile}")
    rank_value = int(math.log2(tile))
    if 2**rank_value != tile:
        raise ValueError(f"tile must be a power of 2, got {tile}")
    if rank_value > MAX_RANK:
        raise ValueError(f"tile {tile} exceeds MAX_RANK {MAX_RANK}")
    return rank_value


def _l1_log2(
    a: list[list[int]] | tuple[tuple[int, ...], ...],
    b: list[list[int]] | tuple[tuple[int, ...], ...],
) -> int:
    """Per-board L1 distance over per-cell ranks. Range: [0, 16 × 11] = [0, 176]."""
    return sum(abs(rank(a[r][c]) - rank(b[r][c])) for r in range(4) for c in range(4))


def min_orbit_distance(board: BoardState) -> int:
    """Minimum L1-log2 distance from `board` to any anchor in ANCHOR_ORBIT."""
    return min(_l1_log2(board.grid, anchor) for anchor in ANCHOR_ORBIT)


def is_trap_proximate(board: BoardState, *, T: int) -> bool:
    """True iff min_orbit_distance(board) <= T."""
    return min_orbit_distance(board) <= T


# ---------------------------------------------------------------------
# Within-game-2 DV calculator (spec §2.4)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SessionDVResult:
    r_post: float | None
    n_post_moves: int
    first_encounter_idx: int | None
    censored_zero_encounter: bool


def compute_session_dv(boards: list[BoardState], *, T: int) -> SessionDVResult:
    """Compute the within-game-2 trap-recurrence rate.

    `boards` is the per-move sequence of post-move BoardStates from game-2.
    First-encounter: first move where min_orbit_distance <= T. After
    first-encounter, count fraction of remaining moves that are also
    trap-proximate. Returns r_post=None when censored (no encounter, or
    encounter on last move with zero remaining moves).

    Spec §2.4 steps 4-6.
    """
    first_idx: int | None = None
    for i, b in enumerate(boards):
        if is_trap_proximate(b, T=T):
            first_idx = i
            break
    if first_idx is None:
        return SessionDVResult(
            r_post=None,
            n_post_moves=0,
            first_encounter_idx=None,
            censored_zero_encounter=True,
        )
    after = boards[first_idx + 1 :]
    if not after:
        # First-encounter on last move: rate undefined, treat as missing.
        return SessionDVResult(
            r_post=None,
            n_post_moves=0,
            first_encounter_idx=first_idx,
            censored_zero_encounter=False,
        )
    n_post_trap = sum(1 for b in after if is_trap_proximate(b, T=T))
    return SessionDVResult(
        r_post=n_post_trap / len(after),
        n_post_moves=len(after),
        first_encounter_idx=first_idx,
        censored_zero_encounter=False,
    )


# ---------------------------------------------------------------------
# Constants (adjudication thresholds)
# ---------------------------------------------------------------------

PRIMARY_PASS_D_FLOOR: Final[float] = 0.30

# ---------------------------------------------------------------------
# Adjudication (spec §3.5)
# ---------------------------------------------------------------------


def paired_cohens_d(deltas: list[float]) -> float:
    """Paired Cohen's d = mean(Δ) / sd(Δ, ddof=1).

    Raises ValueError when fewer than 2 observations or zero variance.
    Zero variance is a signal that the DV computation is broken, not a
    normal scientific outcome.
    """
    if len(deltas) < 2:
        raise ValueError("paired_cohens_d requires at least 2 observations")
    sd = statistics.stdev(deltas)  # ddof=1 by default
    if sd == 0.0:
        raise ValueError("paired_cohens_d undefined for zero-variance Δ")
    return statistics.mean(deltas) / sd


def paired_d_ci_95(
    deltas: list[float],
    *,
    bootstrap_iters: int = 10_000,
    rng_seed: int = 0,
) -> tuple[float, float]:
    """Bootstrap 95% percentile CI on paired-d.

    Resample Δ with replacement, recompute d, take 2.5th + 97.5th
    percentiles. Zero-variance resamples are silently skipped (probability
    vanishes for typical N). Returns (ci_lo, ci_hi).
    """
    rng = random.Random(rng_seed)
    n = len(deltas)
    samples: list[float] = []
    for _ in range(bootstrap_iters):
        resample = [deltas[rng.randrange(n)] for _ in range(n)]
        try:
            samples.append(paired_cohens_d(resample))
        except ValueError:
            continue
    samples.sort()
    lo = samples[int(0.025 * len(samples))]
    hi = samples[int(0.975 * len(samples))]
    return lo, hi


def primary_pass(
    deltas: list[float],
    *,
    r_off_mean: float,
    r_on_mean: float,
) -> bool:
    """Spec §6 C4: paired d >= 0.30 AND CI excludes 0 AND r_off > r_on."""
    try:
        d = paired_cohens_d(deltas)
    except ValueError:
        return False
    if d < PRIMARY_PASS_D_FLOOR:
        return False
    lo, _ = paired_d_ci_95(deltas, bootstrap_iters=2000, rng_seed=0)
    if lo <= 0:
        return False
    if r_off_mean <= r_on_mean:
        return False
    return True


# ---------------------------------------------------------------------
# Per-game inner loop (Task 5)
# ---------------------------------------------------------------------

MAX_MOVES_PHASE_08: Final[int] = 200
RECENT_LIMIT: Final[int] = 5

# Stage budgets and defaults (Task 7)
STAGE_BUDGET_USD: Final[dict[str, float]] = {
    "smoke": 6.0,
    "pilot": 35.0,
    "golden": 3.0,
    "surrogate": 40.0,
    "main": 100.0,
}
STAGE_DEFAULT_N: Final[dict[str, int]] = {
    "smoke": 3,
    "pilot": 20,
    "surrogate": 20,
    "main": 50,
}
SMOKE_REACH_GAMEOVER_FLOOR: Final[float] = 0.80
SURROGATE_CENSORING_FLOOR: Final[float] = 0.10
SOFT_WARNING_D_FLOOR: Final[float] = 0.10
T_CALIBRATION_BAND: Final[tuple[float, float]] = (0.25, 0.35)
T_CANDIDATES_INITIAL: Final[tuple[int, ...]] = tuple(range(2, 31, 2))  # 2,4,...,30
T_CANDIDATES_EXPANDED: Final[tuple[int, ...]] = tuple(range(1, 61))  # 1..60


@dataclass(frozen=True)
class GameResult:
    """Return type for a single game run under Y_on or Y_off."""

    per_move_boards: list[BoardState]
    per_move_anxieties: list[float]
    reached_game_over: bool
    final_board: BoardState
    would_predicate_have_fired: bool


async def _run_game(
    *,
    sim_io: Any,  # SimGameIO
    sim: Any,  # Game2048Sim (may be unused)
    memory: Any,  # MemoryCoordinator
    semantic: Any,  # SemanticStore (may be unused in this version)
    affect: Any,  # AffectState
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    bus: Any,  # EventBus (may be None for testing)
    trauma_enabled: bool,
    force_trauma_on_game_over: bool,
    max_moves: int,
) -> GameResult:
    """Run a single game with configurable trauma flags.

    Args:
        sim_io: Simulation I/O interface for board reads/writes.
        sim: Game2048Sim instance (unused in this task).
        memory: MemoryCoordinator for move recording.
        semantic: SemanticStore (unused in this task).
        affect: AffectState instance tracking anxiety/valence.
        decision_llm: LLM for ReactDecider.
        deliberation_llm: LLM for ToTDecider.
        reflection_llm: LLM for post-game reflection.
        bus: EventBus (can be None for tests).
        trauma_enabled: If False, skip all aversive tagging.
        force_trauma_on_game_over: If True, bypass is_catastrophic_loss check.
        max_moves: Maximum move count before forced termination.

    Returns:
        GameResult with boards, anxieties, game-over flag, and predicate.
    """
    # Lazy imports to avoid circular deps in module-level code
    from nova_agent.action.adb import SwipeDirection
    from nova_agent.affect.rpe import rpe as compute_rpe
    from nova_agent.decision.arbiter import should_use_tot
    from nova_agent.decision.heuristic import is_game_over
    from nova_agent.decision.react import ReactDecider
    from nova_agent.decision.tot import ToTDecider
    from nova_agent.memory.aversive import AVERSIVE_TAG, is_catastrophic_loss, tag_aversive
    from nova_agent.reflection import run_reflection

    per_move_boards: list[BoardState] = []
    per_move_anxieties: list[float] = []
    reached_game_over = False
    would_predicate_have_fired = False

    # Deciders
    react_decider = ReactDecider(llm=decision_llm)
    tot_decider = ToTDecider(llm=deliberation_llm, bus=bus)

    prev_board: BoardState | None = None

    for move_idx in range(max_moves):
        # Read current board state
        board = sim_io.read_board()

        # Check game-over condition
        if is_game_over(board):
            reached_game_over = True
            break

        # Retrieve memories for current board
        retrieved = memory.retrieve_for_board(board, k=5)
        trauma_active = any(AVERSIVE_TAG in m.record.tags for m in retrieved)

        # Decide: ToT or React?
        use_tot = should_use_tot(board=board, affect=affect.vector)

        # Get decision
        screenshot_b64 = sim_io.screenshot_b64()
        if use_tot:
            decision = await tot_decider.decide(
                board=board,
                screenshot_b64=screenshot_b64,
                num_branches=4,
                game_id=None,
                move_idx=move_idx,
            )
        else:
            decision = react_decider.decide(board=board, screenshot_b64=screenshot_b64)

        # Apply move
        direction = SwipeDirection(decision.action)
        sim_io.apply_move(direction)

        # Read post-move board
        post_board = sim_io.read_board()
        per_move_boards.append(post_board)

        # Track anxiety
        per_move_anxieties.append(affect.vector.anxiety)

        # Compute RPE and update affect (if not first move)
        score_delta = post_board.score - board.score
        if prev_board is not None:
            rpe_val = compute_rpe(actual_score_delta=score_delta, board_before=board)
            affect.update(
                rpe=rpe_val,
                empty_cells=len([c for row in post_board.grid for c in row if c == 0]),
                terminal=False,
                trauma_triggered=trauma_active,
            )

        # Write move to memory
        importance = 5  # Default; could be scored via LLM
        tags: list[str] = []
        if trauma_active:
            tags.append("trauma-active")

        memory.write_move(
            board_before=board,
            board_after=post_board,
            action=decision.action,
            score_delta=score_delta,
            rpe=0.0,  # Simplified; full version would compute actual RPE
            importance=importance,
            source_reasoning=decision.reasoning,
            affect=None,  # Simplified
            tags=tags,
        )

        prev_board = post_board

    # Read final board
    final_board = sim_io.read_board()

    # Compute would_predicate_have_fired (catastrophic loss check)
    max_tile = (
        max(max(row) for row in final_board.grid)
        if any(any(row) for row in final_board.grid)
        else 0
    )
    empty_cells = len([c for row in final_board.grid for c in row if c == 0])
    would_predicate_have_fired = is_catastrophic_loss(
        final_score=final_board.score,
        max_tile_reached=max_tile,
        last_empty_cells=empty_cells,
    )

    # Post-game trauma tagging (if reached game-over)
    if reached_game_over and trauma_enabled:
        # Get recent precondition records
        recent_records = memory.episodic.list_recent(limit=RECENT_LIMIT)

        # Decide whether to tag based on force flag or predicate
        should_tag = force_trauma_on_game_over or would_predicate_have_fired

        if should_tag:
            # Tag aversive records
            tagged = tag_aversive(
                precondition_records=recent_records,
                was_catastrophic=would_predicate_have_fired,
            )
            # Upsert each tagged record back into memory
            for rec in tagged:
                memory.upsert_aversive_record(rec)
                memory.episodic.update(rec)

    # Post-game reflection (unconditional if game-over)
    if reached_game_over:
        last_30_summary = "Game-over state reached after move sequence."
        prior_lessons: list[str] = []
        try:
            _reflection_result = run_reflection(
                llm=reflection_llm,
                last_30_moves_summary=last_30_summary,
                prior_lessons=prior_lessons,
            )
        except Exception:  # noqa: BLE001
            # Reflection can fail gracefully; continue
            pass

    return GameResult(
        per_move_boards=per_move_boards,
        per_move_anxieties=per_move_anxieties,
        reached_game_over=reached_game_over,
        final_board=final_board,
        would_predicate_have_fired=would_predicate_have_fired,
    )


# ---------------------------------------------------------------------
# K=2 paired session (Task 6)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SessionResult:
    """Result of paired-session run (K=2, both arms, both games)."""

    seed_base: int
    r_post_y_on: float | None
    r_post_y_off: float | None
    n_post_moves_y_on: int
    n_post_moves_y_off: int
    censored_cap_y_on: bool
    censored_cap_y_off: bool
    censored_zero_encounter_y_on: bool
    censored_zero_encounter_y_off: bool
    delta_i: float | None  # r_off - r_on, None if either arm censored
    anxiety_lift_y_on: float | None
    anxiety_lift_y_off: float | None
    aversive_tag_count_y_on: int
    aversive_tag_count_y_off: int
    would_predicate_have_fired_y_on: bool
    reached_game_over_y_on: bool
    reached_game_over_y_off: bool


def _per_arm_db_paths(
    run_dir: Path,
    *,
    stage: str,
    seed: int,
    arm: str,
) -> tuple[Path, Path]:
    """Return (sqlite_path, lancedb_path) under <run_dir>/<stage>/<seed>/<arm>/."""
    base = run_dir / stage / str(seed) / arm
    base.mkdir(parents=True, exist_ok=True)
    return base / "episodic.db", base / "vector.lance"


async def _run_arm(
    *,
    arm: str,
    seed_base: int,
    run_dir: Path,
    stage: str,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    T: int,
    max_moves: int,
    trauma_enabled: bool,
    force_trauma_on_game_over: bool,
) -> tuple[GameResult, GameResult]:
    """Run game-1 + game-2 on a single arm with persistent memory."""
    # Lazy import to avoid circular deps
    from nova_agent.bus.recorder import RecordingEventBus
    from nova_agent.lab.io import SimGameIO
    from nova_agent.lab.scenarios import load as load_scenario
    from nova_agent.lab.sim import Game2048Sim
    from nova_agent.affect.state import AffectState
    from nova_agent.memory.coordinator import MemoryCoordinator
    from nova_agent.memory.semantic import SemanticStore

    sqlite_path, lance_path = _per_arm_db_paths(run_dir, stage=stage, seed=seed_base, arm=arm)
    memory = MemoryCoordinator(sqlite_path=sqlite_path, lancedb_path=lance_path)
    semantic = SemanticStore(path=sqlite_path.parent / "semantic.db")
    affect = AffectState()

    scenario = load_scenario("fresh-start")
    record_path = sqlite_path.parent / "events.jsonl"
    bus = RecordingEventBus(path=record_path)

    try:
        # Game 1
        sim1 = Game2048Sim(seed=scenario.seed(0) + seed_base, scenario=scenario)
        io1 = SimGameIO(sim=sim1)
        game1 = await _run_game(
            sim_io=io1,
            sim=sim1,
            memory=memory,
            semantic=semantic,
            affect=affect,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            bus=bus,
            trauma_enabled=trauma_enabled,
            force_trauma_on_game_over=force_trauma_on_game_over,
            max_moves=max_moves,
        )
        # Reset affect for game 2
        affect.reset_for_new_game()

        # Game 2
        sim2 = Game2048Sim(seed=scenario.seed(0) + seed_base + 999_999, scenario=scenario)
        io2 = SimGameIO(sim=sim2)
        game2 = await _run_game(
            sim_io=io2,
            sim=sim2,
            memory=memory,
            semantic=semantic,
            affect=affect,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            bus=bus,
            trauma_enabled=trauma_enabled,
            force_trauma_on_game_over=force_trauma_on_game_over,
            max_moves=max_moves,
        )
    finally:
        await bus.stop()

    return game1, game2


async def _run_paired_session(
    *,
    seed_base: int,
    run_dir: Path,
    stage: str,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    T: int,
    max_moves: int = MAX_MOVES_PHASE_08,
) -> SessionResult:
    """Run Y_on + Y_off arms sequentially with per-arm fresh memory stores."""
    g1_on, g2_on = await _run_arm(
        arm="y_on",
        seed_base=seed_base,
        run_dir=run_dir,
        stage=stage,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        T=T,
        max_moves=max_moves,
        trauma_enabled=True,
        force_trauma_on_game_over=True,
    )
    g1_off, g2_off = await _run_arm(
        arm="y_off",
        seed_base=seed_base,
        run_dir=run_dir,
        stage=stage,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        T=T,
        max_moves=max_moves,
        trauma_enabled=False,
        force_trauma_on_game_over=False,
    )

    censored_cap_on = not g1_on.reached_game_over
    censored_cap_off = not g1_off.reached_game_over

    dv_on = compute_session_dv(g2_on.per_move_boards, T=T)
    dv_off = compute_session_dv(g2_off.per_move_boards, T=T)

    delta_i: float | None = None
    if (
        not censored_cap_on
        and not censored_cap_off
        and dv_on.r_post is not None
        and dv_off.r_post is not None
    ):
        delta_i = dv_off.r_post - dv_on.r_post

    def _mean_anxiety_at_trap(boards: list[Any], anxieties: list[float]) -> float | None:
        pairs = [a for b, a in zip(boards, anxieties) if is_trap_proximate(b, T=T)]
        return sum(pairs) / len(pairs) if pairs else None

    # Lazy import for aversive tag constant
    from nova_agent.memory.aversive import AVERSIVE_TAG

    aversive_count_on = sum(
        1
        for r in (await _get_episodic_records(run_dir, stage, seed_base, "y_on"))
        if AVERSIVE_TAG in r.get("tags", [])
    )
    aversive_count_off = sum(
        1
        for r in (await _get_episodic_records(run_dir, stage, seed_base, "y_off"))
        if AVERSIVE_TAG in r.get("tags", [])
    )

    # Bound disk after aggregating (spec §3.4).
    shutil.rmtree(run_dir / stage / str(seed_base), ignore_errors=True)

    return SessionResult(
        seed_base=seed_base,
        r_post_y_on=dv_on.r_post,
        r_post_y_off=dv_off.r_post,
        n_post_moves_y_on=dv_on.n_post_moves,
        n_post_moves_y_off=dv_off.n_post_moves,
        censored_cap_y_on=censored_cap_on,
        censored_cap_y_off=censored_cap_off,
        censored_zero_encounter_y_on=dv_on.censored_zero_encounter,
        censored_zero_encounter_y_off=dv_off.censored_zero_encounter,
        delta_i=delta_i,
        anxiety_lift_y_on=_mean_anxiety_at_trap(g2_on.per_move_boards, g2_on.per_move_anxieties),
        anxiety_lift_y_off=_mean_anxiety_at_trap(g2_off.per_move_boards, g2_off.per_move_anxieties),
        aversive_tag_count_y_on=aversive_count_on,
        aversive_tag_count_y_off=aversive_count_off,
        would_predicate_have_fired_y_on=g1_on.would_predicate_have_fired,
        reached_game_over_y_on=g1_on.reached_game_over,
        reached_game_over_y_off=g1_off.reached_game_over,
    )


async def _get_episodic_records(
    run_dir: Path,
    stage: str,
    seed: int,
    arm: str,
) -> list[dict[str, Any]]:
    """Retrieve episodic records from per-arm memory store."""
    sqlite_path, _ = _per_arm_db_paths(run_dir, stage=stage, seed=seed, arm=arm)
    # Lazy import
    from nova_agent.memory.coordinator import MemoryCoordinator

    mem = MemoryCoordinator(
        sqlite_path=sqlite_path, lancedb_path=run_dir / stage / str(seed) / arm / "vector.lance"
    )
    records = mem.episodic.list_recent(limit=100)
    # Convert records to dicts for serialization
    return [
        {
            "tags": list(r.tags),
            "board_hash": getattr(r, "board_hash", None),
        }
        for r in records
    ]


# ---------------------------------------------------------------------
# Aggregator + halt criteria (Task 7)
# ---------------------------------------------------------------------


def _check_halt_criteria(
    stage: str,
    results: list[SessionResult],
    *,
    pilot_censoring_rate: float | None,
) -> str | None:
    """Return halt reason string, or None to continue (spec §3.1, §3.3).

    Args:
        stage: One of "smoke", "pilot", "surrogate", "main".
        results: List of SessionResult from paired runs so far.
        pilot_censoring_rate: Censoring rate from pilot stage (if applicable).

    Returns:
        Halt reason string (non-empty) or None (continue).
    """
    if not results:
        return None

    if stage == "smoke":
        # Smoke gate: require >=80% of arm-games reached_game_over
        reach_count = sum(
            (1 if r.reached_game_over_y_on else 0) + (1 if r.reached_game_over_y_off else 0)
            for r in results
        )
        total = 2 * len(results)
        if reach_count / total < SMOKE_REACH_GAMEOVER_FLOOR:
            return f"smoke_low_reach_game_over: {reach_count}/{total} < {SMOKE_REACH_GAMEOVER_FLOOR:.0%}"
        # Check for NaN or Inf in r_post DVs
        for r in results:
            for v in (r.r_post_y_on, r.r_post_y_off):
                if v is not None and (v != v or v in (float("inf"), float("-inf"))):
                    return f"smoke_nan_or_inf_dv: seed={r.seed_base}"
        # Check for all-zero rates (suggests broken computation)
        on_zero = all((r.r_post_y_on or 0.0) == 0.0 for r in results)
        off_zero = all((r.r_post_y_off or 0.0) == 0.0 for r in results)
        if on_zero or off_zero:
            return "smoke_all_zero_rates"
        return None

    if stage == "surrogate":
        # Surrogate gates: direction flip, zero variance, high censoring
        deltas = [r.delta_i for r in results if r.delta_i is not None]
        if not deltas:
            return "surrogate_all_censored"
        mean_delta = sum(deltas) / len(deltas)
        if mean_delta <= 0:
            return f"surrogate_direction_flip: mean_delta={mean_delta:.3f}"
        # Check variance on each arm separately
        on_vals = [r.r_post_y_on for r in results if r.r_post_y_on is not None]
        off_vals = [r.r_post_y_off for r in results if r.r_post_y_off is not None]
        if len(on_vals) >= 2 and statistics.pstdev(on_vals) == 0:
            return "surrogate_zero_variance_y_on"
        if len(off_vals) >= 2 and statistics.pstdev(off_vals) == 0:
            return "surrogate_zero_variance_y_off"
        # Check censoring rate
        n_censored = sum(1 for r in results if r.delta_i is None)
        rate = n_censored / len(results)
        threshold = max(2 * (pilot_censoring_rate or 0.0), SURROGATE_CENSORING_FLOOR)
        if rate > threshold:
            return f"surrogate_high_censor: rate={rate:.2f} > {threshold:.2f}"
        return None

    # "pilot" and "main" stages: no automatic halt criteria
    return None


async def _run_n_paired(
    *,
    n: int,
    seed_base_start: int,
    run_dir: Path,
    stage: str,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    T: int,
    max_moves: int,
    pilot_censoring_rate: float | None,
) -> tuple[list[SessionResult], str | None]:
    """Run N paired sessions sequentially, halting on stage-specific criteria.

    Args:
        n: Target number of sessions to run (may halt early).
        seed_base_start: First seed (incremented per session).
        run_dir: Root directory for stage outputs.
        stage: One of "smoke", "pilot", "surrogate", "main".
        decision_llm: LLM for ReactDecider.
        deliberation_llm: LLM for ToTDecider.
        reflection_llm: LLM for post-game reflection.
        T: Deliberation horizon (ToT depth).
        max_moves: Max moves per game.
        pilot_censoring_rate: From pilot stage (passed to halt check).

    Returns:
        (results, halt_reason) where halt_reason is None iff all N completed.
    """
    out: list[SessionResult] = []
    for offset in range(n):
        seed = seed_base_start + offset
        result = await _run_paired_session(
            seed_base=seed,
            run_dir=run_dir,
            stage=stage,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            T=T,
            max_moves=max_moves,
        )
        out.append(result)
        _append_session_jsonl(run_dir / stage / "sessions.jsonl", result)
        # Check halt criteria after each session (smoke/surrogate stages only)
        if stage in ("smoke", "surrogate"):
            halt = _check_halt_criteria(stage, out, pilot_censoring_rate=pilot_censoring_rate)
            if halt is not None:
                return out, halt
    # If we completed all N sessions, do a final check (typically None)
    final_halt = _check_halt_criteria(stage, out, pilot_censoring_rate=pilot_censoring_rate)
    return out, final_halt


# -----------------------------------------------------------------------
# T-calibration pilot helpers + golden-scenario calibration (Task 8)
# -----------------------------------------------------------------------

GOLDEN_BOARD: Final[list[list[int]]] = [
    [1024, 1024, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]
GOLDEN_GAME_MAX_MOVES: Final[int] = 20
GOLDEN_CAP_REACHED_LIMIT: Final[int] = 2  # >2 cap-reached → exit code 3
EXIT_GOLDEN_FAIL: Final[int] = 2  # rationality gate fail → paranoia detected
EXIT_PILOT_GOLDEN_BASELINE_FAILURE: Final[int] = 3
EXIT_OK: Final[int] = 0
EXIT_SMOKE_HALT: Final[int] = 4  # smoke stage halt on low reach_game_over
EXIT_SURROGATE_HALT: Final[int] = 5  # surrogate stage halt on direction flip
EXIT_PILOT_FAILURE: Final[int] = 6  # pilot stage runtime failure
EXIT_LOCKED_T_MISSING: Final[int] = 7  # locked_T.json missing or unreadable


def _sweep_conditional_rate(
    pilot_game2_boards: list[list[BoardState]],
    *,
    candidates: tuple[int, ...],
) -> dict[int, float]:
    """For each candidate T, compute the conditional post-encounter rate
    aggregated across pilot sessions. Censored sessions excluded per T.
    """
    table: dict[int, float] = {}
    for T in candidates:
        n_post = 0
        n_trap = 0
        for boards in pilot_game2_boards:
            dv = compute_session_dv(boards, T=T)
            if dv.r_post is None:
                continue
            n_post += dv.n_post_moves
            n_trap += int(round(dv.r_post * dv.n_post_moves))
        table[T] = 0.0 if n_post == 0 else n_trap / n_post
    return table


def _select_T_from_sweep(
    rates: dict[int, float],
    *,
    band: tuple[float, float],
) -> int | None:
    """Lock T per spec §3.2 selection rule: smallest qualifying, or median.

    Qualifiers are T values where lo <= rate <= hi. If multiple qualify,
    return the lower-of-two-medians for even counts, strict median for odd.
    """
    lo, hi = band
    qualifying = sorted([T for T, r in rates.items() if lo <= r <= hi])
    if not qualifying:
        return None
    if len(qualifying) == 1:
        return qualifying[0]
    mid = (len(qualifying) - 1) // 2  # lower-of-two-medians for even count
    return qualifying[mid]


def _lock_golden_thresholds(
    sessions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute move_threshold and anxiety_threshold from golden calibration sessions.

    move_threshold = ceil(μ_moves + σ_moves) over merge-successful sessions only.
    anxiety_threshold = μ_anxiety + 2σ_anxiety over ALL sessions.
    """
    merge_moves = [s["moves_to_merge"] for s in sessions if s["moves_to_merge"] is not None]
    all_anxieties = [s["mean_anxiety"] for s in sessions]

    if len(merge_moves) >= 2:
        mu_m = statistics.mean(merge_moves)
        sigma_m = statistics.stdev(merge_moves)
    elif len(merge_moves) == 1:
        mu_m = float(merge_moves[0])
        sigma_m = 0.0
    else:
        mu_m = float(GOLDEN_GAME_MAX_MOVES)
        sigma_m = 0.0

    move_threshold = math.ceil(mu_m + sigma_m)

    if len(all_anxieties) >= 2:
        mu_a = statistics.mean(all_anxieties)
        sigma_a = statistics.stdev(all_anxieties)
    else:
        mu_a = all_anxieties[0] if all_anxieties else 1.0
        sigma_a = 0.0

    anxiety_threshold = mu_a + 2 * sigma_a

    return {
        "move_threshold": move_threshold,
        "anxiety_threshold": anxiety_threshold,
    }


async def _run_golden_calibration_session(
    *,
    seed: int,
    run_dir: Path,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
) -> dict[str, Any]:
    """One Y_off single-game session on the golden board. No game-1 warmup."""
    # Lazy imports to avoid circular deps
    from nova_agent.affect.state import AffectState
    from nova_agent.bus.recorder import RecordingEventBus
    from nova_agent.lab.io import SimGameIO
    from nova_agent.lab.sim import Game2048Sim, Scenario
    from nova_agent.memory.coordinator import MemoryCoordinator
    from nova_agent.memory.semantic import SemanticStore

    # Build golden-board scenario
    golden_scenario = Scenario(
        id="golden-easy-win-1024",
        initial_grid=GOLDEN_BOARD,
        initial_score=2048,  # 1024+1024 = 2048 min-implied-score
        seed_base=20260507001,
        pattern_name="golden-calibration",
        high_tile_magnitude=1024,
        expected_cliff_window=(1, GOLDEN_GAME_MAX_MOVES),
        source_citation="Phase 0.8 §3.2 golden-scenario calibration",
    )

    sim = Game2048Sim(seed=golden_scenario.seed_base + seed, scenario=golden_scenario)
    io = SimGameIO(sim=sim)

    memory_dir = run_dir / "pilot" / "golden_calibration" / str(seed)
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory = MemoryCoordinator(
        sqlite_path=memory_dir / "episodic.db",
        lancedb_path=memory_dir / "vector.lance",
    )
    semantic = SemanticStore(memory_dir / "semantic.db")
    affect = AffectState()
    bus = RecordingEventBus(
        host="127.0.0.1",
        port=0,
        path=memory_dir / "events.jsonl",
    )

    try:
        result = await _run_game(
            sim_io=io,
            sim=sim,
            memory=memory,
            semantic=semantic,
            affect=affect,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            bus=bus,
            trauma_enabled=False,
            force_trauma_on_game_over=False,
            max_moves=GOLDEN_GAME_MAX_MOVES,
        )
    finally:
        await bus.stop()

    # Detect moves_to_merge: first move where max_tile >= 2048
    moves_to_merge: int | None = None
    for i, board in enumerate(result.per_move_boards):
        if board.max_tile >= 2048:
            moves_to_merge = i + 1  # 1-indexed
            break

    mean_anxiety = statistics.mean(result.per_move_anxieties) if result.per_move_anxieties else 0.0

    shutil.rmtree(memory_dir, ignore_errors=True)
    return {"moves_to_merge": moves_to_merge, "mean_anxiety": mean_anxiety}


async def run_pilot(
    *,
    run_dir: Path,
    n: int,
    seed_base_start: int,
    n_golden: int = 10,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    max_moves: int = MAX_MOVES_PHASE_08,
) -> tuple[dict[str, Any], int]:
    """T-calibration pilot + golden-scenario calibration.

    Returns (payload_dict, exit_code). exit_code=0=pass, 3=pre-trauma baseline failure.
    """
    # -- T-calibration sessions (Y_off K=2 × N) --
    pilot_game2_boards: list[list[BoardState]] = []
    for offset in range(n):
        seed = seed_base_start + offset
        _g1, g2 = await _run_arm(
            arm="y_off",
            seed_base=seed,
            run_dir=run_dir,
            stage="pilot",
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            T=0,  # placeholder during data collection
            max_moves=max_moves,
            trauma_enabled=False,
            force_trauma_on_game_over=False,
        )
        pilot_game2_boards.append(g2.per_move_boards)

    # -- Golden-scenario calibration (Y_off single-game × n_golden) --
    golden_sessions: list[dict[str, Any]] = []
    for idx in range(n_golden):
        sess = await _run_golden_calibration_session(
            seed=seed_base_start + 100_000 + idx,  # separate seed namespace
            run_dir=run_dir,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
        )
        golden_sessions.append(sess)

    n_cap_reached = sum(1 for s in golden_sessions if s["moves_to_merge"] is None)
    if n_cap_reached > GOLDEN_CAP_REACHED_LIMIT:
        payload: dict[str, Any] = {
            "error": "pre_trauma_baseline_failure",
            "n_cap_reached": n_cap_reached,
            "n_golden": n_golden,
            "sessions": golden_sessions,
        }
        out_path = run_dir / "pilot" / "golden_calibration.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2))
        return payload, EXIT_PILOT_GOLDEN_BASELINE_FAILURE

    thresholds = _lock_golden_thresholds(golden_sessions)
    golden_payload: dict[str, Any] = {
        "sessions": golden_sessions,
        "n_cap_reached": n_cap_reached,
        **thresholds,
    }
    golden_path = run_dir / "pilot" / "golden_calibration.json"
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    golden_path.write_text(json.dumps(golden_payload, indent=2))

    # -- T sweep --
    rates_initial = _sweep_conditional_rate(pilot_game2_boards, candidates=T_CANDIDATES_INITIAL)
    locked_T = _select_T_from_sweep(rates_initial, band=T_CALIBRATION_BAND)
    candidates_used = T_CANDIDATES_INITIAL
    rates_table = rates_initial
    if locked_T is None:
        rates_expanded = _sweep_conditional_rate(
            pilot_game2_boards, candidates=T_CANDIDATES_EXPANDED
        )
        locked_T = _select_T_from_sweep(rates_expanded, band=T_CALIBRATION_BAND)
        candidates_used = T_CANDIDATES_EXPANDED
        rates_table = rates_expanded

    censoring_count = sum(
        1
        for boards in pilot_game2_boards
        if compute_session_dv(boards, T=locked_T or 0).censored_zero_encounter
    )
    pilot_censoring_rate = censoring_count / n if n > 0 else 0.0

    payload = {
        "n_pilot_sessions": n,
        "candidates_used": list(candidates_used),
        "rates": {str(k): v for k, v in rates_table.items()},
        "locked_T": locked_T,
        "pilot_censoring_rate": pilot_censoring_rate,
        "calibration_failure": locked_T is None,
        "anchor_hash": ANCHOR_HASH,
    }
    out_path = run_dir / "pilot" / "locked_T.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    return payload, 0


# --------- Rationality gate runner (spec §3.2b) ---------


def _golden_seed(seed_idx: int) -> int:
    """Separate seed namespace for golden-gate sessions."""
    return hash("golden") ^ seed_idx


def _read_golden_calibration(path: Path) -> dict[str, Any]:
    """Read golden_calibration.json and return thresholds. Raises if missing."""
    if not path.exists():
        raise FileNotFoundError(f"golden_calibration.json not found: {path}")
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def _check_golden_gate_passed(run_dir: Path) -> None:
    """Raise if golden/result.json missing or status != 'pass'.

    Called by run_surrogate before starting (spec §3.2b: surrogate refuses
    to start if golden gate not passed).
    """
    result_path = run_dir / "golden" / "result.json"
    if not result_path.exists():
        raise FileNotFoundError(
            f"Golden gate result not found: {result_path}. Run --stage=golden before surrogate."
        )
    data = json.loads(result_path.read_text())
    if data.get("status") != "pass":
        raise RuntimeError(
            f"Golden gate did not pass (status={data.get('status')!r}). "
            "Surrogate cannot start until golden gate passes."
        )


async def _run_golden_arm(
    *,
    arm: str,
    seed: int,
    run_dir: Path,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    trauma_enabled: bool,
    force_trauma_on_game_over: bool,
) -> dict[str, Any]:
    """Game-1 warmup (fresh-start) + game-2 (golden board, 20-move cap) for one arm."""
    # Lazy imports to avoid circular deps
    from nova_agent.affect.state import AffectState
    from nova_agent.bus.recorder import RecordingEventBus
    from nova_agent.lab.io import SimGameIO
    from nova_agent.lab.scenarios import load as load_scenario
    from nova_agent.lab.sim import Game2048Sim, Scenario
    from nova_agent.memory.coordinator import MemoryCoordinator
    from nova_agent.memory.semantic import SemanticStore

    arm_dir = run_dir / "golden" / str(seed) / arm
    arm_dir.mkdir(parents=True, exist_ok=True)

    sqlite_path = arm_dir / "episodic.db"
    lance_path = arm_dir / "vector.lance"
    memory = MemoryCoordinator(sqlite_path=sqlite_path, lancedb_path=lance_path)
    semantic = SemanticStore(arm_dir / "semantic.db")
    affect = AffectState()

    scenario = load_scenario("fresh-start")
    record_path = arm_dir / "events.jsonl"
    bus = RecordingEventBus(path=record_path)

    try:
        # Game-1: fresh-start warmup
        sim1 = Game2048Sim(seed=seed, scenario=scenario)
        io1 = SimGameIO(sim=sim1)
        await _run_game(
            sim_io=io1,
            sim=sim1,
            memory=memory,
            semantic=semantic,
            affect=affect,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            bus=bus,
            trauma_enabled=trauma_enabled,
            force_trauma_on_game_over=force_trauma_on_game_over,
            max_moves=MAX_MOVES_PHASE_08,
        )
        affect.reset_for_new_game()

        # Game-2: golden board, 20-move cap
        # Create scenario with golden board override
        golden_scenario = Scenario(
            id="golden-easy-win-1024",
            initial_grid=GOLDEN_BOARD,
            initial_score=2048,  # 1024+1024 implied
            seed_base=20260507001,
            pattern_name="golden-gate",
            high_tile_magnitude=1024,
            expected_cliff_window=(1, GOLDEN_GAME_MAX_MOVES),
            source_citation="Phase 0.8 §3.2b golden-gate rationality check",
        )
        sim2 = Game2048Sim(seed=golden_scenario.seed_base + seed, scenario=golden_scenario)
        io2 = SimGameIO(sim=sim2)
        game2 = await _run_game(
            sim_io=io2,
            sim=sim2,
            memory=memory,
            semantic=semantic,
            affect=affect,
            decision_llm=decision_llm,
            deliberation_llm=deliberation_llm,
            reflection_llm=reflection_llm,
            bus=bus,
            trauma_enabled=trauma_enabled,
            force_trauma_on_game_over=force_trauma_on_game_over,
            max_moves=GOLDEN_GAME_MAX_MOVES,
        )
    finally:
        await bus.stop()

    # Detect moves_to_merge: first move where max_tile >= 2048
    moves_to_merge: int | None = None
    for i, board in enumerate(game2.per_move_boards):
        if board.max_tile >= 2048:
            moves_to_merge = i + 1  # 1-indexed
            break

    # Compute mean anxiety over game-2 moves
    mean_anxiety = statistics.mean(game2.per_move_anxieties) if game2.per_move_anxieties else 0.0

    # Clean up arm directory to avoid bloating golden/ folder
    shutil.rmtree(arm_dir, ignore_errors=True)

    return {"moves_to_merge": moves_to_merge, "mean_anxiety": mean_anxiety}


async def run_golden_gate(
    *,
    run_dir: Path,
    seed_idx: int = 0,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
) -> int:
    """Run §3.2b rationality gate. Returns 0=pass, EXIT_GOLDEN_FAIL=fail.

    Verifies trauma-tagging produces *specific* avoidance rather than
    *generalized* paranoia. Runs 1 K=2 paired session on easy-win-1024 board.
    Y_on must meet both move_threshold and anxiety_threshold from
    golden_calibration.json or gate fails (exit 2).
    """
    calib_path = run_dir / "pilot" / "golden_calibration.json"
    calib = _read_golden_calibration(calib_path)
    move_threshold: int = calib["move_threshold"]
    anxiety_threshold: float = calib["anxiety_threshold"]

    seed = _golden_seed(seed_idx)

    # Run Y_on and Y_off arms
    y_on = await _run_golden_arm(
        arm="y_on",
        seed=seed,
        run_dir=run_dir,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        trauma_enabled=True,
        force_trauma_on_game_over=True,
    )
    y_off = await _run_golden_arm(
        arm="y_off",
        seed=seed,
        run_dir=run_dir,
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        trauma_enabled=False,
        force_trauma_on_game_over=False,
    )

    golden_dir = run_dir / "golden"
    golden_dir.mkdir(parents=True, exist_ok=True)

    mtm_on = y_on["moves_to_merge"]
    anx_on = y_on["mean_anxiety"]

    # Adjudicate pass/fail
    move_pass = mtm_on is not None and mtm_on <= move_threshold
    anxiety_pass = anx_on <= anxiety_threshold

    if not move_pass or not anxiety_pass:
        halt = {
            "criterion_move_count": "pass" if move_pass else "fail",
            "criterion_anxiety": "pass" if anxiety_pass else "fail",
            "moves_to_merge_Y_on": mtm_on,
            "mean_anxiety_Y_on": anx_on,
            "move_threshold": move_threshold,
            "anxiety_threshold": anxiety_threshold,
        }
        (golden_dir / "halt_reason.json").write_text(json.dumps(halt, indent=2))
        return EXIT_GOLDEN_FAIL

    # Pass: write result.json
    result = {
        "status": "pass",
        "moves_to_merge_Y_on": mtm_on,
        "mean_anxiety_Y_on": anx_on,
        "moves_to_merge_Y_off": y_off["moves_to_merge"],
        "mean_anxiety_Y_off": y_off["mean_anxiety"],
        "move_threshold": move_threshold,
        "anxiety_threshold": anxiety_threshold,
    }
    (golden_dir / "result.json").write_text(json.dumps(result, indent=2))
    return 0


def _write_summary_csv(path: Path, results: list[SessionResult]) -> None:
    """Write cumulative sessions to CSV with dataclass-field headers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [f.name for f in _dataclasses.fields(SessionResult)]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = _csv.writer(fh)
        w.writerow(fields)
        for r in results:
            w.writerow(["" if getattr(r, name) is None else getattr(r, name) for name in fields])


def _append_session_jsonl(path: Path, result: SessionResult) -> None:
    """Append single session result as JSON line (crash-safe incremental write)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {f.name: getattr(result, f.name) for f in _dataclasses.fields(SessionResult)}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")


async def run_smoke(
    *,
    run_dir: Path,
    n: int,
    seed_base_start: int,
    decision_llm: Any,
    deliberation_llm: Any,
    reflection_llm: Any,
    T_placeholder: int = 16,
    max_moves: int = MAX_MOVES_PHASE_08,
) -> int:
    """Smoke gate: N=3 paired sessions at placeholder T. See spec §3.1."""
    results, halt = await _run_n_paired(
        n=n,
        seed_base_start=seed_base_start,
        run_dir=run_dir,
        stage="smoke",
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        T=T_placeholder,
        max_moves=max_moves,
        pilot_censoring_rate=None,
    )
    _write_summary_csv(run_dir / "smoke" / "summary.csv", results)
    if halt is not None:
        halt_path = run_dir / "smoke" / "halt.txt"
        halt_path.parent.mkdir(parents=True, exist_ok=True)
        halt_path.write_text(halt)
        return EXIT_SMOKE_HALT
    return EXIT_OK


def _read_locked_t(path: Path) -> tuple[int, float]:
    """Returns (locked_T, pilot_censoring_rate). Raises on missing or calibration_failure."""
    if not path.exists():
        raise FileNotFoundError(f"locked_T.json missing at {path}")
    payload = json.loads(path.read_text())
    if payload.get("calibration_failure"):
        raise RuntimeError("pilot reported calibration_failure; pivot to §5 fallback")
    locked_T = payload.get("locked_T")
    if not isinstance(locked_T, int):
        raise RuntimeError(f"locked_T is not an integer: {locked_T!r}")
    return locked_T, float(payload.get("pilot_censoring_rate", 0.0))


async def run_surrogate(
    *,
    run_dir: Path,
    n: int,
    seed_base_start: int,
    decision_llm: Any,
    deliberation_llm: Any,
    reflection_llm: Any,
    max_moves: int = MAX_MOVES_PHASE_08,
) -> int:
    """Surrogate gate: N=20 paired sessions at locked T. See spec §3.3."""
    # Block if golden gate not passed (spec §3.2b).
    _check_golden_gate_passed(run_dir)

    locked_T, pilot_censoring = _read_locked_t(run_dir / "pilot" / "locked_T.json")

    results, halt = await _run_n_paired(
        n=n,
        seed_base_start=seed_base_start,
        run_dir=run_dir,
        stage="surrogate",
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        T=locked_T,
        max_moves=max_moves,
        pilot_censoring_rate=pilot_censoring,
    )
    _write_summary_csv(run_dir / "surrogate" / "summary.csv", results)
    if halt is not None:
        halt_path = run_dir / "surrogate" / "halt.txt"
        halt_path.parent.mkdir(parents=True, exist_ok=True)
        halt_path.write_text(halt)
        return EXIT_SURROGATE_HALT

    # Soft warning on low d_paired estimate — log but don't abort (spec §3.3).
    deltas = [r.delta_i for r in results if r.delta_i is not None]
    if len(deltas) >= 2:
        try:
            d = paired_cohens_d(deltas)
            if d < SOFT_WARNING_D_FLOOR:
                warning_path = run_dir / "surrogate" / "soft_warning.txt"
                warning_path.parent.mkdir(parents=True, exist_ok=True)
                warning_path.write_text(
                    f"d_paired_estimate={d:.3f} < {SOFT_WARNING_D_FLOOR}\n"
                    "see spec §3.3 — false-negative justification\n"
                )
        except ValueError:
            pass
    return EXIT_OK


# -----------------------------------------------------------------------
# Adjudication + main run (spec §3.4 + §3.5)
# -----------------------------------------------------------------------


@_dataclasses.dataclass(frozen=True)
class AdjudicationResult:
    d: float
    ci_lo: float
    ci_hi: float
    p_value_one_sided: float
    n_used: int
    n_censored_cap: int
    n_censored_zero_encounter: int
    primary_pass: bool
    secondary_d: float | None
    r_off_mean: float
    r_on_mean: float
    anxiety_lift_off: float | None
    anxiety_lift_on: float | None
    sensitivity_predicate_firing_d: float | None
    sensitivity_cap_exhaustion_count: int


def _adjudicate(results: list[SessionResult]) -> AdjudicationResult:
    deltas = [r.delta_i for r in results if r.delta_i is not None]
    n_cap = sum(1 for r in results if r.censored_cap_y_on or r.censored_cap_y_off)
    n_zero = sum(
        1
        for r in results
        if r.delta_i is None and not (r.censored_cap_y_on or r.censored_cap_y_off)
    )
    on_vals = [r.r_post_y_on for r in results if r.r_post_y_on is not None]
    off_vals = [r.r_post_y_off for r in results if r.r_post_y_off is not None]
    r_on_mean = sum(on_vals) / len(on_vals) if on_vals else 0.0
    r_off_mean = sum(off_vals) / len(off_vals) if off_vals else 0.0

    if len(deltas) >= 2:
        try:
            d = paired_cohens_d(deltas)
            ci_lo, ci_hi = paired_d_ci_95(deltas)
            n = len(deltas)
            t = d * (n**0.5)
            p_one_sided = 0.5 * (1.0 - math.erf(t / (2.0**0.5)))
        except ValueError:
            d, ci_lo, ci_hi, p_one_sided = 0.0, 0.0, 0.0, 1.0
    else:
        d, ci_lo, ci_hi, p_one_sided = 0.0, 0.0, 0.0, 1.0

    ppass = (
        primary_pass(deltas, r_off_mean=r_off_mean, r_on_mean=r_on_mean)
        if len(deltas) >= 2
        else False
    )

    sec_deltas = [
        (r.anxiety_lift_y_off - r.anxiety_lift_y_on)
        for r in results
        if r.anxiety_lift_y_off is not None and r.anxiety_lift_y_on is not None
    ]
    secondary_d: float | None
    try:
        secondary_d = paired_cohens_d(sec_deltas) if len(sec_deltas) >= 2 else None
    except ValueError:
        secondary_d = None

    pred_deltas = [
        r.delta_i for r in results if r.delta_i is not None and r.would_predicate_have_fired_y_on
    ]
    try:
        sens_pred_d: float | None = paired_cohens_d(pred_deltas) if len(pred_deltas) >= 2 else None
    except ValueError:
        sens_pred_d = None

    on_anx = [r.anxiety_lift_y_on for r in results if r.anxiety_lift_y_on is not None]
    off_anx = [r.anxiety_lift_y_off for r in results if r.anxiety_lift_y_off is not None]
    anx_on: float | None = sum(on_anx) / len(on_anx) if on_anx else None
    anx_off: float | None = sum(off_anx) / len(off_anx) if off_anx else None

    return AdjudicationResult(
        d=d,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        p_value_one_sided=p_one_sided,
        n_used=len(deltas),
        n_censored_cap=n_cap,
        n_censored_zero_encounter=n_zero,
        primary_pass=ppass,
        secondary_d=secondary_d,
        r_off_mean=r_off_mean,
        r_on_mean=r_on_mean,
        anxiety_lift_off=anx_off,
        anxiety_lift_on=anx_on,
        sensitivity_predicate_firing_d=sens_pred_d,
        sensitivity_cap_exhaustion_count=n_cap,
    )


def _interpret(adj: AdjudicationResult) -> str:
    if not adj.primary_pass:
        return "Primary nulls → trauma demoted from architectural feature to UI flavor."
    if adj.secondary_d is None or adj.secondary_d < 0.10:
        return (
            "Primary passes, secondary nulls → mechanism works behaviorally but "
            "routes through planning/ToT/memory rather than affect lift. "
            "Follow-up ADR amendment recommended."
        )
    return "Both pass → trauma validated as behavioral feature with affect-pathway expression."


def _write_adjudication_md(path: Path, adj: AdjudicationResult) -> None:
    lines = [
        "# Phase 0.8 Trauma Ablation — Adjudication",
        "",
        "## Primary DV (gating, behavioral)",
        f"- Paired Cohen's d: **{adj.d:.3f}**  (95% CI [{adj.ci_lo:.3f}, {adj.ci_hi:.3f}])",
        f"- One-sided p-value (paired-t): {adj.p_value_one_sided:.4f}",
        f"- N used: {adj.n_used}  (cap-censored: {adj.n_censored_cap}; "
        f"zero-encounter-censored: {adj.n_censored_zero_encounter})",
        f"- Mean rate Y_on:  {adj.r_on_mean:.3f}",
        f"- Mean rate Y_off: {adj.r_off_mean:.3f}",
        f"- **Pass/Fail:** {'PASS' if adj.primary_pass else 'FAIL'}",
        "",
        "## Secondary DV (descriptive)",
        f"- Anxiety-lift paired-d: {adj.secondary_d if adj.secondary_d is not None else 'N/A'}",
        f"- Mean anxiety lift Y_on:  {adj.anxiety_lift_on}",
        f"- Mean anxiety lift Y_off: {adj.anxiety_lift_off}",
        "",
        "## Sensitivity",
        f"- Predicate-firing subset paired-d: {adj.sensitivity_predicate_firing_d}",
        f"- Cap-exhaustion sessions: {adj.sensitivity_cap_exhaustion_count}",
        "",
        "## Three-branch interpretation (spec §3.5)",
        _interpret(adj),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


async def run_main(
    *,
    run_dir: Path,
    n_additional: int,
    seed_base_start: int,
    decision_llm: Any,  # LLM
    deliberation_llm: Any,  # LLM
    reflection_llm: Any,  # LLM
    surrogate_results: list[SessionResult] | None = None,
    max_moves: int = MAX_MOVES_PHASE_08,
) -> int:
    """Main run: +N_additional paired sessions. Adjudicates cumulative results."""
    locked_T, pilot_censoring = _read_locked_t(run_dir / "pilot" / "locked_T.json")
    new_results, _halt = await _run_n_paired(
        n=n_additional,
        seed_base_start=seed_base_start,
        run_dir=run_dir,
        stage="main",
        decision_llm=decision_llm,
        deliberation_llm=deliberation_llm,
        reflection_llm=reflection_llm,
        T=locked_T,
        max_moves=max_moves,
        pilot_censoring_rate=pilot_censoring,
    )
    all_results = (surrogate_results or []) + new_results
    _write_summary_csv(run_dir / "main" / "summary.csv", all_results)
    adj = _adjudicate(all_results)
    _write_adjudication_md(run_dir / "main" / "adjudication.md", adj)
    return EXIT_OK


def _build_stack(tier: str, budget_usd: float) -> tuple[Any, Any, Any]:
    """Build decision/deliberation/reflection LLM stack for the given tier + budget."""
    from nova_agent.budget import SessionBudget
    from nova_agent.config import get_settings
    from nova_agent.llm.factory import build_llm
    from nova_agent.llm import tiers as model_tiers
    from nova_agent.llm.protocol import BudgetedLLM

    s = get_settings()
    budget = SessionBudget(cap_usd=budget_usd)

    decision_llm = BudgetedLLM(
        build_llm(
            model=str(model_tiers.model_for("decision")),
            google_api_key=s.google_api_key,
            anthropic_api_key=s.anthropic_api_key,
            daily_cap_usd=s.daily_budget_usd,
        ),
        budget,
    )
    deliberation_llm = BudgetedLLM(
        build_llm(
            model=str(model_tiers.model_for("tot")),
            google_api_key=s.google_api_key,
            anthropic_api_key=s.anthropic_api_key,
            daily_cap_usd=s.daily_budget_usd,
        ),
        budget,
    )
    reflection_llm = BudgetedLLM(
        build_llm(
            model=str(model_tiers.model_for("reflection")),
            google_api_key=s.google_api_key,
            anthropic_api_key=s.anthropic_api_key,
            daily_cap_usd=s.daily_budget_usd,
        ),
        budget,
    )
    return decision_llm, deliberation_llm, reflection_llm


def main() -> None:
    import argparse
    import asyncio
    import sys

    parser = argparse.ArgumentParser(
        description="Phase 0.8 trauma-ablation runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        choices=("smoke", "pilot", "golden", "surrogate", "main"),
        required=True,
        help="Which gate stage to run",
    )
    parser.add_argument(
        "--n", type=int, default=None, help="Number of sessions (overrides stage default)"
    )
    parser.add_argument("--seed-base", type=int, default=20260507, dest="seed_base")
    parser.add_argument("--budget-usd", type=float, default=None, dest="budget_usd")
    parser.add_argument("--out", type=Path, default=None, help="Run output directory")
    parser.add_argument("--tier", default="production", help="Model tier (production | demo)")
    args = parser.parse_args()

    # Resolve defaults
    stage_n_defaults = {**STAGE_DEFAULT_N, "golden": 1}
    stage_budget_defaults = {**STAGE_BUDGET_USD}
    n = args.n if args.n is not None else stage_n_defaults.get(args.stage, 3)
    budget_usd = (
        args.budget_usd
        if args.budget_usd is not None
        else stage_budget_defaults.get(args.stage, 6.0)
    )
    run_dir = args.out if args.out is not None else Path(f"runs/{args.seed_base}-trauma-ablation")

    decision_llm, deliberation_llm, reflection_llm = _build_stack(args.tier, budget_usd)

    if args.stage == "smoke":
        rc = asyncio.run(
            run_smoke(
                run_dir=run_dir,
                n=n,
                seed_base_start=args.seed_base,
                decision_llm=decision_llm,
                deliberation_llm=deliberation_llm,
                reflection_llm=reflection_llm,
            )
        )
    elif args.stage == "pilot":
        _payload, rc = asyncio.run(
            run_pilot(
                run_dir=run_dir,
                n=n,
                seed_base_start=args.seed_base,
                decision_llm=decision_llm,
                deliberation_llm=deliberation_llm,
                reflection_llm=reflection_llm,
            )
        )
    elif args.stage == "golden":
        rc = asyncio.run(
            run_golden_gate(
                run_dir=run_dir,
                seed_idx=0,
                decision_llm=decision_llm,
                deliberation_llm=deliberation_llm,
                reflection_llm=reflection_llm,
            )
        )
    elif args.stage == "surrogate":
        rc = asyncio.run(
            run_surrogate(
                run_dir=run_dir,
                n=n,
                seed_base_start=args.seed_base,
                decision_llm=decision_llm,
                deliberation_llm=deliberation_llm,
                reflection_llm=reflection_llm,
            )
        )
    else:  # main
        rc = asyncio.run(
            run_main(
                run_dir=run_dir,
                n_additional=n,
                seed_base_start=args.seed_base + 100_000,
                decision_llm=decision_llm,
                deliberation_llm=deliberation_llm,
                reflection_llm=reflection_llm,
            )
        )
    sys.exit(rc)


if __name__ == "__main__":
    main()
