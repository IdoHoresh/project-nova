# ADR-0007: blind-control-group-for-cliff-test

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** ihoresh07@gmail.com (solo founder), principal engineer (red-team review)

---

## Context

The Phase 0.7 Cliff Test is the load-bearing falsification criterion for the entire Nova methodology — it answers the question "does the cognitive architecture *predict* human-style cliffs, or does it merely *narrate* them after the fact?" If it predicts, every downstream commercial claim works. If it narrates, the architecture is interpretable but commercially weak.

The original test design (per the methodology doc and the original 30-day-sprint plan) was single-armed:

- N=20 trials of the Casual Carla persona on 3-5 documented hard 2048 scenarios
- Record affect-vector trajectories
- Pass if Carla's `Anxiety > 0.6` event precedes her game-over move by ≥ 2 moves in > 80% of trials

The principal engineer red-teamed the test on 2026-05-04 and found a falsifiability gap: a single-armed test cannot distinguish "the cognitive architecture predicts" from "ANY agent fails at this threshold because the game's mechanics get harder past it." Carla could be reading the geometry of the board (number of free cells, distance to a forced merge), not its cognitive load — and her `Anxiety` peak might just be tracking the geometry. Without a non-affective control arm, an apparent pass is unfalsifiable: we cannot claim the affect layer earns its keep.

This is a methodology defect, not an implementation defect. Catching it before Week 1 begins prevents shipping a result that looks scientific but isn't.

The cost of fixing it is small: ~100 extra games per scenario × 3-5 scenarios = +300-500 games on the cliff test budget. At plumbing-tier pricing (~$0.05-0.10 per game) that is <$50 of additional spend. The cost of *not* fixing it is the entire commercial pitch: a single-armed cliff test "pass" cannot answer the question "what does Nova add over a stupid score-maximizer."

## Decision

**Adopt a Blind Control Group design for the Phase 0.7 Cliff Test. Run two persona configurations on the same seeded scenario, evaluate the cognitive architecture's prediction lead time over the non-affective baseline as the load-bearing pass criterion.**

### The two arms (per scenario)

| arm     | persona            | cognitive features active                               | what we record                                  |
|---------|--------------------|---------------------------------------------------------|-------------------------------------------------|
| test    | Casual Carla       | memory, affect, ToT deliberation, reflection            | full affect-vector trajectories per move        |
| control | Baseline Bot (NEW) | none — single purely-logical score-maximizer prompt     | move sequence + game-over move index only       |

**Baseline Bot prompt (definitive):**

> *"You are an AI agent playing 2048. Your only goal is to maximize score. Compute the next move."*

No affect, no memory retrieval, no ToT, no reflection. Same LLM model as Carla (so the comparison isolates the cognitive architecture, not the underlying intelligence).

### N and seeding

- N=20 trials per arm per scenario (matches the existing Carla N=20)
- Both arms run on the **same seeded board sequences** so the mechanics are identical and the only varying factor is the cognitive configuration

### Pass criteria (both must hold)

1. **Prediction-validity test (existing):** Carla's `Anxiety > 0.6` event precedes her own game-over move by ≥ 2 moves in > 80% of her N=20 trials per scenario.
2. **Affect-earns-its-keep test (new):** `Δ = t_baseline_fails - t_carla_predicts ≥ 2` moves in ≥ 3 of the 3-5 scenarios, where `t_carla_predicts` is the mean move index at which Carla's `Anxiety` first crosses `0.6` and `t_baseline_fails` is the mean game-over move index of the Baseline Bot.

### Failure modes (three branches)

- **Both pass:** architecture-as-predictor claim is alive. Demo / pitch line: "Baseline Bot failed at move 100, Nova raised the alarm at move 96 — 4 moves of warning your studio can use," with the actual `Δ` from the corpus.
- **Single-arm pass (Carla predicts, but `Δ < 2`):** architecture demoted to "architecture-as-narrator" — interpretable but not predictive. Reposition the demo around interpretability. No pitch conversations claiming prediction.
- **Both fail (no early Anxiety peak in Carla):** full failure of the prediction hypothesis. Two-week affect-rework branch per the original Week 1 fail path; no demo until rework completes and a follow-up cliff test passes.

### Tier discipline

The Cliff Test runs at `NOVA_TIER=production` (both arms — Carla AND Baseline Bot). The cliff test is exactly the cognitive-judgment work that `NOVA_TIER=plumbing` is **forbidden for** per ADR-0006: Flash-Lite's shallow reasoning would degrade Carla's affect curve and corrupt the falsification.

## Alternatives considered

- **Keep the single-armed test** (no control). Rejected — not falsifiable, can't distinguish prediction from mechanical exhaustion, can't survive a serious external review.
- **Use a different control persona** — e.g., a "random-move" bot or a "human-replay" persona. Rejected. Random-move would fail far before either Carla or Baseline Bot and tell us nothing about whether affect adds lead time. Human-replay would require a corpus we don't have. Score-maximizing baseline is the right control — same LLM, same scenario seeding, no affect; the only varying factor is the architecture itself.
- **Compare against ground-truth human churn data** instead of a synthetic baseline. Rejected for Phase 0.7 — we don't have human ground truth on these specific 2048 scenarios. Ground-truth-anchored validation is the Phase 4 KPI Translation work; Phase 0.7 is the synthetic-only validity gate.
- **Inflate N=20 to N=100** instead of adding a control arm. Rejected — solves precision but doesn't solve falsifiability. A 1000-trial single-armed test still can't distinguish prediction from mechanical exhaustion.
- **Delay the test until ground truth is available.** Rejected — cliff test is the load-bearing demo gate per ADR-0005; without it Phase 0.7 cannot exit. Synthetic baseline is the right scope for the time.

## Consequences

**Positive**

- Cliff test becomes scientifically falsifiable. The pass/fail decision answers a real question ("does affect add lead time over a non-affective baseline?") rather than a vacuous one ("did Carla's Anxiety peak before her game-over?").
- Pitch material gains a concrete number — `Δ` becomes the load-bearing slide, not "Nova has anxiety." Studios understand "4 moves of advance warning over a baseline" because it maps directly to "we can intervene before the cliff."
- Counter-positions Nova against nunu.ai more sharply: nunu's QA-replacement story doesn't claim affect-driven prediction. Nova's `Δ` over baseline is the differentiator nunu can't replicate without re-running their entire architecture.
- Surfaces a graceful failure mode: if `Δ < 2` we still have an interpretable architecture (architecture-as-narrator), just not a predictive one. Reposition rather than collapse.

**Negative**

- +300-500 games of cliff-test compute. Mitigation: still <$50 at production-tier pricing; well within the 6-week sprint budget.
- Adds Week 1 day-4-5 complexity — two arms running same seeds, comparison stat to compute. Mitigation: Game2048Sim is being built specifically for this; the second arm is N=20 more iterations of the existing harness with a different system prompt.
- The "single-arm pass" failure mode is harder to message externally. "We have an interpretable architecture but it doesn't predict cliffs faster than baseline" is a real outcome we have to be willing to ship honestly. Mitigation: methodology integrity is the moat; pretending a single-arm pass is a full pass would destroy us in any serious external review.

**Neutral**

- The `Δ ≥ 2` threshold and the "≥ 3 of 3-5 scenarios" are judgment calls. We commit to them now; if Phase 0.7 results suggest a different threshold would have been more informative, we document the change in a follow-up ADR rather than retroactively softening the original criterion.
- The Baseline Bot prompt is fixed at "maximize score, no affect" by ADR. Future variants (e.g., baseline with memory but no affect) require their own ADR to keep the experiment stable.

**Reversibility**

- Easily reversible. Removing the control arm reverts to the original single-armed test — no code dependencies on the Baseline Bot persona definition. If a future ground-truth-anchored validation makes the Baseline Bot redundant, this ADR is superseded by a new one.

## References

- ADR-0001 — cognitive architecture as product moat (the moat the Cliff Test validates)
- ADR-0002 — state-transition signatures (the methodology the Cliff Test rests on)
- ADR-0005 — defer v1 demo until Phase 0.7 passes (this ADR sharpens the gate Phase 0.7 must pass)
- ADR-0006 — cost-tier discipline (cliff test runs at `NOVA_TIER=production`, NOT plumbing)
- `docs/product/methodology.md` §4.1 — Cliff Test method (this ADR motivates the §4.1 update)
- `docs/product/product-roadmap.md` Week 1 — task list (this ADR motivates the two-arm task split)
- `docs/product/competitive-landscape.md` — nunu.ai counter-positioning (the `Δ` over baseline is the differentiator nunu cannot replicate without re-architecting)
- Principal engineer red-team review of the cliff-test design recorded in conversation transcript 2026-05-04.

---

## Amendment 1 — Baseline Bot operational refinements (2026-05-05)

**Status:** Accepted
**Companion artifact:** `docs/superpowers/specs/2026-05-05-baseline-bot-design.md`

### Why this amendment

The original ADR-0007 (above) pinned the high-level Bot shape — same LLM family as Carla, no affect / memory / ToT / reflection, two-sentence prompt — and left operational specifics to a follow-up spec. The Baseline Bot design spec (companion artifact) was authored through six rounds of red-team review and surfaced six load-bearing decisions that need methodology-level ratification. This amendment ratifies them.

### Pinned refinements

#### A1.1 Bot is LLM-based, not heuristic

The original "Alternatives considered" section evaluated random-move and human-replay baselines. Heuristic baseline (deterministic score-greedy / monotonicity-preserving) was raised in post-ADR red-team review and is rejected here for the same reason as random-move: a heuristic Bot would conflate "no cog-arch" with "no LLM at all," producing an unfalsifiable Δ on a different axis from the one this ADR was written to close. Cost discipline is addressed structurally via a cost-cap envelope handed to the Test Runner spec (Bot spec §4) rather than by model substitution.

#### A1.2 Bot prompt is extended with JSON-output instructions

The original two-sentence prompt — *"You are an AI agent playing 2048. Your only goal is to maximize score. Compute the next move."* — is preserved verbatim and extended with JSON-output directives matching the schema in A1.3. The full canonical Bot system prompt is recorded in Bot spec §3.1.

#### A1.3 Output schema and temperature

**Schema (per call, both arms):** `{observation, reasoning, action, confidence}` — the existing `_ReactOutput` shape in `nova_agent/decision/react.py:18-22`. Bot reuses this schema to close the per-call CoT-as-compute confound: denying Bot a `reasoning` field while granting it to Carla would impose a per-call compute asymmetry that is not part of the cog-arch bundle this ADR tests.

**Temperature:** Bot at `temperature = 0`; Carla at `temperature = 0.7` (her existing deployed configuration). The asymmetry is intentional and methodologically defended: Bot's prompt is sparser than Carla's (no memories, no affect text), so at the same temperature Bot's logit distribution would spread more; pinning Bot at temp = 0 forces greedy max-prob play and removes API stochasticity from the control arm. Variance contribution to Δ comes purely from spawn-schedule divergence (paired by trial seed, scenarios spec §2.2), not API sampling noise.

#### A1.4 Mixed ablation profile is a deliberate design choice

Phase 0.7 tests the **deployed** cognitive architecture as a bundle, not affect+memory in isolation:

- **Per-call compute is symmetric** (both arms use the same schema, same `reasoning` scratchpad, same response_schema enforcement).
- **Per-move compute is asymmetric** (Carla has ToT deliberation across multiple LLM calls per move; Bot is one-shot per move).

This mixed-ablation profile is the bundle-attribution scope per ADR-0001 (cog-arch as product moat) and ADR-0005 (Phase 0.7 as demo gate for the deployed product). It is **not** a contradiction: per-call asymmetry is incidental (CoT scratchpad is not part of the cog-arch); per-move asymmetry is the experiment (ToT is part of the bundle being tested).

The methodology paper preempts the hostile-reviewer bullet with: *"Per-call compute is symmetric to close incidental confounds; per-move compute is asymmetric by design — Carla has ToT as part of the bundle being tested. The bundle is the product."*

A side consequence the methodology paper also documents: ToT is one of affect's deployed channels (`decision/arbiter.py:should_use_tot(board, affect)` gates ToT on the affect vector). Disabling ToT for Carla in Phase 0.7 would therefore truncate affect's mechanism, not isolate it. Bundle-attribution is the right scope.

#### A1.5 Per-call retry/abort policy + trial-level abort policy

Per-call:
- **API errors** (timeout / 5xx / rate-limit): retry up to 3× with exponential backoff. If exhausted, **abort the trial**. Do not fall back to tie-break (would inject non-LLM decisions into the control arm and pollute the same-intelligence baseline).
- **Parse failures** (malformed JSON, schema-invalid): retry once. If exhausted, **abort the trial**. Do not fall back to tie-break.
- **Invalid moves** (legal parse, illegal action): apply UP > RIGHT > DOWN > LEFT tie-break per scenarios spec §2.3. Trial proceeds; LLM intent is recorded in telemetry alongside executed direction.

Trial-level: **no re-runs on abort.** Bot at `temperature = 0` + fixed scenario seed produces deterministic prompt sequences; re-running an aborted trial would reproduce the same parse failure deterministically and waste compute.

#### A1.6 Paired-discard logic — scoped to test 2 only

If trial `i` aborts in *either* arm, trial `i` is discarded from the paired Δ calculation (test 2, the affect-earns-its-keep test) in **both** arms. Test 1 (the prediction-validity test) operates on Carla's individual N=20 trials and is not paired-discarded by Bot-side aborts; Bot-side artifacts must not contaminate Carla's predict-self test. Test 1 excludes only Carla-side aborts.

#### A1.7 Threshold — ≥ 18 valid pairs per scenario

≤ 2 paired aborts allowed before a scenario is flagged as broken (matching the symmetric ≤ 2 right-censoring rule in scenarios spec §5.2 for operational pragmatism). Methodology paper documents the threshold and its rationale.

### What this amendment does NOT change

- The two-arm design (test = Carla, control = Bot).
- Same-seed trial pairing per index.
- N = 20 trials per arm per scenario.
- Pass criteria 1 (prediction-validity) and 2 (affect-earns-its-keep) at the high level. The amendment refines test 2's discard rule (paired) and threshold (≥ 18) but does not redefine the pass criterion's structure.
- The Bot's "purely-logical score-maximizer" intent.
- The "same intelligence" baseline rationale.
- `NOVA_TIER=production` requirement for both arms.

### Reversibility

- Each refinement is independently reversible. If pilot calibration on the three scenarios surfaces unexpected abort rates, the threshold (A1.7) is the most likely amendment surface.
- The temperature asymmetry (A1.3) is the most methodologically loaded refinement; if a future external review surfaces a stronger argument for symmetric temperatures, the amendment can be revisited.
- The mixed-ablation profile (A1.4) is the foundational design choice; reversing it would re-open Phase 0.7's purpose (demo gate vs ablation study) and require a new ADR rather than another amendment.

### References

- `docs/superpowers/specs/2026-05-05-baseline-bot-design.md` — companion spec with full operational detail
- `nova_agent/decision/react.py:18-22` — the `_ReactOutput` schema this amendment ratifies as Bot's output schema
- `nova_agent/decision/arbiter.py:should_use_tot` — the affect channel that grounds the bundle-attribution rationale (A1.4)
- Six-round red-team review of the Bot spec recorded in conversation transcript 2026-05-05.
