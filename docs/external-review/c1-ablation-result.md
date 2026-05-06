# C1 Ablation — Result

> **Test:** Round 3 synthesis §4 single-can't-dodge attack.
> **Original test:** `Pearson(t_predicts, min_i: empty_cells_i ≤ 3)` on
> the 2026-05-06 morning-pilot CSV.
> **Available-data weakening:** the morning-pilot JSONL only logs
> `tot_branch` / `tot_selected` events; per-move `empty_cells`
> trajectories were not recorded. The exact Pearson cannot be run.
> **Test executed:** within-scenario t_predicts variance + between-
> scenario t_predicts gradient as a function of initial `empty_cells`.
> **Script:** `docs/external-review/c1-ablation.py`.
> **Cost:** $0 (analysis on existing CSV).

---

## Pre-registered thresholds

The script set thresholds before reading the data:

- Within-scenario stdev < 1.0 move = anxiety deterministic given
  scenario → C1 strongly supported.
- Within-scenario stdev > 2.0 moves = anxiety responds to factors
  beyond initial cells → C1 weakened.
- 1.0 ≤ stdev ≤ 2.0 = ambiguous; full synthesis ablation needed.

---

## Result

| Scenario | Initial `empty_cells` | Carla `t_predicts` (raw) | mean | stdev | min | max | Verdict |
|---|---:|---|---:|---:|---:|---:|---|
| `corner-abandonment-256` | 1 | `[1, 0, 0, 1, 0]` | 0.40 | 0.55 | 0 | 1 | **C1 strongly supported** |
| `512-wall` | 1 | `[1, 0, 1, 1, 0]` | 0.60 | 0.55 | 0 | 1 | **C1 strongly supported** |
| `snake-collapse-128` | 4 | `[4, 7, 6, 8, 3]` | 5.60 | 2.07 | 3 | 8 | **C1 weakened (stdev just over 2.0)** |

All 15 Carla trials returned finite `t_predicts` (no aborts).

---

## Between-scenario gradient

Sharp. The two scenarios that start at `empty_cells = 1` cluster
`t_predicts` at 0-1. The one scenario that starts at `empty_cells = 4`
clusters at 3-8. ~5 moves of separation tracks the difference in
initial `empty_cells`. This is exactly the prediction C1 makes if
anxiety is a deterministic function of `empty_cells`.

If the cognitive architecture were doing the predictive work, we would
expect significant overlap between scenarios — Carla's reasoning about
"this snake formation is collapsing" would generate `t_predicts` ≈ 5
even on a corner scenario where the anxiety formula's mechanical
trigger fires at move 0. We see no such overlap.

---

## Within-scenario variance interpretation

### Corner + 512-wall (init = 1)

stdev = 0.55 across the binary range {0, 1}. On a 50-move dynamic range
(per `MAX_MOVES = 50`), `t_predicts` is essentially pinned at the
formula's mechanical trigger. The LLM stochasticity at temp=0.7, the
memory retrieval, the trauma flag, the RPE-via-other-dimensions —
collectively add zero meaningful variance to `t_predicts`. The 0 vs 1
distinction reflects whether `anxiety` first crosses 0.6 on move 0 or
move 1, which is downstream of small float-precision differences and
the exact "≥ 2 consecutive moves" qualifier in the prediction-validity
test.

**C1 holds completely on these two scenarios.**

### Snake-collapse-128 (init = 4)

stdev = 2.07, just over the 2.0 weakening threshold. Range [3, 8].

Two interpretations:

1. **Mechanical (C1 holds):** With init = 4, the formula gives zero
   anxiety contribution until `empty_cells` drops to ≤ 3. Stochastic
   spawn schedules + Carla's stochastic move choices determine when
   that happens. Once it happens, anxiety crosses 0.6 within ~1 move.
   The t_predicts ∈ [3, 8] range is consistent with "first move at
   which empty_cells crosses 3" + small variance. The variance is
   not cognitive.

2. **Cognitive (C1 weakened):** Carla's LLM may be choosing moves that
   delay or accelerate the empty-cell crossing differently than a
   random or greedy policy would. Some of the variance may reflect
   genuine decision-making about whether to collapse the snake
   formation early or stall.

The available data cannot fully discriminate (1) from (2). The
synthesis's prescribed counterfactual — 1 trial per scenario with
anxiety pinned to a constant 0.5 — would discriminate. Until that
counterfactual runs, snake gives C1 a partial defence.

---

## Verdict on C1

**C1 lands hard on 2 of 3 scenarios.** Anxiety > 0.6 on corner + 512-
wall is essentially the formula firing mechanically on initial grid
state; the cognitive architecture is not contributing to the
prediction. On snake-collapse-128, the data is consistent with
mechanical depletion-driven crossing but does not rule out cognitive
contribution.

**The synthesis's recommendation stands.** The N=5 Sonnet pilot in
current form should not proceed. The recalibration spec's empty-cell
adjustments (corner 1→4, 512-wall 1→2) map those scenarios into the
snake regime — t_predicts in [3, 8] mechanically — which is exactly
the engineered outcome the spec calls "Delayed Detection." C2 is
mechanically confirmed: the spec is tuning the only signal that drives
the metric.

---

## Recommendations (refined from synthesis §7)

1. **Do not authorize the N=5 Sonnet pilot in current form.** The result
   would mechanically pass the recalibration spec's t_predicts targets
   and provide zero new information about cognitive prediction.

2. **Run the constant-anxiety counterfactual** before any further pilot
   spend. 1 trial per scenario with anxiety pinned at 0.5 (or any
   constant). Cost: ~$1.50 in LLM spend. Discriminates mechanical from
   cognitive on the snake regime.

3. **Methodology rewrite (synthesis §7(b) item 1) is now urgent.** The
   citation chain (Russell/Schultz/Yehuda) is no longer just an
   academic credibility risk — it is actively contradicted by the
   pilot data. The methodology must reframe the affect formula as an
   empty-cells-dominated heuristic, not a Russell-anchored cognitive
   primitive.

4. **The recalibration spec needs a redesign**, not a parameter tweak.
   Recalibrating `empty_cells` to defer the metric trigger is direct
   goalpost-tuning. The right fix is either (a) a non-`empty_cells`
   driver for anxiety (e.g., RPE composite, frustration plateau), or
   (b) abandoning anxiety as the prediction primitive and using a
   composite affect signal that the LLM CAN add variance to.

5. **Phase 0.7 architecture (synthesis §7(c)) needs the 0.7a/0.7b
   split.** Phase 0.7a = signal-content audit (this ablation +
   constant-anxiety counterfactual). Phase 0.7b = the pilot, gated on
   0.7a passing. Total cost increment: <$2; cost saving on a confounded
   $5–7 run: $5–7 plus all downstream contamination.

---

## What this ablation does NOT establish

- It does not establish that the project is unsalvageable. The affect
  formula's empty-cells dominance is a fixable architectural defect,
  not a category error. A multi-driver anxiety formula (empty_cells +
  RPE plateau + frustration + memory-retrieval) would respond to
  factors the LLM controls.

- It does not test the trauma-tagging mechanism (M-01, C5). Phase 0.8
  remains a separate gate.

- It does not invalidate the entire methodology. The Cognitive Audit
  Trace (Brain Panel) and the State-Transition Signatures (with
  rewrite per H9, H10) survive as product surfaces.

What it does is establish that the **current** Phase 0.7 specification
cannot answer the question Phase 0.7 was designed to answer, and the
**current** affect formula does not produce the predictive lead-time
the methodology claims it does. Both are fixable. Neither is fixed by
running the N=5 Sonnet pilot as specified.
