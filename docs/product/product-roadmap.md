# Project Nova — Product Roadmap

> **Read first:** [`README.md`](./README.md) for strategic context. This doc
> assumes you've read it.
> **Status:** Phase 0 (cognitive architecture demo) is mid-build on
> `claude/practical-swanson-4b6468`; ~2 weeks remaining on the original
> 57-task plan. Everything below this line is post-v1.0.0.
> **Audience:** the team executing the build, week-by-week.

---

## Phase overview

| Phase | What | Duration | Cumulative wall-clock | LLM-cost gate |
|---|---|---|---|---|
| 0 | Finish v1.0.0 cognitive architecture demo on 2048 | 2 weeks | week 2 | ~$50 |
| 0.5 | Lightweight validation (5 friends-and-family) + repositioning | 1 week | week 3 | $0 |
| 1 | `GameAdapter` extraction + Tetris port | 4–6 weeks | week 9 | ~$50 |
| 2 | Exploration-learning + general perception (the "drop in any game" capability) | 8–12 weeks | week 21 | ~$200 |
| 3 | Persona system (4 personas v1, 10 personas v2) | 2–3 weeks (parallel with 2) | week 21 | ~$100 |
| 4 | Reporting + A/B comparison layer | 4–6 weeks | week 27 | ~$200 |
| 5 | Production infra (headless emulator farm, multi-tenant API, billing) | 8–12 weeks | week 39 | $500–2K cloud |
| 6 | First 3 paid pilots, real-user validation, iterate | open-ended | from week 28 onward | revenue from here |

**MVP-as-product:** Phases 0–4 → ~6 months wall-clock, ~$600 in LLM credits.

**Full v1 product:** through Phase 5 → ~9 months wall-clock.

These are realistic estimates assuming one full-time engineer (you) plus
LLM/infra costs. With a second engineer, Phases 1–4 can run partially in
parallel and compress to ~5 months.

---

## Phase 0 — finish v1.0.0 (current plan, ~2 weeks remaining)

**Status:** in-flight. Don't deviate. The 57-task plan + the supplementary
work this week (thinking-stream viewer, OCR palette, Pro thinking-budget fix,
prompt-voice tightening, real timestamps + newest-on-top order) IS Phase 0.

What's left in the original plan beyond what's already shipped:
- Anthropic Sonnet for production-tier reflection (Week 5 deferred work — gated
  on you funding the API key)
- Claude Design static-state mockups (Task 41 — the visual-references doc is
  ready as input)
- OBS recording (Task 53)
- Final polish + v1.0.0 cut + demo recording

**Exit criteria for Phase 0:**
- Demo recording of nova playing 2048 end-to-end on emulator with brain panel
  rendering live
- Memory + affect + ToT + reflection all visibly active
- Game-over → reflection → semantic rule extraction loop working
- v1.0.0 git tag

**Do not** start any Phase 1+ work until Phase 0 is shipped. Half-done
foundations make every subsequent phase harder.

---

## Phase 0.5 — lightweight validation + repositioning (1 week)

**Updated 2026-05-02:** the original phase called for a $600 + 3-week
formal study (N=20 paid playtesters via PlaytestCloud). Replaced with a
~$0 + 1-week hybrid that splits formal validation across two stages.

**Goal:** get directional evidence that Nova's persona predictions track
something real about human play, without spending $600 or three weeks
upfront. Defer the rigorous validation to the first pilot, where real
users do the work for free.

### Why repositioning matters more than rigorous numbers right now

The product pitch can lean on the **cognitive-architecture-as-design-tool**
story rather than the **predictor-of-real-players** story. Buyers
(designers, UA managers, live-ops PMs) value the visible brain-panel
reasoning — they want to *see* Nova's thought process and judge
plausibility themselves, not trust a statistical correlation claim sight
unseen. The brain-panel "show your work" artifact is a stronger first
sell than r-values.

The rigorous "Nova predicts humans at r=0.X" claim becomes an enterprise-
upsell artifact later — generated from real pilot user data instead of
a paid playtest cohort.

### Stage 1 — friends & family lite (1 week, $0)

**Target N:** 5 people you know personally. Mix of "casual" (rarely plays
2048) and "experienced" (knows the game well). Friends, family, ex-
colleagues — anyone you can ask in person.

**What humans do:**
- Play 2048 once each in the emulator setup. ~10-20 minutes per session.
- Think aloud throughout (you take notes; or record audio if comfortable).
- Single self-report at the end: "what was the most frustrating moment?"

**What Nova does:**
- Plays the same fixed seeded starting positions as your humans (so
  comparison is apples-to-apples).
- Two persona runs per seed: Casual + Hardcore.

**Comparison — directional, not statistical:**
- Did Nova's `anxiety_high` crossing coincide (within ±2 moves) with the
  human's self-reported frustration moment? Count hits / 5.
- Did Nova's final score fall within ±20% of the human's? Count hits / 5.
- Did Nova's reflection lesson echo something the human said
  while thinking aloud? Subjective yes/no per session.

**Honest framing for the pitch deck:** "in our N=5 informal pilot, Nova's
Casual persona's frustration peak coincided with human frustration in
[N]/5 cases." Not statistically significant. Real evidence of directional
alignment. Sufficient for the first 5 studio conversations.

### Stage 2 — first paid (or pilot) studio is the formal validation

The first studio engagement bundles "free 30-day measurement period" into
the pilot terms. During that period:
- Run Nova predictions on the studio's pre-launch build with their persona
  mix.
- Studio launches the build to real users.
- Compare Nova predictions vs real-user metrics 30 days later.

This produces the formal r-value paper / case study **using the studio's
own real users as the validation cohort**. Free for both sides — they get
the playtesting tool, you get the validation data.

### Phase 0.5 exit criteria

- Friends & family hit-rate captured (a small markdown doc in the repo with
  the raw observations + the 3 directional metrics counted)
- Pitch deck reframed around "design tool with visible cognitive
  reasoning" rather than "statistical predictor of real players"
- First-pilot terms drafted to include the 30-day measurement window

### What changed and why

The original Phase 0.5 made the validation study a gating prerequisite
("don't sell before Phase 0.5"). That assumed enterprise sales as the
primary motion. In practice the first-pilot motion is more like
"friendly studio agrees to try the tool because the demo is compelling
and the cognitive-architecture story is novel." The validation data is
upsell ammunition for pilots #2 onwards, not a precondition for pilot #1.

---

## Phase 1 — GameAdapter extraction + Tetris port (4–6 weeks)

**Goal:** prove the cognitive architecture is game-agnostic by porting to a
second game. Tetris is the right second target — different action space
(rotate + drop vs swipe), different scoring (line clears, not tile merges),
similar visual complexity, well-known so demos resonate.

### Work units

**1.1 — Define the `GameAdapter` interface** (3–5 days)
Refactor everything 2048-specific into a single Python interface. Sketch:
```python
class GameAdapter(Protocol):
    def perceive(self, screenshot: Image) -> GameState: ...
    def available_actions(self, state: GameState) -> list[Action]: ...
    def is_game_over(self, state: GameState) -> bool: ...
    def is_catastrophic_loss(self, state: GameState) -> bool: ...
    def render_for_prompt(self, state: GameState) -> str: ...
    def execute(self, action: Action) -> None: ...
```
The cognitive architecture above the adapter (memory, affect, ToT, reflection)
becomes game-agnostic.

**1.2 — Wrap 2048 logic in `Game2048Adapter`** (2–3 days)
Move existing OCR, BoardState, ADB swipes, game-over logic behind the
interface. No behavior change. Tests still pass.

**1.3 — Build `TetrisAdapter`** (2–3 weeks)
Find a Tetris APK that runs in the same emulator. Build:
- Tetris-specific OCR (board state, score, level)
- Action mapping (left/right/rotate/drop)
- Game-over detection (top row filled or pause-screen shown)
- Catastrophic-loss heuristic (lost without clearing 10 lines, etc.)
- Tetris-specific decision prompt (mentions "rotate" + "drop" not "swipe")

**1.4 — Port the cognitive architecture above the adapter** (5–7 days)
Memory + affect + ToT + reflection must work without ANY code change against
either game. If they don't, the adapter abstraction is wrong.

**1.5 — Demo recording** (2 days)
Side-by-side: Nova plays 2048 + Nova plays Tetris. Same brain panel UI,
different game underneath. This is the "two-game proof" that opens enterprise
sales conversations.

**Exit criteria for Phase 1:**
- Cognitive architecture code unchanged between two games
- Both demos recorded
- Architecture diagram updated in design docs

---

## Phase 2 — exploration-learning + general perception (8–12 weeks)

**Goal:** Nova plays a game it's never seen before by watching the tutorial,
forming hypotheses through play, and updating its memory with learned game
rules. This is the "drop in any game" capability.

This phase is the highest-risk. Voyager-style hypothesis-testing works for
some games, fails for others. Don't promise it works on all games —
honest expectations are: turn-based puzzles, slow strategy, narrative games
all work. Real-time action and complex 3D do not.

### Work units

**2.1 — General visual perception** (2–3 weeks)
Replace per-game OCR with a Gemini/Claude vision call that identifies:
- Score field (where it is on screen, what number it shows)
- Game-state region (where the game world is)
- UI elements (buttons, menus, prompts)
- Game-over indicator (red "Game Over" text, modal overlay, etc.)
This needs prompt engineering + a small benchmark suite of game screenshots.

**2.2 — Action-space discovery** (2–3 weeks)
Nova starts a new game and tries random taps/swipes/drags to learn what
actions exist. Each trial generates a "I tapped at (x,y) and the screen
changed in this way" hypothesis. Hypotheses go into memory.

**2.3 — Tutorial-watching pipeline** (2 weeks)
When Nova encounters a tutorial sequence (text overlay, arrow indicator),
it follows the instructions exactly while logging the cause-effect. This
seeds the game-rules memory before free play begins.

**2.4 — Skill induction loop** (2–3 weeks)
After exploration + tutorial, Nova has a memory full of "when X happened, Y
followed" observations. The reflection LLM consolidates these into game
rules: "tapping a colored tile next to two same-color tiles makes them
merge." Rules go into the semantic store. Future decisions retrieve relevant
rules.

**2.5 — Validation: drop in 3 unseen games** (2 weeks)
Pick three games of varying genres (e.g., a match-3, a tower defense, a
narrative point-and-click). Run Nova on each from scratch. Measure:
- Time-to-first-meaningful-action (how long until Nova does something the
  game responds to)
- Time-to-tutorial-complete
- Time-to-first-progression-event (level cleared, score above zero, etc.)
- Reflection lessons after 30 minutes of play

**Exit criteria for Phase 2:**
- Nova succeeds on at least 2/3 of three pre-specified unseen games
- Demo recording: "Nova learns [game name] from scratch in 15 minutes"

---

## Phase 3 — persona system (2–3 weeks, can run parallel with Phase 2)

**Goal:** turn the persona library from a doc into runtime configurations.

### Work units

**3.1 — `PersonaConfig` data model** (2 days)
Schema covering: name, AffectVector baselines, decision biases (risk
tolerance, exploration weight, time-pressure tolerance), memory seeds,
trigger thresholds, primary motivation (Bartle/Yee category).

**3.2 — Persona injection into the architecture** (3 days)
- AffectState constructor takes baselines from the persona
- Decision prompt augmented with "you tend to [persona-specific behavior]"
- Reflection prompt augmented with "as a [persona type], the lesson here is..."
- Memory store seeded with the persona's pre-existing experience (or empty
  for first-time players)

**3.3 — Implement the first 4 personas** (1 week)
- Casual Carla
- Hardcore Hana
- Whale Wei
- Returning Rishi
Spec from [`personas-and-use-cases.md`](./personas-and-use-cases.md).

**3.4 — Cross-persona run harness** (3–4 days)
Run the same game session N times with N different personas. Capture all
their stream logs. Diff them: where did Casual hit anxiety_high while
Hardcore stayed flat? This is the input to the reporting layer (Phase 4).

**Exit criteria for Phase 3:**
- 4 personas pluggable via config
- Same game produces visibly different brain-panel arcs per persona
- Demo recording: "the same level played by 4 different personas"

---

## Phase 4 — reporting + A/B comparison layer (4–6 weeks)

**Goal:** turn raw stream logs into insights studios pay for.

### Work units

**4.1 — Aggregate metrics** (1 week)
Per-session: time to game-over, peak affect values, ToT trigger count,
trauma trigger count, score curve, most-cited reflection lesson. Per-cohort
(N sessions of same persona): mean / median / P90 of each metric.

**4.2 — Insight generation via LLM** (1–2 weeks)
Take the aggregate metrics + selected stream excerpts and prompt an LLM to
generate the studio-facing report:
> "Of 50 Casual personas: peak frustration occurred at minute 4.2 (mean),
> typically in the gold-tier paywall encounter. 28% of sessions ended in
> churn-equivalent behavior (no progression for 5 minutes followed by
> game-over). Top reflection lesson across sessions: 'I shouldn't have
> wasted gold on the dragon.'"

**4.3 — A/B comparator** (1 week)
Run the same persona mix against version A and version B. Statistical diff:
Mann-Whitney U on continuous metrics, chi-square on categorical (churn
vs progression). Output: "Version B shows significantly lower frustration
peak (p < 0.05) but no significant difference in completion rate."

**4.4 — Report rendering** (1 week)
HTML output (interactive dashboards), PDF export (for clients who want a
shareable artifact). Charts: affect curves over time per persona; cohort
funnel visualization; reflection lesson word cloud.

**4.5 — Pilot deck** (3 days)
Combine a real Nova report (from running the architecture against your own
demo game) with the validation-study data + competitive positioning. This
is the deck for the first studio pitch.

**Exit criteria for Phase 4:**
- End-to-end: studio uploads APK → 50 personas run → HTML report in their
  inbox
- One real generated report committed to the repo as the canonical example
- Pilot deck ready

---

## Phase 5 — production infrastructure (8–12 weeks)

**Goal:** make Nova rentable at scale. Not creative work; mostly cloud
engineering. Defer until Phase 4 has produced a first paid pilot signal.

### Work units (sketch — flesh out at the time)

**5.1 — Headless emulator farm** (3–4 weeks)
Android emulator running headless on cloud GPUs (or CPU instances if
emulation is fast enough). Auto-spin up per session. Scaledown when idle.

**5.2 — Job queue + session orchestrator** (2–3 weeks)
Studio submits APK + persona mix + run count. Orchestrator: spin up
emulators, install APK, run sessions, collect logs, generate report,
notify.

**5.3 — Multi-tenant API + auth** (2 weeks)
REST or webhook API. API keys per studio. Rate limiting. Quotas.

**5.4 — Billing + dashboards** (2–3 weeks)
Stripe integration. Per-session metering. Studio dashboard showing recent
runs, costs, reports.

**Exit criteria for Phase 5:**
- One studio (paid or pilot) can self-serve a run end-to-end without
  engineering involvement
- 99% uptime over a 1-month measurement window
- Pricing model decided + live (per-session, per-report, or subscription)

---

## Phase 6 — first paid pilots + iteration (open-ended)

**Goal:** convert architecture + product into revenue + validation data.

### What goes here

- Identify 5 friendly mobile studios (warm intros via Twitter game-dev
  network, GDC contacts, etc.)
- Free or $5K pilots in exchange for testimonials + case studies
- Each pilot: pre-arranged measurement (Nova's predictions vs the studio's
  actual real-player data after launch). This data feeds back into the
  validation moat.
- Iterate on report format based on what the buyer actually opens / acts on
- After 3 successful pilots: switch to paid tier. Pricing models to test:
  - Per-session: $1–5
  - Per-report (50 sessions): $250–500
  - Subscription (unlimited within fair-use): $5K–25K/year per studio

**This phase doesn't end.** It's the rest of the company.

---

## Cross-cutting decisions to make early

These don't fit into a single phase but matter throughout.

### 1. Open-source vs proprietary

The cognitive architecture is novel. There's an argument for open-sourcing
the core (build mindshare, attract contributors, become the standard) and
selling the production hosting + persona library + reporting as
proprietary. Counter-argument: open-source attracts copies that undercut
pricing.

**Recommendation:** open-source the architecture (memory, affect, ToT,
reflection, brain panel) under MIT. Keep the persona library, reporting
LLM prompts, and validation data proprietary. This is the "open core"
model that worked for HashiCorp, GitLab, etc.

Decide before Phase 4 — affects all marketing and code structure.

### 2. Single LLM provider vs multi-provider

Today: dependent on Gemini (paid quota). Tomorrow: should support Anthropic
+ OpenAI + local models for studios with provider preferences (or banned
LLMs for IP reasons).

**Recommendation:** keep the LLM adapter pattern (already in place via
`build_llm`). Add OpenAI adapter in Phase 1. Add a local-LLM adapter (Ollama
or vLLM) in Phase 5 — some studios will refuse cloud LLM calls on their
unreleased games.

### 3. The "Nova reads our trade-secret game build" trust problem

Studios will not upload pre-launch builds to a third party without strong
NDA + data handling guarantees. Plan for:
- On-prem deployment option (probably Phase 5+)
- SOC 2 compliance roadmap (Phase 5+)
- Opt-in vs opt-out training data use (Phase 4+)

### 4. Hiring trigger points

When do you hire a second engineer? Roughly Phase 4 — when the build/test
cycle for the reporting layer + persona system is parallelizable. Before
that, a second engineer is more coordination cost than productivity gain.

When do you hire a sales/BD person? When 3 pilots are live and the bottleneck
is "find more studios" rather than "build features." Probably mid-Phase 6.

### 5. Funding decision

Bootstrap path: Phases 0–4 done solo (~7 months). One paid pilot funds the
next quarter. Slow but founder-controlled.

Seed round path: pitch after Phase 1 (Tetris demo + validation study) for
$500K–1.5M. Hire 2–3 engineers, compress Phases 2–5 to 4 months. Raise on
"category-defining cognitive playtesting platform with [validation study
results] and [N] studio pilots committed."

**Recommendation:** decide after Phase 1 demo. If the Tetris port goes
smoothly + validation correlates well, the seed pitch is strong. If either
struggles, bootstrap and revisit.

---

## What NOT to do

- **Don't pivot mid-Phase-0.** The architecture demo is the foundation. Any
  refactor without v1.0.0 shipped first will compound complexity.
- **Don't sell before Phase 0.5.** Without validation data the pitch is
  speculative — first impressions matter, the first 5 conversations should
  be after you can show the r-value chart.
- **Don't try to support real-time or 3D games in Phase 2.** Out of scope
  for the current architecture. Promise turn-based / strategy / puzzle.
- **Don't build a marketplace.** "Studios upload APKs, gamers download
  Nova-generated playtests" is a different product. Stay focused on B2B
  studio tooling.
- **Don't over-engineer the persona library before pilot data.** 4
  personas is enough for the first pitch. More personas after studios tell
  you which segments they care most about.
