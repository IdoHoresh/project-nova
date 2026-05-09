# Layer 2 Review — RPE Pivot Decision

**Date:** 2026-05-09
**Reviewer:** External Claude (Claude.ai project, offline-redteam-prompt loaded)
**Subject:** Phase 0.7a RPE-pivot decision; pre-Layer-2 author leaning was H6
(HYBRID PRECONDITION) per `docs/external-review/decisions/2026-05-09-rpe-pivot-ach.md`
**Verdict:** Trigger fires for Layer 3 (≥2 high/critical findings against H6),
but the single highest-leverage move is a $0 verification that may make Layer 3
unnecessary. Per `LESSONS.md` §4.4, the cheaper investigation precedes the more
expensive review.

---

## Reviewer's verification notes (preceding findings)

The reviewer flagged two artifact-integrity issues before opening findings:

1. **README staleness.** `README.md` on `main` says "Currently in design phase.
   No runnable code yet." This contradicts everything the prompt + worksheet
   describe (Phase 0.7a complete, 658 per-move events, 12 ADRs, PR #32 merged,
   working emulator demo). Side fix queued.
2. **`LESSONS.md` heading drift.** The §4 anti-pattern headings cited in the
   offline-redteam-prompt do not appear verbatim in the public `LESSONS.md` —
   they are paraphrases / newer entries not yet pushed. The conceptual content
   aligns with several real entries (2026-05-06 "Carla anxiety firing at move
   0–1," 2026-05-05 "Verify red-team cost-leakage claims numerically"), but the
   citation chain has a gap. Side fix queued.

A clarifying question was also asked at the top of the response (Q1): was the
morning-pilot CSV collected at the same commit as Phase 0.7a, and is
`rpe.py:14-18` the only code path touching frustration in either run? The
answer is dispositive for several findings.

---

## Findings — verbatim from reviewer

### §3.1 — Option A vs H6 (and the H1 → H6 reversal)

**[critical] H6 is reframe-after-cave dressed up as ACH discipline; it is the
original Option C relabeled, with zero new evidence between rounds.**

- **Where:** Compare red-team memo's Option C ("Halt + fix `rpe.py:14-18` axis
  bias + re-launch... already rejected because it would test a different
  architecture than the morning pilot") with ACH worksheet §6 (H6 = "Option A
  done right rather than Option A as proposed under deadline pressure"). The
  fix is the same fix. The justification flipped from "rejected" to "leaning"
  with no intervening data.
- **Why it matters:** The worksheet §6 *literally uses the §4.3 escalation
  phrase form* — "Option A done right" — and §7 admits this is the first
  reversal in the thread. The escalation is the finding, not the reversal
  count.
- **Pattern from §4:** §4.3 (framing escalation between rounds without new
  evidence). Also §4.4 (option-space scope-escalation: A/B/C became A/B/C/D/E/F
  precisely when none of A/B/C felt satisfying).
- **What kills the finding:** A `git log --follow nova-agent/src/nova_agent/affect/rpe.py`
  showing the buggy lines were committed *between* the morning-pilot CSV and
  the Phase 0.7a run, AND a numerical demonstration that the bias direction
  differentially affects the Pearson estimate. Without both, H6 is
  reframe-after-cave.
- **What the author should do:** Either (a) keep Option A and explicitly
  enumerate its bounded debts per §4.9 (do not call it "the disciplined
  choice"), or (b) revert C's rejection and adopt C with the same honest
  framing it was originally rejected under ("tests a different architecture,
  accept that as the cost") — but stop calling C "A done right." That phrase
  is the tell.

**[critical] The contamination claim that justifies H6 is asserted, not
verified, and is mathematically loose where it needs to be precise.**

- **Where:** ACH worksheet §4 hidden assumption 2 says the morning-pilot CSV
  "was collected with the SAME `rpe.py`" — but treats this as a RISK to be
  flagged, not a fact to be checked. The §1 description of `rpe.py:14-18` is
  "axis bias (counts horizontal merges only)" — which is a *direction* of
  bias, not a magnitude.
- **Why it matters:** H6's entire payoff hinges on the Pearson result on
  existing data being unsafe to use. But "axis bias counts horizontal merges
  only" doesn't tell us whether fixing it (a) increases frustration variance,
  (b) shifts mean, (c) increases or decreases correlation with `1/empty_cells`,
  or (d) leaves the gating threshold unchanged. If fixing it leaves `r` in the
  same actionable band, H6 was an expensive rephrase.
- **Pattern from §4:** §4.10 (loose statistical phrasing as a defense vector).
- **What kills the finding:** A back-of-envelope on a 2048 board: when the
  board is locked along the dominant axis of play, what fraction of would-be
  merges are horizontal vs vertical? If the answer is ~50/50, the bias is a
  ~2× scale factor and the *correlation* with `1/empty_cells` is approximately
  preserved — meaning the Pearson gating threshold barely moves and H6 buys
  nothing. If the answer is heavily asymmetric, the bias is direction-
  distorting and H6 is justified. **Run the numbers.**
- **What the author should do:** Before locking H6, compute on the existing
  morning-pilot CSV: (1) `r_buggy = Pearson(frustration_buggy, 1/empty_cells)`;
  (2) reconstruct what `frustration_fixed` would have been from raw move data
  and compute `r_fixed`; (3) report `|r_buggy - r_fixed|`. If < 0.1, H6's
  marginal value is ~zero and Option A holds. If ≥ 0.1, H6 has actual content.

**[high] H6's Pearson-protocol-post-fix is unspecified — H6 is a placeholder,
not a decision.**

- **Where:** ACH worksheet §6 says "running them in parallel adds ~2h to the
  rewrite-ADR timeline" but does not say whether Pearson runs on (i) the
  existing morning-pilot CSV (which by H6's own logic is contaminated),
  (ii) a re-collected morning-pilot CSV under fixed `rpe.py` (which would
  re-incur the methodology debt of running new data, contradicting the
  "$0 Pearson is free" justification), or (iii) reconstructed-frustration-from-
  raw-events (which depends on raw events being preserved at sufficient
  granularity).
- **Pattern from §4:** §4.10.
- **What the author should do:** Write the H6 sub-spec answering exactly which
  CSV feeds Pearson, and the cost of producing it.

**[high] Pre-registration is being applied asymmetrically, in the direction
the author already wanted to go.**

- **Where:** H2 rejection (red-team memo §3) says halting mid-run because
  external argument lands = goalpost shift. But H6 *introduces a new
  precondition* (rpe.py fix + Pearson) post-run that was not in spec §7 R1's
  four-clause sequence. ACH worksheet §4 hidden assumption 5 explicitly states
  the original H1 plan deferred the fix to post-rewrite-ADR; H6 reverses that
  without the rigor it imposes on H2.
- **Pattern from §4:** §4.8 + §4.6.
- **What kills:** Quote spec §7 R1 verbatim. If the four-clause sequence does
  not name `rpe.py:14-18` as a precondition, concede H6 introduces a new
  precondition mid-flight — and either re-open H2 question, or reject H6 on
  the same pre-registration grounds H2 was rejected.

**[high] §4.5 cap/max-collapse — the `rpe.py` fix may be cosmetic at the
observable.**

- **Where:** Prompt §4.5 cites `_enforce_aversive_cap` + `max(...)` selection
  in `main.py:274` as the collapse point. If frustration feeds through that
  collapse before reaching anxiety, fixing the upstream calculation changes the
  input set N but not the collapse-surviving value the rewrite ADR cares about.
- **What kills:** Trace whether the morning-pilot CSV's frustration column is
  the pre-cap value or post-cap. If pre-cap, the finding partially dissolves.
  If post-cap, the finding is structural and H6 is dead.

**[medium] "First reversal in the thread" undercounts.**

- **Where:** ACH worksheet §7. The original red-team memo recommended Option
  A; the author internally adopted A; the worksheet then reversed to H6.
  That's one reversal *during* the worksheet. Borderline.
- **Pattern from §4:** §4.1.
- **What the author should do:** If any finding here causes reversal away from
  H6, pause before adopting the new position. Do not let me push you to H1.

### §3.2 — Architecture-rewrite candidate axes

**[high] Candidate (b) is theatre being demoted, not a candidate axis.**
Aversive recall produced 0.0 across 658 obs; root-cause why before listing as
candidate. Demote to "deferred until silent-mechanism investigation closes."

**[high] Candidate (c)'s ToT-branch-disagreement subcandidate is circular.**
ToT only fires when anxiety > 0.6; using ToT-disagreement to drive anxiety
bootstraps a cycle. Either drop or write the bootstrapping spec.

**[high] §4.7 Pearson independence test must apply to (b) and (c), not just
(a).** Add pre-commit to rewrite ADR: every candidate axis must pass
`Pearson(candidate, 1/empty_cells) < 0.5` on morning-pilot CSV before
adoption, OR be adopted as hybrid with explicit residualisation.

**[medium] Hybrid-driver auditability.** Pre-register hybrid coefficients
before computing on data, OR commit to single-axis with binary outcome.

### §3.3 — "C1 confirmed" verdict

**[critical] "C1 confirmed" is comparing two mechanical regimes and concluding
the mechanism is the mechanism. Tautological, not falsifying.**

- **Where:** LESSONS.md verbatim entry "Carla anxiety firing at move 0–1 is
  'fast reaction,' not 'predictive lead-time'" (2026-05-06). Morning-pilot
  baseline showed `t_predicts ∈ {0, 1}` on corner + 512-wall.
- **Why it matters:** If baseline signal is mechanical (initial-empty-cells
  thresholding at move 0), and counterfactual nulls empty_cells, the ablation
  shows that nulling the mechanical signal removes the mechanical signal. It
  does NOT show that a non-mechanical signal *exists or could exist*.
- **What kills:** Re-run Phase 0.7a on scenarios that pass §7.4 calibration
  (Bot game-over within `expected_cliff_window` for ≥3/5 trials). Until then,
  C1 confirmed = comparing two non-calibrated runs.

**[high] Bot arm zero data is being spec'd retroactively as "no-op."**
Run `git blame` on the spec line declaring bot a no-op. If post-hoc,
spec change is rationalization and C1 verdict has zero control-arm data.

**[high] The flag may be doing more than nulling one term.**
Produce diff of `null_empty_cells_anxiety_term` code path before locking
rewrite ADR.

### §3.4 — Methodology survival narrative

**[critical] Brain Panel + State-Transition Signatures survival narrative is
non-responsive to the actual broken claim.** Load-bearing claim = predictive
lead-time. Phase 0.7a result = 0/15. "Brain Panel still looks pretty" is true
and irrelevant. Stop framing methodology as "surviving R1." Honest framing:
"predictive lead-time claim is provisionally falsified pending rewrite +
re-run; product surfaces unaffected but not the load-bearing claim."

**[high] Signature Alpha gates on the same anxiety threshold the formula
failed to cross.** ADR-0002 doesn't survive R1 independently — contingent on
the same anxiety driver the rewrite is about to replace. State the contingency.

**[high] Phase 0.8 trauma ablation is dead on current evidence.**
Levene's W on a constant signal is degenerate (variance = 0 in both arms).
Phase 0.8 cannot run until trauma_intensity fires non-trivially in normal
operation. Add to rewrite ADR a clause that trauma silence is in scope.

### §3.5 — The decision to NOT do Option D (kill)

**[high] H4 dismissal conflates "the falsification gate worked" with "the
project survives."** Two distinct claims fused. Methodology of falsification
worked (R1 fired as designed). Cognitive-architecture hypothesis the
falsification was supposed to test failed (predictive lead-time = 0/15). The
project IS the hypothesis, not the framework.

- **What kills:** Pre-committed numeric N: "if N more rewrites or N more
  games produce R1, kill the project." Without that, project is asymptotically
  unfalsifiable. Suggested concrete: "if rewrite ADR ships and Phase 0.7a
  re-run produces R1 on calibrated scenarios, OR if 2 of 3 single-game
  ablations under H5 produce R1, project is killed."

**[medium] H5 (multi-game pivot) was named then dismissed without engaging the
underlying claim.** H5's claim is "2048's geometry is the constraint, not the
architecture" — independent of the Pearson result. Cheapest test: 1-trial
Snake smoke with current architecture. Do that before authoring rewrite ADR.

---

## Reviewer's verdict per §3 decision

- **§3.1 — does H6 survive?** **No.** Reframe-after-cave + 3 unverified
  claims. Honest position: neither H1 nor H6 as currently specified. Lock
  Option A with explicitly enumerated bounded debt per §4.9, OR engage H4
  honestly with pre-committed N.
- **§3.2 — do candidate axes survive?** **Partially.** (b) silent → demote;
  (c) ToT subcandidate circular → drop or specify; §4.7 Pearson must apply
  universally.
- **§3.3 — does "C1 confirmed" survive?** **No, not in strong form.**
  Downgrade from "fully confirmed" to "confirmed against an uncalibrated
  comparator."
- **§3.4 — does methodology survive?** **Product surfaces yes; load-bearing
  predictive-lead-time claim no.** ADR-0002 contingent on failing driver;
  Phase 0.8 dead on a constant.
- **§3.5 — should the project stop?** **Not yet, but the no-true-Scotsman
  line is closer than the worksheet admits.** Pre-commit N.

---

## Reviewer's top 5 attacks, ranked

1. **[critical]** H6 = Option C relabeled. §4.3 framing escalation. Reverses
   §3.1.
2. **[critical]** "C1 confirmed" compares two mechanical regimes; comparator
   failed §7.4 calibration. Forces re-running C1 on calibrated scenarios
   before rewrite ADR. Reverses §3.3 strong form.
3. **[critical]** Contamination claim asserted not measured. Bias-direction
   math not run. Empties H6 of content. Reverses §3.1.
4. **[critical]** Brain Panel + STS "survival" non-responsive to broken
   predictive-lead-time claim. ADR-0002 Signature Alpha contingent on failing
   anxiety driver. Phase 0.8 dead on a constant signal. Forces methodology-
   survival rewrite. Reverses §3.4.
5. **[high]** §4.5 cap/max-collapse — fixing `rpe.py` upstream of
   `_enforce_aversive_cap` may be cosmetic at the observable. If true, kills
   H6 structurally. Reverses §3.1.

## The single attack you should not be allowed to dodge

**Run the contamination math before locking H6.** Compute `r_buggy` on
morning-pilot CSV; reconstruct `frustration_fixed`; compute `r_fixed`; report
`|r_buggy − r_fixed|`. If < 0.1, H6 is reframe-after-cave with no measurable
content → lock Option A with named bounded debt. If ≥ 0.1, H6 has actual
stakes and is defensible — but only then.

If `frustration_fixed` cannot be reconstructed from existing raw events, that
is a finding, not a reason to skip the test: it means the rewrite ADR's Pearson
gate is computed against data the author cannot validate, and the entire
"Pearson is free" justification collapses.

## Anti-patterns from §4 observed

- **§4.3 framing escalation.** ACH §6 calls H6 "Option A done right" — verbatim
  the framing-escalation pattern. Original Option C was "rejected"; relabeling
  occurred without intervening data.
- **§4.4 pre-emptive scope-escalation.** Option space inflated A/B/C → A/B/C/
  D/E/F precisely when none of A/B/C felt satisfying. Honest move: contamination-
  math test, not introducing H6.
- **§4.6 convenience-bias.** H6 preserves Pearson optionality AND ships the
  rpe.py fix author wanted to ship anyway. Both convenient. Mirror test: if
  morning-pilot CSV had no rpe.py problem, would author still recommend H6?
  Almost certainly not.
- **§4.9 pragmatic-with-bounded-debt framing honesty.** ACH §6 frames H6 with
  no enumeration of bounded debts. Honest framing: "pragmatic-with-bounded-debt
  {1, 2, 3, 4}" — not "Option A done right."
- **§4.10 loose statistical phrasing.** "Contamination" asserted without
  magnitude or direction.
- **§4.1 cave-velocity.** First reversal H1 → H6 fired. Warning, not hard-stop.
  If next move is H6 → anything-else without re-deriving from first principles,
  that IS the §4.1 hard-stop.

Reviewer explicitly notes: "I am not pushing you to H1. The findings reject
H1 and H6 symmetrically. The two viable end-states are: (i) Option A locked
with enumerated bounded debt and a §4.7 pre-commit on candidate axes, or (ii)
honest engagement with H4 contingent on a pre-committed N for the next
falsification gate. If you read this review as 'go back to H1,' re-read it."

---

## Author response (pending)

Findings are substantive and the trigger condition for Layer 3 fires (5 high+
findings against H6). However, per `LESSONS.md` §4.4, the cheapest
verification precedes the more expensive review. The single attack the reviewer
named as un-dodgeable (the contamination math) is a $0 verification that
empties or fills H6 of content. Layer 3 is queued contingent on what the $0
verifications produce — see next file in this directory.
