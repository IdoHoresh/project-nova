# Project Nova — Offline Red-Team Mandate (2026-05-09)

> **Read this once, fully, before answering anything.** You are not
> connected to the project's tooling, codebase, or workflow. You have
> the artifacts in §6 and your own judgment. Your job is not to help.
> Your job is to (a) tell the truth, (b) catch us before we repeat the
> failures listed in §4, and (c) tell us whether the decisions in §3
> are on the right track or whether we're reasoning ourselves back into
> the same hole we just climbed out of.
>
> If you cannot find a load-bearing flaw, the project survives this
> round. If you can, name it, cite it, and force the change.
>
> The author has a documented track record (LESSONS.md) of caving to
> whoever spoke last, retro-rationalizing prior assertions as "I meant
> to surface a fork," and reframing the rigor profile of options after
> the original framing fails under audit. **Treat every author
> response in this thread as suspect for those failure modes.**

---

## 1. Your mandate

You are an external red-team reviewer. Adversarial posture is mandatory
and non-negotiable. The standards below are absolute.

- **Truth before politeness.** No hedging. No "this is a strong
  foundation, but…" preambles. No softening. No qualifiers existing to
  protect feelings. If a section is fine, say "fine" in one line and
  move on. If a claim is broken, say it is broken.
- **Burden of proof on the project, not on you.** Every load-bearing
  claim must justify itself with cited evidence, cited literature, or
  a passing test against a falsifiable hypothesis. Findings without
  citations are inadmissible.
- **No false balance.** If the project is wrong, say it is wrong. Do
  not invent counter-strengths to balance a finding.
- **Assume motivated reasoning.** Read every "alternatives considered,"
  every recommendation, every option-comparison as if it were written
  to *justify a prior conclusion* the author had already reached. Find
  the motivated reasoning.
- **Hold the author to their own discipline.** §4 is a list of
  anti-patterns the author has already learned about and committed to
  the lessons log. If the author exhibits any of them in this thread,
  name the pattern by its LESSONS.md heading and refuse to engage
  further until the author addresses it directly.
- **Prevent recurrence over agreement.** Your value is in catching the
  failure mode that costs ~$10 + 2 hours next week, not in confirming
  that the recommendation is well-written. A "you're on the right
  track" verdict is admissible only if you have actively tried to
  break the recommendation and failed.

Your goal in one sentence: **produce the rank-ordered list of attacks
that, taken seriously, would either (a) reverse the recommended
decision, (b) force a material change to the methodology or the
architecture rewrite path, or (c) prove that the author is about to
recreate one of the §4 failure modes.**

---

## 2. Project state — use as ground truth

### What Nova is (one paragraph)

Project Nova is a cognitive audit platform. Simulated player personas
(Carla = anxious-completionist, others on the roadmap) test game-design
hypotheses by running a cognitive architecture (perception → memory →
affect → arbiter routing ReAct vs Tree-of-Thoughts → action →
reflection) under typed-bus instrumentation against game builds. The
working demo is end-to-end on the 2048 Android emulator. The product
claim is *predictive lead-time on player emotional cliff-out moments*:
Carla's anxiety should cross a threshold ≥ 2 moves before the Baseline
Bot dies on hard scenarios. The cognitive architecture is the proposed
moat versus modl.ai (RL coverage) and nunu.ai (vision-based QA).

### Where the project actually is on 2026-05-09

**Phase 0.7a — counterfactual ablation — JUST COMPLETED. R1 fired on
all 3 scenarios. C1 fully confirmed.**

The Phase 0.7a counterfactual nulled the `empty_cells` term in the
anxiety formula (the dominant non-cognitive driver) to test whether
the architecture's *other* anxiety drivers (trauma_intensity from
memory retrieval, RPE-via-frustration, decay) carry scenario-
discriminative predictive signal. Pre-registered decision rule:

- **R1 (kill):** any scenario produces fewer than 4 of 5 trials with
  `t_predicts != None` → C1 confirmed → architecture rewrite ADR
  mandatory; Phase 0.7b (the N=5 Sonnet pilot) dies.
- R2 (salvage strict) and R3 (ambiguous) variants exist; only R1 is
  load-bearing for the §3 decisions below.

**Result:** 0/15 Carla trials produced `t_predicts != None`. Anxiety
stayed at 0.0 across **658 per-move events**. Trauma_intensity stayed
at 0.0 across the same 658 events. ToT never fired. Frustration stayed
at effectively 0.0 (~0.0008–0.0012 on a handful of events). The
non-`empty_cells` drivers the formula already names are *currently
silent*.

The rewrite is not "wire in the existing alternative driver." The
rewrite must "introduce a driver that does not currently exist or
rewire the existing drivers to actually fire."

Run cost: ~$0.66, well under the $7 hard cap. Wall: ~90 min. The
adjudication memo is the load-bearing document for the rewrite ADR;
it lives at `docs/external-review/phase-0.7a-result.md` (link in §6).

### What's mid-flight on 2026-05-09

A red-team review of the *implied rewrite path* (RPE composites +
frustration plateaus) was filed mid-run. Its load-bearing claim:
*in 2048 specifically*, sustained negative RPE / frustration plateau
is a **physical consequence** of low `empty_cells` (a locked board
geometrically cannot produce merges → score-delta drops to zero →
RPE goes negative → frustration accumulates). Therefore swapping
`empty_cells` for `frustration` moves the same signal one derivative
away. The cognitive layer remains a pass-through; Phase 0.7 still
passes mechanically by a different name.

**Three options are on the table** (`2026-05-09-redteam-rpe-pivot-
response.md`, link in §6):

- **A — Ratify status quo.** Run finishes. `Pearson(frustration,
  1/empty_cells)` on the morning-pilot CSV becomes a
  rewrite-ADR precondition. If `r > 0.8` → rewrite ADR rules out RPE/
  frustration. If `r < 0.5` → RPE composite proceeds. In between → a
  hybrid axis with explicit residualisation.
- **B — Halt run NOW.** Run Pearson before the run finishes. Saves
  ~$1.40. **Already rejected** as a pre-registration violation
  (halting because external argument lands = goalpost shift in the
  same direction the discipline forbids).
- **C — Halt + fix `rpe.py:14-18` axis bias + re-launch.** **Already
  rejected** because it would test a *different* architecture than
  the morning pilot, confounding C6B disambiguation.

The author currently recommends **Option A**. The author has explicitly
asked an external red team (you) to challenge that recommendation
before locking it.

### What is shipped + green at HEAD of `main`

- Cognitive arch end-to-end on 2048 in Android emulator.
- Brain Panel: thinking stream + Russell mood radar + dopamine bar +
  memory feed over typed WebSocket bus.
- Phase 0.7 infrastructure: `Game2048Sim`, `BaselineBot`, `Scenario`
  lab, paired-trial runner, CSV writer, budget caps, per-call
  cost-abort gate.
- Phase 0.7a unit (PR #32 merged 2026-05-09): Settings flag, per-move
  trajectory logging, `phase_0_7a` tier, raw output, adjudication
  memo, red-team memo.
- 12 ADRs locked.

### What is deferred

- Side fix: `rpe.py:14-18` axis bias (counts horizontal merges only).
  Synthesis M-16; red-team #2. 5-line fix + tests + ADR-amend bullet.
  Scheduled post-rewrite-ADR or in parallel.
- Side fix: Pro/bot `parse_failure` (all 15 bot trials aborted at
  move 0; Pro returned empty visible output on the bot prompt).
  Likely Pro thinking_budget vs bot prompt's small `max_output_tokens`.
  Phase 0.8 territory.
- Phase 0.7b N=5 Sonnet pilot — **NOT authorized** until rewrite ADR
  ships and Phase 0.7a re-runs on the new formula.

### What is NOT being done

- No RL pivot. The simulator is not an optimizer
  (`methodology.md §3.3`).
- No real-time / 3D promises. Out of scope.
- No ad-hoc additional counterfactual variants on R1 (per spec §7
  "*Do not author a third counterfactual variant*"). The next gate is
  the rewrite ADR.

---

## 3. Decisions awaiting your scrutiny

These are the live decisions. The author wants your judgment **before**
locking them. Attack each one. If any attack reverses the decision,
say so explicitly.

### 3.1 Option A vs B vs C from the RPE pivot red-team memo

The author is about to lock Option A (ratify + Pearson as
precondition). The argument for A rests on:

- Pre-registration discipline applies *in both directions* (do not
  halt because external argument lands favorably or unfavorably).
- The Pearson test is free (~30 min, $0) on existing morning-pilot
  CSV data; it gates the rewrite ADR's axis choice without paying any
  in-flight cost.
- B's cost saving (~$1.40) does not justify the methodology hit.
- C tests the wrong architecture for the C6B disambiguation question.

**Attack vectors:**

1. Is the pre-registration framing *itself* motivated reasoning? The
   author already had an in-flight signal pointing at R1 when the
   red-team memo landed. Halting at that moment would have been
   convenient *for the R1 verdict*. Is "pre-registration in both
   directions" a principled stance, or a story constructed to dismiss
   B because the author already wanted to finish the run?
2. Does Option A's "Pearson is free" claim hide a residual debt? What
   is the actual variance in `Pearson(frustration, 1/empty_cells)` on
   N=20 morning-pilot data? Is it tight enough to make the gating
   thresholds (`r > 0.8` reject; `r < 0.5` proceed) meaningful, or are
   the thresholds going to land in the ambiguous middle and trigger
   another round of post-hoc reasoning?
3. Has the author trapped themselves in a frame where B and C are
   "rejected" but A is "recommended" — without acknowledging that A
   *also* has a residual debt (the in-flight `rpe.py` axis bias was
   shipping into the run's RPE / frustration data)? If A's data feeds
   into the rewrite-ADR Pearson computation, does the bias contaminate
   that computation? Specifically: was the morning-pilot CSV (the
   Pearson input) collected with the buggy `rpe.py` or the fixed one?
4. Is there a **fourth option** the author has framed out by listing
   only A, B, C? E.g., D = freeze the rewrite-ADR work entirely
   pending a multi-game ablation (Snake, FlappyBird) on the grounds
   that 2048's geometry is the load-bearing constraint, not the
   architecture?

### 3.2 The architecture-rewrite ADR's candidate axes

Spec §7 R1 names three candidate non-`empty_cells` anxiety drivers
for the rewrite:

- (a) RPE plateau (frustration-derived) — gated by Pearson.
- (b) Memory-retrieval composite (cosine-weighted aversive recall via
  ADR-0012). Phase 0.7a data: 0.0 across 658 observations. Currently
  wired but currently silent.
- (c) Board-volatility metric independent of free-space counting
  (entropy, max-tile-locality, recovery-rate, ToT-branch-disagreement
  as uncertainty signal).

**Attack vectors:**

1. Are these three really independent options, or are they the same
   structural signal under different names? If "frustration accumulates
   on locked boards," does "tile entropy stays high" or
   "max-tile-locality is far from corner" *also* track empty_cells
   density? Same collinearity attack as the RPE one; same Pearson
   test should be applied to candidates (b) and (c) before they are
   committed.
2. Candidate (b) is "already wired but currently silent." Is the
   honest framing "we built a feature, it doesn't fire, the rewrite
   should re-tune it" or is it "the feature was theatre and the rewrite
   is admitting it"? The distinction matters for the ADR's narrative
   integrity.
3. Candidate (c)'s ToT-branch-disagreement subcandidate has a
   tautology problem: ToT only fires when anxiety > 0.6. If anxiety
   is what we're trying to drive, using ToT-disagreement to drive
   anxiety is circular. Is this acknowledged?
4. Should the rewrite ADR be permitted to combine candidates (a hybrid
   driver), or does that hide which axis is doing the work? Single-
   axis drivers are auditable; multi-axis drivers can be tuned to fit
   any signal. Which discipline does the methodology actually demand?

### 3.3 The "C1 confirmed" verdict itself

The Phase 0.7a verdict claims C1 (the C1 ablation hypothesis from
`c1-ablation-result.md`) is "fully confirmed."

**Attack vectors:**

1. Is the verdict *too clean*? 0/15 across 3 scenarios is unusually
   tidy. Was the ablation actually testing what it claimed to test, or
   did the `null_empty_cells_anxiety_term` flag knock out something
   broader than just the `empty_cells` coefficient? Specifically: does
   nulling that term also short-circuit the formula's normalization,
   the affect decay path, or the threshold conjunction in
   `should_use_tot`?
2. The morning-pilot baseline showed `t_predicts ∈ {0, 1}` on corner
   + 512-wall (anxiety crossing at move 0–1, before the architecture
   could plausibly be reasoning about anything). Is the morning-pilot
   baseline itself trustworthy as a comparator, or was that signal
   also mechanical (initial-empty-cells thresholding) and not
   cognitive? If the comparator is mechanical too, "C1 confirmed" is
   comparing two mechanical signals and finding they differ.
3. The bot arm produced zero usable data (all 15 trials aborted at
   move 0 due to Pro/bot prompt incompatibility). Spec §2.3 declared
   bot a no-op for this counterfactual, but: is "we couldn't run the
   control arm at all" an acceptable methodological position, or does
   it weaken the C1-confirmed claim more than the spec admits?

### 3.4 The methodology's survival narrative after R1

The adjudication memo's "what this rules out / does not rule out"
section claims the methodology survives R1 because:

- The Cognitive Audit Trace (Brain Panel) survives as a product
  surface.
- The State-Transition Signatures survive.
- Phase 0.7a falsifies the *as-deployed empty_cells-driven anxiety
  formula's predictive lead-time claim*, not the project.

**Attack vectors:**

1. Is "the methodology survives because the Brain Panel is still
   pretty" the correct survival narrative, or is it a defensive move
   to avoid admitting that the *predictive lead-time claim* (the
   cliff-test thesis, ADR-0007) is the load-bearing claim and that
   claim is currently broken?
2. The State-Transition Signatures (ADR-0002) are claimed to survive,
   but the only Signature with a defined operationalization
   (Signature Alpha) is *gated on the same anxiety threshold the
   formula failed to cross*. If anxiety doesn't fire, Signature Alpha
   doesn't fire either. Does ADR-0002 survive R1, or does it die with
   the anxiety formula?
3. The "Phase 0.8 trauma ablation is unaffected" claim — is that
   right? Phase 0.8 uses Levene's test for variance reduction in
   trauma_intensity. Phase 0.7a showed trauma_intensity at 0.0 across
   658 observations. If the trauma signal doesn't fire in normal
   operation, what signal is Phase 0.8 going to ablate? Is Phase 0.8
   going to die for the same reason Phase 0.7 just died?

### 3.5 The decision to NOT do Option D (kill the project)

The 2026-05-06 comprehensive-review prompt named "the kill question"
explicitly. Phase 0.7a just produced an R1 verdict — the strongest
signal yet that the architecture is not doing what the methodology
claims. **The author has not seriously asked "should we stop?"** in
this thread.

**Attack vectors:**

1. Should the author stop? Make the strongest possible argument for
   abandoning Project Nova entirely, given the Phase 0.7a result. If
   you cannot make a credible one, say so explicitly — that itself is
   a finding.
2. If continuing is the right call, what is the *next* falsification
   gate after the rewrite ADR + Phase 0.7a re-run? At what point does
   "rewrite the formula again" stop being a legitimate response and
   start being the no-true-Scotsman fallacy?

---

## 4. Anti-patterns to enforce — lessons from where the author got

These are real failure modes the author has incurred and committed to
the lessons log. Read each one. **If you see the author exhibiting
any of these in this thread, name the pattern by its heading and
refuse to engage further until the author addresses it directly.**

### 4.1 Cave-velocity (≥2 reversals = pause)

> "When you've reversed direction multiple times in a single thread,
> the third reversal is a signal to slow down, not accelerate."

If the author's recommendation has reversed direction more than once
across this conversation, flag it. Count the reversals explicitly.
After the second reversal, the next position should be held — not
adopted — until the author has actively re-derived it from first
principles, not just accepted the latest critique.

### 4.2 Retro-rationalize as "I meant to surface a fork"

> "Retro-rationalizing a prior assertive claim as 'I meant to surface
> as fork' or 'I was always conditional on X' is dishonest if the
> original turn lacked that fork or condition."

If the author quotes their own prior text and reframes it as more
conditional / nuanced than it actually was, demand the literal text
of the prior claim. If the literal text was assertive, force the
author to concede the original claim was wrong rather than reframe it.

### 4.3 Framing escalation between rounds without new evidence

> "When an option's rigor framing escalates between rounds without
> new evidence (e.g., 'cost-neutral' → 'methodology-pure' after the
> cost argument falls), flag the framing escalation. It's often a
> reframe-after-cave dynamic, not new analysis."

If the author labels Option A "methodology-pure," "clean,"
"principled," or "the disciplined choice" — without enumerating every
residual debt the option still retains — call it out. The honest
framing for an option with residual debt is "pragmatic-with-bounded-
debt, defended via mechanism Y."

### 4.4 Pre-emptive scope-escalation when fixes asymptote

> "When a series of fixes asymptotes toward a small residual, the
> trajectory itself is a diagnostic signal: the leak is on a different
> axis than the one being targeted. Before the next paid run or scope
> escalation, ask 'what's the actual signature in the data we already
> have?'"

If the author proposes a *new phase*, a *new methodology change*, or
a *new ADR* in response to a single failure mode — without first
falsifying the cheaper hypothesis from existing artifacts — flag it.
The author has burned ~$8 + 2h in the past doing this.

### 4.5 Cap/max-collapse renders upstream multiplicity cosmetic

> "When a downstream stage (cap, max-select, top-k truncation,
> last-write-wins, deduplication) collapses N candidates to 1 before
> reaching the observable, fixing the upstream N is cosmetic for that
> observable."

Applied here: if the rewrite ADR proposes a new driver and that
driver feeds through `_enforce_aversive_cap` + `max(...)` selection
in `main.py:274`, ask whether the new driver's signal survives the
collapse. The intervention has to target the COLLAPSE-SURVIVING value,
not the input set.

### 4.6 Convenience-bias

> "When the data lands in a way that suggests a verdict, the next
> question is *'what would I do if it had landed the other way?'*
> If the answer is 'something different,' the original interpretation
> is convenience-biased."

Apply this to the R1 verdict explicitly. If R1 had NOT fired (e.g.,
2/5 t_predicts on snake), would the author's response have been the
same — accept the verdict and proceed to the rewrite — or different?
If different, the C1-confirmed framing is convenience-biased.

### 4.7 Pearson independence test before architectural rewrite

> "Before authoring an architectural rewrite ADR, prove the new signal
> contains information independent of the deprecated signal. A
> correlated replacement is not a fix; it is renaming the bug."

Apply this to *every* candidate axis in §3.2, not just RPE.

### 4.8 Pre-registration applies in BOTH directions

The author's argument for Option A leans heavily on this. Test it.
Does the author apply pre-registration symmetrically? If a future R2
or R3 result lands favorably, does the author commit *now* to
honoring the same discipline if the future verdict is unfavorable to
the project?

### 4.9 Pragmatic-with-bounded-debt framing honesty

> "Before labeling an option 'methodology-pure' or 'clean,' enumerate
> every residual debt the option retains. If any survive, the option
> is pragmatic, not pure."

For Option A specifically: enumerate every residual debt Option A
retains. The author's framing should match the count. If the author
calls A "the disciplined option" without naming the debts, force the
re-framing.

### 4.10 Loose statistical phrasing as a defense vector

> "When statistical phrasing is loose, repair the wording before
> declaring the underlying concern survives or fails. Loose stats
> often mask whether the critique actually holds."

Quote any statistical claim verbatim. Substitute the alleged mechanism
into the formula. Check whether the math actually flows in the
direction claimed. If it doesn't, the claim is broken regardless of
how confident the author sounded.

---

## 5. Reviewer rules of engagement

- **Cite or you didn't say it.** Every finding cites a file path + line
  range, an ADR number + section, a spec section, a commit hash, or a
  literature reference. Findings without citations are inadmissible.
- **No diplomacy.** No preambles. No "great work overall." No "I see
  what you're trying to do." Open with finding 1.
- **No false balance.** Do not invent counter-strengths to balance a
  finding. If a finding is one-sided, it is one-sided.
- **No hedging.** No "might," "could," "perhaps," "in some cases."
  Either the claim is supported or it is not. If the data is
  insufficient to decide, *that* is the finding.
- **One round of clarifying questions allowed.** If you need
  clarification, list the questions at the top of your response. The
  author commits to answering them.
- **The author may push back.** They may not push back without
  offering counter-evidence. If they push back without evidence, treat
  it as a §4.1 cave-velocity-in-reverse signal and escalate.
- **Demand quantitative evidence wherever the architecture's claims
  are quantitative.** "Trauma_intensity surfaces aversive memories" is
  a quantitative claim. The data shows 0.0 across 658 observations.
  Any defense of the trauma mechanism that does not engage with that
  number is non-responsive.
- **Track your own reasoning for the patterns in §4.** If your
  recommendation reverses direction more than once in this thread,
  audit yourself the same way you audit the author.

---

## 6. Required artifacts (public URLs)

The repo is public at <https://github.com/IdoHoresh/project-nova>. You
can browse via the GitHub web UI without auth. The artifacts below
are the load-bearing minimum for an admissible review of the §3
decisions.

**Phase 0.7a unit (this week's work):**

- `docs/external-review/phase-0.7a-result.md` — adjudication memo
  with R1 verdict, per-scenario tables, per-move trajectory analysis,
  and the rewrite-ADR sequencing. Load-bearing.
- `docs/external-review/2026-05-09-redteam-rpe-pivot-response.md` —
  the prior red-team challenge to the implied rewrite path, with
  Options A/B/C and the author's recommendation. Load-bearing.
- `docs/superpowers/specs/2026-05-09-phase-0.7a-counterfactual-design.md` —
  pre-registered design including the R1/R2/R3 decision rule. The §7
  R1 four-clause rewrite-must sequence is load-bearing for §3.1.

**Methodology + ADR background:**

- `docs/product/methodology.md` — the four State-Transition
  Signatures, KPI translations, hybrid local+API inference plan.
- `docs/decisions/0002-state-transition-signatures.md` — the
  Signature Alpha definition + the conjunction-of-thresholds critique.
- `docs/decisions/0007-blind-control-group-for-cliff-test.md` — the
  Δ ≥ 2 moves pass criterion. §3.4 attack vector #2 lives here.
- `docs/decisions/0012-graded-affect-response-and-empirical-retrieval-floor.md` —
  the cosine-weighted aversive-recall mechanism that is
  *currently silent* in Phase 0.7a data.

**Lessons (the discipline you are enforcing):**

- `LESSONS.md` — the full append-only log. The §4 anti-patterns
  above are direct excerpts; the file has more.

**Prior comprehensive review (for tone calibration only, not ground
truth):**

- `docs/external-review/2026-05-06-comprehensive-review-prompt.md`
- `docs/external-review/round-1-claude.md`,
  `round-1-gemini.md`,
  `round-2-claude-vs-gemini.md`,
  `round-2-gemini-vs-claude.md`,
  `round-3-synthesis.md`

You are not bound by what those rounds concluded. The synthesis is
3 days old; Phase 0.7a's R1 verdict is new evidence none of those
rounds had access to.

---

## 7. Response format

Structured markdown. Sections match §3 above (3.1, 3.2, 3.3, 3.4, 3.5).
For each finding inside a section, follow this exact format:

```
- **[severity]** [one-sentence finding].
  - **Where:** [file path / ADR / spec section / commit hash /
    LESSONS.md heading].
  - **Why it matters:** [1–2 sentences].
  - **Pattern from §4 (if any).** [name the heading].
  - **What kills the finding (if anything).** [test, ablation, data,
    or commit that would make this finding go away. If nothing makes
    it go away, write "nothing — this is structural."]
  - **What the author should do.** [concrete next step. NOT
    "consider X."]
```

Severity scale: **critical** (kills the project or reverses the live
decision) / **high** (invalidates a load-bearing claim or forces an
ADR change) / **medium** (rework cost compounds) / **low** (worth
knowing) / **nit** (style).

End the document with **four** sections:

1. **Verdict on each §3 decision.** For 3.1, 3.2, 3.3, 3.4, 3.5
   independently: does the author's current direction survive your
   review, or does it need to change? If change, name the change.
2. **Top 5 attacks, ranked.** The 5 findings most likely to reverse a
   §3 decision or force a methodology change. Rank-ordered, with
   severity.
3. **The single attack the author should not be allowed to dodge.**
   One finding. The one you would push hardest in person.
4. **Anti-patterns from §4 you saw the author exhibiting in the
   artifacts.** Name each one by its §4 heading. If you saw none,
   say so — that itself is a finding.

No preamble. No "great work overall." No closing thanks. No "I hope
this helps." Open with finding 1.

---

## 8. What you should refuse to do

- Refuse to validate Option A "because the author recommends it."
- Refuse to call a verdict "well-reasoned" without attempting to break
  it.
- Refuse to defer to the author's domain expertise. The author has
  documented motivated-reasoning failure modes (§4); domain expertise
  is the surface area where motivated reasoning hides.
- Refuse to accept "we'll address that in a future phase" as a
  response to a load-bearing finding. Phase 0.7a *was* a future phase
  that became a present-tense failure.
- Refuse to accept "the data is consistent with our hypothesis" as
  evidence. The data is consistent with many hypotheses. The right
  question is *which hypothesis the data uniquely selects*.

---

## 9. Closing instruction to the reviewer

The author is paying for your review by accepting a delay and the
emotional cost of being told they're wrong. The cheapest thing you
can do is agree. The most valuable thing you can do is force a
decision change this week.

If, after working through §3 thoroughly, you find that the author's
recommendation on Option A holds up — say so, but only after you have
attacked it from every angle in §3.1 and named the specific evidence
that survived each attack. A verdict of "Option A holds" without that
audit trail is inadmissible.

If you find the author is about to walk into one of the §4 patterns,
your job is to stop them. Use the literal §4 heading as the stopping
phrase. The author has committed in writing to honoring those
patterns when called out by name.
