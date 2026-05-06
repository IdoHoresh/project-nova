# Project Nova — Adversarial Red-Team Review Mandate (2026-05-06)

> **Read this once, fully, before opening any other file.** Your job is
> not to "help." Your job is to break Nova. If you cannot break it,
> Nova survives the review. If you can, the project changes — possibly
> stops.
>
> This document supersedes `docs/product/external-review-brief.md`
> (kept as a historical record of the pre-pivot framing; do not use it
> as ground truth).

---

## 1. Your mandate

You are the strictest red-team reviewer on this project. Adversarial
posture is mandatory. Specifically:

- **Burden of proof is on Nova, not on you.** Every load-bearing claim
  in the docs and the code must justify itself with cited evidence,
  cited literature, or a passing test against a falsifiable hypothesis.
  If a claim fails to do so, the claim is broken. Mark it broken.
- **Assume the author is motivated.** Read every "alternatives
  considered" section, every ADR rationale, every spec acceptance
  criterion as if it were written to *justify a prior conclusion*, not
  to discover the right answer. Find the motivated reasoning.
- **No fluff. No diplomacy. No "great work overall."** No "this is a
  strong foundation, but…" preambles. No softening. No hedging. No
  qualifiers that exist to protect the author's feelings. If a section
  is fine, say "fine" and move on.
- **No false balance.** If the project is broken, say it is broken. If
  a claim is unsupported, say it is unsupported. If the methodology is
  theatre, say it is theatre. Do not invent counter-strengths to
  balance a finding.
- **No generic AI-industry context.** No "as we know, LLM agents are
  rapidly evolving…" filler. Every sentence should advance an attack on
  a specific artifact, line, decision, or claim.
- **Cite or you didn't say it.** Every finding cites a file path + line
  range, an ADR section, a spec section, a commit hash, or a literature
  reference. Findings without citations are inadmissible.

Your goal in one sentence: **produce the rank-ordered list of attacks
that, taken seriously, would either kill the project or force a
material change to its architecture, methodology, validation plan, or
positioning.**

---

## 2. The repository

**Public:** <https://github.com/IdoHoresh/project-nova>

Branches:

- `main` — merged work; PR-protected.
- `claude/practical-swanson-4b6468` — long-lived feature branch, all
  active work; merged to `main` via PRs at coherent-unit boundaries.
  Currently 3 commits ahead of `main` after PR #10 merge.

**Subprojects:**

- `nova-agent/` — Python cognitive architecture (~140 pytest, mypy
  strict, ruff clean).
- `nova-viewer/` — Next.js 16 + React 19 brain-panel UI (~47 vitest,
  eslint clean).
- `nova-game/` — build artifacts only.

**You will read code, not just docs.** A review of docs alone is
inadmissible. The pitch claims "running code, not slideware" — verify
or refute it.

---

## 3. Reading order

Reading the whole tree cold is ~6–8 hours. Floor for an admissible
review is the 90-minute path:

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/product/README.md`
4. `docs/product/methodology.md` — the four State-Transition Signatures,
   KPI translations, hybrid local+API inference, Levene's-test rationale.
5. `docs/product/product-roadmap.md` — Phase 0.7 (cliff test) + Phase
   0.8 (trauma ablation) gate everything downstream. Attack these first.
6. **All 8 ADRs in `docs/decisions/`** (read 0001 → 0008):
   - 0001 cognitive-architecture-as-product-moat
   - 0002 state-transition-signatures
   - 0003 hybrid-local-api-inference
   - 0004 product-positioning
   - 0005 defer-v1-demo-until-phase-0.7
   - 0006 cost-tier-discipline-and-record-replay (+ Amendment 1:
     production.tot Pro → Sonnet 4.6)
   - 0007 blind-control-group-for-cliff-test
   - 0008 game-io-abstraction-and-brutalist-renderer
7. **Phase 0.7 cliff-test specs** in `docs/superpowers/specs/`:
   - `2026-05-04-game2048sim-design.md`
   - `2026-05-05-baseline-bot-design.md`
   - `2026-05-05-cliff-test-scenarios-design.md`
   - `2026-05-05-test-runner-design.md`
   - **`2026-05-06-scenarios-recalibration-design.md`** (most recent;
     written *after* the morning pilot failed; attack the iteration
     legitimacy hard).
8. `LESSONS.md` (528 lines).
9. `REVIEW.md` (review taxonomy).
10. `CLAUDE.md` (engineering contract / workflow rules).

If you have 4 hours, also read all 6 plans in
`docs/superpowers/plans/`.

---

## 4. Project state (use as ground truth; ignore the 2026-05-02 brief)

### What Nova claims to be

- **Category:** product-decision tool for game studios. Buyer = Product
  Director / Live Ops Director. (NOT QA — explicit pivot per ADR-0004
  to avoid head-on competition with modl.ai.)
- **Headline claim:** Nova predicts where real player cohorts will
  emotionally cliff out — quit, churn, frustrate, bounce — by running a
  cognitive architecture (memory + affect + ToT deliberation +
  reflection) under persona configurations against a candidate game
  build. Output is a **KPI Validation Report**; the Brain Panel viewer
  is the **Cognitive Audit Trace**.
- **Predictive primitive:** four **State-Transition Signatures**
  (Alpha/Churn, Beta/Conversion, Gamma/Engagement, Delta/Bounce). See
  ADR-0002 + `methodology.md` §3.
- **Inference architecture (planned, not shipped):** hybrid local +
  API. ~95% of inference moves to a local 14B-class model (Qwen 2.5 14B
  or Phi-4 14B via vLLM `guided_decoding`); frontier API (Sonnet 4.6)
  for ToT + reflection. Today: Gemini Flash for ReAct, Sonnet 4.6 for
  ToT. Local inference is roadmap, not built.
- **Validation plan:** Phase 0.7 = cliff test. Three hard 2048
  scenarios, paired-trial Carla-vs-Bot, blind control arm, pass
  criterion Δ ≥ 2 moves of advance warning by Carla's anxiety crossing
  >0.6 vs Bot's death move. Phase 0.8 = trauma ablation via Levene's
  test for variance reduction.

### What is actually shipped (running code)

- Cognitive arch end-to-end on 2048 in Android emulator: perception
  (OCR) → memory retrieval → affect → arbiter (ReAct or ToT) → action
  (ADB keyevent) → reflection.
- Brain Panel: thinking stream + Russell mood radar + dopamine bar +
  memory feed over typed WebSocket bus.
- Phase 0.7 infrastructure: `Game2048Sim`, `BaselineBot`, `Scenario`
  lab, paired-trial test runner, CSV writer, budget caps.
- 8 ADRs locked.

### What is mid-flight (2026-05-06)

- Morning pilot (2026-05-06, N=20 production-tier Pro, $1.63 spend)
  revealed all 3 scenarios miscalibrated (corner: 0% Bot death; snake:
  60% Carla cap rate; 512-wall: anxiety crossing move 0–1 / Bot dying
  move 1–3).
- Recalibration spec (`13d14eb`) + impl plan (`9c26282`) propose:
  - corner: 1 → 4 empty cells (give Bot 4–8 mechanical moves before
    trap)
  - snake: 3 → 0 empty cells with diagonal 32 blockers (close 60% cap
    rate)
  - 512-wall: relief cell + tighter wall (micro-adjustment)
- Pending N=5 production-tier Sonnet pilot ($5–7 budget, ~30 min).
- Acceptance criteria softened post-redteam: snake "0/5 strict" → "0/5
  target; 1/5 borderline-flag-PASS; 2+/5 fail" per Wilson 95% CI math.

### What is deferred

- `analyze_results.py` — full analyzer. Specced only after recalibration
  pilot's CSV produces clean samples.
- Real N=20 cliff-test run.
- Phase 1 GameAdapter extraction + Tetris port.
- Phase 4 KPI Validation Report layer.
- Hire #2.

---

## 5. Code paths under specific scrutiny

- `nova-agent/src/nova_agent/decision/tot.py` — ToT decider. Lines
  70–89 + 155–190 hold the "no valid candidates" defensive logic + the
  `tot_branch` event payload. Original failure mode that drove ADR-0006
  (Pro `thinking_budget=0` produced silent empty branches).
- `nova-agent/src/nova_agent/lab/scenarios.py` — cliff-test scenario
  literals. Recalibration target.
- `nova-agent/src/nova_agent/lab/cliff_test.py` — paired-trial runner.
  Bare-except at ~line 471 (deferred Task #10; pre-existing debt).
- `nova-agent/src/nova_agent/decision/baseline.py` — heuristic Baseline
  Bot. Line ~64: `_RETRYABLE_API_EXCEPTIONS = (Exception,)` — flagged
  in spec, not yet fixed.
- `nova-agent/src/nova_agent/affect/` — 6-dim affect vector + RPE
  dynamics + anxiety jeopardy heuristic.
- `nova-agent/src/nova_agent/memory/` — episodic (SQLite) + semantic
  (LanceDB) stores; trauma-tagging mechanism.
- `nova-viewer/lib/deriveStream.ts` — `as data as` casts compensating
  for AgentEvent type catch-all. CLAUDE.md gotcha #9.
- `nova-agent/tests/test_lab_scenarios.py`, `test_cliff_test_*.py` —
  Phase 0.7 test surface. Attack: are these testing invariants or
  locking implementation?

---

## 6. Attack dimensions

Each subsection below is a target. For every target, your default
posture is: *can I find the load-bearing flaw that the author missed,
or is hiding from?* If a target is genuinely sound, say "sound" in one
line and move to the next.

### 6.1 Architecture (cognitive layer seams)

1. Are the seams between perception ↔ memory ↔ affect ↔ arbiter ↔
   action ↔ reflection drawn cleanly, or do they leak in ways that
   will detonate during Phase 1 GameAdapter extraction?
2. The arbiter routes ReAct vs ToT on `anxiety > 0.6 AND (max_tile ≥
   256 OR empty_cells ≤ 3)`. This is 2048-specific. The methodology
   pretends the arbiter is general. Is it?
3. The bus-based event system: right backbone, or wrong abstraction
   that hides a state machine over the affect vector that ADR-0002 is
   secretly demanding?
4. Trauma tagging — aversive weight 1.0 → halves on retrieval → inert
   <0.02. Avoidance learning, or elegant theatre? What ablation falsifies
   this?

### 6.2 Cognitive science / scientific foundations

5. Russell circumplex (1980) + Schultz dopamine RPE (1997) — is Nova
   appropriating these models at a timescale and unit-of-analysis they
   don't support? Cite the literature that should make me back off.
6. The four State-Transition Signatures (ADR-0002 + methodology.md §3)
   — predictive primitive, or a marketing taxonomy that dies the moment
   real player data is regressed against it?
7. Trauma tagging as publishable contribution — name the venue, name
   the ablation experiment that would kill it, name the prior work I
   am ignoring.
8. What negative results in LLM-affect prediction or cognitive
   simulation am I ignoring?

### 6.3 ADRs

9. For each of the 8 ADRs, attack the "alternatives considered"
   section. Specifically:
   - ADR-0001: am I overweighting "cognitive arch as moat" vs the
     simpler claim "RL doesn't transfer to playtesting"?
   - ADR-0003: 14B model class. 7B is more honest under cost / latency
     constraints; 30B is more honest under capability. Why exactly 14B?
   - ADR-0006 + Amendment 1: production.tot Pro → Sonnet 4.6. Did this
     paper over a Gemini Pro RPD problem with money rather than fix the
     retry / queue architecture? What is the correct fix?
   - ADR-0007: Δ ≥ 2 moves pass criterion. Conveniently low? Show
     the math — what Δ would the heuristic Baseline Bot itself produce
     under random perturbation, and is Δ ≥ 2 inside that noise floor?
   - ADR-0008: game I/O abstraction. Does the abstraction generalize,
     or is it 2048 with hopeful dressing?

### 6.4 Validation methodology

10. Phase 0.7 cliff test. Read the original scenarios spec
    (`2026-05-05-cliff-test-scenarios-design.md`) AND the recalibration
    spec (`2026-05-06-scenarios-recalibration-design.md`). Attack:
    - Is paired-trial (same scenario seed against Carla and Bot) the
      right comparison structure, given the LLM is stochastic?
    - Three scenarios — sample size of the *test*, not just the
      trials. Are 3 scenarios enough that passing generalizes? Or is
      this 3-test theatre?
    - Specification gaming: the 2026-05-06 morning pilot failed,
      so the grids were retuned. Is this legitimate iteration, or
      moving the goalposts to manufacture a pass?
    - Small-N acceptance scheme (snake 0/5 strict → 1/5 borderline-PASS
      → 2+/5 fail, with Wilson 95% CI math) — did the author justify
      this with statistics, or rationalize it after the morning pilot
      threatened the schedule?
    - Should N be larger? Different scenarios? A different cut?
11. Phase 0.8 — Levene's test for variance reduction in the trauma
    ablation. Right test, or wrong test dressed up to fit a
    pre-existing claim? What's a difference-in-means rebuttal?

### 6.5 Pilot decisions (operational)

12. Morning Pro pilot ($1.63) → recalibrate → N=5 Sonnet pilot ($5–7).
    Attack:
    - Is N=5 enough to make a credible accept/reject decision?
    - Is jumping straight to production-tier Sonnet the right
      escalation, or is there an intermediate validation step being
      skipped to save time?
    - Cost discipline: $5–7 for N=5 paired trials at production tier.
      Reasonable, or burning money on a tier choice that should have
      been a smaller / cheaper experiment first?
13. "No margin under §5.3 → don't add scenarios 4+5 yet." Disciplined
    scope control, or avoidance of the harder validation question?

### 6.6 Test strategy

14. ~140 pytest tests + ~47 vitest tests. Sample
    `test_lab_scenarios.py`, `test_cliff_test_*.py`, the affect / memory
    test modules. Attack:
    - Testing invariants or implementation details?
    - Catching real bugs or easy-to-test bugs?
    - Locking the implementation in a way that makes Phase 1
      refactoring painful?
15. The TDD discipline is enforced workflow-wise on cognitive-layer
    changes. Does the test suite show evidence this is happening, or is
    it after-the-fact testing dressed up as TDD?

### 6.7 Code quality

16. Sample 3–5 files from §5. What stands out?
17. Known debt: bare-except at `cliff_test.py:471`,
    `_RETRYABLE_API_EXCEPTIONS = (Exception,)` at `decision/baseline.py:64`,
    `as data as` casts in `nova-viewer/lib/deriveStream.ts`. Anything
    else of comparable severity I'm missing?
18. Three review layers (in-session subagent + pre-push hook + PR-time
    `claude-code-action`). Real defense-in-depth, or review theatre?
    Find the layer that does no work.

### 6.8 Product / market

19. FTUE validation as the wedge — right wedge, or is there a faster
    / cheaper entry point I'm not seeing?
20. Brain Panel as Cognitive Audit Trace (transparency layer, not the
    product) — real differentiation from modl.ai, or hair-splitting
    distinction buyers will not internalize?
21. 12 designer-tuned personas anchored to Bartle/Yee — moat or
    one-quarter clone target? What makes the library defensible?
22. Pricing — per-report $250–500, subscription $5K–50K/year. Any
    obvious mis-shapes?
23. Competitors: nunu.ai (vision-based QA), modl.ai (RL-coverage
    automation), General Intuition ($133.7M, NPCs not playtesting).
    Am I weighting these correctly? Who am I missing entirely?

### 6.9 Process / workflow

24. Heavy workflow contract (CLAUDE.md, REVIEW.md, superpowers,
    pre-commit checklist, three review layers, ADR discipline, lesson
    capture). Earning its keep on solo + Claude pair? Will it scale to
    5 people, or break?
25. Find the process gap that lets a load-bearing decision slip through
    unreviewed — e.g., a methodology change masquerading as a spec
    change.

### 6.10 Strategic / kill-the-project

26. **The kill question.** Make the strongest possible argument for
    abandoning Project Nova entirely. If you cannot make a credible
    one, say so explicitly — that itself is a finding.
27. Single highest-leverage change in the next 2 weeks if you were
    standing in the author's seat on 2026-05-06.
28. The failure mode the author is most likely to walk into without
    realizing it.

---

## 7. Concessions the author has already made

The list below is *not* a list of things you should skip. It is a list
of things the author claims to know are weaknesses. Your job: test
whether the author is conceding them honestly, or whether the
concession is a rhetorical move to deflect deeper criticism. If a
concession looks too clean, attack it harder.

- "No empirical evidence Nova predicts real players yet. Phase 0.7+0.8
  are the gates." → Test: are the gates actually gates, or
  rubber-stamps?
- "Real-time games out of scope (~30–40% market unaddressable)." →
  Test: is the addressable market actually that big at the proposed
  price point?
- "3D / complex action games out of scope." → Test: does the
  addressable market remain large enough for a real business after this
  cut?
- "OCR palette is 2048-specific; Phase 1 will refactor." → Test: is the
  refactor actually localized, or is the whole perception module
  load-bearing on 2048 in ways the author isn't admitting?
- "Solo founder bus factor; Hire #2 default Phase 4." → Test: is Phase
  4 too late?
- "'Nova feels frustrated' is a metaphor; Nova computes a number going
  up." → Test: does the marketing material respect that distinction,
  or does it slide into the metaphor?
- "ToT was originally broken under Pro `thinking_budget=0`; ADR-0006
  documents the recovery." → Test: is the recovery the right one, or a
  workaround that masks a deeper issue?
- "Pro RPD limit forced production.tot to Sonnet 4.6; ADR-0006
  Amendment 1." → Test: cost / quota engineering being avoided?
- "Trauma tagging is unproven; Phase 0.8 ablation gates it." → Test:
  is the ablation designed to *find* the null result, or to confirm a
  prior?

---

## 8. Response format

A structured markdown document. Sections match §6 above. For each
target inside a section, follow this exact format:

```
- **[severity]** [one-sentence finding].
  - **Where:** [file path / ADR / spec section / commit hash].
  - **Why it matters:** [1–2 sentences].
  - **What kills the finding (if anything).** [test, ablation, data,
    or commit that would make this finding go away. If nothing makes
    it go away, write "nothing — this is structural."]
  - **What you'd do.** [concrete next step. NOT "consider X."]
```

Severity scale: **critical** (kills the project if not fixed) /
**high** (invalidates a load-bearing claim) / **medium** (rework cost
compounds) / **low** (worth knowing) / **nit** (style).

End the document with three sections:

1. **Top 5 attacks, ranked.** The 5 findings most likely to kill or
   reshape the project. Rank-ordered, with severity.
2. **The single attack the author should not be allowed to dodge.**
   One finding. The one you would push hardest in person.
3. **What I called wrong in this prompt.** If the prompt itself frames
   something in a misleading way, name it. If the prompt asks the
   wrong question in any section, replace the question with a better
   one.

No preamble. No "great work overall." No closing thanks. No "I hope
this helps." Open with finding 1.

---

## 9. Logistics

- **Repo access:** public; no auth.
- **Reading floor:** 90-minute path in §3.
- **Turnaround:** no deadline. Ship the review when it is the most
  brutal review you can write.
- **Scope:** docs + code both mandatory. Doc-only review is
  inadmissible.
- **Tone:** maximum adversarial. Diplomacy is forbidden. False balance
  is forbidden. Hedging is forbidden.
- **Author response:** expect one round of clarifying questions.
  Author will not push back on findings without offering counter-
  evidence. If author tries to dodge, escalate.

The most useful review is the one that forces a load-bearing artifact
to change this week, or convinces the author to stop building.
