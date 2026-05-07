# Project Nova — Product Roadmap

> **Read first:** [`README.md`](./README.md) for strategic context, then
> [`methodology.md`](./methodology.md) for the technical foundation. This doc
> assumes you've read both.
>
> **Status as of 2026-05-02:** Phase 0 (cognitive architecture demo) is in
> final polish on `claude/practical-swanson-4b6468`. The 30-day validation
> sprint detailed below starts the day v1.0.0 is tagged.
>
> **Audience:** the team executing the build, week-by-week.
>
> **Versioning:** v2 of this roadmap, incorporating the brainstorm decisions
> documented in [`external-review-brief.md`](./external-review-brief.md):
> Unity SDK promoted to Phase 1 lead, KPI Translation Layer becomes the
> spine of Phase 4, Phase 0.5 (paid validation study) replaced with Phase
> 0.7 (Python-sim cliff test) + Phase 0.8 (trauma ablation), hybrid local +
> API inference stack added.

---

## Phase overview

| Phase | What | Duration | Cumulative wall-clock | Cost |
|-------|------|----------|------------------------|------|
| **0** | Finish v1.0.0 cognitive architecture demo on 2048 | 1 week | week 1 | ~$50 LLM |
| **0.7** | Cliff Test (Python `Game2048Sim` + documented hard boards) | 1 week | week 2 | $0 |
| **0.8** | Trauma Ablation (dual-DV: within-game trap re-engagement + Anxiety lift) | 1 week | week 3 | $0 |
| **0.9** | KPI Report Mockup v0.1 (4 Signatures defined; CSV export) | 1 week | week 4 | $0 |
| **1** | **Unity SDK** + GameAdapter abstraction + Tetris port (proof of generality) + hybrid local+API inference | 6–8 weeks | week 12 | ~$100 + $1.5K hardware |
| **2** | Exploration learning + general perception ("drop in any game") | 8–12 weeks | week 24 | ~$200 |
| **3** | Persona system v1 (4 personas) → v2 (10 personas) | 2–3 weeks (parallel with 2) | week 24 | ~$100 |
| **4** | **KPI Translation Layer + Validation Report** (lead deliverable) + Long-Horizon Simulation Loop (§4.6) | 5–8 weeks | week 32 | ~$250 |
| **5** | Production infra (headless emulators, multi-tenant API, billing) | 8–12 weeks | week 44 | $500–2K cloud |
| **6** | First 3 paid pilots, real-user validation corpus, iterate | open-ended | from week 33 onward | revenue from here |

**MVP-as-product:** Phases 0–4 → ~7.5 months wall-clock, ~$750 in
LLM/hardware costs.

**Polished v1 product:** through Phase 5 → ~10.5 months wall-clock.

Estimates assume one full-time engineer plus LLM/hardware costs. With a
second engineer hired around Phase 4, Phases 1–4 can compress to ~5 months.

---

## The 30-day validation sprint (Phases 0–0.9)

Phases 0 through 0.9 form a single tightly-scoped 30-day sprint that
front-loads the experiments that could *kill* the product thesis. Each week
has a self-judged gate that determines whether to proceed or to repair.

### Sprint principles

- **Falsifiable gates only.** Every week ends with a binary pass/fail
  determined by an observable metric, not a subjective judgment.
- **No new features.** Polish, validate, document. Feature freeze on the
  viewer UI for the entire 30 days.
- **Failure is information, not failure.** A failed gate triggers a
  defined repair branch (re-tune the affect logic, demote trauma to UI
  flavor, etc.) — not a project-end signal.

### Week 0 — Pre-Phase-0.7 hardening (demo deferred per ADR-0005)

**Milestone:** Cognitive architecture clean, review system shipped, `Game2048Sim` scaffolded so Week 1 cliff test can start on Day 1.

**Demo recording is deferred** until Phase 0.7 cliff test passes — see [ADR-0005](../decisions/0005-defer-v1-demo-until-phase-0.7.md). The v1.0.0 git tag is parked until then; the demo records the full story (cognitive architecture + cliff-test result), not the architecture in isolation. Days 3–7 originally budgeted for demo prep + recording reallocate to direct Phase 0.7 work.

**Tasks (revised):**
- ✅ Final code-review pass on the cognitive architecture (covered by the new `/review` orchestrator + Layer 2 GitHub Action shipped 2026-05-04)
- ✅ AgentEvent type system cleanup (shipped via PR #1)
- Live validation run of the AgentEvent validator on a full 50-move game; final cog-arch review pass with `/review`
- Begin `nova_agent.lab.Game2048Sim` build early (originally Week 1 Day 1–2) — pull this work forward into the freed Days 3–7 of Week 0
- Synthetic "demo dry run" (no recording, just a walk-through to surface brain-panel UX gaps the same way an actual recording would)

**Self-judged gate:**
- Cognitive architecture review pass clean (no BLOCK findings from `/review`)?
- `Game2048Sim` boots and consumes the existing `BoardState` interface end-to-end on at least one canned scenario?
- Brain-panel walk-through surfaces no critical UX regressions?

**Pass:** proceed to Week 1.
**Fail:** address the failing item(s) before Week 1 begins. Do NOT proceed to cliff-test work with an unreviewed cognitive architecture or a non-functional simulator.

### Week 1 — Cliff Test

**Milestone:** Python `Game2048Sim` built; cliff test run on documented
hard 2048 scenarios; affect-curve alignment documented.

**Why this matters:** every Nova claim about predicting human behavior
depends on this question. If Nova's affect curve only spikes *after*
game-over, Nova is narrating outcomes (interesting but commercially
useless). If it spikes *before* the failure point, Nova is predicting them
(the entire product thesis works).

**Tasks:**
- Build `nova_agent.lab.Game2048Sim` (~2 days). In-process Python 2048
  simulator with the same `BoardState` interface the cognitive architecture
  already consumes. Removes OCR + emulator latency as a confound.
- Identify 3-5 documented hard 2048 scenarios from community sources
  ("snake collapse" patterns, "1024-wall" board states, dead-end
  configurations)
- Seed the simulator with each scenario. For EACH scenario, run **two
  arms on the same seeded sequence** (Blind Control Group, per
  [ADR-0007](../decisions/0007-blind-control-group-for-cliff-test.md)
  and `methodology.md` §4.1):
  - **Test arm:** N=20 with Casual Carla persona (full cognitive
    architecture). Record affect-vector trajectories.
  - **Control arm:** N=20 with Baseline Bot persona (purely-logical
    score-maximizer prompt; no affect, no memory, no ToT, no
    reflection). Record only move sequences and game-over indices.
- Compare timing of Carla's `Anxiety > 0.6` event against (a) Carla's
  own failure point, AND (b) the Baseline Bot's mean failure move.
  Report `Δ = t_baseline_fails - t_carla_predicts` per scenario.

**Self-judged gate (the falsification criterion — both must hold):**
- Did Carla's affect peak precede her own failure point by at least 2
  moves in > 80% of her N=20 trials? (prediction-validity test)
- AND did Carla predict the cliff at least 2 moves earlier than the
  Baseline Bot's mean failure move (`Δ ≥ 2`) in ≥ 3 of the 3-5
  scenarios? (affect-earns-its-keep test)

**Pass (both arms):** affect predicts AND adds material lead time over
a non-affective baseline. Architecture-as-predictor claim is alive.
Proceed to Week 2.

**Fail — single-arm pass (Carla predicts but Δ < 2):** affect tracks
the cliff but doesn't precede it more than mechanical exhaustion would.
Architecture demoted to "architecture-as-narrator" — interpretable but
not predictive. Reposition the demo around interpretability; no pitch
conversations claiming prediction.

**Fail — both arms (no early Anxiety peak):** full failure of the
prediction hypothesis. Two-week affect-rework branch begins: re-derive
the RPE weights, ablate each affect dimension's update rule, identify
which dimension is decoupled from outcomes. The schedule slips by 2-3
weeks but the architecture gets fixed before any pitch conversations.
A failed cliff test is a publishable result, not a kill signal.

**Cost note:** Blind Control Group adds ~300-500 games to the test
budget. At plumbing-tier pricing (`NOVA_TIER=plumbing`, ~$0.05-0.10
per game) that is <$50 of additional spend — negligible against the
scientific-validity gain. Cliff test runs at `NOVA_TIER=production`
(both arms), not plumbing — the cliff test is exactly the cognitive-
judgment work plumbing tier is forbidden for, per ADR-0006.

### Week 2 — Trauma Ablation

**Milestone:** Paired trauma-on / trauma-off run via `Game2048Sim` per
methodology §4.2 dual-DV. Trauma keep / demote / amend decision
finalized. Sample size and cost set by the Phase 0.8 spec
(`docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md`).

**Why this matters:** trauma-tagging is currently marketed as a
differentiating cognitive feature. Without empirical evidence that it
produces avoidance learning, the marketing claim is exposed. The
dual-DV test specifically targets the *on-thesis* claim — within-game
adaptation to trap-similar states — and validates the affect pathway
as a secondary, descriptive read.

**Tasks:**
- Run paired trauma-on / trauma-off games on identical seeded board
  sequences in `Game2048Sim`. Sample size from the Phase 0.8 spec
  power calc on Cohen's `d ≥ 0.3`.
- Compute primary DV: within-game trap-recurrence rate after the first
  trap encounter, per [`methodology.md`](./methodology.md) §4.2.
  Trap-similarity metric, proximity threshold `T`, and trap-pattern
  dictionary defined in the Phase 0.8 spec.
- Compute secondary DV: Anxiety value distribution at trap-similar
  states (proximity ≥ `T`). Reported alongside the primary, non-gating.
- Pre-register both DVs and the gate before pilot data exists.

**Self-judged gate (primary, gating):**
- Cohen's `d ≥ 0.3` on the within-game trap-recurrence rate, with
  95% CI excluding 0 and trauma-on rate < trauma-off rate.

**Self-judged secondary (descriptive, non-gating):**
- Cohen's `d` and 95% CI on the Anxiety lift at trap-similar states.

**Pass (primary):** trauma is a real avoidance-learning mechanism.
Keep marketing it as a core architectural feature. Add the Phase 0.8
result to [`methodology.md`](./methodology.md) §4.2 as the validation
citation. If primary passes but secondary nulls, write a follow-up
ADR amendment reframing the affect-pathway claim per §4.2's
three-branch failure-mode table.

**Fail (primary):** trauma is **demoted** from a core architectural
feature to UI flavor. The mechanism stays in the code; the brain-panel
render stays for visual interest; marketing copy drops the
"competitive differentiator" framing. Update accordingly.

**Why this design and not Levene's-on-score variance:** the original
2026-05-04 plan applied Levene's Test for equality of variances on
final-score distributions. External red-team review (round 1, attacks
C5 / M-02 in `docs/external-review/round-3-synthesis.md`) flagged
three independent failure modes: (a) same-seed pairing breaks because
trauma-on retrieves different memories per move, (b) 2048's score
ceiling invalidates the asymptotic chi-square approximation at finite
N, and (c) the test cannot distinguish avoidance learning from
over-conservative play. Methodology §4.2 was rewritten 2026-05-06
(commit `a6f92dc`) to replace Levene's-on-score with the dual-DV
design above. The within-game trap-recurrence DV is the on-thesis
test for avoidance learning that Levene's-on-score was meant to be.

### Week 3 — KPI Report Mockup v0.1

**Milestone:** First end-to-end mockup of the studio-facing Validation
Report. PDF + HTML versions.

**Why this matters:** the report is the actual product. The brain panel,
the cognitive architecture, the State-Transition Signatures — all of these
are *means*. The report is the *deliverable*. Building the mockup forces
us to confront which signals translate cleanly to KPI predictions and
which don't.

**Tasks:**
- Wireframe the report (template in [`README.md`](./README.md) Core
  Deliverable section)
- Render a real example using outputs from a Week 1/2 simulator run
- All four Signatures (Alpha/Beta/Gamma/Delta) defined and demonstrated
- Every prediction line footnoted to a methodology citation
- CSV/JSON export available as a first-class feature (not an afterthought)

**Self-judged gate:**
- Does the mockup look like a Firebase / Looker dashboard (information-
  dense, KPI-led, drill-down available) or a sci-fi UI (pretty,
  affect-curve-led, no clear KPIs)?
- Would a Product Director who's never heard of cognitive architecture
  understand what they're looking at in 60 seconds?

**Pass:** Phase 4 (full reporting layer build, weeks 24-30) is now de-risked
because the format is locked.

**Fail:** redesign the mockup. The whole product hinges on this artifact
being readable.

### Week 4 — Phase 1 Specification

**Milestone:** Detailed Phase 1 spec written. Unity SDK package structure,
GameAdapter interface, hybrid inference router design. Public-facing
writeup of the validation results from Weeks 1-2.

**Tasks:**
- Spec the `Nova.Studio` Unity package (install command, integration API,
  required Unity version, OnSessionStart/OnDecision/OnSessionEnd hooks)
- Spec the `GameAdapter` Python interface
- Spec the hybrid inference router (`LocalLLMAdapter` using vLLM +
  `guided_decoding`, fallback chain to API)
- Write the validation results post (Cliff Test result, Trauma Ablation
  result) for the company blog / future investor deck
- Update [`competitive-landscape.md`](./competitive-landscape.md) and
  [`personas-and-use-cases.md`](./personas-and-use-cases.md) with anything
  the validation work surfaced

**Self-judged gate:**
- Could a developer who's never seen Nova install the (yet-to-be-built)
  SDK and run their first simulated playtest in <30 minutes from the
  install command?
- Or would they need to schedule a setup call?

**Pass:** Phase 1 build kicks off Week 5.

**Fail:** simplify the SDK API. Production-grade developer experience
requires shorter time-to-first-value than research-quality APIs.

---

## Phase 0 — Finish v1.0.0 (current week)

**Status:** in flight. Don't deviate.

The 57-task original implementation plan + the supplementary work this
session (thinking-stream viewer, OCR palette, Pro thinking-budget fix,
prompt-voice tightening, real timestamps + newest-on-top order, type
system cleanup) IS Phase 0.

What's left (revised per [ADR-0005](../decisions/0005-defer-v1-demo-until-phase-0.7.md) — demo deferred until Phase 0.7 passes):
- ✅ AgentEvent type cleanup (shipped via PR #1)
- ✅ Final code-review pass on the cognitive architecture (covered by the new `/review` orchestrator)
- Live validation run + brain-panel walk-through (no recording)
- Pull `Game2048Sim` work forward from Week 1 into the freed Days 3–7 of Week 0
- ~~Demo recording: ≤4 min~~ → deferred to post-Phase-0.7
- ~~v1.0.0 git tag~~ → parked, re-tag when demo records

**Revised exit criteria:**
- `/review` pass clean on cognitive architecture (no BLOCK findings)
- Memory + affect + ToT + reflection all functionally working end-to-end on a real 50-move game (verified via the dry-run walk-through, not a recording)
- Game-over → reflection → semantic rule extraction loop demonstrably working in the dry run
- `Game2048Sim` scaffold compiles, consumes `BoardState`, and runs at least one canned hard-scenario seed end-to-end

**Do not** record the v1.0.0 demo until Phase 0.7 passes. Architecture polish without the cliff-test result is the wrong artifact for the product story (per ADR-0005). Phase 0.7 work begins as soon as the revised exit criteria are met — no separate "Week 1 boot" step needed.

---

## Phase 0.7 — Cliff Test (Week 1 of sprint)

Detailed in the [Week 1 — Cliff Test](#week-1--cliff-test) section above.

**Phase 0.7 is now also the demo-recording gate** per [ADR-0005](../decisions/0005-defer-v1-demo-until-phase-0.7.md). The v1.0.0 demo records on the back of a passed cliff test, not on the architecture in isolation. If Phase 0.7 fails, the affect-rework branch begins per the Week 1 fail path; no demo recording until the rework completes and a follow-up cliff test passes.

**Net architectural addition:** new module `nova_agent.lab.Game2048Sim`
under `nova-agent/src/`. Pure Python, no external deps beyond what's
already in the agent. Same `BoardState` interface. Used only for lab
experiments; production path remains OCR + emulator (and eventually Unity
SDK).

**Why a Python sim instead of forcing the emulator:** scientific isolation.
If the cliff test fails on the emulator stack, we don't know whether the
failure is in perception (OCR misreads a tile), action (ADB keyevent
doesn't register), or cognition (affect logic doesn't predict). The
Python sim removes perception and action as confounds, leaving the
cognitive layer as the only variable under test. This is the lab
methodology; production deployment is something else entirely.

---

## Phase 0.8 — Trauma Ablation (Week 2 of sprint)

Detailed in the [Week 2 — Trauma Ablation](#week-2--trauma-ablation)
section above.

**Statistical foundation:** dual-DV per methodology §4.2 — primary
behavioral DV (within-game trap-recurrence rate, Cohen's `d ≥ 0.3`)
gates pass/fail; secondary affective DV (Anxiety lift at trap-similar
states) is descriptive. Operational definitions (trap-similarity
metric, proximity threshold `T`, trap-pattern dictionary, sample size,
power calc) live in the Phase 0.8 spec.

**Why within-game adaptation, not cross-game optimization:** trauma in
the cognitive architecture is *avoidance learning within a session* —
the agent remembers what killed it during the current playthrough and
shifts behavior for the remaining moves. The expected empirical
signature is reduced within-game re-engagement with trap-similar
configurations after a first trap encounter, not optimal play across
separate games. See [`methodology.md`](./methodology.md) §4.3 for the
full rationale and the three independent failure modes that retired
the prior variance-on-score design.

**Failure mode handled:** if the primary DV nulls, trauma is
**demoted** rather than removed. The mechanism stays in the code; the
brain-panel render stays for visual interest; the marketing claim
drops to "trauma-tagged memories receive elevated retrieval weight
(UI artifact)" rather than "trauma improves agent performance." If
primary passes but secondary nulls, the affect-pathway framing is
amended in a follow-up ADR — the mechanism still works, but routes
through planning / ToT / memory-conditioned retrieval rather than
through Anxiety lift.

---

## Phase 0.9 — KPI Report Mockup (Week 3 of sprint)

Detailed in the [Week 3 — KPI Report Mockup v0.1](#week-3--kpi-report-mockup-v01)
section above.

**Why this is a phase, not just a doc:** the mockup is the alignment
artifact between the cognitive architecture (what we built) and the
commercial product (what we sell). Building it tonight, before any
pitches, prevents the failure mode where we discover at pitch #1 that
the report we *think* studios want is not the report they *actually* want.

---

## Phase 1 — Unity SDK + GameAdapter abstraction (weeks 5–12)

**Goal:** prove the cognitive architecture is game-agnostic AND
production-deployable, by porting to a Unity-integrated game via SDK
rather than emulator. Tetris is the second target — different action
space (rotate + drop vs swipe), different scoring, well-known so demos
resonate.

**Reframed scope (key change in v2):** Phase 1's lead deliverable is the
**Unity SDK**, not the GameAdapter abstraction. The SDK is the production
integration path; the GameAdapter abstraction is the architectural
refactor that supports both SDK-integrated and OCR-fallback paths.

### Phase 1 hard constraints (added 2026-05-04 per principal engineer red-team)

Two architectural commitments locked into the Phase 1 spec before any
SDK code is written. Both reduce future sales-cycle friction by
removing objections studios will raise during procurement / security
review.

- **Zero-PII guarantee.** The Unity SDK MUST ingest zero
  Personally-Identifiable Information from the host game build.
  Permitted payload: board state, tile/piece coordinates, score,
  health/resource bars, action enums, RNG seeds. Forbidden payload:
  player IDs, device IDs (advertising IDs, IDFA, Android Ad ID),
  IP addresses, account email, geolocation, session tokens, push
  notification IDs. The SDK is architecturally a JSON pipe over a
  schema validated at the Python boundary; if a studio's game build
  attempts to send a forbidden field, the SDK rejects the payload at
  serialization time and logs a structured warning to the studio's
  own log channel — never to a Nova-controlled endpoint. This is
  the "Dumb Pipes" architecture: the SDK does no cognition and
  carries no PII; cognition + storage stays in the Python backend
  the studio runs themselves (or that we run for them under their
  data agreement). Hardcoding the guarantee at the SDK layer drops
  the procurement / cybersecurity review timeline by an estimated 3
  months because Nova bypasses the typical AI-vendor data-processing
  agreement (DPA) negotiation entirely — there is no PII to process.
  An ADR captures the field allowlist and the rejection-on-violation
  contract before the first commit of SDK code.

- **Unity LTS version lock — Unity 2022.3 LTS.** Unity is notoriously
  fragmented across versions (2019 LTS, 2020 LTS, 2021 LTS, 2022 LTS,
  6.x). Supporting the full matrix means drowning in C# compilation
  errors and runtime API differences. Nova v1 supports **only Unity
  2022.3 LTS** — declared explicitly in the SDK README, the package
  manifest, and the studio onboarding doc. Studios on older or newer
  versions are told "we will support your version when we have a
  paying customer on it"; that is honest scope clamp, not a
  limitation. The choice of 2022.3 specifically: it is the most
  recent LTS at the time of writing with the broadest mid-2026
  studio penetration, includes the C# 9 features the SDK relies on
  for source generators, and has long-term support extending into
  2026-2027 so the lock survives the v1.x lifecycle without forcing
  a Unity version migration mid-pilot. An ADR captures the version
  decision + the upgrade-criteria the studio team will use to decide
  when v2 should support a newer LTS.

### Work units

**1.1 — Define the `GameAdapter` interface** (3–5 days)
Refactor everything 2048-specific into a single Python interface. Sketch:
```python
class GameAdapter(Protocol):
    def perceive(self, raw_input: PerceptionInput) -> GameState: ...
    def available_actions(self, state: GameState) -> list[Action]: ...
    def is_game_over(self, state: GameState) -> bool: ...
    def is_catastrophic_loss(self, state: GameState) -> bool: ...
    def render_for_prompt(self, state: GameState) -> str: ...
    def execute(self, action: Action) -> None: ...
```
Same shape supports OCR-driven (`PerceptionInput = Image`) and
SDK-driven (`PerceptionInput = StructuredGameState`).

**1.2 — Build `Nova.Studio` Unity package** (2–3 weeks)
- C# package installable via Unity Package Manager
- Hooks: `OnSessionStart`, `OnFrameDecision`, `OnGameOver`
- Local server inside Unity that bridges to Python cognitive architecture
  via WebSocket
- Sample integration: studio drops in 3 lines of C# to instrument their
  game

**1.3 — Build `LocalLLMAdapter`** (1 week)
- New `nova_agent.llm.local` adapter using vLLM's OpenAI-compatible API
- `guided_decoding` with JSON-schema constraints for ReAct path (Qwen 2.5
  14B Instruct or Phi-4 14B)
- Fallback chain: if local fails, fall back to API; if API rate-limited,
  fall back to cheaper API tier
- Configured via `build_llm` factory the same way Gemini/Anthropic are
  today

**1.4 — Wrap 2048 logic in `Game2048OcrAdapter`** (2–3 days)
Move existing OCR, BoardState, ADB swipes, game-over logic behind the
GameAdapter interface. No behavior change. Tests still pass.

**1.5 — Build `TetrisUnityAdapter`** (2–3 weeks)
Find or build a Tetris implementation in Unity, integrate via the SDK.
Build:
- Tetris-specific GameState type
- Action mapping (left/right/rotate/drop)
- Game-over detection (top row filled)
- Catastrophic-loss heuristic (lost without clearing 10 lines)
- Tetris-specific decision prompt

**1.6 — Verify cognitive architecture unchanged** (3–5 days)
Memory + affect + ToT + reflection must work without ANY code change
across (2048-OCR, 2048-Sim, Tetris-SDK) game adapters. If they don't, the
adapter abstraction is wrong and needs revision.

**1.7 — Demo recording** (2 days)
Side-by-side: Nova plays 2048 in emulator (OCR adapter) + Nova plays
Tetris in Unity (SDK adapter). Same brain panel UI, same cognitive
architecture, three different perception paths.

**Exit criteria for Phase 1:**
- Cognitive architecture code unchanged across all three adapters
- Unity SDK installable + first session running in <30 min for a developer
  who's never seen Nova
- Local LLM (Qwen 2.5 14B + vLLM `guided_decoding`) shipping zero JSON
  parse errors across 1000-call test sequence
- Hybrid inference router fully functional (System 1 local, System 2 API)
- Tetris demo recorded

---

## Phase 2 — Exploration learning + general perception (weeks 13–24)

**Goal:** Nova plays a game it's never seen before by watching the
tutorial, forming hypotheses through play, and updating its memory with
learned game rules.

This phase is the highest-risk in the roadmap. Voyager-style hypothesis-
testing works for some games, fails for others. **Honest expectations:**
turn-based puzzles, slow strategy, narrative games all work. Real-time
action and complex 3D do not. Don't promise universal coverage.

### Work units (sketch — flesh out at the time)

**2.1 — General visual perception** (2–3 weeks)
Replace per-game OCR with a vision-LLM call that identifies score, game-
state region, UI elements, game-over indicator. Gemini Flash-Lite or a
local vision model.

**2.2 — Action-space discovery** (2–3 weeks)
Nova starts a new game and tries random taps/swipes/drags to learn what
actions exist. Each trial generates "I tapped at (x,y) and the screen
changed in this way" hypotheses stored in memory.

**2.3 — Tutorial-watching pipeline** (2 weeks)
When Nova encounters a tutorial sequence (text overlay, arrow indicator),
it follows the instructions exactly while logging the cause-effect.
Seeds the game-rules memory before free play.

**2.4 — Skill induction loop** (2–3 weeks)
After exploration + tutorial, the reflection LLM consolidates trial
observations into game rules. Rules go into the semantic store. Future
decisions retrieve relevant rules.

**2.5 — Validation on 3 unseen games** (2 weeks)
Pick three games of varying genres (e.g., a simple match-3, a tower
defense, a narrative point-and-click). Run Nova on each from scratch.

**Exit criteria:**
- Nova succeeds on at least 2/3 of three pre-specified unseen games
- Demo recording: "Nova learns [game name] from scratch in 15 minutes"

---

## Phase 3 — Persona system (weeks 13–15, parallel with Phase 2)

**Goal:** turn the persona library from a doc into runtime configurations.

### Work units

**3.1 — `PersonaConfig` data model** (2 days)
Schema covering: name, AffectVector baselines, decision biases, memory
seeds, trigger thresholds, primary motivation tag.

**3.2 — Persona injection** (3 days)
- AffectState constructor takes baselines from the persona
- Decision prompt augmented with persona-specific behavior cues
- Reflection prompt augmented with persona-specific lesson framing
- Memory store seeded with the persona's pre-existing experience

**3.3 — Implement first 4 personas** (1 week)
Casual Carla, Hardcore Hana, Whale Wei, First-Time Felix. Spec from
[`personas-and-use-cases.md`](./personas-and-use-cases.md).

**3.4 — Cross-persona run harness** (3–4 days)
Run the same game session N times with N different personas. Capture all
their stream logs. Diff them.

**Exit criteria:**
- 4 personas pluggable via config
- Same game produces visibly different brain-panel arcs per persona
- Demo recording: "the same level played by 4 different personas"

---

## Phase 4 — KPI Translation Layer + Validation Report + Long-Horizon Simulation (weeks 25–32)

**Reframed scope (key change in v2):** Phase 4's lead deliverable is the
**KPI Translation Layer**, not the affect-curves dashboard. Affect curves
become drill-down evidence; KPI predictions become headline.

### Work units

**4.1 — Signature firing-rate aggregator** (1 week)
Per-session: detect Signature Alpha/Beta/Gamma/Delta firings (per
[`methodology.md`](./methodology.md) §1). Per-cohort: aggregate firing
rates, mean/median/P90/P10 of each, confidence intervals.

**4.2 — KPI Translation engine** (2 weeks)
Implement the four Signature → KPI mappings from
[`methodology.md`](./methodology.md) §2:
- Alpha → predicted abandonment rate at game position
- Beta → predicted spend trigger location + intensity
- Gamma → predicted time-on-task / flow window
- Delta → predicted D1 retention delta

Each mapping is testable; each output is footnoted to a methodology
citation.

**4.3 — A/B comparator** (1 week)
Run the same persona mix against version A and version B. Statistical diff:
Mann-Whitney U on continuous metrics, chi-square on categorical (churn
vs progression). Output: signature-firing-rate deltas with significance
levels.

**4.4 — Report rendering** (1 week)
HTML output (interactive dashboards), PDF export, CSV/JSON export.
Layout per the [`README.md`](./README.md) Core Deliverable spec.

**4.5 — Pilot deck generation** (3 days)
Combine a real Nova report (from running the architecture against a sample
game) with the validation results from Phases 0.7/0.8 + competitive
positioning. Pitch deck for the first studio conversations.

**4.6 — Long-Horizon Simulation Loop** (1–2 weeks)
Implements the Day-N retention prediction capability spec'd in
[`methodology.md`](./methodology.md) §1.6. Three concrete deliverables:

- **Simulated-time clock primitive.** New `nova_agent.lab.SimulatedClock`
  service exposed via the Unity SDK as `FastForward(timedelta)`.
  Advances the virtual game clock and Nova's internal time counter in
  lockstep. Decay functions consume the elapsed-since-last-event reading.
- **Multi-rate decay function on memory records.** Each `EpisodicRecord`
  and `SemanticRule` gains `last_decay_check_at_simulated_time`.
  Implements three-channel decay (episodic ~24h half-life, semantic
  ~7d, affective ~30d with floor) per the Tulving / Ebbinghaus / Bahrick
  / Yehuda literature anchors.
- **Cross-session state persistence.** New `PlayerState` snapshot type
  that captures `AffectVector` baselines + memory store state at
  session-end and restores them at next-session-start with decay
  applied for the elapsed simulated gap. Extends the existing
  `AffectState.reset_for_new_game()` (Task 36) to soft-reset rather
  than hard-reset.

**Cohort-distribution reporting:** every long-horizon prediction is
returned as a distribution (median, P25, P75, 95% CI) across N=50+
personas, never as a single-trajectory point estimate. The widening CI
*is* the prediction. Reports use the format: "Median 28% Day-30 churn
(95% CI [22%, 38%]), driven by accumulated affective baseline drift
over the Day 3-7 difficulty band."

**Gates this phase has to clear:**
- Phase 0.7 cliff test passed (single-session affect prediction works)
- Phase 0.8 trauma ablation passed (dual-DV primary: within-game trap
  re-engagement rate is lower with trauma-on, Cohen's `d ≥ 0.3`) —
  confirms the avoidance-learning mechanism Nova relies on for the
  "scar" effect in Day-N predictions
- Empirical CI-width check: at Day 30 in a synthetic-validation run on
  2048 with N=50 Casual personas, the 95% CI for Signature Alpha
  firing rate must stay below ±15 percentage points. If wider, the
  product framing adapts to "useful Day-N prediction up to N = [the day
  where CI crossed the threshold]" — honest framing matters more than
  the longer horizon.

**Exit criteria:**
- End-to-end: studio uploads APK (or runs SDK-integrated build) → 50
  personas → HTML report in their inbox
- One real generated report committed to the repo as canonical example
- One canonical 30-day cohort-distribution report committed as the
  long-horizon example
- Pilot deck ready

---

## Phase 5 — Production infrastructure (weeks 33–44)

**Goal:** make Nova rentable at scale. Mostly cloud engineering. Defer
until Phase 4 has produced a first paid pilot signal.

### Phase 5 hosting strategy (added 2026-05-04 per principal engineer red-team)

**Default hosting target: Modal** for serverless Python execution
(GPU and CPU), with **RunPod** as the GPU-tier fallback if Modal's
A100/H100 capacity becomes a bottleneck. Both are serverless container
platforms purpose-built for Python / AI workloads, billed per compute-
second, scaling 0 → 1000 parallel containers in seconds without an ops
team.

Why this default (vs AWS / GCP):

- A 2000-game ablation run (Phase 0.8 today, repeated per studio in
  Phase 5) needs 0 → 1000 parallel containers for ~30 minutes, then
  back to 0. AWS Lambda / GCP Cloud Run technically can do it but
  require Kubernetes / IAM / networking expertise a solo dev does not
  have time for. Modal hides every one of those concerns behind a
  Python decorator (`@app.function(gpu="A100")`).
- Modal's pricing model is pay-per-second of actual compute, not
  reserved capacity. Idle Phase 5 cost = $0; spike cost = ~$1-3 per
  ablation run at A100 prices. Matches the lumpy per-pilot demand
  shape exactly.
- Modal's image cache + cold-start optimizations are < 5s, fast
  enough that interactive studio dashboards (one-off persona runs)
  feel responsive without a permanent warm pool.

When to escalate from Modal to a managed-Kubernetes setup (EKS / GKE):

- Sustained > 1000 concurrent containers across multiple studios
- A dedicated platform engineer is on the team
- A specific compliance regime (SOC 2 Type II, HIPAA-adjacent gaming)
  requires VPC isolation Modal cannot offer

Until any of those triggers fires, Modal is the right tool — and
defaulting to it now (rather than to AWS) avoids the solo-founder
trap of "we built our infra on AWS because that's what real companies
do" and burning weeks on ops work that doesn't move the product.

An ADR captures the Modal decision + the escalation criteria + the
RunPod GPU-fallback contract before the first deployment.

### Work units (flesh out at the time)

**5.1 — Headless emulator farm OR SDK-only deployment** (3–4 weeks)
For studios with Unity SDK: no emulator needed; sessions run in
ephemeral cloud VMs. For OCR-fallback path: Android emulator running
headless. Auto-spin up per session.

**5.2 — Local LLM inference cluster** (2–3 weeks)
vLLM serving tier (cloud GPUs or owned hardware). Load-balanced across
sessions. Cost model: hourly GPU rental at low traffic, owned hardware
at high traffic.

**5.3 — Job queue + session orchestrator** (2–3 weeks)
Studio submits build + persona mix + run count. Orchestrator runs
sessions, collects logs, generates report, notifies.

**5.4 — Multi-tenant API + auth** (2 weeks)
REST + webhook. API keys per studio. Rate limiting. Quotas.

**5.5 — Billing + dashboards** (2–3 weeks)
Stripe integration. Per-session metering. Studio dashboard.

**Exit criteria:**
- One studio (paid or pilot) can self-serve a run end-to-end without
  engineering involvement
- 99% uptime over a 1-month measurement window
- Pricing model live (per-session, per-report, or subscription)

---

## Phase 6 — First paid pilots + iteration (open-ended)

**Goal:** convert architecture + product into revenue + validation
corpus.

### What goes here

- Identify 5 friendly mobile/PC studios (warm intros via game-dev Twitter,
  GDC contacts, Discord communities)
- Free or $5K pilots in exchange for testimonials + case studies + the
  30-day measurement window for validation corpus
- Each pilot: pre-arranged measurement (Nova's signature predictions vs
  studio's actual real-user data after launch). This data feeds the
  validation corpus that becomes Nova's primary moat.
- Iterate on report format based on what the buyer actually opens / acts on
- After 3 successful pilots: switch to paid tier

**Pricing models to test:**
- Per-session: $1–5
- Per-report (50 sessions): $250–500
- Subscription (unlimited within fair use): $5K–25K/year for mid-size
  studio, $50K+ for enterprise

**This phase doesn't end.** It's the rest of the company.

---

## Cross-cutting decisions

### 1. Open-source vs proprietary

**Recommendation:** open-core. The cognitive architecture (memory,
affect, ToT, reflection, brain panel) under MIT. Persona library tuning
data, KPI Translation methodology, validation corpus, hosted
infrastructure proprietary.

**Why:** open architecture attracts contributors and academic
legitimacy; proprietary data + methodology + infra is the moat. This is
the HashiCorp / GitLab / Vercel pattern.

Decide before Phase 4. Affects all marketing and code structure.

### 2. Single-provider vs multi-provider LLM

**Already decided (v2):** multi-provider hybrid. Local LLM for System 1,
frontier API for System 2. Adapter pattern in `nova_agent.llm` already
supports it. No further decision needed.

### 3. The "Nova reads our trade-secret game build" trust problem

Studios will not upload pre-launch builds to a third party without
strong NDA + data handling guarantees. Plan for:
- On-prem deployment option (Phase 5+)
- SOC 2 compliance roadmap (Phase 5+)
- Opt-in vs opt-out model-training data use (Phase 4+)

The local-LLM hybrid stack helps here: most inference happens local to the
studio's infrastructure, not on third-party cloud. Smaller IP exposure
surface.

### 4. Hiring trigger points

- **Engineer #2:** Phase 4 — when the build/test cycle for the reporting
  layer + persona system is parallelizable. Before that, a second engineer
  is more coordination cost than productivity gain.
- **Sales/BD:** when 3 pilots are live and the bottleneck is "find more
  studios" rather than "build features." Probably mid-Phase 6.

### 5. Funding decision

- **Bootstrap path:** Phases 0–4 done solo (~7 months). One paid pilot
  funds the next quarter.
- **Seed round path:** pitch after Phase 1 (Tetris demo + validation
  results) for $500K–1.5M. Compress Phases 2–5 to 4 months.

**Recommendation:** decide after Phase 1 demo. If the Tetris port goes
smoothly + Phase 0.7 cliff test passed strongly, the seed pitch is
strong. If either struggled, bootstrap and revisit at Phase 4.

---

## What NOT to do

- **Don't pivot mid-Phase-0.** The architecture demo is the foundation. Any
  refactor without v1.0.0 shipped first compounds complexity.
- **Don't sell before Phase 0.7 passes.** The cliff test is the falsification
  gate for the entire pitch. Without it, claims are theoretical. With it,
  claims are evidence-backed.
- **Don't try to support real-time games or 3D in Phase 2.** Out of scope
  for the current architecture. Promise turn-based / strategy / puzzle /
  slow live-service.
- **Don't build a marketplace.** "Studios upload APKs, gamers download
  Nova-generated playtests" is a different product. Stay focused on B2B
  studio tooling.
- **Don't over-engineer the persona library before pilot data.** 4
  personas is enough for the first pitch. More personas after studios tell
  you which segments they care most about.
- **Don't pivot to RL.** RL produces optimizers; Nova produces simulators.
  The cognitive architecture is the moat. Trading it for inference speed
  kills the product. (See [`methodology.md`](./methodology.md) §3.3 for the
  full rationale.)
- **Don't promise General Intuition-scale capabilities.** They have
  $133.7M and a 2B-clip video corpus. We have a CoALA-shaped agent with a
  publishable trauma-tagging mechanism (if Phase 0.8 validates). Different
  shape, different size, possibly complementary, but not the same kind of
  competitor.
