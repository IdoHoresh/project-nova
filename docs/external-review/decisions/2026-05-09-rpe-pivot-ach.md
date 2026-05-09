# Decision Worksheet — RPE/Frustration Affect Rewrite Path

**Date:** 2026-05-09
**Branch:** `claude/phase-08-run` (PR #32 merged)
**Triggered by:** `docs/external-review/2026-05-09-redteam-rpe-pivot-response.md`
**Method:** Layer 1 (ACH) of the 3-layer adversarial review architecture
documented in `docs/external-review/2026-05-09-redteam-channel-research.md`.
**Author state at time of writing:** has documented motivated-reasoning
failure modes (`LESSONS.md` §4.1–§4.10); leaning Option A but has not
locked it.

---

## 1. Hypotheses (exhaustive, NOT just A/B/C from the red-team memo)

The red-team memo named A, B, C. ACH discipline requires enumerating
every plausible option, including the kill case and structural pivots
the author has framed out.

- **H1 — Option A.** Ratify Phase 0.7a R1 verdict. Run the
  `Pearson(frustration, 1/empty_cells)` test on the morning-pilot CSV
  as a hard precondition for the rewrite ADR. ADR axis choice is
  conditional on the Pearson result.
- **H2 — Option B.** Halt the run mid-flight. Run Pearson before the
  run finishes. Decide based on `r`.
- **H3 — Option C.** Halt the run, fix `rpe.py:14-18` axis bias
  (Synthesis M-16), re-launch Phase 0.7a with corrected RPE.
- **H4 — Option D (KILL).** Abandon Project Nova. Phase 0.7a R1 +
  trauma_intensity at 0.0 across 658 observations + ToT never firing
  = the architecture is structurally not doing what the methodology
  claims. Multiple rewrite attempts now look like the no-true-Scotsman
  fallacy.
- **H5 — Option E (DEFER + PIVOT GAME).** Pause Phase 0.7 entirely.
  Pull Phase 1 multi-game work (Snake, FlappyBird) forward to test
  whether the methodology's predictive lead-time claim survives
  outside 2048's geometric constraints. The red-team memo's load-
  bearing claim is "in 2048 specifically" — H5 attacks that frame
  directly.
- **H6 — Option F (HYBRID PRECONDITION).** Run Pearson AND the
  `rpe.py` axis-bias fix in parallel BEFORE writing the rewrite ADR.
  Both are cheap; both carry residual debt that gates rewrite quality.
  H6 is the "Option A + Option C side fix done early" union.

H4, H5, H6 were not on the red-team memo's option list. Including
them is the point of ACH — the option set proposed under stress is
typically incomplete.

---

## 2. Evidence matrix

| Data | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|
| Phase 0.7a: 0/15 t_predicts | + | + | + | ++ | + | + |
| trauma_intensity 0.0 across 658 obs | + | + | + | ++ | + | + |
| ToT never fires across run | + | + | + | ++ | + | + |
| frustration ~0.001 across run | + | + | + | + | + | + |
| Run cost ~$0.66 (well under $7 cap) | + | − | − | 0 | 0 | + |
| Pearson(frustration, 1/empty_cells) on morning CSV | ? | ? | ? | 0 | 0 | ? |
| `rpe.py:14-18` axis bias unfixed during run | − | − | + | + | 0 | + |
| Pre-registration discipline (LESSONS §4.8) | ++ | −− | −− | 0 | 0 | + |
| 2048-specific geometric constraint (red-team #6c) | 0 | 0 | 0 | + | ++ | 0 |
| Sunk cost: 12 ADRs, ~6 weeks shipped | + | + | + | −− | − | + |
| Author motivated-reasoning track record | −− | 0 | 0 | + | + | 0 |
| Convenience-bias risk: A is the easy lock | −− | 0 | 0 | 0 | 0 | − |

Legend: ++ strong support, + support, 0 neutral, − contradicts,
−− strong contradiction, ? unknown until measured.

**Aggregated read:** H1 has the highest count of ++/+ but also
carries two −− (motivated-reasoning track record + convenience-bias
risk). H6 has comparable + count without the −− entries but adds
parallel work. H4 has the strongest +/++ on the data but the strongest
−− on sunk cost — a classic motivated-reasoning anti-signal that
deserves the §4 audit.

---

## 3. Kill-question explicit answer (LESSONS §4.6 mandatory check)

If the author restarted on a different approach today, the $0
opportunity-cost base case is:

| Pivot target | Cost to restart | Verdict |
|---|---|---|
| Vision-based playtest QA (compete w/ nunu.ai) | High — wrong wedge per ADR-0004 | Not justified |
| RL coverage automation (compete w/ modl.ai) | High — explicitly rejected per ADR-0001 | Not justified |
| Multi-game cognitive simulator FIRST, defer 2048 | Low — same architecture, different surface | This is H5 |
| Drop the project, take a job | $0 — opportunity cost is real but separate from architecture verdict | Not the question being asked |

**Honest answer:** H4 (full kill) is not justified yet because the
falsification gate worked exactly as designed. Phase 0.7a producing
R1 is the architecture FAILING SAFE — it's the methodology working,
not the methodology dying. The R1 verdict + the rewrite ADR cycle is
what the spec said would happen if R1 fired. H4 collapses the
distinction between "the predictive lead-time claim was wrong" (true)
and "the methodology of falsification was wrong" (not true).

H5 has theoretical force but is premature without the Pearson result.
If `r > 0.8` on the morning-pilot CSV, the 2048-geometric-constraint
hypothesis gains evidence and H5 escalates from "premature" to "likely
correct." If `r < 0.5`, H5 weakens.

**Conclusion:** H4 stays on the worksheet but does not bind the
2026-05-09 decision. Re-evaluate H4 after the rewrite ADR + Phase 0.7a
re-run. If the second Phase 0.7a run also produces R1, H4 binds.

---

## 4. Hidden assumptions in the leaning position (H1)

The author is leaning H1. Pre-locking, name every hidden assumption
the leaning depends on.

1. **The Pearson result will land in an actionable band.** The decision
   tree assumes `r > 0.8` (reject RPE) OR `r < 0.5` (proceed with RPE)
   OR `0.5 ≤ r ≤ 0.8` (hybrid axis with residualisation). Hidden
   assumption: the morning-pilot CSV has enough samples to make the
   `r` estimate tight. **Risk:** if N=20 produces a wide CI on `r`, the
   actionable band collapses and the rewrite ADR has no quantitative
   gate.
2. **The morning-pilot CSV was collected with the SAME `rpe.py` that
   fed Phase 0.7a's 658 observations.** If yes, the Pearson computation
   has consistent input data. **Risk:** if the Pearson input itself was
   contaminated by the axis bias, the Pearson result inherits the bias
   and the rewrite ADR's gating threshold is computed against a wrong
   baseline.
3. **"Pre-registration applies in both directions" is a principled
   stance, not convenience-bias.** The author rejected H2 (halt) on
   pre-registration grounds. The pre-registration argument is *also*
   convenient because halting would have wasted ~$1.40 in flight.
   **Risk:** the author cannot self-audit whether the principle came
   first or the convenience came first. This is exactly the failure
   mode `LESSONS.md` §4.6 names.
4. **Phase 0.7a's per-move trajectory data is sufficient to bind the
   rewrite ADR's axis choice.** The 658-observation distribution is the
   evidence base for "trauma_intensity is silent" and "frustration is
   silent." **Risk:** 658 observations across 15 Carla trials × 3
   scenarios is N=15 at the trial level, not N=658 at the independent-
   sample level. The rewrite ADR's evidentiary claims need the right
   N.
5. **Side fixes (`rpe.py:14-18`, Pro/bot `parse_failure`) are
   genuinely deferrable.** The author's plan: land them post-rewrite
   ADR. **Risk:** the rewrite ADR's Pearson computation uses RPE data
   produced by the buggy `rpe.py`. Deferring the fix means the rewrite
   ADR is committed against contaminated data. H6 directly addresses
   this; H1 implicitly assumes the contamination doesn't matter.

**Net:** assumptions 2 and 5 are the same concern from different angles
and they map to the H6 option. If either holds, H6 dominates H1.

---

## 5. Layer 3 trigger condition (pre-committed)

Layer 2 (Claude.ai project review with the offline-redteam-prompt)
fires next. Trigger Layer 3 (multi-model cross-rebuttal) if EITHER of
these conditions is met:

- Layer 2 produces ≥ 2 findings rated `[high]` or `[critical]` against
  H1 specifically.
- Layer 2 surfaces a hypothesis NOT on this worksheet (i.e., H7+) that
  the author cannot immediately dismiss with citation.

If Layer 2 produces only `[medium]` / `[low]` findings against H1, lock
H1 and proceed to ADR drafting. Do NOT escalate to Layer 3 — that
would be Layer-3-as-comfort-blanket, not Layer-3-as-circuit-breaker.

**Hard stop:** if the author reverses direction more than once across
Layer 1 + Layer 2 (e.g., H1 → H6 → H1, or H1 → H4 → H1), pause before
Layer 3. Re-derive from first principles. Two reversals is the
`LESSONS.md` §4.1 cave-velocity signal, not an escalation signal.

---

## 6. Pre-Layer-2 leaning position (committed before Layer 2 fires)

**Leaning H6 (HYBRID PRECONDITION), not H1.**

Reasoning, in one paragraph: the ACH evidence matrix's −− entries on
H1 (motivated-reasoning track record + convenience-bias risk on the
"easy lock") are not present on H6. Hidden assumptions 2 and 5 in §4
both point at the contamination risk that H6 fixes for free. The
`rpe.py` axis-bias fix is 5 lines + tests + an ADR-amend bullet (per
the red-team memo §4 cost table); the Pearson test is ~30 min and $0;
running them in parallel adds ~2h to the rewrite-ADR timeline and
removes the contamination question entirely. The pre-registration
argument that defeats H2 (halt mid-run) does NOT defeat H6, because
H6 lands AFTER the run completed naturally. H6 is "Option A done
right" rather than "Option A as proposed under deadline pressure."

**This leaning is the input to Layer 2, not the conclusion.** Layer 2
should attack H6 the same way it would have attacked H1. If Layer 2
produces ≥ 2 high-severity findings against H6 OR identifies an
unforeseen hypothesis, escalate to Layer 3.

---

## 7. What this worksheet costs and what it bought

- **Time:** ~30 min author + ~30 min Claude (this artifact).
- **Money:** $0.
- **Caught:** option H4, H5, H6 (none in the original red-team memo);
  the contamination risk in H1's Pearson input; the convenience-bias
  anti-signal on "easy lock"; the pre-Layer-2 reversal from H1 to H6
  before any LLM-based critique landed.

The reversal from H1 to H6 is itself a `LESSONS.md` §4.1 signal — but
this is the FIRST reversal in the thread, so it does not yet trigger
the cave-velocity hard stop. If Layer 2 reverses back to H1 without
new evidence, that IS the signal.

---

## 8. Next action

Run Layer 2. The user pastes:

1. The defense paragraph from §6 above.
2. This entire worksheet.
3. The instruction: "Per the offline-redteam-prompt, attack my H6
   leaning. Do not validate it because I recommend it. Open with
   finding 1."

Into the Claude.ai project that has `2026-05-09-offline-redteam-prompt.md`
loaded as the project prompt.

Captures Layer 2 output as
`docs/external-review/decisions/2026-05-09-rpe-pivot-layer2.md`.

Then evaluate the Layer 3 trigger condition (§5).
