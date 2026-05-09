# Layer 2 Round 2 Review — RPE Pivot Decision (Methodology-vs-Code Gap)

**Date:** 2026-05-09
**Reviewer:** External Claude (Claude.ai project, offline-redteam-prompt loaded)
**Subject:** P5 position — methodology document claims a frustration→anxiety driver the code does not implement. Rewrite ADR scope shifts to "add the linkage + audit other code-vs-spec gaps."
**Brief:** `docs/external-review/decisions/2026-05-09-rpe-pivot-layer2-round2-brief.md`
**Verdict:** P5 must be HELD, not LOCKED. §4.1 cave-velocity hard line fires. Two prerequisites before Layer 3 can fire: (1) desk demonstration on existing 658-event data; (2) first-principles re-derivation from cold context.

---

## Findings — verbatim from reviewer

### [critical] The methodology-vs-code gap is partially fatal to the C1-confirmed framing, not fully — distinguish what R1 still tells you from what it doesn't.

- **Where:** Adjudication memo's claim "the non-empty_cells drivers the formula already names are currently silent" (per prompt §2 description) versus reported grep result on `nova-agent/src/nova_agent/affect/state.py` showing all anxiety-write sites are decay, empty_cells (gated), trauma_intensity, terminal-override.
- **Why it matters:** Two distinct claims are tangled. (1) "RPE-via-frustration is silent" — falsified; the driver doesn't exist, can't be silent. (2) "Architecture-as-coded fails to produce predictive lead-time without empty_cells" — still true; trauma_intensity stayed at 0.0 across 658 obs and decay alone doesn't drive anxiety to threshold. R1 fired because the code-as-shipped has only one functional anxiety driver and the ablation removed it. That is a real empirical finding. What R1 cannot tell you is whether the architecture-as-described in methodology.md (with frustration→anxiety wired) would have produced t_predicts != None.
- **Pattern from §4:** §4.10 — adjudication memo's "currently silent" wording is the loose-phrasing pattern. The right wording is "not wired." The author cannot fix this by amending the memo's tone; the author must amend the verdict's scope.
- **What kills:** Nothing structural — this is the verdict's actual shape. Memo must be amended to two separate sub-verdicts: (a) C1-as-implemented confirmed; (b) C1-as-specified untested.
- **What to do:** Issue erratum to phase-0.7a-result.md today. Erratum names exactly which non-empty_cells drivers are implemented (decay, trauma_intensity, terminal-override) and which were claimed but not implemented (frustration→anxiety). Rewrite ADR's preamble cites the erratum, not the original memo. Do not retro-rationalize the original framing as "I meant currently-silent-because-not-wired" — §4.2.

### [critical] P5 understates rewrite scope. Wiring the linkage is necessary but not sufficient — the magnitude data shows it.

- **Where:** Test 6 result — frustration max value 0.052; threshold ~0.6. ~12× gap. Even if frustration→anxiety wiring is added with coefficient 1.0, frustration cannot drive anxiety past threshold under the observed distribution.
- **Why it matters:** P5 frames the rewrite as "add the linkage." Real rewrite is "add the linkage AND fix the magnitude AND verify the combined signal crosses threshold under realistic play." Each is a separate decision. Naming only the first is §4.9 framing pattern.
- **Pattern from §4:** §4.9 (pragmatic-with-bounded-debt framing honesty). Forward-looking §4.5 risk: if the rewrite multiplies frustration by 12 to hit threshold, frustration's contribution to anxiety becomes saturated whenever frustration fires at all, and `_enforce_aversive_cap` collapses the signal again — same cap-collapse pattern, new axis.
- **What kills:** Demonstrate, on existing 658-event data, that ANY linear or nonlinear function of {frustration, decay, trauma_intensity} crosses the 0.6 threshold ≥ 4 times in 5 trials on at least one scenario. If yes, P5's wiring claim is closer to sufficient. If no, P5 is missing the magnitude axis.
- **What to do:** Before locking the rewrite ADR scope, run that demonstration as a desk exercise on existing CSV — no new run needed. Report maximum value of f(frustration, decay, trauma_intensity) for any candidate f defendable ahead of time. If max < 0.6, P5 must explicitly include "magnitude calibration" as a second-half scope item.

### [high] The methodology audit is justified, but must be timeboxed with binary pass/fail criteria, or it becomes §4.4 procrastination dressed as discipline.

- **Where:** P5's framing: "the methodology document needs an audit for other code-vs-spec gaps." LESSONS.md "Always define what failure looks like before running the test" entry.
- **Why it matters:** "Audit the methodology" is the kind of phrase that grows. Without a timebox, the audit blocks the rewrite ADR indefinitely; with a timebox + clear gates, it's the cheap §4.4-disciplined test the author is owed before authoring.
- **Pattern from §4:** §4.4 risk (not yet realized).
- **What kills:** Pre-committed audit spec, max 4 hours wall, with three binary outputs: (1) list of methodology.md mechanism claims; (2) for each, present-or-absent in code; (3) for each absent, severity {load-bearing for predictive-lead-time / load-bearing for product surfaces / cosmetic}. Rewrite ADR scope is fixed by the load-bearing-for-predictive-lead-time row only. Cosmetic gaps documented + deferred.
- **What to do:** Write audit spec before opening any methodology.md file. Spec is the timebox. Do not let the audit grow fix-as-you-go: audit finds gaps; rewrite ADR fixes the load-bearing ones; cosmetic gaps go in a backlog, not the ADR.

### [high] P5 is reversal #2 in the thread; §4.1 says hold, don't adopt.

- **Where:** Round 1 reversal H1 → H6. Round 2 reversal H6 → P5. Two reversals.
- **Why it matters:** §4.1 explicitly: "After the second reversal, the next position should be held — not adopted — until the author has actively re-derived it from first principles, not just accepted the latest critique." At that hard line. P5 was adopted in response to test 6's findings. Discipline is to hold P5 pending an independent first-principles derivation that does not consult Round 1, the ACH worksheet, or test 6.
- **Pattern from §4:** §4.1 verbatim.
- **What kills:** First-principles derivation. Pause thread for 24h. Without referring to Round 1 or H6, write down: (a) what does the code do; (b) what does methodology.md claim; (c) what is the smallest change that closes (a) → (b); (d) what is the next falsification gate. If the answer matches P5 within a small delta, P5 holds. If not, the discrepancy is the finding.
- **What to do:** Pause. Do the derivation. Do not lock P5 until it survives the independent re-derivation. Do not fire Layer 3 until P5 has been held, not just adopted.

### [high] Concrete predictions for Q3 (other code-fictional claims to test in the audit). The list is finite; pre-commit to it before opening methodology.md.

- **Where:** Cross-referencing prompt §3.2/§3.4, ADR list, LESSONS.md "Three-channel memory decay" entry, "Variance reduction is the on-thesis test for trauma-tagging" entry, "State-Transition Signatures > 1:1" entry.
- **Why it matters:** Audit value depends on hitting the right candidates. Drift-into-everything is §4.4. A pre-committed list of N high-priority claims is §4.4-disciplined.
- **Pattern from §4:** §4.7 generalized — independence-and-existence checks before architectural rewrite — applied to every methodology claim.
- **What kills:** N/A — checklist, not hypothesis.
- **What to do:** Run the audit against this priority list, in this order:

  1. **`trauma_intensity` wiring** — given 0.0 across 658 obs, is the trauma-tagging mechanism actually firing? Does cosine-weighted aversive recall in ADR-0012 actually retrieve and emit non-zero values? Highest-priority because Phase 0.8 dies otherwise.
  2. **ADR-0002 Signatures Beta, Gamma, Delta** — only Alpha has defined operationalization. Are Beta/Gamma/Delta in code at all, or spec-only?
  3. **Three-channel memory decay** (episodic ~24h / semantic ~7d / affective ~30d per LESSONS.md) — three separate decay rates in code, or one rate with three labels?
  4. **Reflection → semantic memory consumption** — does `reflect()` write lessons that any future decision actually reads, or are they written-to-disk-and-forgotten?
  5. **Russell mood radar valence × arousal** — consumed by any decision logic, or display-only on Brain Panel?
  6. **ToT-branch-disagreement as uncertainty signal** (named in spec §7 R1 candidate (c)) — any wiring at all, or paper-only?

  Each takes ~10 min to verify. Total audit fits in 4h timebox if scoped to this list.

### [medium] Process learning: the "5-second code read" should have happened during the adjudication memo authoring, not in Round 2.

- **Where:** phase-0.7a-result.md was written before grep was run. Memo's "RPE-via-frustration" framing inherited from methodology.md without code-grounding.
- **Why it matters:** Layer 1 ACH worksheet also did not do the code read. Both adjudication memo + worksheet treated methodology.md as source of truth for what the architecture actually does. Failure mode that produced this round. Fix is a process change, not one-off.
- **Pattern from §4:** Generalization of §4.10 — "loose phrasing as a defense vector" extends to "loose document grounding as a structural input to the next decision."
- **What kills:** Adopt rule: every external-review-quality document that names a mechanism cites the file and line range where the mechanism is implemented, OR explicitly states "spec-only, not implemented." One bullet in CLAUDE.md or the review skill. Cost: trivial. Benefit: this round was free because grep was free; next time gap is in a more expensive layer, cost is not free.
- **What to do:** Add to LESSONS.md as workflow learning: "Before citing a methodology.md mechanism in an external-review document, grep the code for the mechanism's implementation. If absent, name it 'spec-only.' Catch the gap in document authoring, not in Round 2 of an adversarial review."

---

## Verdict on each Q

- **Q1 — is the gap fatal to C1-confirmed?** Partially. R1 still fires on the architecture-as-coded — that empirical content is preserved. Adjudication memo's framing ("non-empty_cells drivers are silent") is wrong-as-written and must be amended to distinguish not-implemented from implemented-but-silent. Strong form of "C1 confirmed" is dead; narrow form ("the architecture as currently shipped does not produce predictive lead-time without empty_cells") survives.
- **Q2 — rewrite ADR vs separate audit phase?** Audit first, timeboxed (≤4h, binary outputs), then rewrite ADR scoped only to load-bearing-for-predictive-lead-time gaps. Do not run them in parallel — running in parallel is the H6 framing escalation pattern repeating one level up. **Sequence: erratum → audit → rewrite ADR.**
- **Q3 — what other claims might be fictional?** Six concrete candidates in Finding 5, ranked by priority. trauma_intensity highest because Phase 0.8 depends on it.
- **Q4 — am I overscoping?** Not by introducing the audit; the audit is the §4.4-disciplined cheap test, not a §4.4 violation. Overscope risk is real but downstream — lives in (a) un-timeboxed audit drift, (b) the rewrite ADR trying to fix every gap rather than the load-bearing ones, (c) treating the audit as new infrastructure rather than a one-time check. All three pre-emptable by spec'ing the audit before opening it. **Bigger risk is §4.1, not §4.4: P5 is reversal #2 and you are about to adopt rather than hold.**

---

## Top 3 attacks (sharper than round 1)

1. **[critical]** P5 understates rewrite scope: max frustration 0.052 vs threshold 0.6 = 12× gap. Wiring alone is insufficient; magnitude is a co-equal axis. Forces P5 re-spec.
2. **[critical]** C1-confirmed verdict needs amendment, not preservation. Erratum on phase-0.7a-result.md separating "as-coded" from "as-specified" sub-verdicts. Forces a doc change before the rewrite ADR can credibly cite it.
3. **[high]** P5 is reversal #2. §4.1 says hold-not-adopt. First-principles re-derivation required before locking. Procedural; blocks Layer 3 firing until satisfied.

## The single attack you should not be allowed to dodge

Run the desk demonstration in Finding 2 today. On existing 658-event CSV, compute the maximum value, across all events, of every reasonable function f(frustration, decay, trauma_intensity) you would defend in the rewrite ADR. If max < 0.6 for every f, the rewrite is not "add the linkage" — it is "add the linkage AND restructure how the inputs scale." That changes the rewrite ADR's scope, falsifiability, and cost.

Tempted to defer this on grounds that "magnitude is a tuning question, not a structural question." That deferral is the §4.10 pattern: rephrasing the load-bearing question to make it sound smaller. **Magnitude IS structural when the data shows the input distribution cannot reach the threshold under any defensible coefficient choice.**

If max ≥ 0.6 for some f, P5 is closer to right than this round credits and you can lock the wiring-only scope. If max < 0.6, the rewrite ADR has two scope items, not one, and the audit's purpose shifts from "find other gaps" to "find other gaps AND verify the magnitude problem isn't recurring on other axes."

## Anti-patterns from §4 observed in round 2

- **§4.1 (cave-velocity).** Reversal #2 in the thread (H1 → H6 → P5). Hold P5; do not adopt without first-principles re-derivation. **§4.1 hard line.**
- **§4.9 (pragmatic-with-bounded-debt framing honesty).** P5 names the wiring fix without naming the magnitude problem the same data exposed. Honest P5 framing: "P5 = wiring + magnitude + audit, with the audit timeboxed." Not "rewrite ADR scope is to add the linkage."
- **§4.10 (loose statistical phrasing).** Adjudication memo's "currently silent" is round 1 instance; not yet repeated in round 2's framing of P5, but at risk if magnitude problem gets reframed as "tuning."
- **§4.4 risk (not yet violated).** "Audit the methodology" is one un-timeboxed phrase away from being a §4.4 violation. Pre-empt by writing the audit spec before opening any file.
- **§4.2 risk (not yet violated).** When you amend the adjudication memo (Finding 1), do not reframe the original "currently silent" wording as "I meant currently-silent-because-not-wired." That would be retro-rationalization. Concede the original wording was wrong, write the erratum cleanly, move on.

Reviewer explicitly: "I do not push you to H6 or to H1. The findings refine P5 and force a hold-not-adopt before Layer 3. If you read this round as 'P5 holds, fire Layer 3 now,' re-read Finding 2 and Finding 4. Layer 3 fires only after the desk demonstration in the single-attack-not-to-dodge runs and after the first-principles re-derivation in Finding 4 is on paper."

---

## Author response (in progress)

Per user's pick:
- §4.1 hold gate honored via cold subagent re-derivation (methodologically equivalent to fresh-eye 24h pause)
- Order: desk demo → erratum → audit spec → hold gate

Tracked as tasks 8, 9, 11, 10.
