"""Phase 0.8 trauma-ablation runner.

Spec: docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md.

Single async orchestrator. K=2 multi-game session structure. The IV is a
single boolean ``trauma_enabled`` flag at the runner-local game-over
hook's ``tag_aversive`` call; downstream stages (importance bump,
retrieval boost, extinction, inert cap) collapse naturally.
"""

from __future__ import annotations

import hashlib
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
    "pilot": 30.0,
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
        # Check halt criteria after each session (smoke/surrogate stages only)
        if stage in ("smoke", "surrogate"):
            halt = _check_halt_criteria(stage, out, pilot_censoring_rate=pilot_censoring_rate)
            if halt is not None:
                return out, halt
    # If we completed all N sessions, do a final check (typically None)
    final_halt = _check_halt_criteria(stage, out, pilot_censoring_rate=pilot_censoring_rate)
    return out, final_halt
