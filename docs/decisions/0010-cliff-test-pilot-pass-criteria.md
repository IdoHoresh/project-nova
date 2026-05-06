# ADR-0010: cliff-test-pilot-pass-criteria

**Status:** Accepted  
**Date:** 2026-05-06  
**Deciders:** ihoresh07@gmail.com (solo founder), synthesis red-team review (2026-05-06)  
**Workflow note:** This ADR is the structural fix for synthesis attack M-04 — the pilot
acceptance criteria in `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md §5`
amended an ADR-0007 §A1.3 methodology-level pass standard without a corresponding ADR.
Spec §4.3 and §5 document the violation in place. ADR-0010 is the authoritative source
going forward; spec §5 is historical context.

---

## Context

ADR-0007 established the cliff test's two formal-run pass criteria:

1. **Prediction-validity test (ADR-0007 §Decision test 1):** Carla's `Anxiety > 0.6` event
   precedes her game-over move by ≥ 2 moves in **> 80%** (≥ 17/20) of her trials per scenario.
2. **Affect-earns-its-keep test (ADR-0007 §Decision test 2):** mean paired
   `Δ = t_baseline_fails − t_carla_predicts ≥ 2` moves in ≥ 3 of the 3–5 scenarios.

Before the formal N=20 run, a smaller pilot (N=5 per arm per scenario) must pass a gating
check that verifies: (a) scenario calibration holds (Bot dies in the expected cliff window),
and (b) Carla's cognitive architecture actually produces a detectable signal at pilot scale.

The original recalibration spec (`2026-05-06-scenarios-recalibration-design.md §5`, authored
2026-05-06 pre-synthesis) specified four pilot acceptance criteria. The synthesis red-team
(2026-05-06) attacked two of them:

- **C3 (Critical):** `snake-collapse-128: 1/5 cap-violation = borderline PASS` violated the
  spec's own no-margin condition (§5.3). The Wilson-CI on 1/5 spans 0–60%, which does not
  reject cap-rate ≥ 10% (the §2.8 "broken scenario" threshold extrapolated to N=20). A single
  cap-violation in a 5-trial pilot is unresolved small-N noise, not a pass.

- **H6 (High):** the original pilot criteria contained no cognitive-architecture validation
  gate. Criteria 1–4 (as originally specified) are Bot-calibration checks and operational
  health checks. They verify the scenario mechanics and abort discipline; they say nothing
  about whether Carla's prediction signal is present. A pilot that omits the cognitive-
  validation analog of the formal test 1 is not gating the right thing.

The spec §5 was revised post-synthesis (same date) to address C3 and H6. Those revisions
changed a methodology-level pass standard — a decision that belongs in an ADR per
`.claude/rules/workflow.md`. Synthesis attack M-04 flags this as a workflow violation.
ADR-0010 closes the gap.

---

## Decision

**Accept the revised pilot acceptance criteria as the authoritative methodology-level standard
for gating the Phase 0.7 formal N=20 run.** All five criteria below must hold. The two that
are new (criteria 3 and 5) are the M-04 structural fix.

### The five pilot acceptance criteria

These apply to the N=5 calibration pilot (per scenario, both arms) that must pass before the
formal N=20 run is authorised.

#### Criterion 1 — §7.4 calibration (Bot mechanics)

≥ 3/5 Bot game-overs must fall in `expected_cliff_window` per scenario.

*Scope: scenario calibration. This criterion does not change from the original spec.*

#### Criterion 2 — §2.8 cap discipline (tiered for N=5)

| scenario | pilot cap threshold |
|----------|---------------------|
| `corner-abandonment-256` | **0/5 strict** — any cap = fail |
| `512-wall` | **0/5 strict** — any cap = fail |
| `snake-collapse-128` | **0/5 target; 1/5 = inconclusive (see § below); 2+/5 = fail** |

**Snake-collapse N-raise rule (C3 fix):** if snake-collapse-128 produces exactly 1/5 cap-
violations in the pilot, the result is **inconclusive — raise N_snake to 15** (≈ $3 incremental
cost at Sonnet 4.6 rates) before authorising the real N=20 run. Do not auto-fail; do not
auto-pass. 1/15 = 6.7% sits cleanly below the §2.8 10% broken-scenario threshold; 2/15
exceeds it. The N-raise resolves the ambiguity that 1/5 cannot.

Rationale: the §2.8 broken-scenario threshold is `>2/20 = >10%` cap rate. At N=5, the 95%
Wilson-CI on 1/5 = 20% spans `[0.5%, 62%]` — it does not reject a 10% cap rate. Auto-
passing 1/5 would violate the spec's §5.3 no-margin condition. Auto-failing 1/5 would
discard a scenario that is likely calibrated (point estimate 5%) for a N=5 small-sample
artifact. The N-raise to 15 is the correct resolution.

*Scope: scenario calibration. C3 fix: "borderline PASS" clause struck.*

#### Criterion 3 — Carla deferral

Median `t_predicts ∈ [4, 8]` for `corner-abandonment-256` and `512-wall`; ≥ 4 for
`snake-collapse-128`. `t_predicts ∈ {0, 1}` on any scenario = fast-reaction failure
(panicking, not predicting) = grid still miscalibrated.

*Scope: scenario calibration. This criterion does not change from the original spec.*

#### Criterion 4 — operational health

**0 Carla aborts** in pilot N=15 (5 trials × 3 scenarios). Zero is the correct expression of
"abort rate < 5%" at this N: 5% × 15 = 0.75 < 1, so even a single abort exceeds the
threshold. Percentage notation was misleading at small-N; absolute count is unambiguous.

*Scope: harness health. This criterion does not change from the original spec.*

#### Criterion 5 — prediction-validity surrogate (H6 fix)

For each scenario, ≥ 4/5 Carla trials must satisfy **both**:

- `t_predicts` is finite (not `None`; not fast-react `∈ {0, 1}`); **AND**
- `game_over_move − t_predicts ≥ 2` (the prediction fires ≥ 2 moves before game-over).

Rationale: this is the N=5-scaled surrogate of ADR-0007 §Decision test 1's ≥ 17/20
prediction-validity gate. The threshold maps directly: 17/20 = 85%; 4/5 = 80% — same
proportional standard, N-adjusted. A pilot that omits every cognitive-architecture validation
gate from the real run is a Bot-calibration check, not a cognitive-architecture test. This
criterion ensures the pilot result says something about Carla's prediction signal, not only
about the scenario mechanics.

This criterion does **not** test whether `Δ ≥ 2` (the affect-earns-its-keep gate) — that
comparison requires paired Bot data at scale. It tests whether Carla's within-arm prediction
lead time is present at pilot scale. Pass on criterion 5 is a necessary but not sufficient
condition for the formal test 1 pass.

*Scope: cognitive-architecture validation gate. NEW — this is the H6 structural fix.*

### Pre-flight smoke step

Before the full N=5 batch, run 1 paired trial per scenario (3 trials total). **Halt** if any
of: any abort, any single trial `> $0.50` pre-call estimate, any `t_predicts ∈ {0, 1}`.
Cost: ≈ $0.15–0.30. Full spec in `2026-05-06-scenarios-recalibration-design.md §5.0`.

*Scope: operational efficiency gate. Not a pass criterion for the formal run.*

---

## Alternatives considered

### Keep "1/5 = borderline PASS" for snake-collapse (reject C3 fix)

Allow a single cap-violation in the 5-trial pilot to count as a pass with a user-review flag.

**Rejected.** The original borderline-PASS clause violated the spec's own §5.3 no-margin
condition. The statistical argument is decisive: the 95% Wilson-CI on 1/5 spans 0–62% and
does not reject cap-rate ≥ 10%. Auto-passing a result that is statistically compatible with
a broken scenario defeats the purpose of the pilot gate. The N-raise to 15 costs ~$3 and
resolves the ambiguity; it is the correct response to small-N uncertainty, not a lowered bar.

### Raise N_snake to 15 unconditionally for all pilot runs

Skip the 5-trial pilot for snake-collapse; go straight to N=15.

**Rejected.** Unconditional N=15 increases pilot cost by ~$6 regardless of whether the
recalibrated snake-collapse-128 grid has the cap problem at all. The 1/5 inconclusive rule
is a conditional N-raise — it fires only if the problem manifests. The correct approach is
N=5 first, N-raise only if warranted.

### Omit the prediction-validity surrogate (reject H6 fix)

Keep the original 4-criterion pilot gate (criteria 1–4 above). The formal test 1 will
validate the cognitive architecture at N=20.

**Rejected.** A pilot that passes criteria 1–4 confirms: Bot dies in the right window,
Carla doesn't abort, costs are in budget. It does not confirm that Carla's Anxiety signal
is present at the pilot scale and producing meaningful lead time. If criterion 5 fails at
N=5 (e.g., Carla has 0/5 finite t_predicts on a recalibrated scenario), the formal N=20
run would be authorised without any evidence the cognitive signal is detectable. Discovering
that failure at N=20 wastes the full-run budget. The surrogate costs nothing to measure —
it is read from the same CSV the pilot already produces.

### Use a stricter surrogate threshold — e.g., 5/5 instead of 4/5

Require all 5 pilot trials to pass the prediction-validity surrogate.

**Rejected.** 5/5 = 100% is a stricter gate than the formal run requires (85%). A single
anomalous trial (e.g., a seeded board with an unusually quick structural collapse) would
block authorisation. The 4/5 = 80% threshold matches the formal test 1's proportional
standard; it is the right N-scaled analog.

---

## Consequences

**Positive**

- Pilot gate now tests the cognitive architecture (criterion 5) in addition to the scenario
  mechanics and harness health. A pilot pass is informative about both what we are testing
  (the architecture's prediction signal) and the environment we are testing it in.
- The N_snake inconclusive rule is pre-committed — it cannot be softened retroactively once
  the pilot runs. This prevents the failure mode of "1/5 happened, we called it a pass."
- The workflow violation is closed: two methodology-level decisions that had been stranded
  in a spec are now in the ADR record.

**Negative**

- Criterion 5 adds one more CSV column to check post-pilot (`t_predicts` must be finite and
  `game_over_move − t_predicts ≥ 2`). Both values are already recorded by the harness
  per `2026-05-05-cliff-test-scenarios-design.md §2.7`; no code change required.
- The N-raise rule means snake-collapse-128 at 1/5 cap-violations will add ~$3 and ~15 min
  to the pilot sequence. This is the correct cost to pay for resolving an ambiguous result.

**Neutral**

- The formal N=20 run pass criteria (ADR-0007 §Decision tests 1 and 2) are **unchanged**.
  ADR-0010 adds pilot-specific gates that are prerequisites to the formal run, not replacements
  for the formal run's criteria.
- If snake-collapse-128 produces 0/5 cap-violations in the pilot, the N-raise rule is moot.
  The rule's cost is zero if the grid is well-calibrated.

**Reversibility**

- The five criteria are individually reversible via a follow-up ADR amendment if pilot data
  suggests a threshold is miscalibrated (e.g., if criterion 5's 4/5 floor proves unachievable
  on a correctly-calibrated scenario). Retroactive softening after a pilot run would require
  explicit user decision and a follow-up amendment, not a silent threshold change.

---

## References

- ADR-0007 §Decision — the formal-run pass criteria this ADR gates (tests 1 and 2);
  criterion 5 is the N=5-scaled surrogate of test 1
- `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md §5` — the spec
  section this ADR promotes to methodology-level authority; §5 is now historical context
- `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md §4.3` — M-04
  workflow note documenting the violation in place
- `docs/external-review/round-3-synthesis.md §7(b)#2` — C3 and H6 attacks that motivated
  the two new criteria
- `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md §5.3` — the original
  no-margin condition that the "borderline PASS" clause violated
