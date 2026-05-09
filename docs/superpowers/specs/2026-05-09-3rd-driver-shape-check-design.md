# 3rd-Driver Shape-Check — ADR-0013 §3 Precondition

**Status:** Draft for user approval (2026-05-09)
**Date:** 2026-05-09
**Author:** ihoresh07@gmail.com (solo founder), with rounds 1–7 red-team discipline in `docs/external-review/`
**Supersedes:** None. Inserts a precondition gate before the ADR-0013 §3 (3rd anxiety driver for 512-wall) commit.
**Related:**

- `docs/external-review/decisions/2026-05-09-rpe-pivot-first-principles-rederivation.md` (P6 lock — wiring + K-tuning + 3rd driver clauses)
- `docs/external-review/decisions/2026-05-09-methodology-code-audit-results.md` §2.6 (ToT-branch-disagreement audit-status, NOT endorsement)
- `docs/external-review/decisions/2026-05-09-phase-0.7b-harness-decision.md` (trauma=0 single-variable comparison)
- `docs/external-review/phase-0.7a-result.md` + erratum (R1 fired; "C1-as-implemented confirmed; C1-as-specified untested")
- `docs/external-review/2026-05-09-redteam-rpe-pivot-response.md` (Option A precondition: Pearson three-band rule)
- `docs/superpowers/specs/2026-05-09-phase-0.7a-counterfactual-design.md` (per-move JSONL schema this spec consumes)
- `nova-agent/src/nova_agent/affect/state.py` (lines 32–53 — affect formula under rewrite)
- `nova-agent/src/nova_agent/affect/rpe.py:14-18` (`value_heuristic` — load-bearing for §5 Option 2 structural kill)

---

## 1. Context

ADR-0013 (anxiety-driver rewrite) has three locked items per `docs/external-review/decisions/2026-05-09-rpe-pivot-first-principles-rederivation.md` §(c):

- **Item 1.** Reduce or remove the `empty_cells` anxiety coefficient (continuation of Phase 0.7a counterfactual posture).
- **Item 2.** Wire frustration → anxiety via single-line addition at `nova-agent/src/nova_agent/affect/state.py:51` (`anxiety += K * _clamp(frustration, 0.0, 1.0)`), with K to be empirically tuned.
- **Item 3.** Introduce a 3rd anxiety driver to fire on 512-wall, where frustration is geometrically silent per re-derivation §(d).

Items 1 and 2 are P6-locked code-change clauses with no remaining contestable structure. Item 3 is the load-bearing open question: the candidate selection has gone through seven red-team rounds with cumulative concessions on (a) audit-citation-as-endorsement bias (round 5), (b) prediction-as-endorsement on entropy (round 6), (c) asymmetric-evaluation second-chance bias (round 5–6), (d) Q1-vs-Q2 question-pinning (round 6), (e) operational-protocol commitment (round 6), (f) most-thorough-as-endorsement bias on schema-extension framing (round 7), and (g) structural-kill applicability to existing-data proxies (round 7).

This spec is the operational protocol that codifies the cumulative round-1–7 discipline before any candidate is pinned to ADR-0013 §3. It runs on existing 658-event Phase 0.7a per-move data plus structural-derivation analysis; no fresh-data collection inside its scope.

The decision rule pre-commits the §3 outcome paths so the post-run adjudication cannot drift toward citation, prediction, or audit-friendly endorsement bias.

---

## 2. Question pinning

ADR-0013 §3 answers exactly one question:

> **Q1.** Which axis drives anxiety on `512-wall` when frustration is geometrically silent?

**Q2** (which axis adds reinforcement on snake/corner once frustration has crossed the gate) is closed by Item 2 (frustration → anxiety wiring) — *claimed*, validated empirically by §4 of this spec. If §4 fails, Q2 is no longer closed by Item 2 alone, the protocol revisits, and §3's question expands.

Q1 is `512-wall`-specific. Per Phase 0.7a per-move data, frustration was effectively zero across all 658 events (typical values ~0.0008–0.0012 per `docs/external-review/phase-0.7a-result.md` Per-move trajectory observations table); the structural reason on 512-wall is that `value_heuristic` (`rpe.py:14-18`) counts horizontal-adjacent-equal pairs and a wall configuration has zero such pairs, so `rpe = score_delta - value_heuristic ≈ score_delta ≥ 0`, so frustration's `min(1.0, -rpe * 0.6)` accumulator never accumulates negative-RPE pressure. The 3rd driver must therefore fire on a signal independent of `value_heuristic`-anchored RPE.

---

## 3. Protocol

**Equal-footing rule (protocol A).** Shape-check is the sole gate for Item 3 candidate selection in ADR-0013. Candidates that cannot be evaluated on Phase 0.7a 658-event existing data are out for ADR-0013. Such candidates may be reconsidered in a follow-up ADR after Phase 0.7b ships under Items 1 + 2 with new production data.

**Why protocol A over alternatives.** The round-5–6 thread evaluated three protocols: (A) equal-footing, (B) sequenced fallback for non-evaluable candidates, (C) parallel evaluation with explicit asymmetry disclosure. Protocol A removes the asymmetric-second-chance structure entirely (no candidate gets a fallback gate that others don't get). Protocol B preserves a contingent path for a non-evaluable candidate but reintroduces the audit-citation-as-endorsement pattern in softer form. Protocol C requires an in-spec commitment that closes the loophole but doesn't remove it. Protocol A is the cleanest discipline-preserving choice and is locked here.

**Operational consequence.** Option 1 (ToT-branch-disagreement) is out for ADR-0013 §3. ToT fired `0/658` events on Phase 0.7a per `docs/external-review/phase-0.7a-result.md`; existing data cannot adjudicate. Option 1 is documented in ADR-0013's Alternatives Considered section as deferred-pending-Phase-0.7b-production-data, with the asymmetric-evaluation disclosure rationale in writing.

---

## 4. Item-2 validation step

**Goal.** Verify that wiring frustration → anxiety with empirically-tuned K reaches anxiety > 0.6 within 5 moves of `final_move_index` on snake-collapse-128 and corner-abandonment-256, without false-positive crossings on benign frustration spikes and without saturating the affect cap.

**Why this validates "Q2 closed by Item 2."** The round-3+ first-principles re-derivation (`2026-05-09-rpe-pivot-first-principles-rederivation.md` §(d)) claimed Item 2 wiring + K-tuning suffices on snake/corner. That claim is asserted from math, not yet verified on Phase 0.7a per-move data. This step is the empirical verification — same shape as the Pearson(frustration, 1/empty_cells) precondition that gated the rewrite ADR per Option A of `2026-05-09-redteam-rpe-pivot-response.md`.

### 4.1 K sweep design

Source data: `docs/external-review/phase-0.7a-raw-2026-05-09/results/events_{snake-collapse-128,corner-abandonment-256}_carla_{0..4}.jsonl`. 5 trials per scenario × 2 scenarios = 10 trials total.

For each trial, replay the per-move frustration trajectory under `K ∈ {0.5, 1.0, 1.73, 2.5, 5.0, 7.5, 10.0}`. The 1.73 anchor is derived from steady-state math: anxiety steady-state under decay 0.85 with constant input `F = K × frustration` is `F / 0.15 ≈ 6.67 × F`; for `anxiety_ss ≥ 0.6` and observed `frustration_max ≈ 0.052` per `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-results.md` (or whichever value the existing data emits), K ≈ 1.73 is the lower-bound steady-state crossing point.

For each (trial, K) pair, compute the simulated anxiety trajectory with `anxiety_t = 0.85 * anxiety_{t-1} + K * frustration_t` (Items 1 and 2 only — no empty_cells term, no trauma_intensity, since trauma was 0/658 on Phase 0.7a anyway).

Record three per-trial-per-K metrics:

- `(a) crossing_within_5`: 1 if `max(anxiety_t for move_index in [final_move_index - 5, final_move_index])` ≥ 0.6, else 0.
- `(b) false_positive_crossings`: count of windows ≥ 5 moves before `final_move_index` where anxiety crossed 0.6 without subsequent cliff.
- `(c) cap_saturation_freq`: fraction of crossing events at which anxiety hit the `_clamp(..., 0.0, 1.0)` ceiling.

### 4.2 Acceptance criteria

Item 2 closes Q2 if there exists a K such that all three of the following hold simultaneously:

- `(a) crossing_within_5 ≥ 4/5` per scenario, on both scenarios independently.
- `(b) false_positive_crossings ≤ 1/5` per scenario, on both scenarios independently.
- `(c) cap_saturation_freq < 0.50` of crossing events (cap-collapse pattern, `2026-05-08` LESSONS.md).

If a K range satisfies all three on both scenarios, pin K's interior value (e.g., midpoint of the passing range) to ADR-0013 Item 2 with the empirical defense.

### 4.3 Fail-mode handling

If no K satisfies all three criteria on both scenarios:

- **Q2 is not empirically closed by Item 2 alone.** β-equal's "§3 is Q1-only" framing collapses.
- The protocol pick (round-6 result) revisits with three branches:
  - (i) §3 must answer Q2 in addition to Q1 (different driver candidates).
  - (ii) Item 2's spec changes (different decay rate, different cap, different accumulation rule, different RPE input shape).
  - (iii) Methodology-narrowing decision opens earlier (drop snake/corner from gate as well as 512-wall).
- Each branch is its own redteam round. Do NOT pick from inside this spec's adjudication; halt and convene a fresh redteam round with the failed K-sweep data as input.

---

## 5. Option 2 (score-velocity) — structural kill

Option 2's candidate definition: `score_velocity_t = (1/K) × Σ_{i=t-K..t} score_delta_i` for window K (e.g., K=5).

**Frustration is geometric-decay-smoothed `positive_part(rpe)`** per `state.py:36, 44`:

```
frustration_t = 0.92 × frustration_{t-1} + min(1.0, -rpe_t × 0.6)   if rpe_t < 0
              = 0.92 × frustration_{t-1}                              otherwise
```

**RPE shares the score_delta input** per `rpe.py:22-31`:

```
rpe_t = clip( (score_delta_t - value_heuristic(board_{t-1})) / scale,  -1, 1 )
```

where `value_heuristic` (`rpe.py:14-18`) is a slow-moving function of board state (counts horizontal-adjacent-equal pairs scaled by tile value).

**Score-velocity is rectangular-window-smoothed `score_delta`:**

```
score_velocity_t = (1/K) × Σ_{i=t-K..t} score_delta_i
```

**Decorrelation budget:** the only sources of decorrelation between `frustration_t` and `score_velocity_t` are:

- `value_heuristic` subtraction (slow-moving relative to per-move `score_delta` on stable tile distributions; near-zero on wall-pattern boards, slowly-varying on snake/corner).
- Geometric-decay (0.92 per move) vs rectangular-window (uniform over K=5) smoothing — small spectral difference for typical K.
- `positive_part` asymmetry (frustration only accumulates negative RPE; score-velocity is signed).

**Conclusion.** `Pearson(frustration_t, score_velocity_t)` is bounded above ~0.7 structurally on any data-generating process where (i) `value_heuristic` is slow-moving and (ii) frustration's `positive_part` gate fires meaningfully. The bound is data-independent. §4.7 (Pearson three-band rule, §8 below) fails by construction at the strict-reject end (`r > 0.8`) for any realistic K and decay parameters; the candidate fails Pearson independence even before the empirical run.

**No empirical run on Option 2 is required.** Option 2 is killed by structural derivation. The spec writes the math; the candidate falls out without measurement. Option 2 is documented in ADR-0013's Alternatives Considered as `killed-by-structural-collinearity-with-frustration`, with the math derivation cited.

---

## 6. Option 3 (tile-distribution entropy) — proxy invalidity

Option 3's candidate definition: `tile_entropy_t = -Σ_v p_v × log p_v` where `p_v = count(v) / sum_counts` over occupied tile values on the board.

**The available existing-data proxy is monotonic in `empty_cells`.** Phase 0.7a per-move JSONL records `empty_cells_pre/post` (and `affect_vector`, `trauma_intensity`, `tot_fired`, `chosen_action`) per `events_*_carla_*.jsonl` schema verified 2026-05-09. The JSONL does NOT record `board_grid` or `score_pre/post`. Any entropy proxy computable from the JSONL is necessarily a function of `empty_cells` alone (no other tile-distribution data is exposed).

**Why a 1D `empty_cells`-based proxy is invalid for screening Option 3.**

Tile-distribution entropy decomposes informally into two axes:

- **Occupancy:** how many cells are filled. Captured directly by `empty_cells`.
- **Value-spread:** how diverse the filled values are. Independent of `empty_cells` — orthogonal axis.

A 1D function of `empty_cells` (any monotonic transform) measures occupancy only. It contains zero information about value-spread.

**The trap.** `empty_cells` IS the deprecated driver from Phase 0.7a R1. It mechanically predicts cliffs in the existing formula's data-generating process. Computing `entropy_proxy = monotonic(empty_cells)` and running shape-check produces:

1. Top-decile clustering near `final_move_index` — passes shape-check trivially, because `empty_cells` mechanically drives anxiety to the cliff.
2. `Pearson(entropy_proxy, frustration) ≈ Pearson(empty_cells, frustration) ≈ +0.12` (per round-3 already-run inverse Pearson `r ≈ -0.12`) — passes Pearson three-band's lower band.

Both gates "pass" not because tile-entropy carries independent signal, but because the proxy IS the deprecated driver under a new name. Pinning §3 on a passed proxy commits to a candidate based on a measurement that doesn't distinguish entropy from `empty_cells`.

**Counter-counter: residualization.** Computing `proxy_residual = entropy_proxy - α × empty_cells_term` requires multi-dimensional input (tile values) to extract any value-spread variance. From a 1D function of `empty_cells`, the residual is zero by construction. There is no value-spread variance to recover from existing JSONL.

**Verdict.** Option 3 cannot be evaluated on Phase 0.7a 658-event existing data. The disciplined response under protocol A (§3 above) is one of two binary-fork branches per §7.

---

## 7. §3 binary fork — pre-commit

After Item 2 validation (§4) returns its verdict and the §5 + §6 derivations are written into ADR-0013's Alternatives Considered, the §3 question reduces to a binary fork conditional on Item 2 passing:

### 7.1 Branch I — fresh `board_grid` data collection

Targeted re-collection of per-move `board_grid` data on Phase 0.7a-tier harness, scoped to evaluating Option 3 (tile-distribution entropy) properly.

- **Schema extension.** Add one field to `cliff_test.py` per_move emitter: `board_grid: list[list[int]]`. Estimated 5 LOC + smoke test in `nova-agent/tests/lab/test_cliff_test.py`. Score and other fields explicitly excluded — Option 2 is dead by §5; no need to pre-collect for it.
- **Run scope.** 15 Carla trials (3 scenarios × 5 trials, same Phase 0.7a cadence). Same `phase_0_7a` tier (`gemini-2.5-pro`). Same `NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM=1` flag (single-variable: this is harness validation of Option 3 only; Items 1+2 not yet shipped).
- **Cost.** ~$0.66 expected (per Phase 0.7a empirical reference); cap $5–7 per existing budget.
- **Wall.** ~90 min (per Phase 0.7a reference).
- **Justification gate.** Branch I is taken if Item 2 validation passes. The fresh-collection scope is *targeted* — driven by a specific empirical question ("does tile-entropy carry signal independent of empty_cells?"), not by spec-completeness.
- **Acceptance criteria after Branch I run:** `Pearson(tile_entropy, frustration)` and `Pearson(tile_entropy, empty_cells)` both reported. Three-band rule (§8) applied. Top-decile-event proximity-to-`final_move_index` clustering on 512-wall reported. Pin Option 3 to ADR-0013 §3 if (i) `Pearson(tile_entropy, empty_cells) < 0.8` (independent of deprecated driver), (ii) `Pearson(tile_entropy, frustration) < 0.5` (Pearson lower band, §8) OR `0.5 ≤ r ≤ 0.8` with explicit residualization, AND (iii) top-decile clustering within 5 moves of `final_move_index` on ≥4/5 trials of 512-wall.

### 7.2 Branch II — methodology-narrowing (drop 512-wall)

The architecture's primitives may genuinely not reach 512-wall. The disciplined response is to narrow the methodology's claim rather than extend the architecture to fit the test.

- **Trigger.** Branch II is taken if Branch I runs and Option 3 fails its acceptance criteria on 512-wall, OR if the user elects Branch II directly (e.g., to bound risk on the architecture-extension scope).
- **Methodology change.** ADR-0013 narrows Phase 0.7b's falsification gate to snake-collapse-128 + corner-abandonment-256 only. 512-wall moves to a Phase 0.9 or follow-up scope as a methodology-bounded scenario the current architecture does not claim to predict. The architecture's commercial claim (multi-game, predictive lead-time) survives only on the non-512-wall scenarios.
- **Cost.** $0 immediate. Pitch cost: the architecture's claim is bounded. External reviewer will see the bounded claim and the scenario's exclusion rationale (geometric silence of `value_heuristic`-anchored RPE).
- **Acceptance criteria for Branch II:** `Pearson(empty_cells, frustration) < 0.5` confirmed on existing data (already known: ~+0.12 per round-3). `final_move_index` distribution on 512-wall already documented from Phase 0.7a result memo (right-censored on 2/5; 47-49 moves on 3/5). The decision rule for Branch II: take it if (i) Item 2 validation passed (so snake/corner are predicted by the new formula), AND (ii) either Branch I was taken and Option 3 failed, OR the user pre-elects Branch II without running Branch I.

### 7.3 Pre-commit on Branch I vs Branch II

The fork is binary; one branch is taken. The decision rule:

- **Item 2 fails** (§4 fail-mode) → halt; redteam round with K-sweep failure data; do not enter §7 fork.
- **Item 2 passes + user elects Branch I** → run Branch I; verdict per §7.1 acceptance criteria.
- **Item 2 passes + user elects Branch II** → narrow methodology per §7.2; commit ADR-0013 with §3 = "Item 2 alone closes Q1 via methodology-narrowing on 512-wall."
- **Item 2 passes + Branch I run + Option 3 fails acceptance** → drop into Branch II per §7.2 trigger.
- **Item 2 passes + Branch I run + Option 3 passes acceptance** → pin Option 3 to ADR-0013 §3.

---

## 8. Pearson three-band rule (preserved from round-1 Option A precondition)

Per `docs/external-review/2026-05-09-redteam-rpe-pivot-response.md` §6 step 3 and round-1's original framing:

- **`r > 0.8`** → **reject** the candidate. Collinear with the deprecated or co-driver signal.
- **`r < 0.5`** → **proceed** with the candidate. Empirically independent.
- **`0.5 ≤ r ≤ 0.8`** → **hybrid axis** with explicit residualization against the co-driver. The candidate is admitted only as a residualized signal `candidate_residual = candidate − β × frustration`, where β is computed from a regression on the 658-event data; ADR-0013 documents the residualization in §3.

Three-band restored after round-5's strict `r < 0.5` over-restriction was flagged in round-6.

---

## 9. Cost + timebox

**Existing-data analysis (Item 2 validation + §5 math write-up + §6 invalidity write-up):** $0, ~30 min for analysis + ~30 min for the two derivations.

**Branch I (if elected):** ~$0.66 expected, ~90 min wall, ~half-day total dev/wall.

**Branch II (if elected):** $0 immediate; pitch cost in ADR-0013 narrative.

**Total upper bound:** ~$0.66 + ~half-day, conditional on Branch I election. Branch II election keeps total at $0.

**Hard timebox:** ≤ 1 working day for the full §4–§7 sequence. If timebox exceeds, halt and convene redteam.

---

## 10. Implementation handoff

Sequencing — atomic commits per `.claude/rules/workflow.md` Tier-1:

1. **Spec commit** (this document) — `docs(specs): 3rd-driver shape-check design`.
2. **Item-2 validation script + run** — `nova-agent/src/nova_agent/lab/shape_check_item2_validation.py`. Light-TDD per `.claude/rules/nova-agent.md` "TDD mandatory for cognitive layer" — `lab/` is harness-tier, smoke test on synthetic per_move JSONL is sufficient. Commit: `feat(lab): item-2 validation K-sweep on Phase 0.7a per-move data`.
3. **Item-2 results + §5 + §6 derivations memo** — `docs/external-review/decisions/2026-05-09-3rd-driver-shape-check-results.md`. Three sections: (a) Item-2 K-sweep verdict + recommended K, (b) Option 2 structural-kill derivation, (c) Option 3 proxy-invalidity derivation. Commit: `docs(external-review): 3rd-driver shape-check results`.
4. **§7 fork decision** — user-direction branchpoint after step 3. No artifact committed at this step; the decision flows to step 5.
5. **Branch I (if elected)** — `feat(lab): add board_grid field to cliff_test per_move emitter` + `chore(runs): Branch I tile-entropy targeted-collection 2026-05-09` + Branch I results memo. Three commits.
6. **ADR-0013 draft** — `docs(decisions): ADR-0013 anxiety-driver rewrite`. Includes:
   - **Preamble:** the trauma=0 harness paragraph per `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_adr_0013_preamble_obligation.md` (verbatim text inserted).
   - **Decision §1:** empty_cells coefficient reduction.
   - **Decision §2:** frustration → anxiety wiring + K (from Item-2 verdict).
   - **Decision §3:** Option 3 (Branch I) OR methodology-narrowing (Branch II), per §7.3 outcome.
   - **Alternatives Considered:** Option 1 (deferred per protocol-A); Option 2 (killed by §5 math); Option 3 fork outcome; status quo; full architectural redesign.
   - **References:** rounds 1–7 redteam thread + audit + harness decision + this spec + shape-check results memo.
7. **Phase 0.7b branch** — fresh `claude/anxiety-driver-rewrite` (or similar). Implement Items 1+2+3 per ADR-0013. TDD per `.claude/rules/nova-agent.md`.
8. **Phase 0.7b run** — falsification gate per `2026-05-09-phase-0.7a-counterfactual-design.md` §9 R2 acceptance.

Per `.claude/rules/workflow.md` PR cadence: this spec + step 2 + step 3 are one coherent unit ("shape-check precondition shipped"). Open ONE PR after step 3 commits. Branch I (step 5) is a separate PR if elected. ADR-0013 (step 6) is a separate PR. Phase 0.7b implementation (step 7) is on a fresh branch with its own PR sequence.

---

## 11. Out of scope (deferred)

- **Option 1 (ToT-branch-disagreement) evaluation.** Deferred to a follow-up ADR after Phase 0.7b ships under Items 1 + 2 with new ToT-firing production data, per protocol A (§3).
- **`rpe.py:14-18` axis bias.** Documented design intent per `docs/external-review/phase-0.7a-result.md` Recommendations Side fixes; 5-line fix + tests + ADR-amend bullet, lands AFTER Phase 0.7b in a separate PR.
- **Pro/bot `parse_failure` issue.** Phase 0.8 territory.
- **Recompute discipline for Branch I `Pearson(tile_entropy, empty_cells)` after main-stage Phase 0.7b ships.** Mechanism-validation question, separate scope.

---

## 12. Pre-registration symmetry

The §4 acceptance criteria, §5 structural-kill argument, §6 proxy-invalidity argument, §7 fork branches, and §8 Pearson three-band rule are pre-committed before any analysis runs. Post-run adjudication shall not re-interpret these criteria. Any post-run discovery of failure modes not captured here triggers a fresh redteam round, not a goalpost-shift.

The cumulative round-1–7 redteam thread is the load-bearing methodology defense for ADR-0013. This spec is its operational artifact.
