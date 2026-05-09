# Methodology-vs-Code Gap Audit — Spec

**Date:** 2026-05-09
**Triggered by:** Layer 2 round 2 finding 3 ([high]) — the methodology audit is justified but must be timeboxed with binary pass/fail criteria, or it becomes §4.4 procrastination dressed as discipline.
**Author:** This is the spec — written BEFORE opening any methodology.md file (the spec is the timebox).
**Wall-clock budget:** ≤ 4 hours.
**Cost:** $0–$2 (no LLM calls required; pure code-read + grep).
**Output target:** `docs/external-review/decisions/2026-05-09-methodology-code-audit-results.md` containing the three binary outputs in §3 below.

---

## 1. What this audit is, and what it is NOT

### Is

A one-time check of `docs/product/methodology.md` and key ADRs against the code in `nova-agent/src/nova_agent/`. For each named architectural mechanism, verify that the code implements it OR mark it `spec-only`. Classify each `spec-only` finding by severity. Use the result to scope the rewrite ADR.

### Is NOT

- A redesign exercise. The audit produces a list; the rewrite ADR fixes the load-bearing items. Cosmetic items go in a backlog, not the ADR.
- Open-ended. The audit is bounded to the priority checklist in §2 below. New candidates surfaced during the audit are recorded but not investigated this pass.
- A code-review of the implementations themselves. The question is "does the mechanism exist in code at all," not "is the implementation correct/idiomatic/efficient."
- A documentation rewrite. The audit produces findings; methodology.md edits land later, after the rewrite ADR.

---

## 2. Priority checklist (pre-committed before opening methodology.md)

These are the candidates supplied by Layer 2 round 2 finding 5, in priority order. Each takes ~10 min to verify. Total: ~60 min for all 6, leaving budget for the report-writing in §3.

### 2.1 `trauma_intensity` wiring (HIGHEST priority)

- **Claim under test:** `methodology.md` describes a trauma-tagging mechanism (`tag_aversive` at game-over, retrieval at decision time via cosine-weighted aversive recall per ADR-0012) that produces non-zero `trauma_intensity` values during normal play.
- **Why highest priority:** Phase 0.7a showed `trauma_intensity = 0.0` across 658 events. Phase 0.8 trauma ablation (Levene's W on variance) is the next gated phase and depends on this signal being non-trivial.
- **How to test:** grep `nova-agent/src/nova_agent/memory/` and `nova-agent/src/nova_agent/main.py` for `tag_aversive` call sites and `trauma_intensity` write sites. Confirm: (a) tag fires only at game-over per `main.py:96`; (b) retrieval fires at every decision tick; (c) cosine threshold value; (d) what the threshold filters in normal play.
- **Output:** present / spec-only / partially-implemented + severity {load-bearing-for-predictive-lead-time / load-bearing-for-product-surfaces / cosmetic} + 1-line evidence citation.

### 2.2 ADR-0002 Signatures Beta, Gamma, Delta

- **Claim under test:** ADR-0002 names four State-Transition Signatures (Alpha = churn, Beta = conversion, Gamma = engagement, Delta = bounce). Per the Layer 2 round 1 reviewer's prompt §3.2, only Alpha has defined operationalization.
- **How to test:** grep `nova-agent/src/nova_agent/` for `signature`, `churn`, `conversion`, `engagement`, `bounce`. Read ADR-0002. Determine: are Beta/Gamma/Delta in code at all (with thresholds, conjunctions, observable outputs), or mentioned only in spec?
- **Output:** per-Signature present / spec-only + severity + 1-line evidence.

### 2.3 Three-channel memory decay

- **Claim under test:** `LESSONS.md` "Three-channel memory decay" entry references episodic ~24h / semantic ~7d / affective ~30d decay. Three separate decay rates in code, or one rate with three labels?
- **How to test:** grep `nova-agent/src/nova_agent/memory/` for decay constants, time-windowed retrieval, expiry logic. Read `MemoryCoordinator` and the SQLite/LanceDB store integrations.
- **Output:** three-rates / single-rate-three-labels / spec-only + severity + 1-line evidence.

### 2.4 Reflection → semantic memory consumption

- **Claim under test:** `methodology.md` and ADR-0001 describe reflection writing lessons to semantic memory and future decisions reading them. Does `reflect()` write lessons that any future decision actually reads, or are they written-to-disk-and-forgotten?
- **How to test:** grep `nova-agent/src/nova_agent/decision/` for retrievals from semantic memory. Trace one reflection write through the bus to a downstream consumer.
- **Output:** read-by-decision / written-only / spec-only + severity + 1-line evidence.

### 2.5 Russell mood radar (valence × arousal)

- **Claim under test:** `methodology.md` references the Russell circumplex; the Brain Panel renders a valence × arousal radar. Is mood radar consumed by any decision logic, or display-only?
- **How to test:** grep `nova-agent/src/nova_agent/decision/` and `nova-agent/src/nova_agent/llm/` for `valence`, `arousal`. Check if any decision uses them as input.
- **Output:** consumed-by-decision / display-only / spec-only + severity + 1-line evidence.

### 2.6 ToT-branch-disagreement as uncertainty signal

- **Claim under test:** Spec `2026-05-09-phase-0.7a-counterfactual-design.md` §7 R1 candidate (c) names ToT-branch-disagreement as a candidate uncertainty signal. Is there any wiring at all, or is this paper-only?
- **How to test:** Read `nova-agent/src/nova_agent/decision/tot.py`. Check if branch outputs are compared / aggregated into any uncertainty measure used downstream.
- **Output:** wired / spec-only + severity + 1-line evidence.

---

## 3. Three binary outputs (mandatory)

The audit's report (`2026-05-09-methodology-code-audit-results.md`) must contain three outputs. No fourth output is permitted. No prose discursion permitted in the report itself; commentary goes in a separate "Notes" appendix the rewrite ADR may or may not consult.

### Output 1 — list of `methodology.md` mechanism claims tested

A bulleted list. One bullet per claim. Format:

```
- [Claim 1] (cite: methodology.md §X.Y, line N OR ADR-NNNN §Z)
- [Claim 2] (cite: ...)
- ...
```

Bounded to the §2 priority checklist for this audit. New candidates surfaced during the audit go in the "Notes" appendix as `out-of-scope-this-pass`.

### Output 2 — present / absent in code

For each claim in Output 1:

```
- [Claim N]: present | spec-only | partially-implemented | undecidable-without-deeper-read
  - evidence: [file path:line range OR `grep produced no matches in <path>`]
```

`undecidable-without-deeper-read` is escape-valve for ambiguous cases. Cap at 2 escape-valve uses across the audit. If the cap is hit, the audit is not done.

### Output 3 — severity classification (for `spec-only` and `partially-implemented` claims)

For each non-`present` claim:

```
- [Claim N]: load-bearing-for-predictive-lead-time | load-bearing-for-product-surfaces | cosmetic
  - reasoning: [one sentence]
```

The rewrite ADR's scope is fixed by `load-bearing-for-predictive-lead-time` rows only.
`load-bearing-for-product-surfaces` rows go in a follow-up ticket.
`cosmetic` rows go in a backlog file, not the ADR.

---

## 4. Stop conditions (anti-§4.4 discipline)

Stop the audit immediately if ANY of the following fires:

- **(a) 4-hour wall budget exhausted.** Report what is done; mark the rest `not-yet-audited` in the appendix. Do not extend.
- **(b) > 2 escape-valve uses** in Output 2. Audit method is not working; pause and re-spec.
- **(c) Audit grows fix-as-you-go.** If the temptation arises to "while I'm here, also fix the gap I just found," STOP. The audit produces findings; the rewrite ADR fixes them. Mixing the two is the H6 framing-escalation pattern repeating.
- **(d) New candidate fires the urge to add it to the priority list mid-audit.** Record in appendix as `out-of-scope-this-pass`. Do not interrupt the priority order.

---

## 5. What this audit does NOT prove

- Does NOT prove `methodology.md` is (or is not) sound as a methodology document. The audit checks claim-vs-implementation, not claim-vs-truth.
- Does NOT prove the rewrite ADR will succeed. The audit narrows the scope; the ADR has to deliver.
- Does NOT replace Layer 2 round 2's other surviving findings (the §4.5 cap-collapse risk, the saturation warning, the desk demo result). Those still feed into the rewrite ADR independently.
- Does NOT replace the §4.1 first-principles re-derivation. The audit produces a list; the re-derivation produces a position. Both are needed; neither substitutes for the other.

---

## 6. Acceptance criteria for "audit complete"

- [ ] Output 1, 2, 3 written and saved to `docs/external-review/decisions/2026-05-09-methodology-code-audit-results.md`.
- [ ] All 6 priority checklist items in §2 covered (or any uncovered explicitly listed in the appendix as `not-yet-audited` due to budget exhaustion).
- [ ] No claim in Output 2 is left without evidence citation.
- [ ] No more than 2 `undecidable-without-deeper-read` markers in Output 2.
- [ ] No prose discursion in the main outputs (commentary fenced to "Notes" appendix).
- [ ] Wall time logged in the appendix.

If all acceptance criteria pass, the audit is complete and the rewrite ADR drafting can begin (after the §4.1 first-principles re-derivation lands and produces a position update).
