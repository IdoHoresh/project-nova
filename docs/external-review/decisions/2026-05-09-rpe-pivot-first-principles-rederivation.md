# §4.1 First-Principles Re-Derivation — RPE Pivot Decision

**Date:** 2026-05-09
**Triggered by:** Layer 2 round 2 finding 4 ([high]) — P5 was reversal #2 in the thread (H1 → H6 → P5); §4.1 hard line requires holding the position pending independent first-principles re-derivation before adoption.
**Method:** Cold subagent dispatch. Subagent received state.py + main.py + methodology.md + desk-demo summary, but was forbidden from reading: ACH worksheet, Layer 2 round 1 review, Layer 2 round 2 review, test 6 results doc, original red-team memo, offline-redteam-prompt, channel-research doc. Equivalent to a 24h fresh-eye pause without the wall-clock cost.
**Subagent ID:** af14eec4cb7f3aca1
**Wall time:** ~5 min
**Cost:** $0 (Sonnet 4.6, included in subscription)

---

## Subagent's task

Answer four questions in order, from first principles, without consulting any prior position document:

(a) What does the code do?
(b) What does methodology.md claim?
(c) What is the smallest change in code that closes (a) → (b)?
(d) What is the next falsification gate after that change ships?

---

## Subagent's verbatim answer

### (a) What the code does

Three independent anxiety drivers in `nova-agent/src/nova_agent/affect/state.py`:

1. Decay (line 37): `anxiety = v.anxiety * 0.85`
2. Empty-cells term (lines 49–50): `anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)`, gated by counterfactual flag
3. Trauma-intensity term (line 51): `anxiety += 0.3 * _clamp(trauma_intensity, 0.0, 1.0)`
4. Terminal override (lines 52–53): `anxiety = 1.0` when game ends

Frustration is computed (line 44: `frustration += min(1.0, -rpe * 0.6)`) but NOT wired to anxiety. The "RPE → frustration → anxiety chain" claimed in methodology.md is architecturally absent.

### (b) What methodology.md claims

Operative claim: anxiety must produce *predictive lead-time* — rise BEFORE failure becomes inevitable. The Cliff Test pass criteria require `Anxiety > 0.6` to PRECEDE bot game-over by ≥2 moves (Δ ≥ 2 across ≥3 scenarios).

The methodology doesn't mathematically specify "RPE → frustration → anxiety" but its architectural commitment requires drivers that respond *faster* than pure board-state exhaustion. Frustration as a negative-RPE accumulator is the implied pre-empty_cells signal.

### (c) Smallest change closing (a) → (b)

Single-line addition to `state.py:51`:

```python
anxiety += 0.3 * _clamp(trauma_intensity, 0.0, 1.0)
anxiety += K * _clamp(frustration, 0.0, 1.0)  # RPE → frustration → anxiety chain
```

K is a scaling coefficient (TBD by the rewrite ADR).

This is the minimum because:
- Frustration is already computed correctly elsewhere
- The formula structure exists; only need to sum frustration's contribution
- No new state variables, inputs, or restructuring

### (d) Next falsification gate

Pre-committed: Re-run Phase 0.7a on the new formula. Spec R2 acceptance:
- All 3 scenarios ≥4/5 `t_predicts is not None`
- AND ≥4/5 `(game_over_move - t_predicts) ≥ 2`
- AND within-scenario `t_predicts` stdev ≥ 1.5 moves

**Subagent's sufficiency assessment:** The single-line change is NECESSARY but NOT SUFFICIENT. Three reasons:

1. **Function shape wrong.** Linear/sqrt saturate anxiety to 1.0 (early alarm, not predictive lead-time).
2. **512-wall is a blocker.** Frustration is 0/199 nonzero events on this scenario — geometric (4 free cells, board never fills enough for negative RPE). No K can make zero non-zero.
3. **K-tuning required.** Coefficient must avoid both no-fire and premature-saturation.

**Rewrite ADR scope (subagent's recommendation):** wire frustration → anxiety + tune K + propose a third driver for 512-wall + run Pearson(frustration, 1/empty_cells) on morning-pilot CSV as precondition. Phase 0.7b re-run is the gate.

### Coherence check (subagent's own self-audit)

Subagent's closing paragraph: "the single-line wiring change will partially close (a) → (b) for snake and corner scenarios but completely fail on 512-wall. The change is the necessary first step toward a complete fix, but the rewrite ADR must simultaneously (1) tune K to avoid saturation, (2) propose a third driver for 512-wall, and (3) confirm frustration is not collinear with the original empty_cells axis via the Pearson test. Phase 0.7b is the gate that determines sufficiency."

---

## Comparison to P6 (the position being held)

P6 was: wiring + magnitude (K-tuning) + 3rd driver firing on 512-wall + methodology audit + erratum.

| P6 element | Subagent independently proposed? | Match? |
|---|---|---|
| Wiring (state.py:51 line addition) | ✓ (verbatim) | exact |
| Magnitude / K-tuning | ✓ | exact |
| 3rd driver for 512-wall | ✓ | exact |
| Pearson precondition | ✓ | exact (already run; r ≈ -0.12) |
| Phase 0.7b re-run as gate | ✓ | exact |
| Erratum on phase-0.7a-result.md | not addressed (subagent's task didn't include process changes) | neither validated nor invalidated |
| Methodology audit | not addressed (subagent's task didn't include process changes) | neither validated nor invalidated |

**All P6 CODE-CHANGE clauses match the subagent's independent derivation.** The audit + erratum are PROCESS additions the subagent wasn't asked about; they neither contradict nor validate.

---

## §4.1 Verdict

**P6 is NOT reframe-after-cave.** An independent reviewer with no exposure to round 1, round 2, ACH worksheet, or reviewer prompts arrived at the same CODE-level position from clean reading of state.py + methodology.md + desk-demo data. The position survives the hold gate.

P6 is **LOCKED** as of this re-derivation. Layer 3 (multi-model cross-rebuttal) does NOT fire — there are no remaining unresolved high-severity findings against P6 after the round 2 prerequisites have been satisfied.

Next: draft the rewrite ADR (path A, Opus already in session) per the locked P6 scope. Run the methodology audit per `2026-05-09-methodology-code-audit-spec.md` as a precondition (≤4h, $0).

---

## Notes on the audit/erratum gap in the subagent's derivation

The subagent did not propose a methodology audit. This is consistent with two possible readings:

1. **The audit is overscope.** The subagent independently found the smallest code change that closes (a) → (b) without needing to enumerate other code-vs-spec gaps. If the audit is justified solely by "find OTHER gaps," that's a separate question the subagent wasn't asked.

2. **The subagent wasn't asked.** The task brief was scoped to "smallest change that closes (a) → (b)" — process changes (audits, errata) weren't in scope. Silence here doesn't validate or invalidate the audit.

Reading 2 is more honest. The audit's justification is independent — it comes from the round 2 reviewer's argument that finding ONE code-fictional claim (frustration→anxiety) statistically suggests others may exist, and the rewrite ADR's preamble should not cite a methodology document with un-audited claims. That argument stands on its own merit, not on whether the subagent independently proposed it.

The erratum is similarly independent — it's a documentation correction owed regardless of the rewrite ADR's scope.

Both proceed on their original §4.4-disciplined timebox (audit ≤4h, erratum already shipped).
