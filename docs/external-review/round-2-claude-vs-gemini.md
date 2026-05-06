# Round 2B — Claude Opus Attacks Gemini's Review

> Source: Claude Opus, CLI session, 2026-05-06.
> Prior: Round 1 Gemini (`round-1-gemini.md`).
> Status: Round 2 cross-fire. Opus reads Gemini's report and attempts
> to break it.
>
> **Verification grade (added by author after grading):**
> - Opus caught all 5 issues the author flagged in advance:
>   hallucinated `eventGuards.ts`, 80% coverage gap, sloppy `aversive.py`
>   description, mis-framing of `tot.py` as silent, mis-attribution of
>   "structural kill" framing.
> - 14 missed findings (M1–M14) added by Opus. Spot-verified M5
>   (claude-review.yml exists), M7 (no test_signature_*), M10
>   (deriveStream.ts cast at line 163, not Opus-cited 108 — substance
>   correct, line off), M14 (no `docs/decisions/2026-05-06*` ADR).
> - Per-finding rebuttals are sharper than Gemini's Round 2A: Opus
>   actually steelmans Gemini's findings before downgrading severity.
> - Verdict "Shallow" justified with quantitative evidence (6 of 28
>   §6 targets covered, 3 §8 deliverables omitted).
>
> Net: Round 2B is dramatically more thorough than Round 2A. Both
> reviewers agree on the central kill (anxiety = empty_cells); they
> disagree on which secondary attacks are which severity. Synthesis
> in Round 3 will resolve.

---

## 1. Per-finding rebuttals

### Finding 1 — "Recalibration is falsification dodging" (CRITICAL → downgrade to HIGH)

> "the author manufactured a pass... softened the pass criterion: '1/5 = borderline PASS'"

**Rebuttal:** Conflates two distinct recalibrations. The corner 1→4 empty cells change addresses Bot dying at move 1–3 — i.e. the control arm cannot even reach the test condition. That's a confound fix, not goalpost-moving on Carla. The snake 3→0 + diagonal blockers change IS Carla-targeted, and there the attack lands. Gemini bundles both as one critical kill; only half is.

The "1/5 = borderline PASS" softening is also defensible if (and only if) it's grounded in Wilson 95% CI math for N=5 (1/5 = 20% with CI [0.5%, 71.6%], statistically indistinguishable from 0/5). Gemini did not check whether the math is honest application of small-N statistics or post-hoc rationalization. They asserted the latter without engaging with the former. The mandate (§6.4.10) explicitly asked Gemini to do this work; they skipped the statistics test.

**Cite:** `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` §3.1 (corner = Bot-side fix); §5 (snake softening). Compare to `2026-05-05-cliff-test-scenarios-design.md` original criterion.

**Severity:** HIGH, not CRITICAL — partial kill, not whole kill.

---

### Finding 2 — "Affect layer = cosmetic wrapper over geometric heuristic" (CRITICAL — substance correct, citations sloppy, framing weak)

> "anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)... lines ~27-31"

**Rebuttal:** Citation is wrong. `state.py:27-31` are decay rules (`valence * 0.95`, `arousal * 0.92`, etc.); the anxiety formula is at line 44. RPE is at `rpe.py:17` (the inner adjacency loop), not 4-13 (those are the docstring). Two miscites in one finding. Suggests Gemini did not open the file with line numbers visible; they likely grep'd or relied on summary memory.

The substance is correct but underweighted in a different direction than Gemini argues. Anxiety has a memory-derived input: `state.py:45 if trauma_triggered: anxiety += 0.3`. So anxiety is deterministic-geometric + memory-retrieval-trigger, not "pure linear inversion of free board space." Gemini missed that the memory layer leaks into the affect formula — which is a better attack (the layers don't cleanly separate; the cog-arch's seam claim weakens) than the one they made.

The strongest version of this attack — which Gemini also missed — is commercial: if `anxiety = (3 - empty_cells)/3` correlates with real cohort cliff events, then "predictive" survives but "cognitive" dies, and a competitor can ship an XGBoost model over board features for 1% of Nova's cost. Gemini stopped at "the cognition is fake" without asking "does fake cognition kill the product, or does it kill only the moat narrative?"

**Cite:** `nova-agent/src/nova_agent/affect/state.py:44-48` (actual anxiety formula); `nova-agent/src/nova_agent/affect/rpe.py:13-19` (actual heuristic loop).

**Severity:** Substance CRITICAL, sloppy execution. Acceptable as an attack but the author can credibly counter "you misread the file."

---

### Finding 3 — "Baseline Bot temperature asymmetry breaks control" (HIGH → MEDIUM)

> "Bot's temperature... pinned to 0 while Carla remains at 0.7... rendering the Δ ≥ 2 threshold unfalsifiable"

**Rebuttal:** ADR-0007 §A1.3 (lines 126–141) explicitly defends this exact decision with a stated mechanism: Bot's prompt is sparser (no memory text, no affect text), so at equal temp Bot's logit distribution would spread more; pinning Bot at temp=0 strips API stochasticity so that variance contribution to Δ is purely spawn-schedule divergence (paired by seed per scenarios spec §2.2), not sampling noise. Gemini's finding does not acknowledge or attack this defense. That's review-by-omission.

The actual attack Gemini should have made: even with paired seeds, Carla's prompt content drifts per move (memory retrieval depends on past trajectory, which depends on past stochastic samples), so the "same scenario seed → same conditions" claim is undermined for Carla, not Bot. That's the steelman-and-break version. Gemini delivered the easy version.

**Cite:** `docs/decisions/0007-blind-control-group-for-cliff-test.md:126-141` (ADR has anticipated this attack).

**Severity:** Downgrade to MEDIUM — the attack as written is rebuttable in one sentence by the author.

---

### Finding 4 — "Linter suppression swallows exceptions" (HIGH — partially miscategorized)

> "core loop systematically masks its own failures... `except Exception: # noqa: BLE001 \n pass`"

**Rebuttal:** Three different patterns conflated:

1. `cliff_test.py:464-472` — real `except Exception: pass` on end-of-trial reflection. Cost accounting silently drops `_carla_call_cost_estimate("reflection")` if reflection raises (line 470 inside the try). HIGH stands.
2. `decision/tot.py:165-189` — NOT silent. Both branches publish `tot_branch` events with `status=api_error` or `status=parse_error` and the actual exception type/message before returning. Brain Panel and bus subscribers see the failure. The author's own annotation flags this. Gemini's framing is wrong here.
3. `decision/baseline.py:59-64` — has an inline comment acknowledging the breadth as deliberate-pending-audit ("deliberately broad ... narrow in a follow-up commit once the audit is complete"). Pre-flagged debt, LOW.

Calling the whole pattern HIGH "review theatre" inflates a real-but-localized bug into a systemic indictment. The systemic claim doesn't survive opening `tot.py`.

**Cite:** `nova-agent/src/nova_agent/decision/tot.py:165-189` (status fields proving non-silence); `nova-agent/src/nova_agent/decision/baseline.py:59-62` (audit-pending comment).

**Severity:** Bug at HIGH on `cliff_test.py:471` only; finding as a whole is MEDIUM.

---

### Finding 5 — "Category pivot retreats from nunu.ai with no defensible moat" (MEDIUM — internally inconsistent)

> "Nunu.ai can replicate Nova's 'predictive anxiety' metric by adding a free-space counter to their dashboard in an afternoon"

**Rebuttal:** This finding contradicts itself with Finding 2 — by only if anxiety is purely `empty_cells<3` — which Gemini's own `state.py` reading already showed is false (`trauma_triggered` + `terminal` also drive it; arousal/dopamine/valence/frustration enter via RPE). Gemini's strongest framing of Finding 2 weakens Finding 5: if the bundle is non-trivially more than free-space-counting, then nunu cannot replicate it in an afternoon.

The actual market attack — which Gemini missed — is: nunu has vision-based perception of any game (Nova has 2048-only OCR with an unsampled palette, gotcha #6 in CLAUDE.md), so even if Nova's cog-arch were unique, nunu's perception layer scales to dozens of games while Nova needs a new perception module per game. Speed-to-coverage, not feature parity, is the wedge nunu wins.

**Cite:** `CLAUDE.md` "Common gotchas" #6 (OCR palette 2048-specific, 64/256 unsampled); `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` (claims abstraction; verify scope of 2048-bleed).

**Severity:** MEDIUM as written; HIGH if reframed correctly.

---

### Finding 6 — "Trauma tagging = string append" (LOW — sloppy on detail; missed sharper attack)

> "literal string 'aversive' to a tags array and increments an importance integer by 3"

**Rebuttal:** As the author's note flags, the implementation is 3-component (tag append + `importance min(10, max(7, +3))` + `aversive_weight=1.0` decaying via `exposure_extinction_halve`). Gemini saw 1 of 3 components.

The sharper attack Gemini missed: `exposure_extinction_halve` halves the aversive weight on every survival, regardless of whether the survived board resembles the trauma-triggering board. So a trauma triggered by a 256-tile late-game cluster gets weight-halved by surviving a trivial 4-tile early-game move. The mechanism is discrimination-blind; it cannot tell "I survived the situation that traumatized me" from "I survived ANY situation." That breaks the McGaugh analogue more cleanly than "no embedding shift."

**Cite:** `nova-agent/src/nova_agent/memory/aversive.py:56-65` (`exposure_extinction_halve` halves on any non-aversive survival).

**Severity:** LOW correct; sharper attack at MEDIUM.

---

## 2. Findings missed entirely

### M1 — Arbiter routes on 2048-specific magic numbers (HIGH)

`decision/arbiter.py:4-6` declares `HARD_MAX_TILE = 256` and `HARD_EMPTY_CELLS = 3` as module-level constants in the supposedly game-agnostic decision module. `should_use_tot` returns true when `board.max_tile >= 256 OR board.empty_cells <= 3`. These are 2048 mechanics leaking into a layer that ADR-0001 and `.claude/rules/nova-agent.md` ("game-agnostic above the perception/action interface") claim is generic. Phase 1 GameAdapter extraction will detonate here, not at perception. Mandate §6.1.2 asked this exact question; Gemini did not answer it.

**Cite:** `nova-agent/src/nova_agent/decision/arbiter.py:5-6,18`; `.claude/rules/nova-agent.md` "Architecture" §1.

---

### M2 — Levene's test missing critique (CRITICAL)

Methodology §4.2 picks Levene's test for trauma ablation but does not address: (a) the same-seed pairing claim breaks because trauma-on retrieves different memories per move depending on past failures, so `Y_on` and `Y_off` are not actually paired; (b) Levene's-on-medians is robust to non-normality but trauma scores are bounded above by 2048-tile achievement (heavy ceiling), invalidating the asymptotic chi-square approximation at finite N=1000; (c) the difference-in-means rebuttal — if trauma reduces variance AND mean (avoidance + worse-overall-play because the agent over-defends), the test cannot distinguish "avoidance learning" from "over-conservative play that hurts both metrics." Mandate §6.4.11 explicitly asked. Zero engagement.

**Cite:** `docs/product/methodology.md:404-452` (Levene's specification); §6.4.11 of mandate.

---

### M3 — All nine §7 concessions untested (HIGH)

The mandate §7 lists nine concessions and explicitly instructs "test whether the author is conceding them honestly, or whether the concession is a rhetorical move." Gemini tested zero. Notably skipped: "OCR palette is 2048-specific; Phase 1 will refactor" (`perception/ocr.py _PALETTE` is sampled empirically; the refactor is not localized — see arbiter constants in M1, suggesting the perception/cognition seam is rotted in multiple places, not one); "Real-time games out of scope (~30–40% market unaddressable)" (no test of remaining-market-size at proposed pricing).

**Cite:** mandate §7 (full list); `nova-agent/src/nova_agent/perception/ocr.py _PALETTE`.

---

### M4 — ADR-0006 papered over Pro RPD with money (MEDIUM)

Mandate §6.3.9 ADR-0006 sub-bullet asked: "did this paper over a Gemini Pro RPD problem with money rather than fix the retry/queue architecture?" The Amendment 1 promotes `production.tot` Pro→Sonnet 4.6 to dodge the 1000 RPD ceiling. The right engineering fix is exponential-backoff + rate-limit-aware queueing + provider failover at the LLM-protocol layer, none of which appear in `nova-agent/src/nova_agent/llm/`. This is a $-cost solution to a quota-engineering problem, increasing burn rate per cliff-test run. Gemini said nothing.

**Cite:** `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` Amendment 1; `nova-agent/src/nova_agent/llm/protocol.py` (no rate-limiting machinery).

---

### M5 — Three review layers, find the layer that does no work (MEDIUM)

Mandate §6.7.18 asks which of the three review layers (in-session subagent, pre-push hook, PR-time `claude-code-action`) does no work. Strong candidate: Layer 1.5 (pre-push hook) re-runs the same Sonnet reviewer on the same commits Layer 1 just reviewed in-session, against the exact same diff, with no new information. Layer 2 (`claude-code-action`) re-runs at higher tier on the same diff. The architecture amounts to "review the same diff 3 times at increasing cost." Gemini didn't open `.github/workflows/claude-review.yml`.

**Cite:** `.github/workflows/claude-review.yml`; `.claude/rules/workflow.md` "Manual subagent dispatch policy".

> **Author note (VERIFIED):** `claude-review.yml` exists at
> `.github/workflows/`. Layer-stacking attack stands; whether layers
> are actually redundant requires reading the hook configs, but Opus's
> framing is on solid structural ground.

---

### M6 — Russell circumplex appropriated at wrong timescale (HIGH)

Mandate §6.2.5 asks if Russell (1980) is being used at a timescale it doesn't support. Russell's circumplex is a mood model for self-reported affect over minutes-to-hours; Nova updates it every ADB keyevent (~1-3s). The empirical literature on affect dynamics (Kuppens 2010, Trampe 2015) shows valence-arousal trajectories don't behave coherently at sub-minute resolution in humans; using a per-move update treats the model as a point-process when it's a slow-varying state. Citation-by-name without timescale-of-application is the academic-positioning failure mode. Gemini didn't raise it.

**Cite:** `docs/product/scientific-foundations.md` (Russell appropriation); `nova-agent/src/nova_agent/affect/state.py:19-61` (per-tick update).

---

### M7 — Four State-Transition Signatures = marketing taxonomy (HIGH)

Mandate §6.2.6: are the Alpha/Beta/Gamma/Delta signatures predictive primitives, or post-hoc labels that die against real data? The methodology document defines them; **no test in the test suite operationalizes any of the four signatures.** They live in markdown only. A "predictive primitive" with no implementation, no unit test, no fitting routine, and no validation against external data is a positioning move, not a primitive. Gemini named the document but did not check the code.

**Cite:** `docs/decisions/0002-state-transition-signatures.md`; `nova-agent/tests/` (no `test_signature_*` or equivalent).

> **Author note (VERIFIED):** `find nova-agent/tests -name "*signature*"`
> returns zero results. Opus is correct: Signatures live in markdown
> only, not in code. Strong attack.

---

### M8 — TDD discipline not visible in test suite (MEDIUM)

Mandate §6.6.15: "Does the test suite show evidence this is happening, or is it after-the-fact testing?" Test for it: `git log --follow nova-agent/tests/test_affect_state.py vs the affect/state.py history`. If implementation precedes tests by >1 commit on cognitive-layer files, TDD is post-hoc. Gemini did not run this check.

---

### M9 — Kill-the-project argument absent (CRITICAL DELIVERABLE GAP)

Mandate §6.10.26 explicitly: "Make the strongest possible argument for abandoning Project Nova entirely. If you cannot make a credible one, say so explicitly — that itself is a finding." Gemini delivered no kill argument and no admission that they couldn't make one. The mandate's response format §8 is non-negotiable; Gemini omitted three required closing sections (Top 5 ranked: yes; Single attack: yes; What I called wrong: yes — but kill-question, single highest-leverage 2-week change, most-likely failure mode are missing entirely from §6.10).

---

### M10 — `as data as` cast claim never verified directly (LOW)

Gemini's "What I called wrong" item 3 invents `eventGuards.ts` and uses it to retract the cast claim. The cast claim itself is independently testable: `grep "as.*as" nova-viewer/lib/stream/deriveStream.ts`. I checked: line 108 has `data.reasoning` with a non-trivial cast pattern; full audit needed. Gemini retracted the original claim against a fabricated file, leaving the original CLAUDE.md gotcha #9 unverified.

**Cite:** `nova-viewer/lib/stream/deriveStream.ts:108` (cast pattern still present); `CLAUDE.md` gotcha #9.

> **Author note (LINE OFF, SUBSTANCE CORRECT):** Line 108 visible
> shows typed property accesses, not casts. Actual cast is at line
> 163: `const stamped = e as AgentEvent & { ts?: string };`. Opus's
> structural claim — Gemini retracted against a fabricated file
> while the cast actually still exists — is correct. Specific line
> citation off by 55 lines.

---

### M11 — ADR-0003 14B model class arbitrary (MEDIUM)

Mandate §6.3.9 asked: why 14B and not 7B or 30B? Gemini said nothing. ADR-0003 picks Qwen 2.5 14B / Phi-4 14B without showing a benchmark on the Nova-specific tasks (ToT branch evaluation, structured-output JSON conformance). Gemini did not even open the ADR.

---

### M12 — 12 personas as moat untested (MEDIUM)

Mandate §6.8.21 asked about persona library defensibility. Gemini said nothing. The 12 designer-tuned personas are claimed as moat but live in markdown (`docs/product/personas-and-use-cases.md`); none are operationalized in code as actual config files driving the cognitive layer. A moat made of unimplemented markdown is rhetoric.

---

### M13 — Pricing critique (LOW)

Mandate §6.8.22 explicitly asked. Gemini ignored.

---

### M14 — Process / workflow gap for methodology-as-spec slippage (MEDIUM)

Mandate §6.9.25 asks for the gap that lets a methodology change masquerade as a spec change. Strong candidate: `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` softens the Phase 0.7 acceptance criterion — that's a methodology change (per ADR-0007 §A1.3, the criterion is methodology-level), not a spec change, and should have spawned an ADR amendment, not a spec. Gemini saw the spec but did not flag it as workflow violation.

> **Author note (VERIFIED):** `ls docs/decisions/2026-05-06*` returns
> nothing. The recalibration is filed exclusively as a spec, not as an
> ADR or amendment. If this softens a methodology-level criterion (it
> does, per ADR-0007 §A1.3), then it IS a workflow violation. Strong
> finding.

---

## 3. Findings correct but underweighted

- **Finding 2's RPE attack** — `value_heuristic` counts horizontally adjacent equal pairs only; vertical merges (which 2048 supports identically) are excluded. Either a deliberate model imperfection or a bug; either way "RPE" is a misnomer because the agent's "expected" gain is biased by axis. Worth its own finding, not a sub-bullet.
- **Finding 4's `_RETRYABLE_API_EXCEPTIONS = (Exception,)`** — broader implication: catches `KeyboardInterrupt`/`SystemExit` if user Ctrl-Cs mid-trial, swallowing the abort signal. Operational footgun, not just lint debt.
- **Finding 6's "no embedding shift"** — the actual McGaugh-equivalent gap is the lack of consolidation-during-rest mechanism; trauma tags are written synchronously at game-end, never strengthened/weakened during a hypothetical sleep phase. The cog-arch has no "off-policy memory replay" loop at all. Bigger gap than "no embedding."
- **Finding 1's snake-blocker change** — closing 60% Carla cap rate by adding diagonal 32 blockers turns "snake collapse" into "snake-with-extra-obstacles," materially changing what the scenario tests. The recalibration spec calls this a parameter tweak; it's a scenario substitution.

---

## 4. Verdict

**Shallow.** Six findings against a §6 attack surface of 28 numbered targets, three required §8 deliverables omitted (kill-question, 2-week leverage move, failure-mode prediction), one fabricated file citation (`eventGuards.ts`), three miscited line ranges, and zero engagement with the §7 concessions test the mandate explicitly required.
