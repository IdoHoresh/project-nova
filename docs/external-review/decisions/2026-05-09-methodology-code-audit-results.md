# Methodology-vs-Code Gap Audit — Results

**Date:** 2026-05-09
**Spec:** `docs/external-review/decisions/2026-05-09-methodology-code-audit-spec.md`
**Wall time:** 2026-05-09T10:30:16Z → 2026-05-09T10:33:24Z (~3 min, well under 4h budget)
**Cost:** $0 (no LLM calls; pure code-read + grep)
**Escape-valve uses:** 0/2

---

## Output 1 — Claims tested

- **§2.1 trauma_intensity wiring:** the architecture computes a non-zero `trauma_intensity` during normal play via `tag_aversive` at game-over (cite: `methodology.md` §3 *Memory* table; ADR-0012 §Decision Change 1) plus cosine-weighted aversive recall at decision time.
- **§2.2 ADR-0002 Signature Alpha (Churn):** `Confidence ↓ → Anxiety ↑ → Frustration plateau` state machine matched in code (cite: ADR-0002 *Decision*; `methodology.md` §1).
- **§2.2 ADR-0002 Signature Beta (Conversion):** `Frustration ↑ + Dopamine starvation near monetization touchpoint` state machine matched in code (cite: ADR-0002 *Decision*; `methodology.md` §1).
- **§2.2 ADR-0002 Signature Gamma (Engagement):** `Confidence ↑ + Dopamine ↑ across consecutive moves with low Anxiety` state machine matched in code (cite: ADR-0002 *Decision*; `methodology.md` §1).
- **§2.2 ADR-0002 Signature Delta (FTUE Bounce):** `Anxiety spike within first 60 seconds of fresh session in empty-memory persona` state machine matched in code (cite: ADR-0002 *Decision*; `methodology.md` §1).
- **§2.3 Three-channel memory decay:** episodic ~24h half-life, semantic ~7d half-life, affective baseline ~30d with floor — three separate decay rates wired in code (cite: `LESSONS.md` "Three-channel memory decay matched to cognitive psychology"; `methodology.md` §3 *Memory* table).
- **§2.4 Reflection → semantic memory consumption:** lessons written to semantic memory by `reflect()` are read by future *decision* code, not just by future reflection (cite: ADR-0001 *Decision* "agent learns across games"; `methodology.md` §3 *Reflection*).
- **§2.5 Russell mood radar (valence × arousal):** consumed by decision logic (LLM prompt or deterministic branch) rather than display-only (cite: `methodology.md` §3 *Affect Vector*).
- **§2.6 ToT-branch-disagreement as uncertainty signal:** branch outputs from `ToTDecider` are aggregated into a downstream uncertainty / confidence measure (cite: spec `2026-05-09-phase-0.7a-counterfactual-design.md` §7 R1 candidate (c)).

---

## Output 2 — present / absent in code

- **§2.1 trauma_intensity wiring: present**
  - evidence: `tag_aversive` call site `nova-agent/src/nova_agent/main.py:97` (catastrophic-loss-gated game-over hook); `trauma_intensity` computation `nova-agent/src/nova_agent/main.py:222-242` (cosine-weighted aversive recall at every decision tick, gated by `AVERSIVE_RELEVANCE_FLOOR = 0.66` per `nova-agent/src/nova_agent/memory/retrieval.py:67`).
- **§2.2 Signature Alpha (Churn): spec-only**
  - evidence: `grep -rin "signature\|churn" nova-agent/src/nova_agent/ --include="*.py"` produced zero matches against ADR-0002 Signature semantics; the only `signature` hits (`bus/recorder.py:16`, `decision/baseline.py:94`) refer to Python function signatures, not state-transition signatures.
- **§2.2 Signature Beta (Conversion): spec-only**
  - evidence: `grep -rin "conversion" nova-agent/src/nova_agent/ --include="*.py"` produced no matches.
- **§2.2 Signature Gamma (Engagement): spec-only**
  - evidence: `grep -rin "engagement" nova-agent/src/nova_agent/ --include="*.py"` produced no matches.
- **§2.2 Signature Delta (FTUE Bounce): spec-only**
  - evidence: `grep -rin "bounce\|ftue\|fresh session\|empty.memory persona" nova-agent/src/nova_agent/ --include="*.py"` produced no matches.
- **§2.3 Three-channel memory decay: spec-only**
  - evidence: only one decay rate exists in code — `recency_score(half_life_days: float = 7.0)` in `nova-agent/src/nova_agent/memory/retrieval.py:9-19`, applied uniformly to episodic recency. `nova-agent/src/nova_agent/memory/semantic.py` (full file 63 lines) has no decay logic. No `affective_baseline` decay path exists; `affect.reset_for_new_game()` (`nova-agent/src/nova_agent/affect/state.py:79-80`) is a defense-D reset, not a gradual decay.
- **§2.4 Reflection → semantic memory consumption: partially-implemented**
  - evidence: reflection-to-reflection loop wired (`main.py:102` reads `semantic.all_rules()` into `prior_lessons`; `main.py:115-116` writes new lessons via `semantic.add_rule()`; `prior_lessons` flows to `run_reflection()`). Reflection-to-decision loop NOT wired: `grep -rin "semantic\|prior_lessons\|all_rules" nova-agent/src/nova_agent/decision/ --include="*.py"` produced zero matches against semantic-memory consumption. `nova-agent/src/nova_agent/memory/semantic.py:6` docstring acknowledges decision-prompt consumption is "(future)."
- **§2.5 Russell mood radar (valence × arousal): present**
  - evidence: `nova-agent/src/nova_agent/affect/verbalize.py:15` partitions valence × arousal into Russell-style mood adjectives ("satisfied" / "calm" / "discouraged"); `nova-agent/src/nova_agent/decision/prompts.py:68` injects the verbalized text as `"Mood: {affect_text}"` in the LLM decision prompt. Also published to bus for brain-panel display (`main.py:301-302, 311-312`).
- **§2.6 ToT-branch-disagreement: spec-only**
  - evidence: `nova-agent/src/nova_agent/decision/tot.py:91` selects via `best = max(candidates, key=lambda c: c.value)`; `tot.py:106` returns `Decision(..., confidence="medium", ...)` with confidence hardcoded, not derived from branch-value variance. The `branch_values` dict is published in `tot_selected` event (`tot.py:99`) for brain-panel display only; no downstream consumer aggregates it into an uncertainty measure.

---

## Output 3 — severity (non-present claims)

- **§2.2 Signature Alpha (Churn): load-bearing-for-product-surfaces**
  - reasoning: ADR-0002 frames Signatures as the methodology spine for the affect → KPI mapping that distinguishes Nova from threshold-based products; absent Alpha, the cliff-test affect math has no path to a churn KPI claim.
- **§2.2 Signature Beta (Conversion): load-bearing-for-product-surfaces**
  - reasoning: same axis as Alpha; without Beta, no conversion-touchpoint prediction.
- **§2.2 Signature Gamma (Engagement): load-bearing-for-product-surfaces**
  - reasoning: same axis as Alpha; without Gamma, no positive-flow engagement signal.
- **§2.2 Signature Delta (FTUE Bounce): load-bearing-for-product-surfaces**
  - reasoning: same axis as Alpha; without Delta, no FTUE-bounce prediction.
- **§2.3 Three-channel memory decay: load-bearing-for-product-surfaces**
  - reasoning: the cross-session "Day-3 frustration → Day-17 churn risk via slow-decaying affective channel" claim in `LESSONS.md` (lines 564-569) depends on multi-rate decay; with only single-rate episodic recency, that cross-session compounding story is currently architectural fiction. Within-game cliff-test predictive lead-time is unaffected (the cliff test runs in seconds-to-minutes; decay rates of 24h–30d are out of band).
- **§2.4 Reflection → semantic memory consumption: load-bearing-for-product-surfaces**
  - reasoning: the "agent learns across games" framing in ADR-0001 implies durable lessons shape future play. Reflection-only consumption means lessons influence the next *post-game narration* but not the next game's *moves*; the agent doesn't actually use what it learned during play. Within-game predictive lead-time is unaffected (Cliff Test trials run within a single game).
- **§2.6 ToT-branch-disagreement: load-bearing-for-predictive-lead-time**
  - reasoning: explicitly named as a candidate for the rewrite ADR's third anxiety driver in spec `2026-05-09-phase-0.7a-counterfactual-design.md` §7 R1 candidate (c) and re-derivation §(d). Wiring branch-value variance into anxiety would make the architecture's deliberation-uncertainty observable to the affect layer; the rewrite ADR scope must decide whether to wire it.

---

## Notes appendix (commentary, not load-bearing)

### §2.1 — production vs lab harness gap

`trauma_intensity` is implemented in `main.py` (production decision loop) but the Phase 0.7a counterfactual ran via `nova-agent/src/nova_agent/lab/cliff_test.py:374-375`, which explicitly disables memory retrieval and pins `trauma_intensity = 0.0`. The Phase 0.7a observation of "trauma=0 across 658 events" is therefore a **harness artifact, not a code gap** against methodology.md.

The rewrite ADR must decide whether Phase 0.7b runs against the production main-loop path (with retrieval enabled, allowing trauma to fire) or continues against `cliff_test.py` (with retrieval disabled, leaving trauma silent). Running the rewrite-ADR's new formula against a harness that nulls one of its three drivers is a falsification-dodge pattern by another name.

The `lab/trauma_ablation.py` Phase 0.8 path (`trauma_ablation.py:394-411`) DOES enable the same trauma-intensity computation, so the architecture is exercised in at least one lab harness — the gap is specifically `cliff_test.py`'s Phase 0.7a-only retrieval-disable.

### §2.2 — ADR-0002 status

All four Signatures are spec-only. ADR-0002 is dated 2026-05-02 and acknowledges in its *Consequences (Negative)* that "more complex to implement than threshold checks. Each Signature needs a state-tracking detector with timing windows" — i.e., it always was forward-looking architecture. The audit confirms: zero detectors have shipped.

This does NOT block the rewrite ADR (which targets within-game anxiety predictive lead-time). It DOES block any product-surface claims about Nova's churn / conversion / engagement / FTUE prediction; those are currently sales-deck-only.

### §2.6 — ToT branch-fired-rate carry-over

The audit confirms `tot.py` does not aggregate branch values into uncertainty. Separately (out of audit scope but relevant to the rewrite ADR): Phase 0.7a memory says `tot_fired = false on every event` across 658 observations. Even if branch-disagreement were wired into anxiety, the gating threshold via `should_use_tot()` is currently restrictive enough that the signal would be silent on the Phase 0.7a scenarios as run. The rewrite ADR must decide whether (a) to wire branch-disagreement, (b) to relax the ToT-firing gate, or (c) both.

### Out-of-scope candidates surfaced during audit

- `defense D affective reset` (`affect/state.py:79-80`) — partial alternative to "affective baseline decay" that could be re-evaluated.
- ToT-firing gate (`should_use_tot`) — see §2.6 carry-over above.
- Aversive memory `_enforce_aversive_cap` (`retrieval.py:71-82`) — limits aversive surfacing to 1 record/move; relevant to whether trauma_intensity ever reaches non-trivial magnitudes under load.

These are recorded but not investigated this pass per spec §4(d).

### Stop conditions — none triggered

(a) wall budget: ~3 min of 4h used. (b) escape-valve: 0 of 2 used. (c) fix-as-you-go: no edits to nova-agent code during audit. (d) new candidates: 3 recorded above for follow-up, not added to priority list.

---

## Implications for rewrite ADR scope

**Predictive-lead-time (in-scope for rewrite ADR):**
- §2.6 ToT-branch-disagreement — candidate 3rd anxiety driver, currently spec-only.

**Product-surfaces (follow-up tickets, NOT rewrite ADR scope per audit spec §3):**
- §2.2 ADR-0002 Signatures Alpha/Beta/Gamma/Delta — all spec-only.
- §2.3 Three-channel memory decay — spec-only single-rate.
- §2.4 Reflection → decision consumption — partially-implemented (reflection loop only).

**Confirmed present (no action):**
- §2.1 trauma_intensity wiring (in production path; harness is the gap, see Notes).
- §2.5 Russell mood radar (consumed via verbalize → LLM prompt).

**Cosmetic backlog:** none this pass.

The rewrite ADR's predictive-lead-time scope is narrowed to one new candidate (ToT-branch-disagreement) on top of the P6-locked scope (frustration → anxiety wiring + K-tuning + 3rd driver + audit + erratum). The §2.1 production-vs-harness gap is a methodological side-question for the Phase 0.7b re-run plan, not part of the ADR's anxiety-formula scope.
