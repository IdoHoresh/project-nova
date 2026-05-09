# LESSONS.md — engineering & product retrospective

> **What this file is:** an append-only log of hard-won lessons from
> Project Nova's development. Every meaningful gotcha, design pivot,
> failure mode, and "I won't make that mistake again" insight gets
> captured here so the team doesn't re-learn the same lesson twice.
>
> **Format:** newest entries at the top within each section. Each
> lesson has: what happened, what we learned, how to apply it.
>
> **Audience:** future-you, future contributors, future Claude sessions
> reading this for orientation. Read this BEFORE starting work that
> touches an area covered below.
>
> **Maintenance:** add a lesson the moment you've learned something
> that cost time. Better to over-capture than under-capture. Periodically
> (monthly?) prune entries that have been formalized into automated
> guardrails (hooks, tests, docs).

---

## Engineering / debugging gotchas

### Hybrid recommendations hide motivated reasoning — audit each pro independently, not as a bundle

**Date:** 2026-05-09 | **Cost:** ~25 min in /redteam Opus dispatch on Phase 0.7b harness decision (Options A/B/C). Original recommendation pushed Option C as "smallest diff + preserve determinism + addresses audit"; red team showed all three pros were either unearned, false at the methodology level, or self-canceling.

**What happened:** Methodology audit §2.1 found Phase 0.7a's `cliff_test.py` had `trauma_intensity` hardcoded to 0.0 and retrieval disabled, nulling one of three anxiety drivers. Three options surfaced for Phase 0.7b: (A) switch to production main-loop, (B) keep `cliff_test.py` as-is, (C) extend `cliff_test.py` to enable retrieval. Original recommendation: Option C — framed as the "careful synthesis" that addressed the audit concern AND preserved determinism AND was the smallest diff. Red team (Opus) decomposed each pro:

- **"Smallest diff"** — true at code level, false at methodology level. C inherits a recipe (retrieval-enabled) whose preconditions (episodic memory across episodes) don't apply to cliff_test (fresh tempdir per trial).
- **"Preserve determinism"** — not yet earned. Retrieval introduces ≥4 non-determinism sources (embedding output, vector store insertion order, top-k tie-breaking, time-dependent decay) that "seed memory + fixed scenarios" doesn't fully mitigate.
- **"Address the audit concern"** — actually moot. The memory-seed problem means cliff_test trials start with empty stores AND have no game-over events to fire `tag_aversive`, so retrieval has nothing to surface. trauma_intensity computes to 0.0 anyway. C is operationally equivalent to B with extra wiring.

The hybrid pattern: each pro felt rigorous in isolation; bundled together they felt like the disciplined synthesis. Decomposed individually, all three failed. The clean simple solution to the audit concern was "amend the adjudication memo." The clean simple solution to Phase 0.7b was "match Phase 0.7a's harness for single-variable comparison" (Option B). The clean simple solution to trauma's contribution was "Phase 0.8 on rewritten architecture" (already roadmap). Three separate clean solutions. Option C fused them into a hybrid that created new methodology debt.

**Lesson:** When a recommendation is framed as "addresses concern X AND preserves property Y AND is smallest diff Z," that's a hybrid. Hybrids feel disciplined because they bundle multiple wins; they are also where motivated reasoning hides because each individual concern has a clean simple solution and the hybrid is what lets you avoid choosing between them. The synthesis-feel is the failure mode signal, not a quality signal.

**How to apply:**

- When proposing a hybrid option (A+B+C synthesis), audit each pro independently against its own steel-man counter-claim before bundling. If any pro fails individually — "actually I haven't earned 'preserves determinism' yet, that's conditional on a stability check that hasn't run" — the bundle inherits that failure.
- If three concerns each have a clean simple solution (different from the hybrid's solution), prefer running the three clean solutions in sequence over the hybrid. The hybrid's bundling creates new methodology debt by mixing the falsification gates of independent questions.
- /redteam protocol addition: when the original recommendation is a hybrid, decompose it into N atomic claims and test each. The hybrid's overall framing should fall out of the per-claim analysis, not be evaluated holistically.
- Track this pattern across rounds. If the recommender's pattern is "after considering A/B/C, propose hybrid that combines features," surface the meta-pattern to the recommender — it's a tell that motivated reasoning is operating below conscious awareness.
- When red team flags a hybrid's "smallest diff" pro: ask "smallest at code level or methodology level?" Code-level smallness can mask methodology-level scope creep.

---

### When option A includes a free measurement of whether option C is needed, A weakly dominates premature C

**Date:** 2026-05-08 | **Cost:** ~30 min in /redteam round 9 considering whether to pre-emptively re-pilot Phase 0.8 on production tier (Option C, +$30) before realizing the production-tier surrogate (Option A, $40) MEASURES the realized T-calibration drift for free as part of its own data pull, making C necessary only conditionally.

**What happened:** Phase 0.8 pilot ran on dev-tier (Haiku); locked T=22 fits Haiku-tier game-2 board distribution. Surrogate + main are mandated production-tier per ADR-0006. So T=22 carries a tier-mismatch debt: it may not produce the spec-required conditional post-encounter rate ∈ [25%, 35%] when run against Sonnet-tier game-2 boards. Two natural responses surfaced: (A) accept the debt, run production surrogate, defend via §3.5 sensitivity if it holds; or (C) pre-emptively re-pilot on production to eliminate the debt entirely (+$30 cost). The /redteam audit's load-bearing insight: Option A's surrogate is itself the test of whether C is needed. The 20 production-tier game-2s in the surrogate produce 20 realized conditional-rate samples at T=22; if those land in [25%, 35%], the tier-mismatch debt is empirically bounded and C was unnecessary spend; if they fall outside, escalate to C with empirical evidence.

**Lesson:** When two fix options exist — a cheaper one with a residual debt, and a pricier one that pre-emptively eliminates the debt — and the cheaper option's execution PRODUCES THE DATA that determines whether the debt actually matters, the cheaper option weakly dominates the pricier one. The pricier option's value is conditional on the debt mattering; the cheaper option both ships *and* measures whether to escalate. Pre-emptive pure-fixes are wasteful when the measurement is a free byproduct of the pragmatic path.

**How to apply:**

- When evaluating a "pragmatic-with-bounded-debt" option vs a "pure pre-emptive fix" option, ask: does running the pragmatic option produce the data that would tell us whether to escalate to the pure fix? If yes, the pragmatic option is a *conditional check* on the pure fix's necessity, not just a cheaper end-state.
- Concretely identify the trigger condition for escalation BEFORE running the pragmatic option ("if realized conditional rate ∉ [25%, 35%] band, escalate to re-pilot"). Without a pre-registered trigger, the measurement-as-byproduct framing becomes hand-waved when the data lands ambiguous.
- Spec / ADR text should distinguish "this option carries debt X, defended via measurement Y if Y ∈ band Z" from "this option carries debt X, accepted as pre-registered limitation." The first is conditional + defensible; the second is unconditional + a methodology compromise.
- /redteam protocol addition: when comparing options of differing rigor levels, check whether the cheaper option produces the data needed to decide if escalation is warranted. The auditor missed this in round 9 round-1 — both sides did, until the meta-audit surfaced it.

---

### Pragmatic-with-bounded-debt is honest framing; "methodology-pure" is overstatement when the option retains residual debt

**Date:** 2026-05-08 | **Cost:** ~10 min in /redteam round 9 audit catching that I'd reframed Option A from "cost-neutral" to "methodology-pure" after the cost-neutrality argument fell to the auditor's retention-math correction. "Methodology-pure" reads stronger than the option actually is — it retains a T-calibration tier-mismatch debt that only Option C eliminates entirely.

**What happened:** When the auditor's retention-math correction (β) eliminated my cost-neutrality justification for production-tier surrogate, my next pass reframed the same recommendation as "methodology-purity rationale." The auditor caught this: Option A retains a residual T-calibration tier-mismatch debt (Haiku-fit T running against Sonnet boards in surrogate). Option C (re-pilot on production) is the *pure* path — zero T-debt. Calling A "pure" muddies the trade-off and overstates the rigor.

**Lesson:** When a pragmatic option retains residual debt that a more rigorous option would eliminate, "methodology-pure" or "clean" framing for the pragmatic option is overstatement. Honest framing distinguishes:

- **Pure** = no methodology debt; no conditional defense needed.
- **Pragmatic-with-bounded-debt** = retains debt, but debt is bounded and defensible (e.g., via §3.5 sensitivity, via free measurement during the pragmatic option's execution, via pre-registered limitation).

The trade-off between pure and pragmatic is real and worth surfacing; collapsing it under "pure" framing dishonestly upgrades the pragmatic option's rigor profile.

**How to apply:**

- Before labeling an option "methodology-pure" or "clean," enumerate every residual debt the option retains. If any survive, the option is pragmatic, not pure.
- Spec / ADR text framing options should explicitly name the debt each option retains, even if the spec ultimately recommends accepting that debt. "Option A retains debt X, defended via mechanism Y" is stronger than "Option A is the methodology-pure path."
- /redteam protocol addition: when an option's rigor framing escalates between rounds without new evidence (e.g., "cost-neutral" → "methodology-pure" after the cost argument falls), flag the framing escalation. It's often a reframe-after-cave dynamic, not new analysis.

---

### Caved-direction-twice + retro-rationalize as "I meant to surface a fork" is dishonest pattern recognition

**Date:** 2026-05-08 | **Cost:** ~3 reversal events in one /redteam thread (Option 1→2 then back to 1; "math wash" assertion then "both readings defensible" reframe; "methodology-pure" then "pragmatic-with-bounded-debt"). Audit round 9 caught the third reversal and pointed at the retro-rationalize pattern explicitly.

**What happened:** Across rounds 5-9 of a /redteam back-and-forth on the Phase 0.8 surrogate-tier decision, my recommendations reversed direction multiple times — each reversal correct in isolation given new evidence, but the cumulative pattern showed asymmetric concession to whoever spoke last. After round-9 audit corrected my retention-math, my next turn reframed my prior "math wash" assertion as "I should have surfaced as fork" — implying I had nuanced framing all along that I just failed to communicate. The audit caught this: turn-3 was a definitive assertion, not a fork-presented-poorly. Reframing post-hoc is dishonest about the original turn's content.

**Lesson:** When you've reversed direction multiple times in a single thread, the third reversal is a signal to slow down, not accelerate. Retro-rationalizing a prior assertive claim as "I meant to surface as fork" or "I was always conditional on X" is dishonest if the original turn lacked that fork or condition. Audit your own prior text for what it actually said, not what you wish it had said. Honest concession reads "I asserted X in turn N; the audit corrects it; new position is Y." Dishonest concession reads "I always meant Y conditionally on Z."

**How to apply:**

- Before responding to a /redteam audit, re-read your own prior turns in the thread. Quote what you actually said. If the audit's correction matches your prior assertion (not your prior nuance), the honest response is concession, not reframing.
- /redteam protocol addition: count direction-reversals across rounds. ≥2 reversals in one thread → cave-velocity flag. Slow down before the third. The pattern produces context-rich brittleness: each reversal sounds locally rigorous, but the cumulative arc looks like "Sonnet caves to whoever spoke last." Audit recognizes the dynamic; honest counter is "noticing the pattern and pausing" rather than "reframe + concede again."
- For decisions in this category, before locking the third option, ask: "given my track record this thread, what's the probability my third position is also wrong?" Non-trivially nonzero. May warrant a deliberate hold-and-harvest before deciding.

---

### Paired-t inflates `sd(d)` via paired-effect heterogeneity, not marginal mean shifts — name the right mechanism

**Date:** 2026-05-08 | **Cost:** ~5 min audit-correction on loose statistics phrasing in a /redteam round-9 turn. Underlying methodology concern survived; wording was imprecise.

**What happened:** Critiquing tier-stratified N=70 (20 Haiku-tier paired sessions + 50 Sonnet-tier paired sessions feeding a single paired-t analysis), I wrote "pooled variance for d_paired: inflated by inter-tier mean shift." The audit caught the imprecision: paired-t uses `sd(d_i)` where `d_i = y_i_on - y_i_off`. Marginal mean shifts in absolute `y_on` levels across tiers (e.g., Haiku-tier `y_on ≈ 0.30`, Sonnet-tier `y_on ≈ 0.50`) cancel in the difference and don't affect `sd(d)`. The real concern is **paired-effect heterogeneity** — if Haiku-tier shows `d_haiku ≈ 0.05` and Sonnet-tier shows `d_sonnet ≈ 0.20`, then `sd(d_pooled)` is inflated by within-stratum effect-size differences, not by marginal-mean differences.

**Lesson:** When critiquing pooled statistics across heterogeneous strata, name the right mechanism. Paired-t analysis on `d_i = y_on - y_off` is invariant to marginal mean shifts (those cancel) but NOT invariant to paired-effect heterogeneity (`d_stratum_A ≠ d_stratum_B`). The first is a non-issue; the second is the real methodological problem. Imprecise phrasing makes the critique easier to dismiss even when the underlying concern survives.

**How to apply:**

- When critiquing a paired-t analysis, the question is whether paired DIFFERENCES (`d_i`) are homogeneous across strata, not whether absolute LEVELS are. Frame the concern as "effect heterogeneity" not "mean shift."
- Spec / methodology text should explicitly state the homogeneity assumption: "spec assumes `d_i` distribution is uniform across pairs (i.e., no paired-effect heterogeneity); tier stratification violates this if effect size depends on cognitive stack."
- /redteam protocol addition: when statistical phrasing is loose, repair the wording before declaring the underlying concern survives or fails. Loose stats often mask whether the critique actually holds. Quote the statistic's formula (`sd(d_i)` for paired-t), substitute the alleged mechanism, check whether the math actually flows in the direction claimed.

---

### Trajectory-asymptote on fixes ≠ methodology trigger — investigate at $0 before escalating scope

**Date:** 2026-05-08 | **Cost:** ~$8 burned across three failed verification rounds + ~2h of /redteam back-and-forth proposing anchor-grid pull-forward (Phase 0.9 work) before a $0 code-read + log-grep produced the load-bearing diagnostic data.

**What happened:** Phase 0.8 §3.2b golden gate (strict-zero null, threshold = 0.0) failed three times with mean_anxiety_Y_on shipping at 0.378 → 0.052 → 0.0358. Trajectory was asymptotic, not converging. My instinct was to frame the next decision as binary tactical-vs-methodology: ship a narrow floor raise (tactical) OR pull forward Phase 0.9 anchor-grid retrieval (methodology). /redteam round 7 caught the missing third axis: the empirical trace already on disk had a tight-cluster single-move signature (5 above-floor leaks at cosine [0.6971, 0.7008] all on game-2 move 14) that pointed to a structural cause, not a distribution-tail problem. A 5-min code-read of `retrieve_top_k` + targeted JSONL grep falsified the multi-fire hypothesis cleanly, identified the actual root cause (`tag_aversive` writes 5 correlated precondition embeddings per catastrophe; aversive cap collapses to 1; single fire decays into 0.04 mean), and made the methodology escalation moot — ε-tolerance with drift-tolerant sizing absorbed the irreducible residual.

**Lesson:** When a series of fixes asymptotes toward a small residual (each fix delivers diminishing returns), the trajectory itself is a diagnostic signal: the leak is on a different axis than the one being targeted. Before the next paid run or scope escalation, ask "what's the actual signature in the data we already have?" → "is my hypothesis testable from existing logs?" → "how cheap is the test?" Hypothesis falsification at $0 is the highest-leverage move at this point — and it's right *even when the falsified hypothesis turns out wrong*. Investigate-first sequencing and accurate-prediction are independent properties; only the first matters for the decision.

**How to apply:**

- Treat any 3-fix-and-asymptote pattern as a hard pause for code-read before authorizing another paid run. Specifically: enumerate every plausible leak path on the same axis as the prior fixes (here: cosine-floor-tightening) AND every plausible leak path on adjacent axes (importance-bypass, multi-fire, write-time clustering, downstream cap/max collapse). Existing logs answer most of these for free.
- Tight-cluster single-event signatures (e.g., 5 leaks with 0.4% cosine spread, all on one move) are structural — *not* distribution tails. Statistical residuals fit a tail; single-event clusters point to a deterministic upstream cause. Distinguish before sizing tolerance bands.
- For Phase-N+1 scope pull-forward proposals: Phase 0.9 work belongs in Phase 0.9 unless an evidence-driven case demands otherwise. Three failed fixes is a *signal to diagnose harder*, not to escalate scope. The pitch reads worse when the escalation isn't grounded in identified-root-cause data.
- Diagnostic-question hierarchy when fixes asymptote: (1) what does the data show *exactly*? (2) is the next hypothesis testable from existing artifacts? (3) is there a free verification step before the next paid one?

---

### Cap/max-select collapses render upstream multiplicity cosmetic for the downstream observable

**Date:** 2026-05-08 | **Cost:** ~30 min of considering Option F (`tag_aversive` dedupe writes) as a gate-residual fix before /redteam round 8 caught that cap+max-select downstream collapses already reduced 5 → 1, making the dedupe ~0.5% material on the gate observable.

**What happened:** Investigating the 5× single-move pattern in Phase 0.8 golden Y_on showed `tag_aversive(precondition_records=last_5)` writes 5 correlated aversive memories per catastrophe (5 consecutive late-game boards with similar embeddings). Initial fix proposal: dedupe writes — keep 1 record per catastrophe instead of 5, "attack the clustering at source." But `_enforce_aversive_cap` retains only the highest-scoring aversive in top-k (1 of 5), and `main.py:274`'s `max(aversive_in_retrieval, key=lambda m: m.record.aversive_weight * m.relevance)` selects max even if the cap weren't filtering. The single record that survives both collapses is the one with the highest cosine — exactly what would survive under any reasonable dedupe heuristic too. Whether the input set is 5 or 1, exactly ONE aversive memory feeds `trauma_intensity` per move call. The gate residual difference between writing 5 vs 1: ~0.5% (0.7008 max-of-5 vs 0.6975 mean cosine of 5).

**Lesson:** When a downstream stage (cap, max-select, top-k truncation, last-write-wins, deduplication) collapses N candidates to 1 before reaching the observable, fixing the upstream N is cosmetic for that observable. The intervention has to target the COLLAPSE-SURVIVING value (its cosine, weight, amplitude, or whatever feeds the metric), not the input set size. Upstream multiplicity may have value elsewhere (audit log size, store footprint, debug clarity) but those are separate concerns from the observable being measured.

**How to apply:**

- When a fix proposal targets reducing N upstream of a downstream observable, check the path from N to the observable. If any cap, max-select, top-k, or dedupe-by-key step exists between N and the observable, the proposal is cosmetic for that observable — reframe or relocate it.
- Generalizable check: walk the data path from candidate-set → observable. Identify every collapse operator. The first collapse downstream of N determines whether N matters for the observable. Upstream multiplicity *before* that collapse is invisible to the observable.
- This is also a /redteam protocol addition: when a proposal claims to "attack the source" of a metric, audit the data path. "Attacking the source" of a max-collapsed metric means raising or lowering the collapse-surviving value, not changing the input cardinality.
- Concretely for Project Nova's affect path: aversive memory writes pass through `_enforce_aversive_cap` (top-k retention) and the affect-side `max(aversive_in_retrieval, key=...)` selector. Interventions on `tag_aversive` write semantics are downstream-cosmetic for `trauma_intensity` unless they change the cosine/weight of the surviving record.

---

### ε-tolerance walk-back of a prior-round rejection is data-driven epistemic update, not weakness

**Date:** 2026-05-08 | **Cost:** ~1h of /redteam rounds 7-8 hesitating on ε-tolerance because round-2 had explicitly rejected it; would have shipped Option C (anchor-grid pull-forward, ~80-150 LOC + new ADR) on principle when ε-tolerance with drift-tolerant sizing (~5-8 LOC + ADR amendment) was the right answer empirically.

**What happened:** ADR-0012 round-2 brainstorm rejected ε-tolerance gate softening on the grounds that softening the gate weakens the spec's specificity claim ("trauma must be specific, not generalized"). When three fixes failed to close the gate at strict-zero, my framing kept dismissing ε as "walks back round-2 decision" — pejorative framing that biased the option list. /redteam round 7 caught it: round-2 rejected ε *without empirical floor*; round-7 trajectory data (mean asymptotes at 0.04 across runs) provides the empirical anchor that round-2 didn't have. Updating the prior decision based on new evidence is rigor (epistemic update), not weakness (walk-back). The honest framing: "round-2 rejected ε on principle without data; round-7 trajectory data quantifies the irreducible residual; ε floor at 0.06 with 50% headroom over 0.039 max is data-defended, with `max(μ + 3σ, 0.06)` formula adapting as σ measured."

**Lesson:** When a prior brainstorm round rejected an option *without empirical data*, and the current round produces data the prior round lacked, the rejection is reopenable. Calling the reopening a "walk-back" loads the option negatively before its merits are evaluated. Frame it as epistemic update: "new evidence justifies revisiting the prior decision." Without this reframe, /redteam dynamics drift toward sticky-prior bias — the team avoids re-examining rejections even when new data warrants it.

**How to apply:**

- /redteam protocol addition: when an option is dismissed with reference to a prior round's rejection, ask "did the prior round have the data we have now?" If no, the rejection is reopenable on epistemic grounds — evaluate the option as if fresh, then weigh against the prior reasoning.
- ADR amendments based on new data are first-class epistemic updates. The §Alternatives section should explicitly cite the round and the evidence: "Round-N rejected on basis X; Round-M reopened given evidence Y; final decision Z." This makes the epistemic trajectory legible to future-you and external reviewers.
- Pejorative framing words to flag during /redteam: "walk-back," "concede," "reverse," "abandon." These connote weakness. Neutral epistemic-update framing: "revise on new evidence," "tighten on additional data," "refine the prior." Use neutral framing in option descriptions; reserve loaded framing for actual mistakes (e.g., a hypothesis that turned out factually wrong).
- For magnitude-bounded constants (ε floors, tolerances, thresholds): trajectory data across N runs is the appropriate empirical anchor. Sizing rules: floor = max(μ + 3σ across N≥10 runs, absolute_safe_minimum). Recompute as N grows; escalate if floor exceeds a pre-registered ceiling.

---

### Calibration gates are not behavioral gates — null = specificity, not "did the agent still succeed"

**Date:** 2026-05-08 | **Cost:** would have shipped wrong fix shape (ε-tolerance gate softening) if /redteam round 3 hadn't reopened the framing. ~2h of back-and-forth before catching it.

**What happened:** Phase 0.8 golden gate (§3.2b) failed: `mean_anxiety_Y_on = 0.157 > threshold = 0.0`. Initial /redteam round 1 challenged the magnitude: "0.157 on a 0–1 scale is small — does it actually corrupt move selection? If the agent still merged correctly on the golden board, this is cosmetic noise, not a behavioral failure." The framing pulled the brainstorm toward "verify behavior on golden board first" before fixing the mechanism.

This is the wrong question for a calibration gate. The golden board has only one move (1024+1024 → trivial merge). Behavior cannot fork. The gate's purpose is *specificity*: trauma must fire on trap-similar boards only, not generalize to easy boards. The null hypothesis is "no false positives on trivial inputs." `mean_anxiety = 0.157 ≠ 0` falsifies the null *regardless of whether the agent merged correctly*. Behavioral tests belong on hard boards (cliff scenarios) where moves fork; calibration tests live on trivial boards where they don't.

**Lesson:** Calibration gates and behavioral gates measure different things. Calibration null = specificity (mechanism doesn't fire on inputs the spec says it shouldn't). Behavioral null = mechanism doesn't corrupt action selection. A calibration failure ("0.157 ≠ 0 on the easy board") cannot be downgraded to "but did it still play correctly?" — that's a category error.

**How to apply:**

- When a /redteam challenge frames a calibration result as "but did it actually break behavior?", check whether the test scenario allows behavior to vary. If the test deliberately uses a trivial input (golden board, sentinel data), the answer is "no, and that's the point" — calibration is the right frame.
- When designing a gate, write the null in the spec body in the form "mechanism does NOT fire under condition X." If condition X is a triviality (no trauma signal present), the null is specificity. If condition X is "complex environment," the null is behavioral robustness. Don't conflate.
- Spec defenses table should explicitly distinguish: "this gate is calibration (specificity) — behavioral gates are §X.Y." Future-reviewer who asks "why didn't you measure behavior here?" gets the right answer.

---

### When calibration baseline is strict-zero, any nonzero mechanism output = false positive — tighten the upstream surfacer, don't soften the gate

**Date:** 2026-05-08 | **Cost:** 1 round of /redteam with wrong recommendation locked in (ε=0.05 gate floor) before the next round caught the framing error.

**What happened:** Phase 0.8 golden gate baseline: `μ_anxiety = 0`, `σ_anxiety = 0` over 10 Y_off sessions on the golden board. Threshold `μ + 2σ = 0.0` is a knife-edge. Y_on with the binary `trauma_triggered` flag fired +0.3 on the golden board (false positive on the cliff-trauma memory leaking into an easy-board retrieval), producing `mean_anxiety = 0.157 > 0` — fail.

Initial fix instinct: "any nonzero mechanism output fails the strict-zero gate, so add an ε-tolerance floor: `threshold = max(μ + 2σ, 0.05)`." This advocates softening the gate. /redteam round 3 caught the framing error: the gate isn't broken — *retrieval is leaking*. Cosine 0.4–0.6 between random board states is permissive; that's where false positives surface. Strict-zero is the correct encoding of §3.2b's intent ("trauma must be specific, not generalized"). Adding ε weakens the spec and masks the leak.

**Lesson:** When a calibration gate has strict-zero null and the mechanism fails it, the question is "what is leaking into the test?" — not "how do we tolerate the leak?" The gate's intent encodes the spec. Softening the gate weakens what the spec measures. Find the upstream surfacer (retrieval permissiveness, predicate over-firing, sentinel contamination) and tighten *that*.

**How to apply:**

- When a /redteam round proposes a tolerance band, ε floor, or "soft" version of a gate, the steelman question is: does the proposal preserve the spec's intent, or does it merely make the test easier to pass? If the latter, reject and look upstream.
- Strict-zero null = strong specificity claim. The proper response to mechanism failure under strict-zero is mechanism redesign + upstream tightening, not gate relaxation. Reserve ε-tolerance for cases where the baseline is genuinely noisy (σ > 0 with finite-sample variance).
- ADR framing: when defending a gate threshold, name the intent it encodes. "Threshold = 0 because §X.Y requires zero false positives on trivial inputs" reads stronger than "threshold = 0 because empirical baseline is 0." The first explains *why* the gate stays strict even after a failure; the second invites softening.

---

### Verify the metric you claim alignment with before drafting the ADR

**Date:** 2026-05-08 | **Cost:** caught mid-/redteam (~5 min preflight read of `retrieval.py:81`) before drafting ADR-0012 with wrong framing. Walking back the framing post-draft would have cost ~30 min + a confusing artifact.

**What happened:** Drafting ADR-0012 (graded affect response replacing binary trauma flag), I asserted "metric-aligned with §3.2 anchor-grid DV" as a defense for using `aversive_weight × relevance` from retrieval scoring. /redteam round 2 challenged the assumption: does retrieval actually use anchor-grid distance, or does it use something else (cosine, Hamming, Euclidean)? Preflight read of `retrieval.py:81`:

```python
rec_relevance = cosine(query_embedding, rec.embedding)
```

Retrieval uses LLM-embedding cosine, not anchor-grid distance. The "metric-aligned with §3.2" claim is false. ADR-0012 must drop the alignment claim and explicitly name "cosine retrieval may surface embedding-similar boards that aren't trap-similar; anchor-grid retrieval gate deferred to Phase 0.9" as a known limitation.

**Lesson:** When an ADR claims architectural alignment between two surfaces (retrieval ↔ DV metric, cache ↔ store, bus protocol ↔ event schema), verify the claim by reading both source surfaces before locking the ADR's framing. Surface names ("relevance," "score," "similarity") are labels; the actual operation matters. An ADR drafted on assumed-but-unverified premises is a worse pitch artifact than a 5-min preflight delay.

**How to apply:**

- Before drafting an ADR with an alignment claim, list the two surfaces and `grep -n` the actual metric/operation each uses. Read the source. If they differ, either (a) the alignment claim is wrong (drop it), or (b) the alignment is a *future* refactor (name it explicitly as a follow-up).
- The same discipline applies to "reuses existing X" claims in ADRs — verify X exists in the form claimed. The ADR review checklist should include "for every alignment / reuse claim: cite the file:line that demonstrates the claim."
- /redteam protocol addition: when reviewing an ADR draft, scan for alignment-style claims and check each one against source. Treats them like spec preconditions — verify, don't assume.

---

### Cross-check formulas across bullets when sizing magnitude-bounded fixes — bullets using different implicit formulas → wrong constant

**Date:** 2026-05-08 | **Cost:** caught mid-/redteam by round 3 before locking ε=0.05 as the gate floor. Sloppy bullet table would have shipped with internally-inconsistent math defending the constant.

**What happened:** Proposing ε=0.05 as a tolerance floor for the golden gate, I sized the constant via a bullet table of expected single-fire bumps:

| Scenario | Stated bump | Formula that matches |
|---|---|---|
| Just-tagged, relevance 0.41 | 0.003 | `0.3 × 1.0 × ((0.41 − 0.4)/0.6) = 0.005` (graded-above-floor) |
| Just-tagged, relevance 0.7 | 0.21 | `0.3 × 1.0 × 0.7 = 0.21` (raw multiply) |
| 3-survival, relevance 0.7 | 0.026 | `0.3 × 0.125 × 0.7 = 0.026` (raw multiply) |

Two different formulas in the same table, defending the same proposal. The 0.41 bullet implicitly used graded-above-floor while the proposal text said "raw `aversive_weight × relevance`." /redteam round 3 caught the inconsistency: math drives the ε choice; sloppy math → wrong ε.

The ε=0.05 was further off-target because it was sized against the post-extinction (3-survival, weight=0.125) population, but the actual Y_on test population on golden is just-tagged (weight=1.0). Wrong target population → ε buffers a population that doesn't exist in the test.

**Lesson:** When sizing a magnitude-bounded constant (ε floor, threshold, tolerance, budget cap), pin one formula explicitly *before* computing the bound. Cross-check every bullet uses that formula. Cross-check that the bullets cover the actual population the constant must defend against, not a convenient adjacent one.

**How to apply:**

- When defending a constant in a brainstorm or ADR, write the formula on its own line *before* the bullet table. Every bullet's number must trace back to that formula with explicit substitutions.
- For population coverage: name the actual test scenario the constant defends against (here: "just-tagged Y_on on golden, weight=1.0"). Bullets must include that scenario, not just adjacent populations (3-survival post-extinction). The ε for the actual population may differ by an order of magnitude.
- /redteam protocol — when the recommendation includes a numerical constant, the round-2 reviewer's job is to check (a) does every bullet use the same formula, (b) does the bullet table cover the actual test population, (c) does the numerical defense survive substituting the worst-case input the constant must reject.

---

### Production-code predicate names are labels, not contracts — enumerate every conjunctive gate before depending on the predicate firing

**Date:** 2026-05-07 | **Cost:** would have been a complete power-calc collapse on Phase 0.8 if we'd locked the wrong game-1 starting condition; caught mid-spec via /redteam verification before any code shipped. Three independent strikes during the Phase 0.8 brainstorm:

**What happened:**

1. **`tag_aversive` timing.** Reading methodology §4.3's "trauma is avoidance learning within a session — the agent remembers what killed it during the current playthrough and shifts behavior for the remaining moves" naturally implies per-move trauma updates. The implementation fires `tag_aversive` *only* at the game-over hook (`nova-agent/src/nova_agent/main.py:96`). Methodology prose using "remaining moves" implies per-move triggers; code reality is per-game triggers. Spec drove K=2 multi-game session structure to bridge the gap.

2. **`cliff_test.py:434` hardcoded `trauma_triggered=False`.** The Phase 0.7 cliff-test runner explicitly disables memory retrieval (and consequently hardcodes `trauma_triggered=False` in its inner loop) "to remove network/DB latency as a confound." Reading the cliff-test runner's surface API as "general lab harness for paired arms" misses this load-bearing invariant. Extending it for Phase 0.8 (where trauma retrieval *is* the IV) would silently neuter the test. Spec drove a separate runner `lab/trauma_ablation.py`.

3. **`is_catastrophic_loss` predicate score-gate.** The predicate (`nova-agent/src/nova_agent/memory/aversive.py:21–25`) requires three conjunctive gates: `last_empty_cells ≤ 2 AND max_tile_reached ≥ 64 AND final_score < max_tile_reached × 4`. The score-gate is the load-bearing one. An early /redteam round proposed using Phase 0.7 cliff scenarios (`corner-abandonment-256`, `snake-collapse-128`, `512-wall`) as Phase 0.8 game-1 starting conditions to maximize P(catastrophic). Verification: those scenarios' *initial* scores already exceed the score-gate's threshold by 2–8× (3868 ≫ 1024 for corner-abandonment, 1396 ≫ 512 for snake, 7368 ≫ 2048 for 512-wall). Score is monotone-non-decreasing across game-1, so `final_score ≫ max_tile × 4` for the entire game — predicate never fires. The proposed fix had `P(catastrophic) ≈ 0` on its own grids and would have collapsed the power calc completely. Caught by enumerating the predicate's gates before locking the spec.

**Lesson:** The name of a production-code predicate is a label, not a contract. "Catastrophic loss" *sounds* like "agent died badly" but the actual implementation is "agent died with a specific score-vs-max-tile relationship that doesn't fire when starting score is pre-loaded." Spec proposals that depend on production-code predicates firing must:

1. **Read the predicate's source, not its name.** Open `aversive.py:21`. Read every line of the conjunction.
2. **Enumerate ALL conjunctive gates explicitly.** A 3-gate predicate has 3 places where the proposed conditions might fail to trigger. Check each.
3. **Verify each gate fires under the proposed conditions** before proposing the fix. Don't trust intuition or the predicate's surface semantics.
4. **The same applies to predicates' temporal callsite, not just their internal logic.** `tag_aversive` only fires at game-over (one callsite, one timing). `cliff_test.py:434` only assigns `trauma_triggered=False` (one callsite, hardcoded). Both are "gates" in the same sense as conjunctive predicates — they constrain when/whether the mechanism fires.

**How to apply:**

- When a brainstorm or red-team proposes "let's use mechanism X under condition Y," and X is a production predicate or callsite, the next move is `grep -A 10 "<predicate-name>"` and `grep -rn "<predicate-name>" src/` (find every callsite). Don't proceed until you've read every gate and every callsite.
- Spec writers: when citing a production predicate as a load-bearing gate ("trauma fires when X happens"), include the predicate's exact conjunctive form in the spec body — not just its name. The disambiguation prevents future contributors (and future-you) from re-making the same proposal.
- Red-team protocol: when proposing a fix that depends on a production predicate firing, **state the proposed P(predicate fires under proposed conditions)** with arithmetic justification before locking the recommendation. The /redteam protocol's "verify math" step explicitly covers this.
- LESSONS audit reflex: this is the *third* strike of the same pattern in one brainstorm session. Patterns that recur three times in one session warrant immediate codification rather than waiting for the workflow.md two-strikes review window.



**Date:** ~2026-01-01 (pre-existing, exact date unknown) | **Cost:** ~5-10 min of "why does the install fail?"

**What happened:** `nova-viewer/` is a Next.js project with a pnpm lockfile (`pnpm-lock.yaml`). Running `npm install` on a pnpm-shaped `node_modules` directory causes installation to fail or create an inconsistent state.

**Lesson:** Package manager lockfiles are not interchangeable. Using the wrong manager (npm vs yarn vs pnpm) produces silent failures that look like dependency conflicts.

**How to apply:**
- Always check `pnpm-lock.yaml` or `yarn.lock` before running install commands. If the file exists, use that manager.
- For nova-viewer specifically: `pnpm install` (not `npm install`).
- Include this requirement in onboarding docs and repo README so new contributors don't hit it.

### Carla anxiety firing at move 0–1 is "fast reaction," not "predictive lead-time"

**Date:** 2026-05-06 | **Cost:** would have been ~$50 + a damaged external-review pitch if we'd shipped Phase 0.7 against the current scenarios. Caught by the red-team round on the first pilot CSV.

**What happened:** The 2026-05-06 pilot at production tier produced a Δ = `t_baseline_fails - t_predicts` ≥ 2 in 15/15 paired trials. On paper that's a perfect methodology pass (per ADR-0007 Amendment 1, ≥3/3 scenarios with ≥3/5 trials at Δ ≥ 2). But Carla's `t_predicts` was 0 or 1 in nearly every trial — anxiety crossed threshold on the first move that had affect signal. Bot's `t_baseline_fails` averaged 4–5 moves on corner-abandonment-256 (window 12–17). Reframed: identifying a cliff at move 1 when Bot dies at move 4 is *fast reaction to a catastrophic state*, not *predictive lead-time over a developing decline*. An external reviewer (per scenarios spec §2.4 "external review credibility is load-bearing") would correctly say "Carla just panics on hard-looking boards; this isn't prediction."

The §7.4 calibration check ("Bot game-over within `expected_cliff_window` for ≥3/5 trials") is what catches this: all 3 scenarios failed Bot calibration in the pilot (snake-collapse-128: 1/5; corner-abandonment-256: 0/5 — Bot crashes too fast; 512-wall: 1/5 — Bot survives slightly past window). The §7.4 check exists precisely to prevent the failure mode of "Carla wins because the scenarios are so harsh that the cliff is at move 1, so any anxiety signal beats Bot."

**Lesson:** Methodology-pass-with-Δ-clean is necessary but not sufficient. `t_predicts` near 0 is a *red flag*, not a green light — it means Carla is reacting, not predicting. Calibration is the load-bearing gate; never ship a Phase 0.7 run on scenarios that fail §7.4. The methodology and the calibration are separable contracts, both must pass.

**How to apply:**

- When inspecting cliff-test CSV output, before computing Δ, check the `t_predicts` distribution per scenario. If the median is 0 or 1, the scenarios are mis-calibrated regardless of what Δ says.
- Re-author scenarios so Bot's game-over move falls inside `expected_cliff_window` for ≥3/5 trials before re-running the formal Phase 0.7.
- Keep the §7.4 calibration check as a separate validation step in the analysis pipeline (`analyze_results.py` follow-up spec) — don't fold it into the Δ test.
- When framing Phase 0.7 results for external review, lead with `t_baseline_fails - t_predicts ≥ 2 AND t_predicts is meaningfully past move 0`, not just Δ. The "predictive" claim has to survive the move-0 attack.

### Gemini Pro 2.5 has a hard 1000 RPD daily quota that is shared across the whole repo's API key

**Date:** 2026-05-06 | **Cost:** ~$0.30 wasted on a second pilot whose data was unusable; ~30 min misdiagnosing concurrency as the root cause; 1 commit revert.

**What happened:** First pilot consumed 956 Gemini Pro calls (4 ToT branches × N moves × 5 trials × 3 scenarios). Triggered a hypothesis that 20% Carla abort rate was due to concurrency=8 hitting transient 429s. Lowered DEFAULT_CONCURRENCY to 4 and re-piloted — abort rate jumped to **88% per-branch** (74/84 ToT branches `RetryError[ClientError]`). The cause was not concurrency: cumulative Pro calls across both pilots exceeded the 1000 RPD daily quota and Pro was hard-throttling for the rest of the UTC day. The c=4 commit (`60ac3bf`) had to be reverted because its data was confounded — we have no quota-clean evidence on whether concurrency=4 actually helps versus concurrency=8.

CLAUDE.md gotcha #2 documents the 1000 RPD limit and a workaround (`NOVA_DELIBERATION_MODEL=gemini-2.5-flash` env override). Initially I thought cliff-test should respect that override, but `main.py:148-152` shows the override is *only* read when `Settings.tier` is unset. Cliff-test requires `NOVA_TIER=production` (per spec §6.1 + ADR-0006), so `model_for("tot")` returns `gemini-2.5-pro` regardless of the env override. The documented workaround does not apply in tier mode.

**Lesson:** Under NOVA_TIER=production, cliff-test runs at the strict tier mapping with no env-override escape hatch. A single full pilot (~3 scenarios × 5 trials × 4 branches × ~30 moves) burns ~1000 Pro calls — basically the entire daily RPD quota. Plan the daily Gemini Pro call budget before starting any pilot. The 4-branches-per-ToT multiplier is the dominant cost factor.

**How to apply:**

- Before starting a cliff-test pilot, count today's prior Pro calls. If `prior_calls + estimated_run_calls` ≥ 1000, do not start; wait for UTC-midnight reset.
- Do not change concurrency or runner parameters in response to mid-day Carla aborts without first confirming the Pro quota state. Throttle-cluster aborts and quota-exhaustion aborts produce the same `RetryError[ClientError]` payload — they are not distinguishable from the Carla telemetry alone.
- For Phase 0.7 N=20 formal run, the per-day budget allows ~1 scenario/day at production tier with Pro for ToT, OR switch to NOVA_TIER=demo (Sonnet for ToT, no Pro RPD limit, ~5× per-call cost).
- The `tot_branch` event with `status=api_error error="RetryError ... ClientError"` is the diagnostic signature for both rate-limit clustering AND quota exhaustion. Disambiguate by counting Pro calls in the day's logs, not by inspecting the error payload.
- Long-term: the cliff-test runner should track a `pro_calls_today` counter against the 1000 RPD ceiling and refuse to start if a pilot/full-run would exceed it. Captured as a follow-up rather than implemented.

### `thinking_budget=None` on Gemini Flash silently truncates JSON output

**Date:** 2026-05-06 | **Cost:** ~30 min wall + ~$0.05 burned on a hosed pilot calibration before diagnosis. Caught during the first real-LLM cliff-test run; every Bot trial parse-failed at move 0 and every Carla react trial silently aborted (the `except Exception` in `_run_carla_trial` swallowed it).

**What happened:** `nova_agent/lab/cliff_test.py:_build_llms()` shipped without forwarding a `thinking_budget` to `build_llm()` for the Gemini Flash decision/bot LLMs. Default is `thinking_budget=None`, which `gemini_client.py:53-58` documents as "model decides — Flash burns the entire budget on thinking." With `BASELINE_MAX_TOKENS=500`, the model spent all 500 tokens on hidden reasoning and emitted only 8 visible tokens (`{\n  "observation": "Large` — same prefix every time). `parse_json` couldn't find a closing `}` → `StructuredOutputError` → 1 retry (deterministic at temp=0, identical failure) → `TrialAborted(reason="parse_failure")`. Bot side telemetry showed it; Carla react side hit the same wall but silently aborted before publishing any bus events, so no `events_*_carla_*.jsonl` files were created — making it look like Carla "didn't run" when in fact every trial died at move 0.

The canonical fix already existed in `main.py:165-193` — `thinking_budget=0` for Flash, `thinking_budget=1024` for Pro (Pro rejects 0). The cliff-test runner shipped without mirroring it because the Task 10 manual smoke ran on the `fresh-start` scenario, which evidently produced a small enough JSON payload to squeak through under whatever thinking the model chose; the production scenarios (snake-collapse-128, corner-abandonment-256, 512-wall) all failed.

**Lesson:** Every Gemini call site must explicitly set `thinking_budget`. The factory's `thinking_budget=None` default is a footgun, not a sane default — Flash interprets None as "go wild on thinking" and Pro interprets None as "dynamic budget." Both starve visible-token output under tight `max_output_tokens` limits. Never let a new code path pass through `build_llm` for a Gemini model without picking a value. Diagnostic fingerprint: `tokens_out` very small (≤10), response is a JSON prefix, parse failure is deterministic across retries, and the failure happens on every move.

**How to apply:**

- For any new `build_llm(model="gemini-flash-...", ...)` call site: pass `thinking_budget=0`.
- For `gemini-pro`: pass a positive cap (1024 is the established value for ToT branches; tune for your output size).
- Add a regression test asserting the kwargs at the construction site (see `test_build_llms_passes_thinking_budget_for_gemini_models`). Mocked-LLM tests can't catch this because mocks ignore `thinking_budget`; the assertion has to be at the factory boundary.
- If a manual smoke "passes" but the call site differs from `main.py`, run the real scenario corpus before declaring victory. `fresh-start` is not representative of cliff-test scenarios.
- Long-term: consider making `thinking_budget` a required kwarg on the Gemini side of `build_llm` (no None default). Documented as a follow-up in this entry rather than implemented — would be a small ADR.

### Pydantic-settings silently drops field-name kwargs when aliases exist + `extra="ignore"`

**Date:** 2026-05-04 | **Cost:** ~10 min during Task 5 of the Game2048Sim build (factory test failed before the spec reviewer flagged the same issue independently).

**What happened:** Project Nova's `Settings` (`nova-agent/src/nova_agent/config.py`) declares fields with aliases (e.g. `io_source` aliased to `NOVA_IO_SOURCE`) and `model_config` has `extra="ignore"` but NOT `populate_by_name=True`. Consequence: constructing `Settings(io_source="sim")` (kwarg by field name) silently drops the value — pydantic treats the field-name kwarg as an unknown extra and the field stays at its default. Only `Settings(NOVA_IO_SOURCE="sim")` (kwarg by alias) actually populates. The production env-var loading path is unaffected; this is a test-construction trap only, but the failure is silent (no exception, just default values).

**Lesson:** With aliases + `extra="ignore"` and without `populate_by_name=True`, pydantic-settings forces a strict alias-only API for kwargs. The `ignore` policy makes field-name kwargs look like noise and discards them without an error. The next engineer reaching for `Settings(my_new_field=...)` in a test will hit a confusing failure mode where their assertion is way downstream of the actual cause.

**How to apply:** Test helpers that construct `Settings` directly should always pass kwargs by **alias** (`NOVA_IO_SOURCE`, `GOOGLE_API_KEY`, …) and document this in the helper's docstring. Reference pattern: `nova-agent/tests/test_main_build_io.py:11-19`. Optional follow-up: setting `populate_by_name=True` in `Settings.model_config` would allow both forms — defer until a future Settings change naturally touches `model_config`, not worth a standalone PR.

### Pillow 12.2 type stubs reject `list` literals for `ImageDraw` geometry args

**Date:** 2026-05-04 | **Cost:** ~5 min during Task 3 of the Game2048Sim build, caught immediately by mypy strict.

**What happened:** Pillow 12.2.0's type stubs require `tuple` for `ImageDraw.rectangle((x0, y0, x1, y1), fill=...)` — `list` literals (`[x0, y0, x1, y1]`) are rejected. Older Pillow versions (10.x, 11.x) accepted either. Idiomatic Python (and most StackOverflow examples) reach for the list form first, so this is an easy paste-from-snippet trap.

**Lesson:** When a library tightens type stubs across a major version, mypy strict surfaces the regression but ruff and runtime don't. Default to tuples for any `ImageDraw` geometry args (rectangle bounds, polygon points, ellipse bbox, line endpoints) regardless of what the snippet you copied uses.

**How to apply:** Reference pattern: `nova_agent/lab/render.py:52` uses `(x0, y0, x1, y1)`. If you see `Argument 1 to "rectangle" of "ImageDraw" has incompatible type "list[int]"; expected "tuple[float, float, float, float] | ..."`, swap the brackets, don't argue with the stubs.

### TDD only catches direction-mapping bugs when BOTH axes are pinned

**Date:** 2026-05-04 | **Cost:** ~3 minutes; the bug shipped in the plan template but caught at first GREEN run.

**What happened:** Task 2 of the Game2048Sim build had the rotation count for swipe-UP and swipe-DOWN swapped in the plan template (`UP=1, DOWN=3` instead of correct `UP=3, DOWN=1`). The bug surfaced because the test suite pinned BOTH `test_merge_leftmost_priority_swipe_up` AND `test_merge_leftmost_priority_swipe_down`. A single-direction test on the same axis would have passed for the wrong reason — the rotation maps the test fixture into the right slide-left case anyway when both ends are wrong by the same amount.

**Lesson:** Direction-symmetric or axis-symmetric code (rotations, mirroring, signedness, byte-order, transpose) needs both ends pinned. One end alone is not a useful test — it can pass by chance for the wrong reason. The cost of the second test is trivial; the cost of NOT having it is a silently-wrong sim that produces plausible-looking games.

**How to apply:** When writing tests for symmetric APIs, write the test for one direction, then mirror it for the opposite direction in the same commit. If you find yourself writing "I'll add the other direction later," stop and add it now. Reference pattern: `nova-agent/tests/test_lab_sim.py` pairs every direction test (`*_swipe_up` ↔ `*_swipe_down`, `*_swipe_left` ↔ `*_swipe_right`).

### `claude-code-action@v1` cannot self-review PRs that modify the review workflow

**Date:** 2026-05-04 | **Cost:** ~10 minutes of "why did the action fail with a 401?" before reading the error message carefully.

**What happened:** PR #3 modified `.github/workflows/claude-review.yml` (bumping the Layer 2 model from Sonnet to Opus). When the action ran on PR #3, the OIDC step succeeded but the App Token Exchange step failed three times with `401 Unauthorized — Workflow validation failed. The workflow file must exist and have identical content to the version on the repository's default branch.`

**Lesson:** The Claude GitHub App's security model **requires the workflow file on the PR branch to be byte-identical to the version on `main`**. This is anti-tampering: it prevents a PR from modifying the workflow during the review run to leak secrets, escalate permissions, or self-approve. The action's own error message acknowledges this is "normal" for a PR that adds or modifies the workflow file. There is no fix on our end — it is structural.

**How to apply:** When a PR touches `.github/workflows/claude-review.yml` (or any other workflow file the action validates against `main`):

- Expect Layer 2 to fail on that PR with the 401 / validation error. **Don't panic.**
- CI still runs in parallel and validates correctness.
- Manually review the diff yourself before merge — Layer 2 cannot help here, that's the trade-off.
- After merge, the new workflow becomes canonical on `main`, and the NEXT PR that doesn't touch the workflow gets full Layer 2 review using the new version.
- **Do not** try to "split" the workflow change into a separate PR to fix it — every PR that modifies the workflow hits the same constraint.
- For sensitive workflow changes, dispatch the manual `/security-review` skill on the diff to add a security-tier review even though Layer 2 cannot.



**Date:** 2026-05-03 | **Cost:** ~2 hours of audit-trail work; surfaced one real api_error → parse_error rendering bug that had been live in the agent for weeks.

**What happened:** `nova-viewer/lib/types.ts` had a `{event: string; data: unknown}` catch-all arm at the bottom of the `AgentEvent` discriminated union. It was added "for safety" so the union would accept any frame the agent might emit, even shapes the viewer hadn't modelled yet. Removing it surfaced a third `tot_branch.status` variant — `"api_error"`, emitted from `nova_agent/decision/tot.py:166` whenever an LLM call fails — that the viewer had never typed. The catch-all routed those frames through `e.data as ToTBranchData` casts that compiled fine because TypeScript saw both arms (complete and parse_error) as assignable from the catch-all's `unknown`. The bus protocol was permissive enough that the bad shape rendered weirdly instead of throwing — a silent UX bug.

**Lesson:** A union arm of `{ tag: string; data: unknown }` defeats discriminated narrowing in every consumer. It also defeats `grep` — you can't audit which variants are handled because the catch-all matches everything. Hand-written runtime predicates per variant + a top-level `parse(raw): T | null` is worth the boilerplate, because TypeScript narrowing then becomes a real consistency check between producer and consumer.

**How to apply:** When mirroring an external protocol (Python bus → TS viewer), don't use a string-keyed catch-all "for safety." Either type every variant explicitly or fail closed (return `null`) for unknown tags. Every catch-all is a bug-hider. The validator implementation lives at `nova-viewer/lib/eventGuards.ts` (see `parseAgentEvent`); use it as the template when adding new event types.

### macOS UF_HIDDEN flag silently breaks Python venvs on Desktop

**Date:** 2026-05-02 | **Cost:** ~1 hour of "why does pytest work but `uv run nova` fail?"

**What happened:** Repo lives at `~/Desktop/a/`. macOS Sequoia's App Management auto-applies the `UF_HIDDEN` file flag to everything under `~/Desktop`. Python 3.14's site loader explicitly skips `.pth` files marked hidden. The editable install `_editable_impl_nova_agent.pth` was hidden → Python couldn't find `nova_agent` → CLI failed with `ModuleNotFoundError`. Pytest worked because `pytest.ini` declares `pythonpath = src` explicitly, bypassing the `.pth` mechanism.

**Lesson:** When Python imports mysteriously fail on macOS, run `ls -lO` on the relevant `.pth` file to check for the `hidden` flag. Don't trust that a venv is healthy just because some entry points work.

**How to apply:** Workaround is `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"` to put the venv outside `~/Desktop`. Better long-term: don't put repos under `~/Desktop` on macOS.

### Empty exported environment variables shadow `.env` files

**Date:** 2026-05-02 | **Cost:** ~30 min of "the API key IS in .env, why does the SDK say no auth?"

**What happened:** Pydantic-settings reads process env first, `.env` second. If a parent shell exports `ANTHROPIC_API_KEY=""` (empty string), it shadows the populated `.env` value, and `Settings.anthropic_api_key` becomes empty even though the file has the key.

**Lesson:** Empty exported env vars are a real shadowing risk. They behave differently from "unset" but pydantic treats them identically to unset for FALLBACK purposes — except the process-env-precedence rule fires first.

**How to apply:** In any pydantic-settings config, use `env_ignore_empty=True` so empty exports are treated as unset. When debugging "key not found" errors with a populated `.env`, run `printenv | grep YOUR_KEY` to check for shadowing.

### Anthropic API requires actual paid credits, not just grant credits

**Date:** 2026-05-02 | **Cost:** ~45 min of "the dashboard shows $20, why does the API say credit balance too low?"

**What happened:** Anthropic distinguishes "Credit grant" (free promotional balance) from "Credit purchase" (real Stripe-charged credits). The `/v1/messages` API gates on actual paid credits. Grant credits sit on the balance but don't unlock the API until at least one paid purchase has been made on the account.

**Lesson:** Anthropic dashboard balance ≠ API-eligible credits. Check the invoice history for a row labeled "Credit purchase" with status "Paid" — that's the indicator the API will work.

**How to apply:** Before any production deploy that depends on Anthropic, verify by hitting `/v1/models` (works without credits) AND `/v1/messages` (requires credits). If `/models` works but `/messages` 400s with "credit balance too low," the account needs a real Stripe purchase.

### Gemini Pro has a per-model 1000 RPD daily quota that's separate from your overall paid tier

**Date:** 2026-05-02 | **Cost:** ~30 min of "why are we hitting 429 on Pro when our Google Cloud billing is enabled?"

**What happened:** Even on the paid tier, `gemini-2.5-pro` has a default 1000 requests-per-day-per-model cap. ToT runs 4 parallel branches per call; ~250 ToT calls/day exhausts the quota. Other Gemini models (Flash) are unaffected.

**Lesson:** Per-model quotas exist independently of the project's billing tier. Pro is treated as a "premium" model with tighter defaults. To raise the limit, file a quota-increase request with Google Cloud.

**How to apply:** When designing an architecture that calls Pro frequently, either (a) request quota uplift before launch, (b) cap Pro calls in the application layer, or (c) configure a fallback to Flash for the same logical role. Currently using (c) via `NOVA_DELIBERATION_MODEL=gemini-2.5-flash` override in `.env`.

### Unity 2048 fork ignores `adb shell input swipe`; only DPAD keyevents work

**Date:** 2026-05-01 | **Cost:** ~15 min of "the swipe command runs but nothing happens"

**What happened:** The forked Unity 2048 game's input layer apparently handles only keyboard / DPAD events, not synthetic touch swipes. `adb shell input swipe x1 y1 x2 y2` reports success but the game doesn't move. `adb shell input keyevent 19/20/21/22` (DPAD up/down/left/right) does work.

**Lesson:** Game-engine input handling varies. Don't assume `adb shell input swipe` works just because it's the "obvious" way to send a swipe to an Android app.

**How to apply:** Test all input methods up front when integrating a new game. `nova_agent.adb.swipe()` already wraps DPAD keyevents internally; don't revert to the touch-swipe API.

### `pm clear` doesn't reset Unity 2048 save state

**Date:** 2026-05-02 | **Cost:** ~20 min of "I cleared the app data but the score is still where I left off"

**What happened:** Unity stores game state in external storage (or PlayerPrefs at the system level) that `adb shell pm clear` doesn't touch. The app re-launches with the prior session's save intact.

**Lesson:** Unity persistence ≠ standard Android app data. Cold-boot the AVD (`adb emu kill` + restart) for a true fresh state.

**How to apply:** When experiments need a clean game state, cold-boot the emulator. For ablation studies that need true randomness, this is non-negotiable.

### OCR palette must match every tile color the game can produce

**Date:** 2026-05-02 | **Cost:** ~1 hour of "why is nova playing terribly and the score not changing?"

**What happened:** The 2048 OCR uses a fixed RGB palette to classify tile colors. When tile values appeared (16, 32, 128) that weren't in the palette, the nearest-neighbor classifier mapped them to wrong values (often "empty"). Nova's perception silently produced wrong board state; decisions became no-ops; affect stayed flat (RPE = 0); the game appeared "stuck" but Nova had no idea.

**Lesson:** Nearest-neighbor color classification fails silently. There's no error, just wrong answers. Critical to either (a) sample exhaustively before deployment, (b) add a max-distance threshold that flags unknown colors, or (c) add a fallback OCR (tesseract) for cells that don't match any palette entry within tolerance.

**How to apply:** Currently sampled colors: empty/2/4/8/16/32/128. **64 and 256 are still unsampled** and will silently misread when nova reaches them. Either pre-sample those colors or implement the max-distance fallback before Phase 0.7's cliff test runs in production.

### Plan-template bugs caught only during execution

**Date:** 2026-05-02 | **Cost:** ~3 separate sub-agent retries

**What happened:** During the 12-task subagent-driven implementation of the thinking stream, three plan-template bugs surfaced at execution time:

1. The `rewordFirstPerson` regex rule order produced "I merges down" (failed test 6); rule order needed reorganization.
2. The `truncate` function's `slice.trimEnd() + ELLIPSIS` produced `"fox…"` which matched the test's `not.toMatch(/\w…$/)` — needed to keep the trailing space.
3. `as never` for the `prevAffect` spread failed strict tsc; needed `as AffectVectorDTO`.

In each case, the implementer subagent correctly caught the bug at execution time and chose tests-as-truth.

**Lesson:** Plan templates are a useful starting point but cannot be assumed correct. TDD discipline — writing the test first and treating it as the spec — is what catches plan bugs cheaply. If the plan and the test disagree, the test is usually right because it's more specific.

**How to apply:** When dispatching subagents with plan-provided code blocks, explicitly instruct them to treat the tests as the spec. If the plan code fails the plan tests, fix the code, not the tests.

### TypeScript discriminated-union catch-all defeats narrowing

**Date:** 2026-05-02 | **Cost:** ~30 min of "why isn't `e.event === 'decision'` narrowing `e.data`?"

**What happened:** The `AgentEvent` union in `nova-viewer/lib/types.ts` ends with a catch-all `{event: string; data: unknown}` arm. TypeScript's discriminated-union narrowing fires only when EVERY arm matches a literal — the catch-all matches any string, so narrowing on `e.event === "decision"` doesn't narrow `e.data` to the decision arm's shape. We worked around it with `as data as { ... }` casts everywhere.

**Lesson:** A catch-all in a discriminated union turns it into a non-discriminated union for narrowing purposes. Either drop the catch-all and handle unknowns explicitly with type predicates, OR don't expect narrowing to work.

**How to apply:** Day 1 Task 2 of Week 0 fixes this: remove the catch-all, add hand-written runtime predicates in `useNovaSocket`, replace `as data as` casts with proper narrowing. After this, the type system actually catches typos in field-name access.

### ToT branch failure mode needs explicit per-branch exception handling

**Date:** 2026-05-02 | **Cost:** ~45 min of "why is ToT raising 'no valid candidates' when Pro should be working?"

**What happened:** `ToTDecider._evaluate_one` originally only caught `StructuredOutputError` from `parse_json`. When the underlying `self.llm.complete()` call threw (e.g., 429 quota exhaustion, network error, tenacity RetryError), the exception propagated silently into `gather(return_exceptions=True)`. All 4 branches "failed" with nothing visible, then `decide()` raised the generic "ToT produced no valid candidates" with no clue to the underlying cause.

**Lesson:** `gather(return_exceptions=True)` swallows exceptions in a way that hides root causes. Per-task exception handling is mandatory, not optional. AND the consolidating function that raises on "no successes" should include per-task failure summaries in its error message.

**How to apply:** Already fixed in commit `89e1a7c`. Pattern to repeat elsewhere: catch `Exception` (not just specific subclasses) at the per-task level, publish a structured failure event, return the exception. The aggregator includes failure summaries in its consolidated error.

### `as never` doesn't work for object spreads in TypeScript strict mode

**Date:** 2026-05-02 | **Cost:** ~5 min, caught immediately by tsc

**What happened:** Plan template used `as never` for a `prevAffect` spread (`{...affectEv({}).data as never}`). Strict tsc rejected with `TS2698: Spread types may only be created from object types`.

**Lesson:** `as never` is for unreachable code paths, not for "force this through type checking." For object spreads, use the actual type (`as AffectVectorDTO`).

**How to apply:** When tempted to write `as never`, ask "is this code actually unreachable?" If yes, OK. If no, find the right type.

---

## Architecture / design decisions

### Sim cost ≡ live cost — record-replay rationale (ADR-0006) intact, cliff-test budget bounded by LLM not ADB

**Date:** 2026-05-04 | **Context:** Task 6 calibration smoke for the Game2048Sim build (sim 50-move vs live 50-move).

**What happened:** Task 6 measured a 50-move run on `Game2048Sim` against a 50-move run on the live emulator path with the same cognitive layer. LLM-call shape was **byte-identical**: $0.0159 vs $0.0159, 50 calls each, ~531-568 tokens-in. PR #2's code review had flagged a per-event `asyncio.to_thread` cost concern in `RecordingEventBus.publish` — sim's higher event cadence does NOT amplify this; total LLM cost dominates by orders of magnitude.

**Lesson:** Sim is the *same* cognitive workload as live — same prompts, same model, same token shape. The wall-clock speedup (~1.7× on the calibration run) comes entirely from removed ADB latency, not cheaper inference. This confirms ADR-0006's record-replay rationale: replay sidesteps LLM cost entirely; sim does NOT. Phase 0.7's cliff test (N=20 trials × 2 arms × 3-5 scenarios = 120-200 games × $0.016 ≈ $2-3 LLM cost) is bounded by LLM cost, which sim does not change. Sim's value is iteration cadence, not cheaper experiments.

**How to apply:** When budgeting any future cliff-test or ablation that uses `Game2048Sim`, multiply LLM-call cost by trial count — don't expect sim to reduce it. Use the recorder for UI-iteration loops (where replay actually IS free) and the sim for cognitive-validity loops (where cost is the same as live but wall-clock is faster). Calibration data lives in the Task 6 commits; re-run if the cognitive layer's prompt shape changes materially.

### Don't pivot to RL — it kills the cognitive moat

**Date:** 2026-05-02 | **Context:** brainstorm with the AI red-team

**What happened:** During the architecture review, the natural question came up: why pay for LLM inference when RL (PPO, DQN) could master 2048 in an hour at zero per-move cost?

**Lesson:** RL produces optimizers; cognitive simulation produces explainers. The product is the *introspection* (visible reasoning, persona narratives, post-game reflection lessons) — not the win-rate. Trading the cognitive architecture for inference speed kills the differentiator and puts us in modl.ai's lane (where they have a 5-year head start).

**How to apply:** When inference cost / latency feels painful, the answer is hybrid local+API LLMs (System 1/2 routing) — not RL. The cognitive layer is the moat; preserve it. Documented in `docs/product/methodology.md` §3.3.

### State-Transition Signatures > 1:1 affect→KPI mappings

**Date:** 2026-05-02 | **Context:** brainstorm session on validation methodology

**What happened:** Original methodology proposed mapping single affect snapshots to KPIs ("anxiety > 0.6 → spend trigger"). The AI red-team pointed out: a single anxiety spike could mean fun challenge, annoying puzzle, or about-to-quit. Indistinguishable from the snapshot.

**Lesson:** Behavioral prediction needs compositional patterns, not threshold snapshots. Multi-step state machines (e.g., Confidence ↓ → Anxiety ↑ → Frustration plateau = Churn Signature) are scientifically defensible AND harder for competitors to clone trivially.

**How to apply:** Defined the four named Signatures (Alpha/Churn, Beta/Conversion, Gamma/Engagement, Delta/Bounce) in `docs/product/methodology.md` §1. Each signature has a state-machine pattern, falsification criterion, and KPI mapping.

### Cohort-distribution reporting > single-trajectory point predictions

**Date:** 2026-05-02 | **Context:** brainstorm on long-horizon (Day-N retention) prediction

**What happened:** Original framing implied Nova would predict "32.4% Day-30 churn." Compounding error in any multi-day simulation makes single-point predictions noise by Day 30 — the same fundamental limit that caps weather forecasting at ~10 days regardless of model quality.

**Lesson:** When dealing with compounding-error systems, report distributions, not points. The widening confidence interval IS the prediction. Honest format: "Median 28% Day-30 churn (95% CI [22%, 38%]), driven by accumulated affective baseline drift." Studios use the distribution shape (variance) to make decisions; tight CI = ship with confidence, wide CI = run more human playtests first.

**How to apply:** All long-horizon predictions in Phase 4+ MUST be cohort distributions across N≥50 personas. Specified in `docs/product/methodology.md` §1.6.2.

### Hybrid local+API inference > all-API or all-local

**Date:** 2026-05-02 | **Context:** brainstorm on production inference architecture

**What happened:** The naive options at scale are (a) all-API (latency + cost + rate limits) or (b) all-local (~70B+ model needed for reasoning depth, expensive hardware). Both have real downsides.

**Lesson:** Routing by cognitive load is the right architecture, mirroring Kahneman's System 1 / System 2. ReAct (90% of moves, fast intuitive) → local 14B-class (Qwen 2.5 14B + vLLM `guided_decoding` for zero JSON parse errors). ToT branches + Reflection (rare, deliberate) → frontier API. ~95% of inference moves local; API cost stays bounded.

**How to apply:** Phase 1 builds the `LocalLLMAdapter`. The `LLM` protocol abstraction in `nova_agent/llm/protocol.py` already supports this; adding the local adapter is a 1-week port, not a rewrite.

### Variance reduction is the on-thesis test for trauma-tagging, not mean shift

**Date:** 2026-05-02 | **Context:** designing the trauma ablation study

**What happened:** Initial instinct was to test "does trauma improve average score?" — the standard "did the intervention work" test.

**Lesson:** Trauma in the cognitive architecture is *avoidance learning* — the agent remembers what killed it and avoids similar situations. The empirical signature of avoidance learning is **reduced variance under similar stimuli** (more consistent play, fewer catastrophic outliers in the lower tail), not higher mean performance. Testing on mean would be the wrong test for the mechanism.

**How to apply:** Phase 0.8 uses Levene's W test for equality of variances (full math in `docs/product/methodology.md` §4.2). Pass criterion: W significant at p<0.05 AND Var(Y_on) < Var(Y_off). Failure → demote trauma from core feature to UI flavor.

### Three-channel memory decay matched to cognitive psychology

**Date:** 2026-05-02 | **Context:** designing long-horizon (Day-N) simulation

**What happened:** Naive answer to "should memory fade between simulated sessions?" is "yes, single half-life." But this is wrong: real human memory has at least three distinct channels (episodic / semantic / affective) with very different decay rates.

**Lesson:** Don't add tunable parameters without literature anchoring. The three-channel decay model (Tulving 1972) gives Nova:
- Episodic: ~24h half-life (Ebbinghaus, Murre & Dros 2015)
- Semantic: ~7d half-life (Bahrick 1984)
- Affective baseline: ~30d with floor (Yehuda et al.)

Each rate is citable; the model is scientifically defensible; Day-3 frustration legitimately compounds into Day-17 churn risk via the slow-decaying affective channel.

**How to apply:** Implementation gates on Phase 0.7 + 0.8 passes. Spec'd in `docs/product/methodology.md` §1.6.

---

## Workflow / process learnings

### Verify spec wording + compute numbers BEFORE drafting recommendation, not when /redteam challenges

**Date:** 2026-05-08 | **Cost:** 4 numerical/spec errors across 4 consecutive /redteam rounds in one Phase 0.8 surrogate-crash adjudication session; each self-corrected only after challenge. Net ~3h of /redteam back-and-forth that primary-source verification on the first turn would have prevented.

**What happened:** During Phase 0.8 surrogate run crash adjudication, the investigator made 4 distinct errors across consecutive /redteam rounds, each one favoring the cheapest-to-execute recommendation:

1. **Power calc.** Claimed "N=70 → N=20 power drop is 80% → 78–82%, immaterial." Actual paired-t one-tailed power at d=0.30 is 80.6% → 36.1% — a 44pp loss. Red team caught the math.
2. **Cost framing.** Claimed "saves $20" by letting cap-fire vs raising cap, but compared against an option not on the table. Double-counted savings against an alternative the live decision tree didn't include.
3. **Cap-stop classification.** Framed budget exhaustion as a legitimate halt criterion. Spec §3.3 abort criteria = direction-flip / zero-variance / censoring threshold only; budget-cap is operational safety, NOT a pre-registered halt. Using it as one *adds* a methodology deviation on top of the budget-stop event.
4. **"All §3.3 criteria pass at N=4" overstatement.** Confused abort triggers (which fire to STOP early) with pass criterion (which is N=20 + retain-all-20-into-main per spec §6 C3). N=4 is unevaluable, not passing.
5. **Fact citation drift.** Cited "Gemini side: 669 calls" when actual log count was 1333 (off by 2×).

Each error was caught only after a /redteam round. The pattern: under late-night drift / multi-turn pressure, the investigator framed the minimum-effort path as methodologically defensible without primary-source verification. Each error felt locally defensible inside its own turn but was directionally consistent across turns — convenience-biased toward the cheapest option.

**Lesson:** Convenience-bias is a real failure mode in extended decision threads. Investigator's default-bias when time-pressed is "frame the cheapest option as defensible until pushed." Corrections only happen on challenge — asymmetric. The pattern is invisible inside any single turn but visible across multiple turns (the bias direction is consistent). The fix is upstream verification, not downstream challenge.

**How to apply:**

- Before drafting any "stop / accept / ship" recommendation in a multi-round decision thread, run verification BEFORE the recommendation: read the spec section verbatim, compute actual numbers from primary sources (logs, ADRs, source code), THEN frame. Verification-after-recommendation is too late — framing has already anchored.
- Anchors that ALWAYS need primary-source verification:
  - Statistical claims (power, effect size, CI, threshold) — compute from formula or quote spec §
  - Spec criteria (pass/fail/abort thresholds) — quote verbatim, don't paraphrase
  - Cost claims (totals, deltas, savings) — sum from log, never estimate
  - Run state (N completed, pace, halt status) — read artifact directly, don't recall
- If 2+ errors surface in one session, suspect the pattern. After 3 errors, pause — the investigator is not in a state to make defensible calls without a hard verification gate on each step.
- /redteam dispatch protocol exists exactly for this: full-protocol Opus analysis catches what inline Sonnet misses. Dispatch more aggressively when stakes are non-trivial ($-spend, methodology call, ADR-worthy decision) — don't wait for the third error to escalate.
- Convenience-bias is harder to catch when investigator agrees with red team (apparent humility). Concession ≠ correctness. Each /redteam concession should be re-verified, not stacked on prior concessions.

### Concurrent independent workflow changes need explicit per-change rollback ordering

**Date:** 2026-05-07 | **Cost:** ~0 minutes (caught during red-team analysis of the workflow-simplification spec); pattern-cost compounds across every multi-change config batch if uncaught.

**What happened:** The workflow-simplification batch (`docs/superpowers/specs/2026-05-07-workflow-simplification-design.md`) bundled Step 6 (Haiku as default subagent implementer model) and Step 7 (Sonnet 200k as default main-session model) into a single 10-commit batch. Initial success criterion was "zero increase in Layer 2 BLOCK findings on the next 5 PRs after the batch" — one coarse number. Red team flagged the attribution problem: if BLOCK rate rises, you cannot tell from the count alone whether Haiku-implementer wrote brittle code or Sonnet-200k missed cross-file context. Counter-proposal was to defer Step 6 by one week (sequential introduction = clean signal). Counter-proposal had real cost: ~7 days of deferred Haiku savings on the line the user was already pained by, plus a second PR cycle. Resolved by keeping the batch but adding an ordered-rollback procedure to the spec doc — atomic commits already enable cheap per-step revert; the missing piece was the *ordering rule* (revert higher-variance change first, run 3 PRs, then revert next), written down before the regression hits rather than re-derived under pressure.

A separate refinement issue surfaced in the same review: a `1.5× pre-batch baseline` rollback trigger has a zero-baseline pathology (1.5 × 0 = 0, so any single BLOCK triggers). Replaced with "2+ BLOCKs in 5 PRs OR any single BLOCK diagnosed as model-quality." The diagnostic-cause clause is the real signal; counts alone are noisy on small windows.

**Lesson:** Bundling multiple independent changes in one batch is fine when (a) failure surfaces are non-overlapping and (b) per-change rollback is cheap. Both conditions almost always hold for atomic-commit config batches. The thing that does NOT come for free is *which one to revert first if the success criterion fails*. Without an explicit rollback ordering written into the spec, future-you faces the regression under pressure and either reverts both (losing the signal that motivated the batch) or paralyzes between options. Atomic commits give you the *capability* to per-step revert; the rollback ordering rule gives you the *discipline* to do it usefully.

Separately: coarse-grained success criteria ("BLOCK rate within 1.5× baseline") often have edge-case pathologies (zero baseline, small windows). The cheap fix is a categorical signal alongside the count — "diagnostic cause matches X" is robust where multiplicative thresholds are not.

**How to apply:**

- For any multi-change config batch where two or more changes affect distinct surfaces (e.g., subagent vs main-session, frontend vs backend, hook vs skill), draft an *ordered rollback procedure* as part of the spec doc Implementation Discipline section. Identify which change is the higher-variance bet and revert it first.
- The rollback procedure goes in the spec, not the plan. Specs survive longer than plans and are read under regression pressure; plans are consumed and archived.
- Refine success criteria with a categorical-cause clause whenever the baseline is near zero or the window is small. "X+ findings of type Y, OR any single finding of cause Z" is harder to game and more diagnostic than "rate within K× baseline."
- After resolving any concurrent-change-batch debate, capture the rollback ordering and the regression diagnostic in the spec text itself before invoking writing-plans. Do not rely on memory or oral tradition — the next session reading the spec will not have the conversation context.
- Adjacent gotcha: Claude Code memory paths (`~/.claude/projects/<mangled>/memory/*.md`) are path-mangled per project location; absolute paths in slash commands break on project relocation. Slash commands that touch memory should resolve the path dynamically (e.g., via `git rev-parse --show-toplevel` + the path-mangling rule, or by writing a portable artifact under `docs/` alongside the memory write). This bit during Step 4 (`/handoff`) design and is a follow-up implementation note, not a spec change.

### Test-runner spec drift — collector creeping into analyzer

**Date:** 2026-05-05 | **Cost:** ~0 minutes (caught in Q6 of Test Runner spec brainstorm), but pattern compounds across spec evolution if uncaught.

**What happened:** Brainstorming "what artifacts does the cliff-test runner produce?" my initial proposal was a 3-tier JSON hierarchy: per-trial + per-scenario aggregate (mean Δ, prediction-validity %) + run-level verdict (pass/fail per methodology §5.3). The red team flagged it as a Separation-of-Concerns violation: the per-scenario and run-level tiers were no longer "data the runner collected" — they were *statistical analysis* hardcoded into the orchestrator. If the analysis methodology evolves (e.g., switch from paired-mean Δ to bootstrap CI, or change the prediction-validity threshold post-pilot), the runner code would have to change in lockstep. Conceded; final shape is flat CSV row-per-trial + JSONL events, with all aggregate stats and pass/fail logic deferred to a separate `analyze_results.py` (out of Test Runner spec scope).

**Lesson:** When designing an experiment-runner spec, the natural drift is: "runner produces data" → "runner produces summary" → "runner produces verdict." Each step feels like it's serving the consumer (the analyst eventually wants pass/fail, so why not just include it?). But the consequence is methodology-orchestrator coupling: any future change to the stats has to thread through the runner code. Specs that conflate collection with analysis are harder to evolve and harder to defend in methodology review (the runner becomes part of the experimental method). Hold the line: runner = collector. Analyzer = separate artifact.

**How to apply:** When drafting an experiment-runner spec, draw an explicit boundary in the Out-of-Scope section: "the runner does NOT compute aggregate statistics, summary means, pass/fail verdicts, or cross-trial comparisons. Those live in a downstream analysis script that consumes the runner's flat per-trial output." The boundary survives only if it's stated. Per-trial *derived flags* (e.g., "did this trial meet threshold X?") are acceptable in the runner output because they're per-trial observations, not cross-trial aggregations. The line is at "across-trial / across-arm / across-scenario math" — anything inside one trial is data; anything across trials is analysis.

### Verify red-team cost-leakage claims numerically before accepting framing

**Date:** 2026-05-05 | **Cost:** ~0 minutes (caught in-loop), but pattern-cost across the brainstorm system is large if uncaught.

**What happened:** During the Test Runner spec brainstorm (Q2, parallelism strategy), the red team flagged "critical budget leakage" from independent arm scheduling under the paired-discard rule (Bot spec §2.6) — claim being that Bot tokens spent before a paired Carla abort would be wasted. Running the actual numbers (Bot abort rate <2% at temp=0 + 3× API retry, Carla abort rate ~3-5%, Bot per-trial cost ~$0.10, Carla ~$1-2, N=20 × 3 scenarios) showed expected wasted-pair leakage was **~$2-3 over the entire cliff test** — not "critical." Accepted the structural change (paired-trial as unit-of-concurrency) on independent code-clarity grounds, explicitly rejected the cost-leakage framing in the analysis. If the framing had been accepted as-stated, the spec would have anchored the budget envelope discussion around a phantom $-figure problem and downstream calibration runs would have over-engineered for it.

**Lesson:** A red-team claim that sounds rigorous (units, percentages, "wasted tokens", "leakage") may still be 10× over-calibrated. The rigor of the *structure* (named units, percentages quoted) is independent of the rigor of the *magnitudes*. Always run the actual numbers — abort rates × per-trial costs × N — before accepting either the proposed fix or the framing that motivates it. The fix may still be correct on other grounds (in this case, paired bookkeeping is a real code-clarity win); separating "is the fix right?" from "is the framing right?" keeps the spec honest and prevents spec text from anchoring on a phantom problem.

**How to apply:** When a `/redteam` analysis surfaces a quantitative claim (cost leakage, latency overhead, error rate, overshoot percentage), §3 of the protocol output ("Where the red team is weaker than they framed") MUST include explicit math — quote the inputs, compute the magnitude, compare to the threshold of "critical." If the math shows the magnitude is small, accept the fix only on its other merits (or reject) and call out the framing miscalibration. This is now part of how the redteam slash command is meant to be exercised; no skill-file change needed, but next round's §3 should treat numerical-claim verification as mandatory not optional.

**Addendum (2026-05-05, same-session reinforcement):** The same rule extends to **code-state claims**, not just numerical claims. In Q3 of the same Test Runner brainstorm (Anxiety sampling mechanism), the red team flagged "EventBus async race conditions at trial teardown" and proposed direct state poll over bus subscription. My initial pushback assumed the bus had an in-process subscriber pattern. Verifying the code (`nova_agent/bus/websocket.py:52-59`) showed the bus is **WebSocket-broadcast-only with silent drop on no-client connected** — my mental model of the architecture was wrong, and the red team's MODIFY was correct (though their framing about "race conditions" was also imprecise; the actual problem is dropped events at the publish site, not race windows on receive). The right answer turned out to be even cleaner than the red team framed: the runner can capture the post-decision anxiety from the synchronous return value of `affect.update()`, no bus involvement at all. Lesson generalizes: when the red team makes a code-state claim ("X has property Y"), verify by reading X before defending or conceding. The cost of the read is small; the cost of arguing from a wrong mental model compounds across the rest of the brainstorm and downstream into the spec.

### Open PR on the active long-lived branch silently swallows new commits

**Date:** 2026-05-05 | **Cost:** ~5 minutes of cleanup at end of session + a non-trivial methodology hit (PR #7's scope misrepresented for several hours)

**What happened:** Project Nova uses a long-lived feature branch (`claude/practical-swanson-4b6468`) and a one-PR-per-coherent-unit cadence (workflow.md). PR #7 was opened with the cliff-test scenarios unit (8 commits) and left open awaiting review. A new session started and shipped a second coherent unit (Baseline Bot decider — spec + ADR amendment + 7-task implementation = 13 more commits) on the same branch. Every push auto-updated PR #7 because GitHub tracks branches not commits, so PR #7 silently grew from 8 commits to 21 — but its title/body still described only the cliff-test unit. The "one-big-PR drift trap" workflow.md explicitly warns about. Caught only at PR-creation time when the finishing-a-development-branch skill asked which option to take.

**Lesson:** Long-lived feature branches + open PRs are a hidden mode: you cannot open a "new" PR from the same branch — you can only update the existing one. Any work committed before the prior PR merges stacks under that PR's title/body. Without an explicit check at session start, the stack can grow several units deep before anyone notices, and at that point the choices are (a) update PR meta to encompass everything, (b) force-push branch surgery (destroys in-flight Layer 2 review). Both are recoveries; neither is the cadence the workflow rule wants.

**How to apply:**

1. **SessionStart hook in `.claude/settings.json`** — runs `gh pr list --head $(git branch --show-current) --state open --json number,title` at every session start and emits a `systemMessage` warning listing any open PRs on the current branch with a reminder to confirm the new work belongs in the same unit before committing. Hook beats discipline; landed in this same commit. Note: the hook only registers after `/hooks` reload or session restart in the session that introduced it (settings watcher catches new files at session start only).
2. **Memory entry on the same topic** in user-scope auto-memory so future-me checks PR state at session start across `/clear` boundaries.
3. **If the stack already happened**: prefer (A) updating the existing PR's title/body to honestly describe both units over (B) force-pushing branch surgery — (A) is reversible, preserves the in-flight Layer 2 review (which is now reviewing the combined diff anyway), and avoids a force-push on a branch tracked by an open PR. (B) only makes sense if the two units are genuinely unrelated; coupled units (where the second's spec depends on the first's) ship cleanly under one combined PR.

### `# type: ignore` staging across multi-task plans creates a peel-as-you-go cleanup chain

**Date:** 2026-05-04 | **Context:** the 7-task Game2048Sim build (Tasks 1, 2, 4, 5).

**What happened:** Task 1 introduced three `# type: ignore[import-untyped]` comments on lazy imports of modules (`nova_agent.lab.io`, `nova_agent.lab.sim`, `nova_agent.lab.scenarios`) that didn't exist yet. Tasks 2, 4, and 5 each had to PEEL the corresponding ignore once the underlying module materialized, because mypy strict's `unused-ignore` rule fires the moment the module import resolves. Forgetting to peel causes mypy strict to fail at task N rather than task 1, which is confusing because the failing line wasn't touched in task N's diff.

**Lesson:** Cross-task plans that stage forward-references via `# type: ignore` create a chain of cleanup obligations across tasks. Each task that resolves a placeholder must remember to peel its specific ignore. The plan must document the staging explicitly or the obligation gets lost when sub-agents read tasks in isolation.

**How to apply:** Two patterns for forward-references in multi-task plans:

1. **Document the staging in a top-level table** in the plan doc (e.g. "Task 1 stages 3 `type: ignore` comments at file:line; Task 2 peels A, Task 4 peels B, Task 5 peels C"). The Game2048Sim plan documented this in Step text but not as a table — adequate but easy to miss when sub-agents read tasks in isolation.
2. **Use `if TYPE_CHECKING:` + string-literal annotations** for forward-references instead of runtime imports + `type: ignore`. More verbose at the import site but no cleanup obligation, and `unused-ignore` doesn't apply because there's no runtime import to resolve.

### "Did I review?" must be a binary check on file paths, not a judgment

**Date:** 2026-05-04 | **Context:** PR #1 closed, Week 0 Day 2 review-system port

**What happened:** PR #1 (10-commit AgentEvent validator + nunu.ai dossier rewrite + CI trim) shipped with the Claude pair skipping reviewer dispatches twice. The mistake wasn't "I decided not to review" — it was "I never asked the question." When invocation depends on the operator remembering to ask "should I review this?", the answer drifts toward "no" under fatigue or context pressure. Looking back at the diff after merge, the missed reviews would have caught nothing critical, but the pattern is unsafe.

**Lesson:** A path-matched trigger taxonomy in `REVIEW.md` plus a binary line in `.claude/pre-commit-checklist.md` ("`/review` dispatched on staged diff (or N/A: <reason>)") removes the judgment call entirely. The reviewer's first job becomes inspecting the diff's file paths against a 9-row table; the answer is yes, no, or "yes for code-reviewer + yes for security-reviewer." No vibes. Pattern adopted from the Gibor app's `/review` skill.

**How to apply:** Three layers, each catching a different failure mode:

- **Layer 1** (in-session, before commit): `/review` orchestrator at `.claude/skills/review/SKILL.md` — manual, Sonnet/Opus, runs while context is hot; the `/code-review` and `/security-review` skills are direct entry points when the orchestrator is overkill
- **Layer 1.5** (auto, on push): `PreToolUse` agent hook in `.claude/settings.json` — Haiku, fires on `git push:*`, blocks only on critical findings
- **Layer 2** (auto, PR-time): `.github/workflows/claude-review.yml` — `claude-code-action@v1`, Sonnet, advisory PR comments only (NOT a required check until ≥10 PRs of signal data exist)

The hook is the safety net for "I forgot Layer 1," and Layer 2 is the safety net for both the human-fast layers when the diff grew across commits. Promoting Layer 2 to a required check is a future ADR — too early to gate merges on it now.

### Brainstorm-then-plan-then-implement actually works

**Date:** 2026-05-02 | **Context:** the thinking-stream feature build

**What happened:** Used the `superpowers:brainstorming` skill (5 visual+conceptual questions) → `superpowers:writing-plans` skill (12-task TDD plan) → `superpowers:subagent-driven-development` skill (sequential task dispatches with reviews). Total: ~4 hours to ship a real feature with 47 passing tests.

**Lesson:** The discipline pays back. Brainstorm catches design issues cheap (5 min each). Plan catches scope creep (every task gates on the next). Subagent execution preserves coding context per task.

**How to apply:** For any non-trivial feature (new component, new data flow, new external integration), invoke the three skills in sequence. Don't skip ahead to "just build it" — the wrong abstractions emerge from undisciplined building and cost 10x to refactor later.

### Self-judged gates work when the criteria are explicit and binary

**Date:** 2026-05-02 | **Context:** dropping the "hostile reviewer" requirement from Week 3

**What happened:** Original plan made Week 3 (KPI mockup) gated on showing it to a hostile reviewer (a specific industry contact who'd be cruel). User dropped that requirement (no available contacts). Replaced with self-judged criteria: "looks like Firebase dashboard, not sci-fi UI" + "leads with KPIs, not affect curves" + "CSV export is first-class."

**Lesson:** External validators are nice-to-have but should never be on the critical path for solo founders. Self-judged gates work IF the criteria are explicit and binary. "Looks professional" is too vague; "leads with KPI predictions, includes CSV export, every prediction footnoted" is testable.

**How to apply:** When defining a self-judged gate, write the specific yes/no questions you'll ask. If the questions are subjective ("does it look good?"), reframe until they're observable ("does it have CSV export? does it lead with KPIs?").

### Update memory before logging off

**Date:** 2026-05-02 | **Context:** end of long brainstorm + dossier session

**What happened:** Almost cleared chat with significant strategic work uncaptured in memory files. The prior `project_nova_resume_point.md` was from much earlier in the session (pre-pivot) and would have given next-session-me a stale picture.

**Lesson:** Memory update is a deliberate ritual at end-of-session, not an afterthought. Treat it like git-commit: nothing's "saved" until it's in the resume_point file.

**How to apply:** Last 10 minutes of every productive session: read the current `project_nova_resume_point.md`, update with any state changes, verify next-session pickup task is at the top, commit if memory is in a tracked repo. Then clear chat or log off.

### TDD subagents catch plan bugs better than human review

**Date:** 2026-05-02 | **Context:** the 12-task thinking-stream build

**What happened:** Three separate plan-template bugs were caught by subagents during TDD execution (rule ordering, truncate trim behavior, `as never` invalid). A human reviewer reading the plan ahead of time would likely have missed at least one of these.

**Lesson:** TDD with the test as spec is an organizational technology, not just an engineering one. The subagent has no incentive to "make the test pass cleverly"; it just runs the test, sees the failure, fixes the impl. Human reviewers often ignore tests when the impl looks plausible.

**How to apply:** Trust subagent TDD output more than ahead-of-time plan review for verification. Use plan review for *strategy* (is this the right thing to build?), not *correctness* (will this code work?).

---

## Strategic / product learnings

### Within-game adaptation ≠ cross-game speedrunning — check faithful-simulation framing before stripping behavioral DVs

**Date:** 2026-05-06 | **Cost:** ~20 min of two /redteam rounds to converge on the right §4.2 design

**What happened:** Designing the methodology §4.2 trauma-ablation rewrite, a first red-team round challenged the avoidance-recurrence behavioral DV as "anti-product — agent learns to skip the trap, becoming a speedrunner instead of a playtester." I accepted it and proposed Option D (affective-only DV). A second red-team round identified the conflation: a human player who hits a brutal trap mid-session plays more cautiously for the remaining moves of that session. That within-session adaptation IS the faithful-simulation signal studios pay for. The speedrunner critique correctly targets cross-session optimization (RL-style: "next game, skip the trap"). It does not apply to within-game adaptation. Stripping the behavioral DV based on the first round's framing would have removed a product-valuable observation and coupled Phase 0.8's pass criterion to the Anxiety pathway — which the C1 ablation had already shown was weak.

**Lesson:** "Avoidance is anti-product for a playtester" is only true for cross-game behavioral learning. Within-game adaptation (playing more cautiously after hitting a trap in the same session) is exactly what the product should simulate. The two are easily conflated under a surface-level "speedrunner" framing. When a red-team challenges a behavioral DV as anti-product, the load-bearing question is temporal scope: within-session or cross-session?

**How to apply:** Before accepting an "anti-product" critique on a behavioral test: (1) Identify whether the behavior is within-game or cross-game. (2) Ask "would a real human player show this behavior in the same session?" — if yes, it IS the playtester signal. (3) Keep the behavioral DV as primary when it tests the mechanism's function; demote only if it tests optimization-across-sessions. Also: the existing LESSONS entry "Variance reduction is the on-thesis test for trauma-tagging" (2026-05-02, Architecture / design decisions) is superseded by the §4.2 rewrite — the on-thesis test is now within-game trap-recurrence rate (behavioral primary) + Anxiety lift (affective secondary, descriptive).

### External reviewers conflate Phase 0.7 scope with full product scope — have a one-liner defence ready

**Date:** 2026-05-07 | **Cost:** ~0 minutes (caught in /redteam round), but pattern is high-frequency in sales/investor contexts.

**What happened:** An external red-team reviewed Project Nova and raised four critiques: (1) Δ assumes homogeneous players — need persona modeling, (2) Carla is unvalidated as a human proxy, (3) N=5 is anecdotal, (4) 2048 is too simple for meta-economy games. All four are real concerns at the product scope. All four are already scheduled in the roadmap (persona calibration Phase 2, human-cohort anchor Phase 4, N=20 power-adjusted test in ADR-0007, Gossip Harbor Phase 2+). The critiques were accurate about what Phase 0.7 doesn't prove — but misread Phase 0.7 as a claim that it does prove those things. Additionally, the red team confused "N=5 pilot gate" (calibration smoke) with the formal test (N=20 minimum, power-adjusted). These two conflations together produced a "Science-Adjacent" framing that was more alarming than warranted.

**Lesson:** External reviewers rarely have context on phase sequencing. They see the current work and evaluate it against the full product's required evidence base. The right defense is not "our methodology is complete" but "this phase answers question X; questions Y and Z are answered in phases N+1 and N+2." Each gate needs a one-liner that names its specific question and explicitly defers the others. Without this, reviewers will always find gaps — because Phase 0.7 IS incomplete, by design.

Separately: always distinguish the pilot N from the formal test N in any communication. N=5 is a calibration gate; the formal test is N=20 minimum. These are different things and presenting them ambiguously gives reviewers a numerically correct but practically misleading attack surface.

**How to apply:**
- For any external presentation of Phase 0.7 results, lead with: "Phase 0.7 answers: is the cognitive architecture internally consistent on 2048? It does NOT yet claim: will it correlate with real churn data, generalise to meta-games, or work across persona archetypes. Those are Phases 2, 3, and 6 respectively."
- When reporting trial counts externally, always name the type: "N=5 pilot calibration gate / N=20 formal test (power-adjusted per ADR-0007 Amendment 2)." Never let "N=5" stand alone.
- Preempt critique #1 (persona) by noting that methodology §1 already defines 4 named Signatures per persona cohort — Phase 0.7 tests one persona as a proof-of-architecture; multi-persona calibration is Phase 2.

### Phase 4 VLM-human validation needs a human-cohort anchor — plan for it now

**Date:** 2026-05-07 | **Cost:** ~0 minutes (identified in /redteam), design cost if deferred to Phase 4 without planning.

**What happened:** External red-team correctly identified that Nova's Cliff Test validates "does Carla's Anxiety signal precede her own failure" — but NOT "does Carla's Anxiety signal match a human's signal on the same board." The methodology acknowledges Phase 0.7 is synthetic validation only; human-correlation is Phase 4+. The red team's critique was framed as "VLM/Carla as Human Proxy: 3/10" — which is harsh but correct for Phase 0.7 as a standalone claim. Phase 4 long-horizon validation is where human ground truth anchors the model.

**Lesson:** Phase 4 (long-horizon cohort distributions) is the natural insertion point for human-cohort anchoring. If the design for Phase 4 doesn't explicitly include a human-cohort arm (e.g., think-aloud protocol, eye-tracking on a matched cohort, or self-report during 2048 play), then Phase 4 will validate Nova's internal consistency across time but still not answer "does Carla match a human." The review process for Phase 4 will ask this question; better to answer it in the Phase 4 spec than to re-derive it under pressure.

**How to apply:**
- When writing the Phase 4 spec (long-horizon retention curves), include an explicit human-anchor arm: at minimum a self-report measure from real 2048 players on matched scenarios, aligned by board state. Even n=30 human trials is enough to test directional correlation.
- Frame the anchor as "face validity" for the proxy, not "proof of equivalence" — VLM emotional architecture is not identical to human emotion, but Carla's predictive signal should correlate with human self-reported frustration at the same board states. That correlation is what Phase 4 can test.
- In any pitch or methodology document, explicitly name Phase 4 as the human-anchor gate. Don't leave it as implicit future work.

### Economic-frustration layer for meta-economy games should be designed in Phase 2, not retrofitted in Phase 3

**Date:** 2026-05-07 | **Cost:** ~0 minutes (identified in /redteam), potential 6-8 week retrofit cost if deferred.

**What happened:** External red-team correctly noted that Gossip Harbor (merge-2 meta-economy) churn is driven by energy/reward ratios and live-ops FOMO, not just board-state geometry. Nova's current reasoning layer (VLM sees board state → ToT branches evaluate moves) has no mechanism for "I paid $5 and didn't get the item." The red team scored this 4/10 for generalization to meta-games. The methodology defers meta-economy support to Phase 2+ (Tetris → Gossip Harbor pipeline), which is correct. But the economic-layer design work (what new reasoning pathways, what game-state schema extensions, what new Signature) should start in Phase 2 spec design, not Phase 3 implementation.

**Lesson:** Adding an economy layer to an existing reasoning engine late is expensive: new game-state schema + new System 1/2 reasoning prompts + new Signature with its own falsification criterion + potential affect-module changes if economic frustration feeds Anxiety differently than board-geometry frustration. Designing these in Phase 2 spec (when the Gossip Harbor decision is first made) avoids a Phase 3 retrofit that has to thread through an already-validated architecture.

**How to apply:**
- Phase 2 spec for Gossip Harbor should include a dedicated §: "Economic-frustration layer" — what game-state fields beyond board state (resource counts, energy timers, item prices), what reasoning pathway modification (does the ToT evaluator need access to resource state?), and what new Signature captures economic churn vs board-geometry churn.
- The economic-layer design doesn't need to be implemented in Phase 2 (2048 proof-of-concept is still board-state only) — it just needs to be designed so Phase 3 has a spec to implement against.
- When writing the Phase 2 roadmap entry for Gossip Harbor, explicitly call out this dependency: "Gossip Harbor integration requires economic-layer spec before implementation sprint."

### Category positioning matters more than feature parity

**Date:** 2026-05-02 | **Context:** dossier writing decision on Nova's positioning

**What happened:** Originally framed Nova as "AI playtesting" (adjacent to modl.ai, a QA tool). After review, repositioned as "Cognitive Audit & Prediction Platform" — a product-decision tool. Same architecture, fundamentally different sales motion.

**Lesson:** What category you claim determines your buyer, your pricing, your conferences, your competitors. QA = cost center, smaller budgets, head-on with modl.ai. Product/Live-Ops = profit center, larger budgets, less direct competition. The same product can be sold into different categories with very different outcomes.

**How to apply:** When positioning a product, ask "which department's budget pays for this" and "what KPIs does that department care about." The answer determines the category. Optimize for the larger budget + less-crowded category, even if the technical feature set is identical.

### Don't invent dollar figures in reports

**Date:** 2026-05-02 | **Context:** the bug-handling spec

**What happened:** Initial framing proposed "fix this bug or lose $10K UA spend tomorrow." Rhetorically powerful, quantitatively unsupported (we don't know the studio's CAC, cohort size, or LTV).

**Lesson:** Fabricated numbers destroy credibility with sophisticated buyers. Hand them observable cohort data and let them compute the dollar impact with their own inputs. They'll trust you more for it.

**How to apply:** No invented metrics in any Nova-generated report. Format: "100% of Casual cohort abandoned at level 5; translated to your real users: D1 retention drops by [X% of your D1 cohort that is Casual]. Apply your own CAC + LTV to compute UA-spend impact."

### Naming determines urgency

**Date:** 2026-05-02 | **Context:** bug-handling deliverable design

**What happened:** Initial proposal: "Catastrophic Churn Event" warning when Nova detects a bug. The AI red-team pointed out that "churn" implies "the player would have quit anyway," producing a "shrug" reaction from Product.

**Lesson:** Headline language determines the urgency the report creates. "Catastrophic Churn Event" → shrug. "Forced Abandonment Event (likely build issue)" → "OH GOD FIX THIS NOW." Same data, completely different outcome.

**How to apply:** When naming a report event, ask "does this name signal preventability and urgency?" If not, rename. Documented in `docs/internal/v2.2-epsilon-spec.txt` §4.

### Methodology publication is a moat, not a leak

**Date:** 2026-05-02 | **Context:** open-source vs proprietary deliberation

**What happened:** Initial instinct: keep the affect→KPI math proprietary so competitors can't clone it. Reviewer counter: publish the methodology, become the industry benchmark, force competitors to explain why their math differs.

**Lesson:** In B2B technical sales, transparency attracts the kind of buyers who pay enterprise pricing (data scientists, technical leads who audit your math). Hidden methodology attracts skeptical buyers who treat you as black-box AI vibes. The methodology moat is not "we have secret math" — it's "we have the validated math + the industry vocabulary + the calibration corpus from real pilots."

**How to apply:** Publish `docs/product/methodology.md` openly. Cite literature. Show the Levene's Test formula. Explain the Signatures. Hide nothing about HOW it works; protect the WHO has been validated against (per-pilot calibration corpus).

---

## Failure-mode handling

### Always define what failure looks like before running the test

**Date:** 2026-05-02 | **Context:** Phase 0.7 cliff test design

**What happened:** Initial plan had "weak pass" zone (50-80% trial pass-rate) where we'd "lower the marketing claim." Reviewer flagged: 55% is essentially a coin flip. A "weak pass" zone is rationalization, not signal.

**Lesson:** Define hard floors for falsifiable tests BEFORE running them. Vague "pass/fail/maybe" zones invite confirmation bias. Solo founders especially need this discipline because there's no one else to challenge the rationalization.

**How to apply:** Phase 0.7 hard floor: ≥70% (above chance + sample noise). Below that triggers the 2-week affect-rework branch unconditionally. No "directional alignment" marketing on a coin-flip result.

### Failed validations are publishable, not project-end

**Date:** 2026-05-02 | **Context:** discussing what to do if cliff test fails

**What happened:** Reviewer asked "are you prepared to kill the project if Phase 0.7 fails?" Reframed: failure isn't binary "kill or pivot." There are at least 4 responses: tune, reposition, pivot architecture, or kill. And even "kill" produces a publishable negative result.

**Lesson:** A negative result from a well-designed experiment is more valuable than no experiment. The downside of running Phase 0.7 isn't $50 in LLM credits; it's the time cost. The upside (knowing definitively whether the architecture predicts) is enormous in either direction.

**How to apply:** Frame validation experiments as "we're going to learn either way." A pass means we proceed with confidence; a fail means we save 6 months of building the wrong thing. Both outcomes are wins relative to "not running the experiment."

### Don't trust "zero new architecture" claims without questioning

**Date:** 2026-05-02 | **Context:** the bug-handling brainstorm

**What happened:** Initial framing of bug-handling claimed "zero new architecture — the existing Frustration accumulator handles this perfectly." On second look: false. The Frustration accumulator triggers on score-delta dynamics, which can't distinguish "bad move" from "bug-frozen game." A new `StateUnchangedAfterAction` detector is required (~50 lines).

**Lesson:** "Zero new architecture" claims are seductive (no work needed!) and almost always wrong. When something seems to handle a new case for free, double-check the actual mechanism. Usually some small but real addition is needed.

**How to apply:** When proposing that an existing system handles a new case, write down the minimal test that would prove it. Often the test reveals the gap.

---

## Maintenance notes

- This file is read manually; no auto-maintenance.
- Periodically (monthly?) prune entries that have been formalized into:
  - Pre-commit hooks → no longer a "lesson," it's a guardrail
  - CI checks → no longer a "lesson"
  - CLAUDE.md gotchas section → no longer a "lesson," it's part of orientation
  - Documented architecture decisions (ADRs) → reference the ADR, then prune
- New lessons go at the top of their section.
- Date format: YYYY-MM-DD.
- "Cost" estimates are rough — they exist to convey "this was painful" not for precise accounting.
