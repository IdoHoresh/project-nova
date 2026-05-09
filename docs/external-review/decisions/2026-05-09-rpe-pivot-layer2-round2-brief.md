# Layer 2 Round 2 — Brief for Reviewer

**Date:** 2026-05-09
**Subject:** Phase 0.7a RPE pivot decision — methodology-vs-code gap discovered
**Reviewer:** External Claude (Claude.ai project, offline-redteam-prompt loaded)
**Cost so far on this decision:** $0–$3 (Layer 1 + Layer 2 round 1 + 6 verifications all under budget)
**Cost expected for round 2:** $1–$3
**Author position progression:** H1 → H6 → P1/P2/P3 uncertainty → P4 → **P5 (this brief)**

---

## What changed since round 1

Round 1 reviewer correctly attacked the H6 (HYBRID PRECONDITION) position and named "run the contamination math" as the un-dodgeable test. Six $0 verifications followed. Three of round 1's high+ findings were falsified by data; H6 collapsed for a different reason (rpe.py "bug" is documented design intent, not a bug).

The contamination math itself ran cleanly. The result was **the opposite** of what the red team predicted:

```
Pearson(frustration, 1/empty_cells_pre) = -0.1126
Pearson(frustration, 0.7*max(0,(3-empty_cells)/3)) = -0.1231
```

Per round 1 reviewer's own gating threshold (`|r| < 0.5` → RPE composite proceeds), the RPE/frustration axis is empirically viable. The collinearity argument that motivated H6 is dead.

Then I ran `grep -rn "anxiety\s*+=\|anxiety\s*=" nova-agent/src/nova_agent/` to confirm the formula's structure before drafting the rewrite ADR. The result is **load-bearing for round 2**:

---

## The new finding (load-bearing)

**There is NO frustration → anxiety linkage in the code.**

All anxiety-write sites in `nova-agent/src/nova_agent/affect/state.py`:

```python
# Line 37 — decay
anxiety = v.anxiety * 0.85

# Line 49-50 — empty_cells term, gated by counterfactual flag
if not self._null_empty_cells_term:
    anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)

# Line 51 — trauma_intensity term
anxiety += 0.3 * _clamp(trauma_intensity, 0.0, 1.0)

# Line 52-53 — terminal override
if terminal:
    anxiety = 1.0
```

Frustration is computed elsewhere (line 44: `frustration += min(1.0, -rpe * 0.6)`) but never appears in any anxiety-write expression in any file under `nova-agent/src/nova_agent/`.

The methodology document and the Phase 0.7a adjudication memo both reference "RPE-via-frustration" as one of the architecture's non-`empty_cells` anxiety drivers. **The code shows this driver is fictional** — there is no coefficient on frustration in the anxiety formula.

---

## Implications

1. **Phase 0.7a's R1 fire was structurally inevitable, not a discovery.** With `empty_cells` nulled, the only remaining anxiety driver in the code was `trauma_intensity` (0.0 across the run because no aversive memories existed mid-game). Frustration could not have crossed the anxiety threshold no matter what amplitude it produced — there is no path from frustration to anxiety. The R1 verdict was discoverable from a 5-second `grep`, not a $0.66 paid-tier Pro run.

2. **C1 wasn't "confirmed by ablation" — confirmed by trivial inspection.** The adjudication memo's "C1 fully confirmed" framing implies the data ruled something out. The data couldn't have shown anything else given the formula's structure.

3. **The Pearson result loses some load-bearing weight.** Independence between `frustration` and `empty_cells` (`r ≈ -0.12`) was supposed to gate the rewrite ADR's axis choice. But independence is moot if the new axis (frustration) has no coefficient on the output (anxiety) anywhere in the code. The "is RPE collinear with empty_cells" question was the wrong question.

4. **Methodology document has been making claims about an architecture that doesn't exist.** This is a documentation/spec integrity issue distinct from the rewrite axis question. Other claims in `docs/product/methodology.md` and the locked ADRs may also be code-fictional.

---

## My new position (P5) — what I'm asking you to attack

**The rewrite ADR scope shifts from "swap empty_cells axis for RPE/frustration" or "re-tune the existing chain" to "ADD the frustration → anxiety linkage that the methodology document has been claiming exists for the past N weeks. Plus audit the methodology document for other code-vs-spec gaps before the rewrite proceeds."**

Specifically:

1. Add a `K_frust * frustration` term to the anxiety formula in `state.py:51` area (coefficient TBD via tuning, not napkin math).
2. Add ADR-0012 retrieval instrumentation to JSONL bus events so future runs can diagnose memory silence (the (a)/(b)/(c) distinction in the test 6 results doc).
3. Re-author scenarios to pass `§7.4` calibration (per round 1 reviewer's surviving §3.3 finding).
4. Pre-commit numeric N for next falsification (per round 1 reviewer's surviving §3.5 finding).
5. Update methodology narrative to reflect what the code actually does (per round 1 reviewer's surviving §3.4 finding).
6. **NEW:** Code-vs-spec audit of `methodology.md`, ADR-0002, and ADR-0012 BEFORE drafting the rewrite ADR. Identify every claim about an anxiety driver, memory mechanism, or affect linkage that the code does not implement.

---

## Questions for you (round 2 reviewer)

Per the offline-redteam-prompt (already in this project's instructions): do not validate P5 because I propose it. Open with finding 1.

1. **Is the methodology-vs-code gap fatal to the C1-confirmed verdict?** I believe it downgrades it ("verdict is mechanically obvious from grep, not earned by ablation"). The honest reframe is "the architecture as implemented has only one non-trivial anxiety driver (`empty_cells`); Phase 0.7a confirmed this trivially." Argue the strongest case that this DOES kill the C1-confirmed framing entirely, not just downgrades it.

2. **Should the rewrite ADR address the gap, OR should it be preceded by a separate spec/code-audit phase?** P5 includes an audit clause (#6 above). Round 1 reviewer's §4.4 anti-pattern (pre-emptive scope-escalation when fixes asymptote) may be firing here. Specifically: am I overscoping by adding a methodology audit on top of the rewrite ADR? The cheap counterargument is "the gap is just one (frustration→anxiety) — fix it; don't audit the whole methodology." Argue both sides.

3. **What other claims in `methodology.md` might be code-fictional and need audit before any rewrite?** I have not enumerated them. Likely candidates given the Phase 0.7a result: the State-Transition Signatures (ADR-0002 — Signature Alpha gates on anxiety; if anxiety has only one driver, Signature Alpha collapses to that driver). Trauma-tagging (ADR-0012 — what aversive-memory mechanism exists vs is described). Russell circumplex appropriations. Schultz dopamine RPE timescale claims. Without a concrete enumeration, "audit the methodology" is a slogan. Force me to list candidates with citations.

4. **Is P5 a §4.3 reframe-after-cave or a §4.4 overscope?** Round 1 reviewer would want to know. The position has now reversed 4 times in this session: H1 → H6 → P1/P2/P3 uncertainty → P4 → P5. Each reversal has been data-driven (ACH worksheet → batch 1 verifications → test 6 Pearson → grep), so per `LESSONS.md` §4.1 the cave-velocity gate (reversal without first-principles re-derivation) has not formally fired. But four reversals in one session is a non-trivial signal regardless. Is the cumulative pattern cave-velocity-by-other-means?

5. **Is there a §4 anti-pattern from `LESSONS.md` I'm walking into by proposing P5?** Specifically — am I about to overscope ("audit the whole methodology") in response to a single discovered gap? Or am I correctly recognizing that one false claim in the methodology document statistically suggests others?

6. **Single-attack equivalent of round 1's "run the contamination math":** what is the un-dodgeable test for P5? I don't yet have a candidate. The contamination math worked because it was a single number that resolved a binary question. The methodology-vs-code gap is structural — there may not be a single-number test. Propose one.

---

## Attached supporting files

The reviewer should request any of these by name if needed for citation:

1. `docs/external-review/decisions/2026-05-09-rpe-pivot-ach.md` — Layer 1 ACH worksheet (the H1 → H6 reversal)
2. `docs/external-review/decisions/2026-05-09-rpe-pivot-layer2.md` — Layer 2 round 1 reviewer output
3. `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-pearson.py` — the Pearson script
4. `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-results.md` — full test 6 results (including the grep finding)
5. `docs/external-review/phase-0.7a-result.md` — original adjudication memo whose "RPE-via-frustration" framing is now disputed
6. `docs/external-review/2026-05-09-redteam-rpe-pivot-response.md` — the original red team memo whose collinearity claim is now empirically falsified
7. `nova-agent/src/nova_agent/affect/state.py` — the file with all anxiety-write sites; lines 37, 49-53 are the load-bearing excerpt

---

## What round 2 should NOT do

- Validate P5 because the author proposes it.
- Defer the methodology-audit question to "future work."
- Treat the four-reversals signal as resolved because each reversal had data backing it. The cumulative pattern needs explicit acknowledgment.
- Assume the round-1 surviving findings (§3.3, §3.4, §3.5) are absorbed into P5 — re-engage them under the new ground truth (the gap discovery makes §3.4 stronger, not weaker).

If round 2 produces ≥2 high-severity findings against P5 specifically, Layer 3 (multi-model cross-rebuttal, $4–$8) fires. Otherwise lock P5, draft the rewrite ADR with the 6-clause scope, and proceed.
