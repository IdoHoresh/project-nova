# Phase 0.7 Test Runner — Design Spec

**Status:** Draft (awaiting user review)
**Date:** 2026-05-05
**Author:** ihoresh07@gmail.com (solo founder), with red-team review applied through six rounds
**Companion artifacts:**

- `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md` — consumes §5 measurement contract
- `docs/superpowers/specs/2026-05-05-baseline-bot-design.md` — consumes §3.4 telemetry contract + §4 cost-cap envelope handoff
- `docs/decisions/0007-blind-control-group-for-cliff-test.md` — Amendment 1 (this spec inherits Q1–Q6 pinned decisions)

---

## 1. Context

The Phase 0.7 cliff test is a falsification gate (per ADR-0005, methodology
§4.1) measuring whether the cognitive architecture predicts cliffs before
failure or merely narrates them after. The cliff-test scenarios spec
(§5) defined the per-trial measurement contract and per-scenario
aggregation rules; the Baseline Bot spec (§3.4 + §4) defined the Bot's
telemetry events and the cost-cap envelope handoff. Both deferred the
runner that orchestrates trials and writes raw results to this spec.

This spec ratifies six load-bearing decisions for the runner. Each
survived a red-team round; the rationale lives in the conversation
transcript and committed `LESSONS.md` entries; the durable contract
is here.

The runner's responsibility is **data collection only.** Aggregate
statistics, mean-Δ computation, prediction-validity %, and the
cliff-test pass/fail verdict are explicitly out of scope. Those live
in a downstream `analyze_results.py` script (separate spec, not
required for the runner to be useful).

## 2. Pinned decisions (six rounds of red-team review)

### 2.1 Scope — Phase 0.7 only, no abstractions (Q1)

The runner is a concrete orchestrator for the Phase 0.7 cliff test:
two arms (Casual Carla + Baseline Bot), three scenarios, N=20 paired
trials per scenario per arm. **No `Arm` Protocol, no `Decider`
abstraction, no `Trial` factory** — the runner imports `ReactDecider`
(Carla's existing decision path) and `BaselineDecider` (the
just-shipped Bot) directly.

**Reasoning preserved.** Phase 0.7 is a falsification gate. Phase 0.8
(trauma-ablation hypothesis) is contingent on Phase 0.7 passing, and
its agent-instantiation shape is undefined today (flag? subclass?
prompt override?). Designing a seam for an undefined object is
premature optimization; copy-and-modify when Phase 0.8 arrives is
~1–2 hours of well-understood code, weighed against an unbounded risk
of designing the wrong seam. If the runner's TDD discipline naturally
produces a per-trial helper function shared between arms, that is
incidental refactoring — not pre-planned abstraction — and does not
belong in this spec.

### 2.2 Parallelism — paired-trial unit-of-concurrency (Q2)

Trials are scheduled in **paired units** `(scenario, trial_index)`,
not as independent arm-trials. A worker function takes one pair,
runs both Carla and Bot trials for the same `seed_base + trial_index`
concurrently within the pair (via `asyncio.gather` of two trial
coroutines), and writes their per-trial CSV rows on completion.
Pairs drain from a queue gated by `asyncio.Semaphore(concurrency_cap)`
with `concurrency_cap = 8` as the default (configurable).

**Reasoning preserved.** Pair-as-unit is a code-clarity win: paired
bookkeeping (seed alignment, telemetry tagging, paired-discard
detection per Bot spec §2.6) is natural at scheduling level rather
than reconstructed at aggregation time. The "wasted Bot tokens on
Carla abort" cost the red team initially flagged is in fact ~$2–3 over
the entire cliff test (Bot abort rate <2%, Carla 3–5%, see Q5 math) —
not the load-bearing motivation. Cleanliness is.

Concurrency cap = 8 is a default chosen to:

- keep wall-clock time under ~30 minutes at expected production-tier latency
- stay under provider-side rate limits (Anthropic Sonnet + Gemini Pro have generous per-key concurrency at our usage volume)
- bound peak in-flight LLM spend for the two-tier cap (§2.3)

**Telemetry under concurrency:** the existing `RecordingEventBus`
(`nova_agent/bus/recorder.py`) writes one event per line to JSONL with
no event ordering guarantee across concurrent publishers. Each event
emitted from the runner OR from Carla/Bot during a trial is tagged
with `(scenario_id, trial_index, arm)` so post-hoc filtering is
deterministic. The runner is responsible for ensuring every
publish-site (its own emits + the deciders' emits) carries the
correlation tuple.

### 2.3 Two-tier cost cap (Q2 sub-decision, Q5)

Two cap thresholds gate spend, both checked **per-trial** (not
per-move):

- **Soft cap** = `BUDGET_PER_SCENARIO_ARM_USD` (per Q5: $5 symmetric).
  When cumulative spend on `(scenario, arm)` reaches this, the
  runner stops dequeuing new pairs for that scenario. In-flight pairs
  drain to completion. After all in-flight complete, runner exits with
  `exit code 2` (soft-cap halt).
- **Hard cap** = `BUDGET_PER_SCENARIO_ARM_USD × 1.3 = $6.50`. Each
  worker checks the hard cap *before* invoking any LLM call for a new
  trial. If hit, the trial does not start; runner exits with
  `exit code 3` (hard-cap kill). The hard cap exists to protect
  against runaway in-flight spend amplification when cap=8 in-flight
  trials are mid-burst (see Q2 reasoning).

**No per-move polling.** Per-trial gating avoids lock contention on a
shared budget counter and avoids the "trial killed mid-burst, partial
telemetry" failure mode. Worst-case overshoot of soft cap = peak
in-flight × max-per-trial cost = 8 × ~$0.11 (Carla) ≈ **$0.88**, well
under the $1.50 hard-cap headroom.

Cost is computed per-trial from the `prompt_tokens + completion_tokens`
fields on the `bot_call_success` events (Bot) and analogous
telemetry events on Carla's path (Anthropic SDK usage objects). The
runner maintains a per-`(scenario, arm)` running total in memory.

### 2.4 Anxiety sampling (Q3)

Carla's `Anxiety > 0.6` (per scenarios spec §2.7) is sampled
**post-decision, raw, once per move**, and read directly from the
`AffectVector` returned by `affect.update(...)` inside the runner's
per-trial Carla loop:

```python
v = affect.update(
    rpe=delta_rpe,
    empty_cells=board.empty_cells,
    terminal=False,
    trauma_triggered=trauma_triggered,
)
anxiety_trajectory.append(v.anxiety)
# downstream §2.7 threshold check happens at trial-end against the
# full trajectory, not in-line during the loop
```

**No bus subscription.** The existing `EventBus.publish`
(`nova_agent/bus/websocket.py:52-59`) is WebSocket-broadcast-only and
silently drops events when no client is connected. The cliff test runs
headless at `NOVA_TIER=production`; using bus subscription for
measurement would either lose every event or require building a new
in-process subscriber pattern that doesn't exist. The
return-value-capture path is strictly simpler: the runner already owns
the per-move loop and already invokes `affect.update()`, so capturing
`v.anxiety` is one assignment.

The bus continues to publish `affect` events for observability
(brain-panel inspection during pilot calibration; JSONL persistence
via `RecordingEventBus` for post-hoc debugging). Bus = observability
channel; return-value capture = measurement channel. Cleanly
orthogonal.

**Smoothing:** none. The methodology threshold (`> 0.6`) was
calibrated against raw deployed Carla anxiety; runner-side smoothing
would re-tune the threshold and break compatibility with §2.7 as
written. The affect coordinator already manages temporal accumulation
and decay internally; that IS the dynamics layer.

**Per-trial threshold check** (the §2.7 "≥ 2 consecutive moves above
threshold" rule) is computed at trial end from the buffered trajectory
list, not in-line. The runner emits a single `anxiety_threshold_met`
boolean column to the per-trial CSV row (§2.7).

### 2.5 Per-trial memory reset (Q4)

Carla's `MemoryCoordinator` is reset per trial by constructing a fresh
instance against a fresh `tempfile.TemporaryDirectory()`:

```python
with tempfile.TemporaryDirectory(prefix=f"nova-cliff-{scenario_id}-{i}-") as tmp:
    sqlite_path = Path(tmp) / "episodic.db"
    lance_path = Path(tmp) / "vector.lance"
    memory = MemoryCoordinator(sqlite_path=sqlite_path, lancedb_path=lance_path)
    # ... run Carla trial ...
# tempdir auto-removed on context exit, including on exception/abort
```

**Reasoning preserved.** Filesystem-level isolation honors scenarios
spec §2.6's i.i.d. assumption (each trial starts from empty episodic +
empty vector + empty affect baseline). `TemporaryDirectory()` handles
abort cleanup deterministically — paired-discard logic does not
require special teardown code. Tempdirs land on macOS local SSD
(`$TMPDIR`); at 8 concurrent × small DB writes per trial, IO is
negligible.

Bot has no memory per ADR-0007 — no symmetric tempdir needed.

### 2.6 Cost-cap envelope figures (Q5)

`BUDGET_PER_SCENARIO_ARM_USD = $5`, **symmetric across arms.**

Calibrated cost expectations (production tier per ADR-0006: decision
= Flash, ToT = Pro, reflection = Sonnet):

- Carla per trial: ~$0.11 (50 Flash decisions + ~8 Pro ToT bursts × 4
  branches + 1 Sonnet reflection)
- Bot per trial: ~$0.005 (50 Flash one-shots, no ToT, no reflection)
- Carla per scenario (N=20): ~$2.20 (44% of envelope)
- Bot per scenario (N=20): ~$0.10 (2% of envelope)

Total cliff-test hard floor: **3 scenarios × $5/arm × 2 arms = $30.**

The asymmetry between Carla and Bot per-arm spend is structural
(bundle vs one-shot per Bot spec §2.2). The envelope is symmetric on
methodology-defense grounds: a single budget figure across both arms
preempts the "control group got 1/Nth the compute budget" hostile-
reviewer bullet. The Bot envelope's headroom is intentional and
documented; the methodology paper will note observed-vs-cap spend per
arm.

**No automatic tier-downgrade.** When the cap is hit, the runner halts
(per §2.3). The operator decides whether to re-run at a lower
`NOVA_TIER`. **If a tier change is made, the entire suite re-runs at
the new tier** — no mixing tiers across scenarios in one cliff test
run. The "symmetric tier" language in Bot spec §4 is a guard against
asymmetric tier abuse, not a directive to auto-downgrade. Mixed-tier
results are not comparable across scenarios; methodology paper would
have to caveat per-scenario which tier ran. Hostile-reviewer-shred
risk; not worth the operational convenience.

### 2.7 Output artifacts (Q6 — collector, not analyzer)

The runner produces two artifacts and **only two**:

1. **`cliff_test_results.csv`** — flat row per trial, appended
   immediately after each trial completes. Columns:

   | column | type | source |
   |---|---|---|
   | `scenario_id` | str | scenario being run |
   | `trial_index` | int | 0..19 |
   | `arm` | str | "carla" \| "bot" |
   | `t_predicts` | int \| null | first move index where Anxiety > 0.6 for ≥ 2 consecutive moves (Carla only; null for Bot) |
   | `t_baseline_fails` | int \| null | move index where `is_game_over() == True` (Bot only; for right-censored Bot trials, set to `MAX_MOVES = 50` per scenarios spec §5.1's right-censor sentinel rule, with `is_right_censored=True`. Null for Carla rows.) |
   | `cost_usd` | float | sum of token costs for this trial's LLM calls |
   | `abort_reason` | str \| null | `"api_error"` \| `"parse_failure"` \| null |
   | `anxiety_threshold_met` | bool \| null | derived: did this Carla trial satisfy §2.7? null for Bot |
   | `final_move_index` | int | move count when trial ended (game-over OR MAX_MOVES) |
   | `is_right_censored` | bool | `final_move_index == MAX_MOVES` |

   **Append-on-trial-completion** = crash-resilient; an interrupted run
   loses only the in-flight trials.

2. **`events_<scenario>_<arm>_<trial>.jsonl`** — one file per trial,
   produced by `RecordingEventBus`. Carries the full event stream
   (Carla affect trajectory, ToT branches, memory writes, Bot
   telemetry events per Bot spec §3.4, runner-emitted per-trial
   metadata). Source-of-truth for any field not summarised in the CSV.

**Out of runner scope:**

- Mean Δ computation, prediction-validity %, scenario-level pass/fail,
  cliff-test top-level verdict — all live in `analyze_results.py` (a
  separate spec, deferred). The runner does not compute cross-trial
  statistics. Per-trial derived flags (e.g., `anxiety_threshold_met`)
  are observations on a single trial, not aggregations, and are
  acceptable in the runner output.
- Plotting, dashboards, methodology-paper LaTeX export.
- Pilot calibration verdict ("does this scenario need re-authoring?")
  — operator inspects the CSV/JSONL by hand and decides.

This boundary is load-bearing: methodology evolution (e.g., switching
the prediction-validity threshold from `> 0.6` to `> 0.55`, or adopting
a Wilcoxon paired-rank test instead of paired-mean Δ) must require
zero changes to the runner code.

### 2.8 Pilot mode and CLI (Q6 sub-decisions)

**Pilot mode** uses the same code path as the real run, gated by a
`--pilot --n=<N>` flag:

- Output writes to `pilot_results/` subdirectory (separate from real
  `results/`)
- Halt-on-cap behavior unchanged (cap still applies; pilot at N=5
  across 3 scenarios × 2 arms is expected to use ~$1.73 total,
  well under the per-scenario per-arm $5 cap, so the cap is rarely
  exercised)
- Used for scenarios spec §7.4 calibration (5 trials per scenario,
  inspect game-over distribution against `expected_cliff_window`,
  re-author scenarios that fall outside)

Pilot is not a different command — same `cliff-test` entry, different
flags. This makes pilot exercise the identical orchestration code as
the real run, catching integration bugs at low cost.

**CLI surface** (per `pyproject.toml` `[project.scripts]`):

```toml
[project.scripts]
cliff-test = "nova_agent.lab.cliff_test:main"
```

Usage:

```bash
uv run cliff-test --scenario all --n 20                  # real run, all 3 scenarios
uv run cliff-test --scenario snake-collapse-128 --n 5 --pilot  # pilot, one scenario
uv run cliff-test --scenario all --n 20 --concurrency 4  # halve in-flight cap
uv run cliff-test --scenario all --n 20 --output-dir runs/2026-05-06  # explicit output
```

Required env: `NOVA_TIER=production` (or `=demo`; runner refuses to
run at `dev` or `plumbing` tiers because those tiers downgrade
cognitive-judgment models — see ADR-0006 §"Tier discipline").

## 3. Runner architecture

A single async orchestrator script: `nova_agent/lab/cliff_test.py`.

Module shape (no class hierarchy needed at this scope):

```
cliff_test.py
├── main() -> None                                  # CLI entry, argparse, dispatches
├── async run_cliff_test(...)                       # top-level coroutine: queue + semaphore
├── async _worker(pair: tuple[Scenario, int], ...)  # one paired trial
├── async _run_carla_trial(scenario, i, ...)        # Carla path (composes ReactDecider + ToT + reflection + MemoryCoordinator with tempdir)
├── async _run_bot_trial(scenario, i, ...)          # Bot path (composes BaselineDecider + tie-break)
├── _check_anxiety_threshold(trajectory: list[float]) -> bool   # §2.7 ≥-2-consecutive check
├── _append_csv_row(...)                            # crash-resilient append
└── _budget_state                                   # per-(scenario, arm) running spend tracking
```

Per-trial helpers `_run_carla_trial` and `_run_bot_trial` may share
implementation details (e.g., the per-move loop body), but the spec
does not pre-commit to a specific extraction pattern — TDD will
produce the natural shape during implementation.

## 4. Per-trial protocol

### 4.1 Carla trial

```python
async def _run_carla_trial(scenario, trial_index, *, llm, tot_llm, reflection_llm, bus, csv_path):
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    affect = AffectCoordinator()
    arbiter = Arbiter()
    react = ReactDecider(llm=llm, ...)
    tot = ToTDecider(llm=tot_llm, ...)
    reflection = ReflectionWriter(llm=reflection_llm, ...)

    with tempfile.TemporaryDirectory(prefix=f"nova-cliff-{scenario.id}-{trial_index}-") as tmp:
        memory = MemoryCoordinator(
            sqlite_path=Path(tmp) / "episodic.db",
            lancedb_path=Path(tmp) / "vector.lance",
        )
        anxiety_trajectory: list[float] = []
        cost_usd = 0.0
        prev_board = None
        prev_decision = None
        for move_index in range(MAX_MOVES):
            board = io.read_board()
            if move_index > 0:  # affect updates from move_index 1 onward (delta requires prev)
                v, delta_cost = await _step_carla(...)  # calls react/tot/reflection composition
                anxiety_trajectory.append(v.anxiety)
                cost_usd += delta_cost
                if sim.is_game_over():
                    break
            # ... apply decision, record events, update prev_board ...
        else:
            pass  # MAX_MOVES reached

        # End-of-trial reflection (writes to memory; not used in the affect trajectory)
        reflection_cost = await reflection.reflect(...)
        cost_usd += reflection_cost

        threshold_met = _check_anxiety_threshold(anxiety_trajectory)
        t_predicts = _first_threshold_index(anxiety_trajectory)  # int or None
        _append_csv_row(csv_path, scenario_id=scenario.id, trial_index=trial_index, arm="carla",
                        t_predicts=t_predicts, t_baseline_fails=None, cost_usd=cost_usd,
                        abort_reason=None, anxiety_threshold_met=threshold_met,
                        final_move_index=move_index, is_right_censored=(move_index == MAX_MOVES - 1))
```

(Pseudocode; exact composition with `Arbiter.should_use_tot()` etc.
follows existing `nova_agent/main.py:271-301` pattern.)

### 4.2 Bot trial

```python
async def _run_bot_trial(scenario, trial_index, *, llm, bus, csv_path):
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    decider = BaselineDecider(llm=llm, bus=bus)

    cost_usd = 0.0
    abort_reason: str | None = None
    for move_index in range(MAX_MOVES):
        board = io.read_board()
        result = await decider.decide(board=board, trial_index=trial_index, move_index=move_index)
        if isinstance(result, TrialAborted):
            abort_reason = result.reason
            break
        # tie-break per scenarios spec §2.3 if invalid move
        applied_direction = _apply_with_tiebreak(io, result.action, board)
        cost_usd += _trial_call_cost(...)  # from telemetry events
        if sim.is_game_over():
            break

    if abort_reason is not None:
        t_baseline_fails = None  # aborted trials don't contribute a fail-time
        is_right_censored = False
    elif sim.is_game_over():
        t_baseline_fails = move_index
        is_right_censored = False
    else:
        # right-censored at MAX_MOVES per scenarios spec §5.1
        t_baseline_fails = MAX_MOVES
        is_right_censored = True
    _append_csv_row(csv_path, scenario_id=scenario.id, trial_index=trial_index, arm="bot",
                    t_predicts=None, t_baseline_fails=t_baseline_fails, cost_usd=cost_usd,
                    abort_reason=abort_reason, anxiety_threshold_met=None,
                    final_move_index=move_index, is_right_censored=is_right_censored)
```

### 4.3 Paired worker

```python
async def _worker(pair, *, semaphore, ...):
    scenario, trial_index = pair
    async with semaphore:
        # Hard-cap pre-check (§2.3)
        if _budget_state.hard_cap_hit(scenario.id, "carla") or _budget_state.hard_cap_hit(scenario.id, "bot"):
            return  # caller observes via _budget_state and exits with code 3
        # Run both arms concurrently within the pair
        carla_result, bot_result = await asyncio.gather(
            _run_carla_trial(scenario, trial_index, ...),
            _run_bot_trial(scenario, trial_index, ...),
        )
        _budget_state.add(scenario.id, "carla", carla_result.cost_usd)
        _budget_state.add(scenario.id, "bot", bot_result.cost_usd)
```

## 5. Cross-spec dependencies

### 5.1 Consumes from `2026-05-05-cliff-test-scenarios-design.md`

- §3 — `Scenario` dataclass + `Scenario.seed(trial_index)` method.
- §4 — three concrete scenarios (`snake-collapse-128`, `512-wall`, `corner-abandonment-256`).
- §5.1 — per-trial protocol contract (per-trial `MemoryCoordinator` reset, `MAX_MOVES = 50` cap).
- §2.7 — measurement contract (`Anxiety > 0.6` for ≥ 2 consecutive moves).
- §2.8 — termination cap and right-censoring rule.

### 5.2 Consumes from `2026-05-05-baseline-bot-design.md`

- §3.4 — telemetry contract (5 Bot event types: `bot_call_attempt`, `bot_call_success`, `bot_call_api_error`, `bot_call_parse_failure`, `bot_invalid_move`, `bot_trial_aborted`).
- §4 — cost-cap envelope handoff (this spec sets `BUDGET_PER_SCENARIO_ARM_USD = $5` symmetric).
- §2.6 — paired-discard logic for test 2 (pair dropped if either arm aborts).
- §2.3 — RNG-discipline constraint + tie-break order (UP > RIGHT > DOWN > LEFT).

### 5.3 Composes existing modules

- `nova_agent/lab/sim.py` — `Game2048Sim`, `Scenario`.
- `nova_agent/lab/scenarios.py` — `SCENARIOS` dict, `MAX_MOVES`.
- `nova_agent/lab/io.py` — `SimGameIO`.
- `nova_agent/decision/react.py` — `ReactDecider` (Carla act-step).
- `nova_agent/decision/tot.py` — `ToTDecider` (Carla deliberation).
- `nova_agent/decision/arbiter.py` — `should_use_tot(board, affect)` trigger.
- `nova_agent/decision/baseline.py` — `BaselineDecider`, `BotDecision`, `TrialAborted`.
- `nova_agent/affect/coordinator.py` — `AffectCoordinator.update()`.
- `nova_agent/memory/coordinator.py` — `MemoryCoordinator` with file-path constructor.
- `nova_agent/reflection/writer.py` — `ReflectionWriter` (end-of-trial reflection).
- `nova_agent/bus/recorder.py` — `RecordingEventBus` (JSONL + WebSocket).

## 6. Operational constraints

### 6.1 Required environment

- `NOVA_TIER=production` (or `=demo`). Runner refuses `dev` and
  `plumbing` because those tiers downgrade cognitive-judgment models.
- `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` populated (via `.env`; loaded
  through `Settings` with `env_ignore_empty=True`).
- `UV_PROJECT_ENVIRONMENT` set per nova-agent README (gotcha #1).
- ADB / emulator NOT required — runner runs entirely on `Game2048Sim`.

### 6.2 Output directory contract

- Default: `runs/<UTC-iso-timestamp>/`
- Real-run subdirectory: `results/`
- Pilot subdirectory: `pilot_results/`
- `cliff_test_results.csv` at the subdirectory root.
- One JSONL file per trial: `events_<scenario>_<arm>_<i>.jsonl`.
- Runner refuses to overwrite an existing non-empty results directory
  without an explicit `--force` flag.

### 6.3 Halt protocol exit codes

| code | meaning |
|---|---|
| 0 | All scenarios completed within envelope; CSV+JSONL written. |
| 2 | Soft cap hit; in-flight trials drained; partial results written; operator may re-run with adjusted envelope or accept partial. |
| 3 | Hard cap hit; in-flight trials killed before LLM invocation; partial results written. |
| other | Unexpected fatal error (e.g., LLM provider auth failure); stack trace logged. |

Note: the ">2 paired-aborts → scenario broken" rule (Bot spec §2.6) is a methodology threshold, not a runner concern. The runner records every trial's `abort_reason` to CSV unconditionally; the downstream `analyze_results.py` enforces the threshold and surfaces the scenario-broken signal. This keeps the SoC boundary clean (per §2.7 — runner does not compute cross-trial aggregations).

A wrapper script or CI job branches on exit code to decide re-run /
abort / proceed-to-analysis.

## 7. Testing — what the implementation plan must cover

### 7.1 Unit tests on per-trial helpers

- `test_check_anxiety_threshold_no_breach`: trajectory all 0.4 → returns `False`, `t_predicts = None`.
- `test_check_anxiety_threshold_single_spike`: trajectory `[0.4, 0.4, 0.7, 0.4, 0.4]` → returns `False` (one move above, not two consecutive).
- `test_check_anxiety_threshold_pair`: `[0.4, 0.7, 0.65, 0.4]` → returns `True`, `t_predicts = 1`.
- `test_check_anxiety_threshold_late_pair`: `[0.4, 0.4, 0.4, 0.7, 0.7]` → returns `True`, `t_predicts = 3`.
- `test_apply_with_tiebreak_invalid_move`: scenario where LLM-chosen direction is no-op; tie-break order UP > RIGHT > DOWN > LEFT applied; emit `bot_invalid_move` telemetry.

### 7.2 Unit tests on budget-state tracker

- `test_budget_state_soft_cap_exact`: spend exactly $5 on (scenario_id, "carla") → soft cap returns `True`.
- `test_budget_state_hard_cap`: spend $6.50 → hard cap returns `True`.
- `test_budget_state_separate_arms`: $5 on Carla + $0 on Bot → Bot still under cap.
- `test_budget_state_separate_scenarios`: cap is per-scenario; spend on `scenario-a` does not affect `scenario-b`.

### 7.3 Unit tests on CSV writer

- `test_csv_append_writes_header_on_first_row`: empty file → first append writes header + row.
- `test_csv_append_no_duplicate_header`: existing file with header → next append writes only row.
- `test_csv_row_serialization_handles_nulls`: `t_predicts=None`, `abort_reason=None` serialize as empty strings (CSV null convention).

### 7.4 Integration tests with `MockLLM`

- `test_one_trial_carla_completes_without_error`: instantiate full Carla path on `snake-collapse-128`, single trial, MockLLM responses; assert CSV row written, anxiety_trajectory non-empty, no exceptions.
- `test_one_trial_bot_completes_without_error`: same for Bot path.
- `test_paired_trial_worker_runs_both_arms`: one paired trial; both arms run concurrently; both CSV rows written; tempdir cleaned up.
- `test_paired_trial_aborts_on_carla_failure`: MockLLM injects sustained failure on Carla; Carla aborts; Bot completes normally; CSV records both rows (Carla with `abort_reason="api_error"`, Bot succeeds); no orphaned tempdir.
- `test_pilot_mode_writes_to_pilot_subdir`: `--pilot --n=2`; output lands in `pilot_results/`, not `results/`.

### 7.5 Integration test on cap halt

- `test_soft_cap_drains_in_flight`: synthetic `_budget_state` pre-loaded near cap; runner dequeues one more pair, completes it, then exits code 2.
- `test_hard_cap_kills_pre_LLM`: synthetic spend at hard cap; worker invoked; aborts before any LLM call; exits code 3.

### 7.6 No production-tier LLM tests in unit suite

Unit tests use `MockLLM`. Production-tier runs (Anthropic + Gemini Pro)
are exercised only by:

- The pilot calibration runs (manual, scenarios spec §7.4).
- The actual cliff-test invocation (manual, gated by ADR-0006 cost
  discipline).

Neither participates in the standard `pytest` trio.

## 8. Out-of-scope

- **`analyze_results.py`** — separate spec, separate implementation. Consumes the runner's CSV + JSONL and computes mean Δ, paired-discard count, prediction-validity %, scenario pass/fail per scenarios spec §5.3, top-level cliff-test verdict per methodology §4.1.
- **Plotting / dashboards / LaTeX export** — analyst's tools; not part of either runner or analysis script.
- **Phase 0.8 trauma-ablation harness** — separate spec, separate runner if needed (per Q1 lock).
- **Distributed / multi-machine execution** — single-process, single-machine. Not needed at $30 cliff-test budget.
- **Resume from checkpoint** — partial CSV is read-by-pandas-friendly on its own; re-running re-executes from scratch at $30 budget.
- **Real-time progress UI** — operator watches structlog output. Brain panel inspection is for pilot calibration, not real-run UX.
- **Automatic re-run on transient failure** — operator decides per exit code.
- **Per-tier benchmarking** — runner refuses non-prod tiers; cross-tier comparison is a different experiment.
- **Heuristic Bot architecture** — rejected per Bot spec §2.1.

## 9. Open follow-ups

- **`analyze_results.py` spec.** This spec deliberately scopes it out; a follow-up spec defines the analysis contract (input: CSV + JSONL; output: pass/fail per §5.3 + per-scenario stats). Order: write the analysis spec after the runner ships and pilot calibration produces real CSV samples to design against.
- **`_RETRYABLE_API_EXCEPTIONS` audit.** Carried from Bot spec security review (MED #2): currently `(Exception,)` in `nova_agent/decision/baseline.py:64`. Narrow to provider-specific classes after auditing `nova_agent/llm/anthropic.py` + `nova_agent/llm/gemini.py`. Not Test Runner work, but the runner exercises this code path heavily, so the audit becomes more urgent once the runner ships.
- **Per-call cost extraction for Carla.** The Bot path emits `bot_call_success` with `prompt_tokens + completion_tokens` per Bot spec §3.4. Carla's existing call sites (react/tot/reflection) emit telemetry but the cost-extraction shape needs verification during implementation; if any Carla LLM caller doesn't surface usage, that telemetry adds during runner implementation.
- **`tempfile.TemporaryDirectory()` cleanup on hard interrupt.** Context manager handles SIGINT-derived `KeyboardInterrupt` cleanly via `__exit__`. Verify behavior under `kill -9` is acceptable (tempdir may leak; `$TMPDIR` cleanup is OS-managed).

## 10. References

- `docs/decisions/0001-cognitive-architecture-as-product-moat.md` — bundle-attribution scope rationale (Q1, Q5)
- `docs/decisions/0005-defer-v1-demo-until-phase-0.7.md` — Phase 0.7 as demo gate
- `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` — `NOVA_TIER` requirement (§6.1) + cost-cap structural rationale (§2.6)
- `docs/decisions/0007-blind-control-group-for-cliff-test.md` + Amendment 1 — two-arm design + Bot operational refinements
- `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` — GameIO contract the runner consumes via `SimGameIO`
- `docs/product/methodology.md` §4.1 — upstream measurement contract
- `docs/product/product-roadmap.md` Week 1 — schedule the cliff test runs against
- `docs/superpowers/specs/2026-05-04-game2048sim-design.md` — simulator spec
- `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md` — scenarios + measurement contract this runner implements
- `docs/superpowers/specs/2026-05-05-baseline-bot-design.md` — Bot operational + telemetry contract
- `LESSONS.md` — three brainstorm-rigor entries from this spec's authoring (numerical-claim verification, code-state verification, collector-vs-analyzer SoC)
- `nova_agent/lab/sim.py:38` — `Scenario` dataclass
- `nova_agent/lab/scenarios.py` — `SCENARIOS` + `MAX_MOVES`
- `nova_agent/lab/io.py` — `SimGameIO`
- `nova_agent/decision/baseline.py` — `BaselineDecider`
- `nova_agent/decision/react.py:18-22` — `_ReactOutput` schema (shared with Bot per Bot spec §2.4)
- `nova_agent/bus/recorder.py` — `RecordingEventBus` for JSONL persistence
- `nova_agent/bus/websocket.py:52-59` — `EventBus.publish` (verified WebSocket-broadcast-only, drives Q3 mechanism choice)
- `nova_agent/main.py:271-319` — existing per-move loop pattern Carla trial composes against
