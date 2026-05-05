"""Phase 0.7 cliff-test runner.

Single async orchestrator that runs paired Carla/Bot trials across the
configured scenarios and writes per-trial CSV + per-trial JSONL artifacts.

This module is a DATA COLLECTOR only. Aggregate statistics, mean-Δ
computation, and the cliff-test pass/fail verdict are explicitly
out-of-scope and live in a separate ``analyze_results.py`` per the spec
§2.7 / §8.

Spec: ``docs/superpowers/specs/2026-05-05-test-runner-design.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from nova_agent.action.adb import SwipeDirection
from nova_agent.affect.rpe import rpe as compute_rpe
from nova_agent.affect.state import AffectState
from nova_agent.affect.verbalize import describe as describe_affect
from nova_agent.bus.recorder import RecordingEventBus
from nova_agent.bus.websocket import EventBus
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.decision.baseline import BaselineDecider, TrialAborted
from nova_agent.decision.heuristic import is_game_over
from nova_agent.decision.react import Decision, ReactDecider
from nova_agent.decision.tot import ToTDecider
from nova_agent.lab.io import SimGameIO
from nova_agent.lab.scenarios import MAX_MOVES
from nova_agent.lab.sim import Game2048Sim, Scenario
from nova_agent.llm.protocol import LLM
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.memory.types import AffectSnapshot
from nova_agent.perception.types import BoardState
from nova_agent.reflection import run_reflection

# Per spec §2.6 + ADR-0006: cognitive-judgment models must run at production tier.
_ALLOWED_TIERS: Final[frozenset[str]] = frozenset({"production", "demo"})

EXIT_OK: Final[int] = 0
EXIT_SOFT_CAP: Final[int] = 2
EXIT_HARD_CAP: Final[int] = 3
EXIT_TIER_REFUSED: Final[int] = 4  # USAGE error; not the methodology >2-aborts-per-scenario flag


# Per spec §2.7 / scenarios spec §2.7: Carla "predicts the cliff" iff
# anxiety > 0.6 for >= 2 consecutive moves. Strict greater-than.
ANXIETY_THRESHOLD: Final[float] = 0.6
ANXIETY_CONSECUTIVE: Final[int] = 2


def _first_threshold_index(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> int | None:
    """Return the index of the first move that begins a run of ``consecutive``
    moves with anxiety strictly greater than ``threshold``. Return None if no
    such run exists.

    Spec §2.7: ``t_predicts`` for Carla = this index, or null if no breach.
    """
    if consecutive <= 0 or len(trajectory) < consecutive:
        return None
    run = 0
    for i, v in enumerate(trajectory):
        if v > threshold:
            run += 1
            if run >= consecutive:
                return i - consecutive + 1
        else:
            run = 0
    return None


def _check_anxiety_threshold(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> bool:
    """True iff the trajectory contains >= ``consecutive`` consecutive values
    strictly greater than ``threshold``.
    """
    return (
        _first_threshold_index(trajectory, threshold=threshold, consecutive=consecutive) is not None
    )


# Per spec §2.3 + §2.6: cost-cap envelope.
BUDGET_PER_SCENARIO_ARM_USD: Final[float] = 5.00
HARD_CAP_MULTIPLIER: Final[float] = 1.3


class _BudgetState:
    """Per-(scenario_id, arm) running spend, with soft- and hard-cap checks.

    Used by the worker (hard-cap pre-LLM gate) and the orchestrator
    (soft-cap drain-in-flight halt). asyncio coroutines do not race on a
    single-threaded event loop, so no lock is needed; ``add`` is a single
    arithmetic update.
    """

    def __init__(
        self,
        *,
        soft_cap_usd: float = BUDGET_PER_SCENARIO_ARM_USD,
        hard_cap_multiplier: float = HARD_CAP_MULTIPLIER,
    ) -> None:
        self._soft_cap = soft_cap_usd
        self._hard_cap = soft_cap_usd * hard_cap_multiplier
        self._spent: dict[tuple[str, str], float] = {}

    def add(self, scenario_id: str, arm: str, cost_usd: float) -> None:
        key = (scenario_id, arm)
        self._spent[key] = self._spent.get(key, 0.0) + cost_usd

    def spent(self, scenario_id: str, arm: str) -> float:
        return self._spent.get((scenario_id, arm), 0.0)

    def soft_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._soft_cap

    def hard_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._hard_cap


# Per spec §2.7. Order is contract — analyze_results.py reads by name,
# not position, but appending new columns at the end is the ratchet.
_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "scenario_id",
    "trial_index",
    "arm",
    "t_predicts",
    "t_baseline_fails",
    "cost_usd",
    "abort_reason",
    "anxiety_threshold_met",
    "final_move_index",
    "is_right_censored",
)


def _append_csv_row(csv_path: Path | str, **fields: Any) -> None:
    """Append a single trial row to ``csv_path``. Creates the file (and parent
    dirs) if missing; writes the header iff the file does not exist or is empty.

    None values serialize as empty strings (CSV null convention). Raises
    KeyError if any expected column is missing from ``fields``.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    row = []
    for col in _CSV_COLUMNS:
        if col not in fields:
            raise KeyError(f"missing column {col!r} in CSV row append")
        v = fields[col]
        row.append("" if v is None else str(v))

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(list(_CSV_COLUMNS))
        writer.writerow(row)


# Tie-break order per scenarios spec §2.3 + Bot spec §2.3.
_TIEBREAK_ORDER: Final[tuple[SwipeDirection, ...]] = (
    SwipeDirection.UP,
    SwipeDirection.RIGHT,
    SwipeDirection.DOWN,
    SwipeDirection.LEFT,
)


def _try_apply(
    io: SimGameIO,
    direction: SwipeDirection,
    board_before: BoardState,
) -> SwipeDirection | None:
    """Apply ``direction`` via ``io``. Return the direction iff the board
    changed, else None (the move was a no-op).

    Relies on Game2048Sim's no-op contract (edge case #3 in sim.py): a no-op
    swipe does not advance RNG and does not spawn a tile, so calling
    apply_move on a no-op direction is safe and leaves the sim state unchanged.
    """
    io.apply_move(direction)
    if io.read_board().grid == board_before.grid:
        return None
    return direction


def _apply_with_tiebreak(
    io: SimGameIO,
    chosen: str,
    board: BoardState,
) -> SwipeDirection:
    """Apply ``chosen`` (e.g. ``"swipe_up"``) via ``io``. If the move is a
    no-op (board unchanged), fall through the tie-break order UP > RIGHT >
    DOWN > LEFT and apply the first direction that changes the board.

    Returns the SwipeDirection that was actually applied.
    Raises ValueError if no direction changes the board (defensive; the
    per-move loop should check ``is_game_over()`` before invoking the decider,
    making this branch unreachable in normal operation).
    """
    chosen_direction = SwipeDirection(chosen)
    applied = _try_apply(io, chosen_direction, board)
    if applied is not None:
        return applied

    for direction in _TIEBREAK_ORDER:
        if direction == chosen_direction:
            continue
        applied = _try_apply(io, direction, board)
        if applied is not None:
            return applied

    raise ValueError("no legal move on this board (game-over should have caught this)")


@dataclass(frozen=True)
class BotTrialResult:
    """Outcome of a single Bot trial.

    ``cost_usd`` aggregates token costs over all bot_call_success events
    emitted during the trial. The placeholder per-call estimate (see
    ``_bot_call_cost_estimate``) is used for cap accounting; exact per-call
    USD is recomputed by ``analyze_results.py`` from JSONL telemetry.
    """

    scenario_id: str
    trial_index: int
    final_move_index: int
    cost_usd: float
    abort_reason: str | None
    t_baseline_fails: int | None
    is_right_censored: bool


async def _run_bot_trial(
    *,
    scenario: Scenario,
    trial_index: int,
    llm: LLM,
    bus: EventBus,
) -> BotTrialResult:
    """Run one Bot trial against ``Game2048Sim``. Returns the per-trial summary.

    Per spec §4.2 pseudocode + Bot spec §3.4 telemetry contract:
    - Game-over before MAX_MOVES → t_baseline_fails = move_index,
      is_right_censored = False.
    - Abort (api_error / parse_failure) → t_baseline_fails = None,
      is_right_censored = False.
    - Exhausted MAX_MOVES without game-over → t_baseline_fails = MAX_MOVES
      sentinel per scenarios spec §5.1, is_right_censored = True.
    """
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    decider = BaselineDecider(llm=llm, bus=bus)

    cost_usd = 0.0
    abort_reason: str | None = None
    move_index = 0

    for move_index in range(MAX_MOVES):
        if sim.is_game_over():
            break
        board = io.read_board()
        decision = await decider.decide(
            board=board,
            trial_index=trial_index,
            move_index=move_index,
        )
        if isinstance(decision, TrialAborted):
            abort_reason = decision.reason
            break
        _apply_with_tiebreak(io, decision.action, board)
        cost_usd += _bot_call_cost_estimate()

    # Termination state derivation per scenarios spec §5.1.
    t_baseline_fails: int | None
    is_right_censored: bool
    if abort_reason is not None:
        t_baseline_fails = None
        is_right_censored = False
    elif sim.is_game_over():
        t_baseline_fails = move_index
        is_right_censored = False
    else:
        # Exhausted MAX_MOVES cap without game-over → right-censored sentinel.
        t_baseline_fails = MAX_MOVES
        is_right_censored = True

    return BotTrialResult(
        scenario_id=scenario.id,
        trial_index=trial_index,
        final_move_index=move_index,
        cost_usd=cost_usd,
        abort_reason=abort_reason,
        t_baseline_fails=t_baseline_fails,
        is_right_censored=is_right_censored,
    )


def _bot_call_cost_estimate() -> float:
    """Per-Bot-call USD estimate at production tier (gemini-2.5-flash for
    the bot decision role). Calibrated to spec §2.6: ~$0.005/trial × 50
    moves = $0.0001/move. The exact tier-rate composition lives in
    nova_agent/llm/tiers.py; this estimate is a coarse placeholder for
    cap accounting. analyze_results.py recomputes from JSONL telemetry.
    """
    return 0.0001


@dataclass(frozen=True)
class CarlaTrialResult:
    """Outcome of a single Carla trial.

    ``anxiety_trajectory`` records every post-decision anxiety value (one per
    ``affect.update`` call); ``t_predicts`` is the §2.7 first-breach index
    (or None if the anxiety threshold was never breached).
    """

    scenario_id: str
    trial_index: int
    final_move_index: int
    cost_usd: float
    abort_reason: str | None
    anxiety_trajectory: list[float]
    t_predicts: int | None
    anxiety_threshold_met: bool
    is_right_censored: bool


async def _run_carla_trial(
    *,
    scenario: Scenario,
    trial_index: int,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bus: EventBus,
) -> CarlaTrialResult:
    """Run one Carla trial end-to-end.

    Mirrors the canonical per-move loop pattern at ``nova_agent/main.py:240-319``
    with these differences:
    - ``SimGameIO`` instead of ``LiveGameIO``; no OCR.
    - Bus passed in by the caller; lifecycle (start/stop) is the caller's.
    - Fresh ``MemoryCoordinator`` on a ``tempfile.TemporaryDirectory`` — auto-
      cleaned on context-manager exit.
    - Memory retrieval disabled; ``trauma_triggered=False`` always (no retrieval
      → no aversive-tag lookups).
    - Anxiety captured from ``affect.update()`` return value, not from the bus
      (WebSocket bus silently drops headless events; return-value is the
      measurement channel per spec §2.4).
    - ``run_reflection`` called at end; failure is non-blocking.
    """
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    affect = AffectState()
    react_decider = ReactDecider(llm=decision_llm)
    tot_decider = ToTDecider(llm=tot_llm, bus=bus)

    anxiety_trajectory: list[float] = []
    cost_usd = 0.0
    abort_reason: str | None = None
    move_index = 0
    prev_board: BoardState | None = None
    prev_decision: Decision | None = None

    with tempfile.TemporaryDirectory(prefix=f"nova-cliff-{scenario.id}-{trial_index}-") as tmp:
        memory = MemoryCoordinator(
            sqlite_path=Path(tmp) / "episodic.db",
            lancedb_path=Path(tmp) / "vector.lance",
        )

        for move_index in range(MAX_MOVES):
            board = io.read_board()
            if is_game_over(board):
                break

            mode = "tot" if should_use_tot(board=board, affect=affect.vector) else "react"
            try:
                if mode == "tot":
                    decision = await tot_decider.decide(
                        board=board,
                        screenshot_b64=io.screenshot_b64(),
                        move_idx=move_index,
                    )
                else:
                    affect_text = describe_affect(affect.vector)
                    decision = react_decider.decide_with_context(
                        board=board,
                        screenshot_b64=None,
                        memories=[],
                        affect_text=affect_text,
                    )
            except Exception:  # noqa: BLE001
                # Per LESSONS: never silently swallow LLM exceptions. Mark
                # trial aborted with a structured reason.
                abort_reason = "api_error"
                break

            cost_usd += _carla_call_cost_estimate(mode)

            io.apply_move(SwipeDirection(decision.action))

            # Affect update — only when there is a previous board to compute
            # RPE against (first move has no reference point).
            if prev_board is not None and prev_decision is not None:
                score_delta = board.score - prev_board.score
                delta_rpe = compute_rpe(actual_score_delta=score_delta, board_before=prev_board)
                # Memory retrieval is disabled in cliff-test trials to remove
                # network/DB latency as a confound; trauma detection requires
                # retrieval, so trauma_triggered is always False here.
                v = affect.update(
                    rpe=delta_rpe,
                    empty_cells=board.empty_cells,
                    terminal=False,
                    trauma_triggered=False,
                )
                anxiety_trajectory.append(v.anxiety)

                snapshot = AffectSnapshot(
                    valence=v.valence,
                    arousal=v.arousal,
                    dopamine=v.dopamine,
                    frustration=v.frustration,
                    anxiety=v.anxiety,
                    confidence=v.confidence,
                )
                memory.write_move(
                    board_before=prev_board,
                    board_after=board,
                    action=prev_decision.action,
                    score_delta=score_delta,
                    rpe=delta_rpe,
                    importance=1,
                    source_reasoning=prev_decision.reasoning,
                    affect=snapshot,
                )

            prev_board = board
            prev_decision = decision

        # End-of-trial reflection. run_reflection is synchronous; failure is
        # non-blocking — the per-move trajectory is the load-bearing measurement.
        try:
            run_reflection(
                llm=reflection_llm,
                last_30_moves_summary="cliff-test trial completed",
                prior_lessons=[],
            )
            cost_usd += _carla_call_cost_estimate("reflection")
        except Exception:  # noqa: BLE001
            pass

    # Derive termination state from trajectory + sim state.
    threshold_met = _check_anxiety_threshold(anxiety_trajectory)
    t_predicts = _first_threshold_index(anxiety_trajectory)
    if abort_reason is not None:
        is_right_censored = False
    else:
        is_right_censored = (move_index == MAX_MOVES - 1) and not is_game_over(io.read_board())

    return CarlaTrialResult(
        scenario_id=scenario.id,
        trial_index=trial_index,
        final_move_index=move_index,
        cost_usd=cost_usd,
        abort_reason=abort_reason,
        anxiety_trajectory=anxiety_trajectory,
        t_predicts=t_predicts,
        anxiety_threshold_met=threshold_met,
        is_right_censored=is_right_censored,
    )


def _carla_call_cost_estimate(mode: str) -> float:
    """Per-Carla-call USD estimate.

    Spec §2.6: ~$0.11/trial total = (50 react × X) + (8 ToT × Y) + (1 reflection × Z).
    Coarse placeholder; analyze_results.py recomputes from JSONL telemetry.
    """
    if mode == "tot":
        return 0.005  # ToT bursts dominate cost
    if mode == "reflection":
        return 0.01  # Sonnet reflection is the largest single call
    return 0.001  # React (Flash) per move


DEFAULT_CONCURRENCY: Final[int] = 8


async def _worker(
    *,
    pair: tuple[Scenario, int],
    semaphore: asyncio.Semaphore,
    budget: _BudgetState,
    csv_path: Path,
    output_dir: Path,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bot_llm: LLM,
) -> None:
    """Run one paired (scenario, trial_index) trial under the semaphore.

    Both arms run concurrently inside the pair via asyncio.gather. Hard-cap
    pre-check happens BEFORE any LLM call. Writes both CSV rows on completion.
    Per spec §2.2 + §4.3.
    """
    scenario, trial_index = pair
    async with semaphore:
        # Hard-cap pre-LLM gate (per spec §2.3). Check either arm; both share
        # the same scenario envelope so a hit on either means skip the pair.
        if budget.hard_cap_hit(scenario.id, "carla") or budget.hard_cap_hit(scenario.id, "bot"):
            return  # caller observes via budget and exits with code 3

        # Build per-trial buses (one per arm — per spec §2.7 "one JSONL file per trial").
        carla_jsonl = output_dir / f"events_{scenario.id}_carla_{trial_index}.jsonl"
        bot_jsonl = output_dir / f"events_{scenario.id}_bot_{trial_index}.jsonl"
        carla_bus = RecordingEventBus(host="127.0.0.1", port=0, path=carla_jsonl)
        bot_bus = RecordingEventBus(host="127.0.0.1", port=0, path=bot_jsonl)

        try:
            carla_result, bot_result = await asyncio.gather(
                _run_carla_trial(
                    scenario=scenario,
                    trial_index=trial_index,
                    decision_llm=decision_llm,
                    tot_llm=tot_llm,
                    reflection_llm=reflection_llm,
                    bus=carla_bus,
                ),
                _run_bot_trial(
                    scenario=scenario,
                    trial_index=trial_index,
                    llm=bot_llm,
                    bus=bot_bus,
                ),
            )
        finally:
            await carla_bus.stop()
            await bot_bus.stop()

        budget.add(scenario.id, "carla", carla_result.cost_usd)
        budget.add(scenario.id, "bot", bot_result.cost_usd)

        _append_csv_row(
            csv_path,
            scenario_id=scenario.id,
            trial_index=trial_index,
            arm="carla",
            t_predicts=carla_result.t_predicts,
            t_baseline_fails=None,
            cost_usd=round(carla_result.cost_usd, 6),
            abort_reason=carla_result.abort_reason,
            anxiety_threshold_met=carla_result.anxiety_threshold_met,
            final_move_index=carla_result.final_move_index,
            is_right_censored=carla_result.is_right_censored,
        )
        _append_csv_row(
            csv_path,
            scenario_id=scenario.id,
            trial_index=trial_index,
            arm="bot",
            t_predicts=None,
            t_baseline_fails=bot_result.t_baseline_fails,
            cost_usd=round(bot_result.cost_usd, 6),
            abort_reason=bot_result.abort_reason,
            anxiety_threshold_met=None,
            final_move_index=bot_result.final_move_index,
            is_right_censored=bot_result.is_right_censored,
        )


async def run_cliff_test(
    *,
    scenarios: list[Scenario],
    n: int,
    output_dir: Path,
    concurrency: int = DEFAULT_CONCURRENCY,
    pilot: bool = False,
    force: bool = False,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bot_llm: LLM,
    _budget_for_test: _BudgetState | None = None,
) -> int:
    """Top-level cliff-test orchestrator. Returns an exit code:

    - EXIT_OK (0): all pairs ran, no cap hit.
    - EXIT_SOFT_CAP (2): soft cap hit; drained in-flight; partial CSV written.
    - EXIT_HARD_CAP (3): hard cap hit; some trials never started.

    Raises FileExistsError if the target subdirectory exists, is non-empty,
    and ``force`` is False.

    ``_budget_for_test`` is a deliberate test seam for cap-halt tests. Production
    callers must not pass it; it exists only to pre-load budget state in tests.
    """
    subdir = output_dir / ("pilot_results" if pilot else "results")
    if subdir.exists() and any(subdir.iterdir()) and not force:
        raise FileExistsError(f"output subdir {subdir} is non-empty; pass force=True to overwrite")
    subdir.mkdir(parents=True, exist_ok=True)
    csv_path = subdir / "cliff_test_results.csv"

    budget = _budget_for_test if _budget_for_test is not None else _BudgetState()
    semaphore = asyncio.Semaphore(concurrency)

    # Pair queue: scheduling is round-robin across scenarios so soft-cap halt
    # affects all scenarios uniformly rather than running scenario A to
    # completion first.
    queue: list[tuple[Scenario, int]] = []
    for trial_index in range(n):
        for scenario in scenarios:
            queue.append((scenario, trial_index))

    soft_cap_observed = False
    hard_cap_observed = False
    in_flight: list[asyncio.Task[None]] = []

    for pair in queue:
        scenario, _ = pair
        # Hard-cap halt: do not start new workers; existing in-flight will see
        # the same condition on their pre-check and self-skip.
        if budget.hard_cap_hit(scenario.id, "carla") or budget.hard_cap_hit(scenario.id, "bot"):
            hard_cap_observed = True
            continue
        # Soft-cap halt: stop dequeuing new pairs (in-flight finish).
        if budget.soft_cap_hit(scenario.id, "carla") or budget.soft_cap_hit(scenario.id, "bot"):
            soft_cap_observed = True
            continue
        task: asyncio.Task[None] = asyncio.create_task(
            _worker(
                pair=pair,
                semaphore=semaphore,
                budget=budget,
                csv_path=csv_path,
                output_dir=subdir,
                decision_llm=decision_llm,
                tot_llm=tot_llm,
                reflection_llm=reflection_llm,
                bot_llm=bot_llm,
            )
        )
        in_flight.append(task)

        # Drain completed tasks to keep in_flight bounded to ``concurrency``.
        # Draining here lets the budget state update between dequeue steps so
        # that the soft-cap check at the top of this loop fires as soon as a
        # worker's spend tips the budget over the cap — rather than after all
        # pairs have been dispatched. This is the mechanism that makes "drain
        # in-flight, then stop dequeuing" work correctly when concurrency < n.
        while len(in_flight) >= concurrency:
            done, pending = await asyncio.wait(in_flight, return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                t.result()  # re-raises any exception (matches return_exceptions=False)
            in_flight = list(pending)

    if in_flight:
        await asyncio.gather(*in_flight, return_exceptions=False)

    # Re-check caps after drain — workers may have lifted spend past either cap.
    final_hard = any(budget.hard_cap_hit(s.id, arm) for s in scenarios for arm in ("carla", "bot"))
    final_soft = any(budget.soft_cap_hit(s.id, arm) for s in scenarios for arm in ("carla", "bot"))

    if hard_cap_observed or final_hard:
        return EXIT_HARD_CAP
    if soft_cap_observed or final_soft:
        return EXIT_SOFT_CAP
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cliff-test",
        description=(
            "Phase 0.7 cliff-test runner: paired Carla/Bot trials per scenario. "
            "Data collector only — does not compute pass/fail verdicts."
        ),
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario id (e.g. 'snake-collapse-128') or 'all' for every cliff-test scenario.",
    )
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        help="Number of paired trials per scenario.",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Pilot mode — output to pilot_results/ subdirectory instead of results/.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Max in-flight paired trials. Default 8.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory root. Default runs/<UTC-iso-timestamp>/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty output directory.",
    )
    return parser


def _check_tier() -> str | None:
    """Validate NOVA_TIER env var. Returns the tier string if OK, else None."""
    import os

    tier = os.environ.get("NOVA_TIER", "").strip()
    if tier not in _ALLOWED_TIERS:
        return None
    return tier


# Per spec §6.2: the three falsification scenarios (excludes the
# fresh-start placeholder which is not part of the pass/fail gate).
_CLIFF_TEST_SCENARIOS: Final[tuple[str, ...]] = (
    "snake-collapse-128",
    "512-wall",
    "corner-abandonment-256",
)


def _resolve_scenarios(arg: str) -> list[Scenario]:
    """Expand '--scenario all' to the three cliff-test scenarios, or look up a single id."""
    from nova_agent.lab.scenarios import SCENARIOS, load as load_scenario

    if arg == "all":
        return [SCENARIOS[s] for s in _CLIFF_TEST_SCENARIOS]
    return [load_scenario(arg)]


def _default_output_dir() -> Path:
    """Returns runs/<UTC-iso-timestamp>/."""
    from datetime import datetime, timezone

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return Path("runs") / ts


def _build_llms() -> tuple[LLM, LLM, LLM, LLM]:
    """Construct the four LLMs the runner needs via tier-resolved model names.

    Roles per nova_agent.llm.tiers.TierConfig:
      decision  — Carla react path + Baseline Bot (same family per Bot spec §2.4)
      tot       — Carla Tree-of-Thoughts deliberation
      reflection — Carla post-game reflection

    model_for(role) reads NOVA_TIER from the environment (set by _check_tier
    before this call). google_api_key and anthropic_api_key are plain str on
    Settings (not SecretStr). Settings.daily_budget_usd is the cap field
    (not daily_cap_usd — adapted from plan draft per actual Settings shape).
    """
    from nova_agent.config import get_settings
    from nova_agent.llm import tiers as model_tiers
    from nova_agent.llm.factory import build_llm

    settings = get_settings()
    # model_for() returns str | int (TierConfig includes int fields like
    # tot_branches); cast to str — the string roles (decision/tot/reflection)
    # are always str in every tier, and build_llm requires str.
    decision_model = str(model_tiers.model_for("decision"))
    tot_model = str(model_tiers.model_for("tot"))
    reflection_model = str(model_tiers.model_for("reflection"))

    google_api_key = settings.google_api_key
    anthropic_api_key = settings.anthropic_api_key
    daily_cap_usd = settings.daily_budget_usd

    return (
        build_llm(
            model=decision_model,
            google_api_key=google_api_key,
            anthropic_api_key=anthropic_api_key,
            daily_cap_usd=daily_cap_usd,
        ),
        build_llm(
            model=tot_model,
            google_api_key=google_api_key,
            anthropic_api_key=anthropic_api_key,
            daily_cap_usd=daily_cap_usd,
        ),
        build_llm(
            model=reflection_model,
            google_api_key=google_api_key,
            anthropic_api_key=anthropic_api_key,
            daily_cap_usd=daily_cap_usd,
        ),
        build_llm(
            model=decision_model,
            google_api_key=google_api_key,
            anthropic_api_key=anthropic_api_key,
            daily_cap_usd=daily_cap_usd,
        ),  # bot — same family as decision per Bot spec §2.4
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    tier = _check_tier()
    if tier is None:
        print(
            f"error: NOVA_TIER must be one of {sorted(_ALLOWED_TIERS)} "
            "(dev/plumbing tiers downgrade cognitive-judgment models — see ADR-0006).",
            file=sys.stderr,
        )
        sys.exit(EXIT_TIER_REFUSED)

    scenarios = _resolve_scenarios(args.scenario)
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    decision_llm, tot_llm, reflection_llm, bot_llm = _build_llms()

    code = asyncio.run(
        run_cliff_test(
            scenarios=scenarios,
            n=args.n,
            output_dir=output_dir,
            concurrency=args.concurrency,
            pilot=args.pilot,
            force=args.force,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bot_llm=bot_llm,
        )
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
