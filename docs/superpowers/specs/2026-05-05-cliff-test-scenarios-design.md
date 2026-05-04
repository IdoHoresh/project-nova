# Phase 0.7 Cliff-Test Scenarios — Design Spec

**Status:** Draft (awaiting user review)
**Date:** 2026-05-05
**Author:** ihoresh07@gmail.com (solo founder), with red-team review applied through six rounds
**Supersedes:** the placeholder mention in `docs/superpowers/specs/2026-05-04-game2048sim-design.md` §Scenarios that deferred the 3-5 hard cliff-test scenarios to "a separate spec under Phase 0.7 prep"

---

## 1. Context

Phase 0.7 is the load-bearing falsification gate for Project Nova: it answers whether the cognitive architecture *predicts* a cliff before failure or merely *narrates* it after. The methodology specifies two arms (Casual Carla + Baseline Bot) running on **3-5 documented hard 2048 scenarios** under same-seeded board sequences, with the affect-earns-its-keep test (`Δ ≥ 2` moves in ≥ 3 of the 3-5 scenarios) as the load-bearing pass criterion. See methodology.md §4.1 and ADR-0007.

The Game2048Sim infrastructure is shipped (PR #5). It already supports a `Scenario` dataclass and a single placeholder `fresh-start` scenario. This spec resolves what the 3-5 scenarios are, what fields the `Scenario` dataclass needs, and what measurement contract the Test Runner must obey when evaluating Carla's affect trajectory and Bot's failure point against those scenarios.

This spec deliberately does **not** define the Test Runner itself or the Baseline Bot's internal architecture. Both are separate Phase 0.7 prep specs. The contract this spec defines is what each scenario provides to those components.

## 2. Pinned decisions (six rounds of red-team review)

The decision rationale is in the conversation transcript; the durable contract is here.

### 2.1 Initial board construction (Q1)

Each scenario specifies a **handcrafted near-cliff 4×4 grid**, not an empty grid driven into hardness by RNG. Reasons: maps to methodology phrasing ("documented community-catalogued patterns"); reproducibility for external review (a reviewer can read the grid in this spec without running the sim); cliff is in the board, not the spawn schedule.

**Illusion-of-Hope constraint** (red-team Q1): each board must offer **10-15 legal, seemingly-productive moves** of low-stakes maneuvering before catastrophic gridlock. A board that's already 3 moves from game-over makes Carla's `Anxiety` spike to 1.0 immediately and gives no slope to compare against the Baseline Bot. A board that's 30+ moves from gridlock dilutes the cliff signal.

**`expected_cliff_window` field** (red-team Q1): each scenario declares the move-index range (inclusive) at which gridlock is anticipated under typical play. Used as a calibration check during pilot runs — if the observed game-over distribution falls wildly outside this window, the scenario is mis-tuned and gets re-authored before the real N=20 trials run.

### 2.2 Same-seed-divergence resolution (Q2)

Each scenario declares a `seed_base: int`. For trial index `i ∈ [0, 19]`, the trial seed is computed as `seed_base + i`. **Carla trial `i` and Bot trial `i` use the same trial seed** — pairing is by trial index, not by scenario. This honors ADR-0007's "same seeded sequences" at the trial level: paired trials see the identical spawn schedule until their decisions diverge, after which `Game2048Sim`'s instance-level RNG (per `sim.py`) drives spawn divergence as the experimental signal.

`Δ` becomes a well-defined paired statistic: per-trial `Δ_i = t_baseline_fails(i) - t_carla_predicts(i)`, aggregated to a mean over the N=20 paired trials. This is preferable to mean-of-means because it preserves trial-level pairing variance.

### 2.3 RNG-discipline constraint (Q2 red team)

**No agent decision path may consume Python's global `random` module.** This protects the sim's spawn schedule from desync regardless of whether the Baseline Bot is LLM-based (per ADR-0007 as written) or heuristic (a possibility surfaced in red-team review). If the Baseline Bot's architecture eventually requires tie-breaking, it uses a fixed priority order (UP > RIGHT > DOWN > LEFT). Carla's stochasticity is bounded to LLM-API randomness, which is a separate stream from the sim's instance-level `random.Random(seed)` (see `sim.py:52`).

The sim already isolates its RNG via `self._rng = random.Random(seed)` in `Game2048Sim.__init__`, so even an undisciplined `random.choice` call from outside the sim could not pollute spawn schedules. The constraint is a defensive guard that protects against accidental coupling, not a correction to the sim.

### 2.4 Sourcing (Q3)

**Every scenario in this spec cites a public reference** for its underlying pattern. No Nova-defined fallback. If a pattern cannot be cited, it does not ship. Reasons: external review credibility is load-bearing; a reviewer who can argue "you cherry-picked scenarios where Carla wins" kills the entire pitch; community canon is rich enough; citation discipline forces honest cliff calibration against patterns real players hit.

### 2.5 Persona-calibrated magnitudes (Q4 red team)

**Scenario magnitudes are calibrated per-persona; pattern names are abstract.** Each scenario specifies a *pattern* (drawn from community canon) and an *instantiation magnitude* (the high-tile value present on the board). The pattern is what is cited; the magnitude tracks the persona's reachable play history. For Casual Carla, magnitudes stay within the 256-512 ceiling — the upper edge of where casual play actually arrives. For higher-skill personas added later (Strategic Sam, etc.), the same patterns instantiate at 1024+.

This reconciles the spec with methodology §4.1's "1024-wall" phrasing: §4.1 names the abstract pattern; this spec documents the Casual-Carla instantiation. No methodology amendment is required. Citations are honest about the adaptation: e.g., the 512-wall scenario says "pattern cited from <1024-wall source>; instantiated at 512 for Casual-Carla persona-fidelity."

### 2.6 Memory protocol across the N=20 trials (Q5)

**Carla's memory is wiped between trials.** Each trial begins with empty episodic and semantic memory; 20 trials per scenario produce 20 i.i.d. samples. Reasons: methodology §4.1 and ADR-0007 frame `t_carla_predicts` as a mean over N=20 with the implicit "≥80% of trials" frequency threshold; both presume i.i.d.; persistent memory introduces serial correlation that invalidates the variance estimate and the frequency threshold; symmetric with Bot (which has no memory by ADR-0007); memory's predictive contribution is the Phase 0.8 trauma-ablation hypothesis, not the Phase 0.7 cliff-prediction hypothesis.

Operationally this requires that the Test Runner instantiate a fresh `MemoryCoordinator` (or an in-memory ephemeral store) per trial. The Test Runner spec encodes this discipline.

### 2.7 Measurement contract for `t_carla_predicts` (Q5 red team)

**`t_carla_predicts(trial)` is defined as: the move index `i` such that Carla's `Anxiety > 0.6` on move `i` AND on move `i+1` (≥ 2 consecutive moves above threshold). If no such `i` exists in the trial, `t_carla_predicts(trial) = ∞`.**

The threshold `> 0.6` is preserved verbatim from methodology §4.1 and ADR-0007 — changing it would be a methodology amendment requiring its own ADR. The `≥ 2 consecutive moves` qualifier addresses red-team noise-immunity concern: a transient single-move spike to 0.61 followed by a return to 0.4 is a measurement artifact, not a prediction event. The qualifying pair's *first* move is the recorded prediction index, preserving the methodology's lead-time arithmetic. The `∞` sentinel formalizes methodology §4.1's "no early Anxiety peak" failure mode and excludes such trials from the `t_carla_predicts` mean while counting them against the ≥ 80% prediction-validity threshold.

### 2.8 Termination cap (Q6 red team)

**`MAX_MOVES = 50`**, enforced symmetrically on both arms. If a trial reaches 50 moves without `Game2048Sim.is_game_over()`, the trial is right-censored: `t_baseline_fails(trial) = 50` (sentinel) for Bot trials, and Carla trials similarly cap. Right-censored trials are recorded but flagged as scenario-invalidation evidence — if more than 2 of the N=20 Bot trials per scenario hit the cap, the scenario is fundamentally broken (the trap was escapable via greedy play) and gets re-authored before the real run.

Cap calibration: `expected_cliff_window` is at most ~15-20 moves; cap at 50 is ~3× the upper safety margin, well above realistic Δ propagation, and well below cost-runaway.

### 2.9 Authoring discipline for `initial_score` (Q6 red team)

The `initial_score` field on `Scenario` is **not new** — it already exists on the dataclass for `fresh-start` (set to `0`, coherent because the grid is empty). Setting it to `0` on a non-empty grid is incoherent state: Bot's "maximize score" prompt reasons against `score=0` while staring at a 512 tile; Casual Carla's affect signal lacks the calibration of "I have invested effort in this game."

**Canonical derivation: minimum-implied-score formula.** For any tile of value `V = 2^n` on `initial_grid`, the contribution to `initial_score` is `(n - 1) × V`. The total is the sum over all non-zero tiles:

```
initial_score = sum((log2(v) - 1) * v for v in grid_tiles if v > 0)
```

This is the floor — the score assuming every tile was built entirely from spawned-2s with no 4-spawn shortcuts and no off-merge-tree merges. Real game histories produce higher scores; the floor is acceptable because the cliff test does not depend on exact history, only on a *coherent* score Bot's prompt and Carla's affect can reason against.

**Enforced via `Scenario.__post_init__` validator.** The validator recomputes the formula from `initial_grid` and asserts equality with the supplied `initial_score`, raising `ValueError` on mismatch. Authors cannot ship scenarios with incoherent scores.

### 2.10 Format / where scenarios live (Q6)

**Scenarios are extended in `nova_agent/lab/scenarios.py`** as additional `Scenario(...)` literals in the `SCENARIOS` dict. No move to JSON/YAML at this scenario count. The `Scenario` dataclass already enforces JSON-serializability at the type level, so the data discipline is preserved. Migration to a data file becomes the right answer at ~10+ scenarios or when non-engineers (game designers) need to author scenarios — both out-of-scope for Phase 0.7.

## 3. The `Scenario` dataclass — required extensions

The current dataclass in `nova_agent/lab/sim.py`:

```python
@dataclass(frozen=True)
class Scenario:
    id: str
    initial_grid: list[list[int]]
    initial_score: int
    seed: int
```

The implementation plan extends it to:

```python
@dataclass(frozen=True)
class Scenario:
    id: str
    initial_grid: list[list[int]]
    initial_score: int
    seed_base: int                              # renamed from `seed`
    pattern_name: str                           # abstract pattern (e.g. "snake-collapse")
    high_tile_magnitude: int                    # the highest tile present on initial_grid
    expected_cliff_window: tuple[int, int]      # (min_move_index, max_move_index), inclusive
    source_citation: str                        # public-reference URL or descriptor

    def __post_init__(self) -> None:
        # 4×4 grid, non-negative, in-palette
        if len(self.initial_grid) != 4 or any(len(r) != 4 for r in self.initial_grid):
            raise ValueError(f"{self.id}: initial_grid must be 4x4")
        valid = {0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048}
        if any(v not in valid for r in self.initial_grid for v in r):
            raise ValueError(f"{self.id}: initial_grid contains out-of-palette tile")
        # initial_score equals minimum-implied-score
        from math import log2
        derived = sum(int((log2(v) - 1) * v) for r in self.initial_grid for v in r if v > 0)
        if self.initial_score != derived:
            raise ValueError(
                f"{self.id}: initial_score {self.initial_score} does not match "
                f"minimum-implied-score {derived} derived from initial_grid"
            )
        # high_tile_magnitude matches the grid's max
        max_tile = max((v for r in self.initial_grid for v in r), default=0)
        if self.high_tile_magnitude != max_tile:
            raise ValueError(
                f"{self.id}: high_tile_magnitude {self.high_tile_magnitude} does not match "
                f"grid max {max_tile}"
            )
        # cliff window is well-formed
        lo, hi = self.expected_cliff_window
        if not (0 < lo <= hi):
            raise ValueError(f"{self.id}: expected_cliff_window {self.expected_cliff_window} ill-formed")
```

The rename from `seed` to `seed_base` is breaking for the existing `fresh-start` scenario. The implementation plan must update `fresh-start` and any callers (currently `Game2048Sim.__init__` consumes `scenario.seed` indirectly through being passed a `seed: int` parameter, and `nova_agent/lab/io.py:SimGameIO` constructs the seed). The plan handles this rename explicitly.

For backward compatibility, the plan introduces a `Scenario.seed(trial_index: int) -> int` method returning `seed_base + trial_index`, and updates `SimGameIO` to accept a trial index and call this method.

## 4. The three scenarios

Each scenario instantiates a community-cited 2048 failure pattern at a Casual-Carla persona-fidelity magnitude. All grids satisfy the 4×4, non-negative, in-palette constraints. All `initial_score` values equal the minimum-implied-score derived from the grid. All `expected_cliff_window` ranges are within `[3, 30]` to satisfy the Illusion-of-Hope constraint with buffer for the `MAX_MOVES = 50` cap.

### 4.1 `snake-collapse-128`

```
[ 0,  0,  0,  2]
[ 4,  2,  4,  8]
[ 0,  4, 16, 32]
[ 2,  8, 64,128]
```

- `pattern_name`: `"snake-collapse"`
- `high_tile_magnitude`: `128`
- `initial_score`: `1308`
- `seed_base`: `20260505001` (chosen distinct per-scenario for traceability)
- `expected_cliff_window`: `(11, 16)`
- `source_citation`: 2048 strategy guides describing the snake formation and its collapse mode (e.g., the Hak.is "How to beat 2048" walkthrough; r/2048 community discussions of snake-stall failure). The implementation plan verifies and pins the specific URLs.

**Pattern rationale.** A casual player anchors the snake bottom-right with descending tiles `128 → 64 → 32 → 16 → 8 → 4 → 2`. The chain is ~80% intact on the bottom two rows. Empty cells in the upper-left admit ~10-12 moves of low-stakes filler-tile maneuvering — typical casual play tries to clean up the upper rows without disturbing the snake. Eventually, the misaligned `2` (bottom-left, breaking strict monotonicity) plus spawn pressure forces a swipe direction that disrupts the chain. Once the chain breaks, recovery from a 128-anchor snake is rare for casual play.

**Why magnitude 128 (not 256 or 512):** The "snake collapse" failure is most documented at the moment the player is **building** the snake, not after they've already maxed it. A casual player typically plateaus at 128-256 with a partial snake; a 512-anchored snake requires Strategic-Sam-tier discipline. 128 is the modal casual-snake magnitude.

### 4.2 `512-wall`

```
[ 0,  4,  8,  2]
[ 4,  8, 16, 32]
[ 8, 16, 32,128]
[256, 64,128,512]
```

- `pattern_name`: `"high-tile-wall"` (instantiating the 1024-wall pattern named in methodology §4.1 at the 512 magnitude)
- `high_tile_magnitude`: `512`
- `initial_score`: `8152`
- `seed_base`: `20260505002`
- `expected_cliff_window`: `(12, 17)`
- `source_citation`: strategy guides describing the wall pattern at 1024 (e.g., 2048 wiki "1024-wall" entry; speedrun community guides on stack-blocking failures). Spec adapts the cited 1024-wall pattern to 512 for Casual-Carla persona-fidelity per §2.5; the citation references the abstract pattern, the spec documents the magnitude adaptation explicitly.

**Pattern rationale.** The 512 is anchored bottom-right. The 256 needed to merge into 512 is far away (bottom-left), separated by an out-of-order `64 + 128` row middle. The supporting stack on row 3 (`8 + 16 + 32 + 128`) is itself disorganized — the 128 in row 3 cannot reach the 128 in row 4 col 3 because of the 32 between them. Casual play tries to slide tiles toward the corner but each slide spawns a new tile that fragments the merge path further. Around moves 10-14, the gridlock manifests: no merge sequence reaches the 256 → 512.

**Why magnitude 512 (not 1024):** Casual Carla's persona never reaches 1024 in normal play; dropping her on a 1024-board is out-of-distribution and tests board-recognition under teleport, not cliff prediction under continuity. 512 is the upper edge of casual reach; the failure mechanic (high-tile blocked by mis-aligned stack) is structurally identical.

### 4.3 `corner-abandonment-256`

```
[ 0,  4,  8,  2]
[ 4,  8, 16, 32]
[16, 32, 64,128]
[64,256,128,  4]
```

- `pattern_name`: `"corner-abandonment"`
- `high_tile_magnitude`: `256`
- `initial_score`: `4364`
- `seed_base`: `20260505003`
- `expected_cliff_window`: `(12, 18)`
- `source_citation`: r/2048 community posts on corner-abandonment failures; strategy walkthroughs describing the consequences of high-tile mobility (e.g., the "never let the high tile leave the corner" rule and what happens when it does). The implementation plan verifies and pins the specific URLs.

**Pattern rationale.** The 256 was anchored in the bottom-left corner; one bad swipe (typically a casual-player-instinctive UP swipe to clear an upper-row jam) pushed it inward. The corner now holds a `64`. Bottom-row reads `64 | 256 | 128 | 4`. Recovering the corner requires sliding 256 left, which would merge `64 + 256` into nothing (different values) — irrecoverable. The two `128`s on row 3-col-4 and row 4-col-3 are diagonal, which 2048 does not allow to merge. Casual play spends ~10-15 moves trying to rebuild structure around the dislocated 256 before mid-board chaos forecloses.

**Why magnitude 256 (not 512 or 1024):** Abandoning a 256 corner is the modal casual-player failure pattern. 512-corner abandonment occurs but is rarer; 1024-corner is OOD per §2.5.

## 5. Measurement contract (handed off to Test Runner spec)

The Test Runner spec consumes this contract. Listed here so this spec's scenarios are usable in isolation if the runner is implemented later.

### 5.1 Per-trial protocol

For each scenario `s` and each trial index `i ∈ [0, 19]`:

1. Compute `trial_seed = s.seed_base + i`.
2. Instantiate `Game2048Sim(seed=trial_seed, scenario=s)`.
3. Instantiate a fresh `MemoryCoordinator` (or ephemeral in-memory equivalent) for Carla. Bot needs no memory.
4. Run the agent loop until `Game2048Sim.is_game_over()` OR move count reaches `MAX_MOVES = 50` (whichever first).
5. Record:
   - For Carla trials: full `Anxiety` trajectory per move; the move index of `t_carla_predicts(trial)` per §2.7; the move index of `Game2048Sim.is_game_over() == True` (Carla's actual game-over).
   - For Bot trials: only the move sequence and `t_baseline_fails(trial) = move index where is_game_over() == True`; if the trial right-censors at `MAX_MOVES`, record `t_baseline_fails(trial) = 50` (sentinel) and flag the trial as right-censored.

### 5.2 Per-scenario aggregation

After all 40 trials (20 Carla + 20 Bot) complete:

- `t_carla_predicts(s) = mean of finite t_carla_predicts(trial)` over Carla trials. Trials with `t_carla_predicts(trial) = ∞` are excluded from the mean and counted toward the prediction-validity test as failures.
- `t_baseline_fails(s) = mean of t_baseline_fails(trial)` over Bot trials. Right-censored trials count if ≤ 2 of 20; if > 2, the scenario is flagged as broken and re-authored before any pass/fail decision.
- `Δ(s) = t_baseline_fails(s) - t_carla_predicts(s)`.

### 5.3 Cross-scenario pass criterion

Per ADR-0007 and methodology §4.1:

- **Prediction-validity test:** ≥ 17 of 20 Carla trials per scenario have `t_carla_predicts(trial)` finite AND `Carla's game-over move - t_carla_predicts(trial) ≥ 2`. The 17-of-20 threshold matches methodology §4.1's strict `> 80%` (16/20 = 80% does not satisfy strict greater-than; 17/20 = 85% does). Must hold for **every** scenario.
- **Affect-earns-its-keep test:** `Δ(s) ≥ 2` for ≥ 3 of the 3-scenario corpus this spec ships.

Both must hold for Phase 0.7 to pass.

**No-margin condition.** Methodology §4.1 says "≥ 3 of the 3-5 scenarios." With only 3 scenarios in this spec, "≥ 3 of 3" means **any single scenario failure on the affect-earns-its-keep test causes the corpus to fail**. This is a deliberate scope choice (per §2.4 sourcing discipline and §8 out-of-scope: scenarios 4-5 are deferred to a follow-up spec). If pilot calibration in §7.4 surfaces a scenario whose `Δ < 2` is a calibration artifact rather than a real signal, the right move is to author scenarios 4-5 in a follow-up spec to restore margin, not to soften the pass criterion.

## 6. Cross-spec dependencies

This spec hands off to two downstream Phase 0.7 prep specs.

### 6.1 Test Runner spec (deferred)

Consumes the measurement contract in §5. Decisions deferred to that spec:

- `Anxiety` sampling cadence (per-move, per-deliberation, or both) and which `Anxiety` field (raw, smoothed, or post-reflection) feeds the threshold check in §2.7.
- The per-trial `MemoryCoordinator` reset implementation (in-memory ephemeral store vs LanceDB table per trial).
- Parallelization strategy across scenarios and trials.
- Cost telemetry per arm and per scenario.

### 6.2 Baseline Bot spec (deferred)

Architectural decision deferred to that spec: LLM-based (per ADR-0007 as written) vs heuristic (a possibility surfaced in red-team review). This spec's scenarios are agnostic to the choice — both Bot architectures consume `Scenario` and produce moves, and the §2.3 RNG-discipline constraint composes with both.

## 7. Testing — what the implementation plan must cover

The implementation plan (the next deliverable after this spec) must include the following test surfaces:

### 7.1 Pure unit tests on the dataclass

- `test_scenario_validates_grid_shape`: a 3×4 or 4×5 grid raises `ValueError`.
- `test_scenario_validates_palette`: a grid containing `7` (out-of-palette) raises.
- `test_scenario_validates_initial_score_matches_grid`: passing `initial_score = 0` on a non-empty grid raises with the minimum-implied-score in the error message.
- `test_scenario_validates_high_tile_magnitude_matches_grid`.
- `test_scenario_validates_cliff_window_well_formed`.
- `test_scenario_seed_method_returns_seed_base_plus_trial_index`.

### 7.2 Pure unit tests on the SCENARIOS dict

- `test_all_scenarios_load_without_error`: instantiating every scenario in `SCENARIOS` does not raise — exercises every validator on every scenario.
- `test_all_scenarios_have_distinct_seed_base`: catches copy-paste authoring errors.
- `test_all_scenarios_satisfy_illusion_of_hope_lower_bound`: every `expected_cliff_window[0] >= 11` (the 10-15 prior-move buffer per §2.1's Illusion-of-Hope constraint requires gridlock manifest no earlier than move 11).
- `test_all_scenarios_satisfy_max_moves_upper_bound`: every `expected_cliff_window[1] < MAX_MOVES`.

### 7.3 Sim-integration tests on each scenario

- `test_scenario_initial_state_loads_into_sim`: instantiate `Game2048Sim(scenario=s, seed=s.seed_base)` for each scenario; assert `sim.board.grid == s.initial_grid` and `sim.board.score == s.initial_score`.
- `test_scenario_admits_at_least_one_legal_move`: each scenario's initial board has at least one swipe direction that produces a board change (catches authoring errors that would game-over on move 0).

### 7.4 Pilot calibration smoke (manual, no commit gate)

After unit + integration tests pass, the implementation plan includes a manual calibration step: run a Baseline Bot (or a placeholder greedy-heuristic standin if the Bot spec hasn't landed yet) for ~5 trials on each scenario; verify the observed game-over distribution falls inside `expected_cliff_window` for at least 3 of 5 trials. If a scenario fails calibration, the grid is re-authored and the test re-run.

This calibration is not a unit test (it requires LLM API access at production tier per ADR-0006) but is a gate before the real N=20 run.

## 8. Out-of-scope

- The Test Runner implementation (§6.1).
- The Baseline Bot architectural choice (§6.2).
- Persona definitions for Casual Carla and Baseline Bot beyond the prompts pinned in ADR-0007 §"The two arms".
- Statistical reporting beyond the pass criteria in §5.3 (e.g., variance, confidence intervals, Cohen's d) — those land in the Test Runner spec or its analysis appendix.
- Scenarios 4-5 (the methodology range is "3-5"; this spec ships 3 with explicit room for two more in a follow-up spec if pilot calibration shows the corpus is too narrow).
- Higher-skill personas (Strategic Sam, etc.) and their corresponding magnitude instantiations.
- Migration of scenarios to a JSON/YAML data file — defer to ~10+ scenarios per §2.10.

## 9. Open follow-ups

- The implementation plan must verify and pin specific URLs for each `source_citation` rather than the source-class descriptors used in this spec.
- After pilot calibration on the three scenarios, this spec gets a one-line follow-up note recording the observed mean game-over per scenario for future-reviewer auditing.

## 10. References

- `docs/decisions/0001-cognitive-architecture-as-product-moat.md` — the moat the cliff test validates
- `docs/decisions/0005-defer-v1-demo-until-phase-0.7.md` — establishes Phase 0.7 as the demo-recording gate
- `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` — cliff test runs at `NOVA_TIER=production` per §"Tier discipline"
- `docs/decisions/0007-blind-control-group-for-cliff-test.md` — the two-arm design and pinned pass criteria this spec implements
- `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` — the GameIO abstraction these scenarios run under
- `docs/product/methodology.md` §4.1 — the upstream methodology contract this spec is consistent with
- `docs/product/product-roadmap.md` Week 1 — the schedule the cliff test runs against
- `docs/superpowers/specs/2026-05-04-game2048sim-design.md` — the simulator spec this scenarios spec extends
- `docs/superpowers/plans/2026-05-04-game2048sim.md` — the implementation plan that built the dataclass this spec extends
- `nova_agent/lab/sim.py:38` — current `Scenario` dataclass to extend
- `nova_agent/lab/scenarios.py` — current `SCENARIOS` dict to extend
- `nova_agent/lab/io.py:SimGameIO` — consumer of `Scenario` requiring update for the `seed` → `seed_base` rename
