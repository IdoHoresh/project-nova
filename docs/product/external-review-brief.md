# Project Nova — External Review Briefing

> **[UPDATE 2026-05-02 PM] — Architecture and roadmap pivoted following
> external review.** The brief below preserves the pre-pivot framing as
> a record of how Nova was originally pitched. Current ground truth
> diverges in several material ways:
>
> - **Category:** Nova is now positioned as a **product-decision tool**
>   (buyer: Product Director / Live Ops Director), not an
>   adjacent-to-QA tool. The QA framing was abandoned because it would
>   have put Nova in head-on competition with modl.ai on their home turf
>   while losing access to product/live-ops budgets.
> - **Predictive primitive:** moved from 1:1 affect → KPI mappings to
>   four named **State-Transition Signatures** (Alpha/Churn,
>   Beta/Conversion, Gamma/Engagement, Delta/Bounce) defined as
>   compositional state-machine patterns. Scientifically more
>   defensible; harder for competitors to clone trivially.
> - **Brain Panel role:** repositioned from "killer demo / the product"
>   to "Cognitive Audit Trace" — a transparency/explainability layer
>   under the actual product, which is the **KPI Validation Report**.
> - **Validation approach:** original $600 + 3-week paid-playtester
>   study replaced with a $0 + 1-week Python-simulator cliff test
>   against documented hard 2048 scenarios (Phase 0.7), plus a
>   statistical trauma ablation using Levene's Test for variance
>   reduction (Phase 0.8).
> - **Inference architecture:** moved from API-only to a **hybrid
>   local + API stack** mirroring Kahneman's System 1 / System 2
>   cognition — 14B-class local model (Qwen 2.5 14B or Phi-4 14B via
>   vLLM with `guided_decoding`) for routine ReAct decisions; frontier
>   API (Claude Haiku/Sonnet) for ToT branches and post-game
>   reflection. ~95% of inference moves local.
> - **Phase 1 reorder:** Unity SDK + GameAdapter abstraction is now the
>   Phase 1 lead deliverable (was: GameAdapter + Tetris port; SDK was
>   in Phase 5). Tetris port becomes a *test* of the abstraction.
> - **Phase 4 reframe:** "KPI Translation Layer + Validation Report"
>   becomes the lead deliverable (was: "Reporting + A/B comparison
>   layer"). Affect curves become drill-down evidence; KPI predictions
>   become headline.
>
> **For current ground truth, read in this order:**
> 1. [`README.md`](./README.md) — strategic positioning and category
>    framing
> 2. [`methodology.md`](./methodology.md) — the four Signatures, KPI
>    translations, hybrid inference architecture, Levene's Test math,
>    full validation methodology
> 3. [`product-roadmap.md`](./product-roadmap.md) — phased build plan
>    with the 30-day validation sprint detailed week by week
>
> The sections below are the original briefing — preserved for
> historical context and as a record of how the pitch evolved through
> external red-team review. Section content describing 1:1 affect → KPI
> mappings, brain-panel-as-product, and the original Phase 0.5 paid
> validation study has been **superseded** by the current docs.

---

> **What this document is:** a self-contained briefing on Project Nova
> intended for an external reviewer (advisor, investor, technical critic,
> or another LLM playing critic). It covers the idea, the technology,
> the science, the product evolution, the market, the persona library,
> the use cases, the competitive landscape, the roadmap, the strengths,
> the weaknesses, and the open questions.
>
> **What I want from you:** a complete, brutally honest review. I don't
> need flattery; I need the things I'm getting wrong, the assumptions I'm
> not stress-testing, the technical risks I'm underweighting, and the
> market positioning I'm missing. The closing section ("Reviewer prompt")
> tells you exactly what kind of review I'm asking for.
>
> **Reading this doc cold should take 25–30 minutes.** If you're skimming,
> read sections 1, 2, 9, 10, 11, and 13.
>
> **Date:** 2026-05-02. **Author:** Ido Horesh (with cognitive-architecture
> implementation help from Claude Code). **Status of the underlying tech:**
> v1.0.0 demo is mid-build on `claude/practical-swanson-4b6468`; the
> cognitive architecture (memory, affect, deliberation, reflection,
> brain-panel viewer) is shipped and functional on the 2048 task as of
> tonight. The product layer (multi-game, persona-based, reporting) is the
> roadmap, not the current state.

---

## 1. Executive summary

Project Nova is a brain-inspired LLM agent that plays games end-to-end with
a cognitive architecture that includes:

- **Memory** — episodic + semantic, vector-retrieved from prior sessions
- **Affect** — a 6-dimensional emotion vector (valence, arousal, dopamine,
  frustration, anxiety, confidence) updated per move with reward-prediction-
  error dynamics borrowed from neuroscience
- **Deliberation** — fast-thinking ReAct decisions for routine moves; Tree-
  of-Thoughts deliberation when the arbiter detects high-stakes situations
  (board density + anxiety crossing 0.6)
- **Reflection** — post-game LLM extracts semantic rules from catastrophic
  losses, persisted for future sessions
- **Trauma** — memories from catastrophic losses get extra retrieval weight,
  biasing future decisions away from situations that previously failed
- **Brain panel viewer** — a live, three-column React app that renders the
  agent's internal state: cognitive thought stream (first-person reasoning
  + ToT branches when deliberating), affect dials, mood radar, dopamine
  bar, retrieved memories, mode badge

The current implementation plays 2048 in an Android emulator on a Pixel 6
AVD. The architecture works end-to-end: the agent decides, swipes via ADB
keyevents, perceives the resulting board via OCR, updates affect based on
score-delta-vs-prediction, writes the move to memory, retrieves relevant
past memories on the next decision cycle, deliberates harder when the board
gets tight, and after game-over runs a reflection LLM that extracts a
"lesson" stored as a semantic rule.

**The product evolution** is into a **synthetic playtesting service** for
game studios. Studios upload a game build; pick a mix of player personas
(Casual, Hardcore, Whale, Returning Lapsed, etc.); receive a report that
shows how each persona segment emotionally arc'd through the game — where
they got stuck, where they hit frustration peaks, where they would have
quit, what they "reflected" about the experience afterward. The deliverable
is a synthetic-player simulation report that lets studios catch retention
problems and economy-balance issues before exposing real users.

**Market signal:** Square Enix has publicly committed to 70% of QA via
genAI by end-2027 (with an open partnership at University of Tokyo).
General Intuition raised $133.7M in Oct 2025 on a video-game-clips corpus.
Razer is shipping AI playtesting on AWS Marketplace through their hardware
distribution. Mobile retention has *worsened* into 2025 (top-quartile D1
26.5%, GameAnalytics) — studios' pain is growing and their willingness to
pay for retention-protecting tools is rising.

**Differentiation:** the existing competitors (modl.ai, Razer Cortex's
hybrid, the academic agents like Voyager and SIMA) focus on bug-finding,
coverage automation, or general game-playing competence. **None ships
persona-based introspective affect reporting**. Nova's brain-panel UI as a
"show your work" artifact + a curated persona library + cognitive science
citations is the unique combination.

**Realistic timeline from today:** MVP-as-product in ~6 months, polished v1
in ~9 months, on a single-engineer build pace.

---

## 2. The two products

### 2.1 The demo (current state)

A working LLM agent that plays 2048 with everything described in section 1.
Code lives in two repositories' worth of project structure on
`claude/practical-swanson-4b6468`:

- `nova-agent/` — Python agent (Gemini Flash for decisions, Gemini Pro for
  ToT deliberation, Anthropic Sonnet planned for production-tier
  reflection). 140 passing tests, mypy strict, ruff clean.
- `nova-viewer/` — Next.js 16 + React 19 + Tailwind 4 brain panel. 47
  passing component + unit tests. Live WebSocket connection to the agent's
  event bus.
- `nova-game/` — Forked Unity 2048 (`com.idohoresh.nova2048`) running on a
  Pixel 6 API 34 AVD via Android Studio.

The demo is the foundation for the product. Every component (memory store,
affect vector, ToT decider, reflection pipeline, brain-panel viewer) is
designed to be game-agnostic above the perception/action interface; the
2048-specific bits (BoardOCR, ADB swipe keyevents, BoardState type) are
deliberately localized so they can be replaced behind a `GameAdapter`
interface in Phase 1 of the product roadmap.

### 2.2 The product (synthetic playtesting service)

The same architecture, scaled across:

- **Multiple games** — adapter per game family in early phases; LLM-driven
  exploration learning for the "drop in any game" capability later
- **Multiple personas in parallel** — same game played by 50 simulated
  Casuals + 50 Hardcores + 20 Whales, with statistical aggregation of
  outcomes per cohort
- **Reporting layer** — raw stream logs become studio-facing insights
  ("47% of Casual personas churned at the level-3 paywall; peak frustration
  at minute 4; top reflection lesson: 'this dragon is impossible without
  spending'")
- **A/B comparison** — same persona mix against version A and version B
  of the same game; statistical diff (Mann-Whitney U on continuous metrics,
  chi-square on categorical) outputs effect sizes per cohort

The deliverable: a one-page-summary + drill-down dashboard that a UA
manager, live-ops PM, or game designer can consume in 10 minutes and act
on.

---

## 3. Technology stack and cognitive architecture

### 3.1 Architecture overview (the cognitive layer)

Inspired by **CoALA — Cognitive Architectures for Language Agents** (Sumers
et al., 2024, TMLR). Nova is a CoALA-shaped agent with the following
modules wired together via an asynchronous event bus:

```
┌──────────────────────────────────────────────────────────────┐
│ PERCEPTION                                                   │
│ Capture screenshot → OCR → BoardState (grid+score)           │
└──────────────┬──────────────────────────────────┬────────────┘
               │                                  │
               ▼                                  ▼
┌─────────────────────┐                  ┌────────────────────┐
│ MEMORY              │                  │ AFFECT             │
│ Episodic store      │                  │ Vector with 6 dims │
│ (SQLite + LanceDB)  │                  │ Updated per move   │
│ Semantic store      │                  │ via RPE dynamics   │
│ (post-game lessons) │                  │ Trauma flag        │
└──────────┬──────────┘                  └─────────┬──────────┘
           │                                       │
           │  retrieved memories       affect_text │
           │                                       │
           ▼                                       ▼
┌──────────────────────────────────────────────────────────────┐
│ ARBITER                                                      │
│ Routine board → ReAct (Gemini Flash, fast)                   │
│ Tight board + anxiety > 0.6 → Tree-of-Thoughts (Gemini Pro)  │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼ Decision (action + reasoning + confidence)
┌──────────────────────────────────────────────────────────────┐
│ ACTION                                                       │
│ ADB keyevent → emulator → next perception                    │
└──────────────────────────────────────────────────────────────┘

Game-over signal triggers:
┌──────────────────────────────────────────────────────────────┐
│ REFLECTION                                                   │
│ LLM (Anthropic Sonnet) examines memory of the failed game,   │
│ extracts a one-sentence lesson, persists to semantic store.  │
│ Trauma-tagged memories get extra retrieval weight next game. │
└──────────────────────────────────────────────────────────────┘
```

All internal events go through a typed WebSocket bus
(`perception`, `decision`, `affect`, `mode`, `tot_branch`, `tot_selected`,
`memory_retrieved`, `trauma_active`, `game_over`). The brain-panel viewer
subscribes to the bus and renders the agent's internal state in real time.

### 3.2 Technology stack

**Agent (Python):**
- Python 3.11+ (uv-managed venv on 3.14 in practice)
- pydantic + pydantic-settings (typed config, strict mode)
- google-genai SDK (Gemini Flash for decisions, Gemini Pro for ToT)
- anthropic SDK (Claude Sonnet for reflection in production tier)
- LanceDB (vector store for semantic memory)
- SQLite (episodic store)
- opencv-python-headless + pytesseract (OCR pipeline)
- fastapi + websockets (event bus)
- structlog + tenacity (logging + retries)
- 140 passing tests; mypy strict + ruff clean

**Viewer (TypeScript):**
- Next.js 16.2.4 + React 19.2.4 + Tailwind 4
- Framer Motion (animations)
- Native WebSocket client (no extra deps)
- vitest + React Testing Library + jsdom (47 passing tests)

**Game environment:**
- Pixel 6 API 34 Android Virtual Device (Android Studio)
- Forked Unity 2048 (`com.idohoresh.nova2048`)
- ADB for input + screen capture (uses keyevents because the Unity fork
  ignores `adb shell input swipe` — quirk of the fork)
- scrcpy for visual mirroring during demos

**LLM choices and why:**
- **Decisions: Gemini 2.5 Flash with `thinking_budget=0`** — disabling
  Pro's hidden thinking is critical because it would otherwise consume
  the entire output budget, leaving zero tokens for the visible JSON.
  Cheap, fast, ~$0.0004/move.
- **Deliberation (ToT): Gemini 2.5 Pro with `thinking_budget=1024`** — Pro
  rejects `thinking_budget=0`; 1024 caps thinking at 1024 tokens leaving
  ~2000 of the 3000 max for output. Without this cap Pro silently produced
  empty branches that crashed the ToT decider with "no valid candidates"
  every time. (Currently overridden to Flash in `.env` due to Pro's 1000
  RPD daily quota cap on the paid tier — recoverable when scaling.)
- **Reflection: Claude Sonnet 4.6 (planned)** — postmortem narration
  benefits from Anthropic's instruction-following + longer context.

### 3.3 Component deep-dive: affect system

The 6-dimensional affect vector:

| Dimension | Range | Updated by | Used for |
|-----------|-------|------------|----------|
| **valence** | [-1, 1] | RPE-weighted score-delta | Mood gauge X-axis; biases reflection toward positive/negative framing |
| **arousal** | [0, 1] | Per-move event energy | Mood gauge Y-axis; arbiter ToT trigger |
| **dopamine** | [0, 1] | Reward-prediction-error (Schultz et al.) | Dopamine bar; threshold-crossing event in stream |
| **frustration** | [0, 1] | No-progress moves accumulator | Stream affect-crossing event |
| **anxiety** | [0, 1] | Board-jeopardy heuristic + recent setbacks | Arbiter ToT trigger threshold (>0.6) |
| **confidence** | [0, 1] | Recent decision outcomes | Tunes ToT branch temperature |

The mood gauge in the brain panel renders **Russell's circumplex model of
affect** literally — valence on X, arousal on Y. The dopamine bar renders
the RPE-driven reward signal. Trauma flag triggers a soft red wash on
trauma-tagged stream entries.

### 3.4 Component deep-dive: memory system

**Episodic store (SQLite + LanceDB):**
- Per-move record: `move_idx`, `board_before`, `board_after`, `action`,
  `score_delta`, `rpe`, `importance` (1-10), `source_reasoning`,
  `affect_snapshot`, `tags` (including `aversive` for trauma)
- LanceDB stores embeddings for vector retrieval by board similarity
- Retrieval per move: top-k similar past situations, with aversive entries
  given extra weight (max-1 surfaced cap by `aversive_weight × relevance`)

**Semantic store (SQLite, separate db):**
- Post-game reflection extracts a one-sentence rule with citations to the
  episodes that triggered the lesson
- Rules persist forever; retrieved alongside episodes if relevant

**Trauma mechanism (the unusual one):**
- Catastrophic loss detection at game-over (low score, no high-tile, board
  filled too quickly)
- All memory records from the precondition window get tagged `aversive`
  with weight 1.0
- Aversive weight halves on each non-aversive retrieval (exposure
  extinction); records with weight < 0.02 become "inert" and stop
  surfacing
- This biases future decisions away from situations that previously failed
  — implementing avoidance learning in the cognitive layer

### 3.5 Component deep-dive: deliberation arbiter

The arbiter routes each decision to one of two paths:

**ReAct (fast):** Gemini Flash, single call, structured JSON output
(observation + reasoning + action + confidence). ~$0.0004/move, ~1-2s
latency.

**Tree-of-Thoughts (slow, deliberate):** Triggered when:
- `anxiety > 0.6` AND
- (`max_tile >= 256` OR `empty_cells <= 3`)

Spawns 4 parallel evaluation branches (one per swipe direction), each on
Gemini Pro. Each branch independently scores its candidate move 0-1.
Highest scorer wins; the branches and their values stream to the brain
panel as a `tot_block` entry with the winner highlighted. ~$0.005/move,
~4-6s latency. Used for ~5-15% of moves in a typical game.

### 3.6 Component deep-dive: reflection pipeline

Triggered on game-over. The reflection LLM examines:
- The full episode history of the failed game
- The catastrophic-loss flag + game-over board state
- The last few aversive memories from prior games

And outputs a structured response:
```json
{
  "summary": "Lost on move 73 with max tile 128. Trapped 16 in corner.",
  "lessons": ["Avoid pushing high tiles into corners early."],
  "trauma_triggers": ["Score collapse from 800 to game-over in 3 moves"]
}
```

Lessons go into the semantic store. Trauma triggers refine the catastrophic-
loss detector for future games.

### 3.7 Component deep-dive: brain-panel viewer (the demo's killer feature)

A three-column React app rendering Nova's internal state in real time:

- **Left column** — game stream placeholder (production: embed scrcpy or
  an MJPEG stream; current: text instructions)
- **Middle column ("Cognition · Stream")** — the **thinking stream**: a
  newest-on-top, chronologically-ordered, type-coded feed of every
  meaningful event (decisions in first-person voice, mode flips, ToT
  deliberations with branches and winner, affect crossings tagged with
  "MOOD" chip, recalled memories, trauma triggers, game-over with extracted
  lesson). Sticky-top auto-scroll. "Jump to live" floating chip when the
  user scrolls down. Subtle 320ms fade-in on new entries; soft red wash on
  trauma entries.
- **Right column ("Brain State")** — the affect dashboard: the affect
  narrative text (e.g., "You feel anxious. The board is tight."), Russell
  mood radar (valence × arousal with the current point), dopamine bar
  (cyan fill height = current dopamine level), retrieved memories list,
  footer telemetry (Score / Move / Games / Best).

This panel **is** the product's core trust artifact. Buyers don't need to
trust a black-box prediction; they can watch Nova think and judge the
plausibility themselves. The first-person internal-monologue voice ("Merge
the 2s. Clear some space. Try to build on the right.") is what makes the
agent feel like a player rather than a chess engine. Achieved via prompt
engineering (system prompt asks for "5-15 word fragments, like you're
thinking to yourself") with example phrases that anchor the voice.

---

## 4. Scientific foundations

The full citation index (41 papers) lives in
`docs/product/scientific-foundations.md`. The most load-bearing for the
pitch:

### 4.1 LLM-driven agent architecture

- **CoALA: Cognitive Architectures for Language Agents** (Sumers et al.,
  2024, TMLR) — gives Nova an architectural box to sit in; connects to
  ACT-R/Soar lineage and modern LLM agents simultaneously.
- **Voyager: An Open-Ended Embodied Agent with Large Language Models**
  (Wang et al., NVIDIA, 2023) — the prototype for LLM-driven game-playing
  via memory + skill induction.
- **Generative Agents: Interactive Simulacra of Human Behavior** (Park et
  al., Stanford, 2023) — Nova's architecture blueprint at the cognitive
  layer; pioneered LLM agents with reflection + retrieval-augmented memory.
- **Tree of Thoughts** (Yao et al., 2023) and **ReAct** (Yao et al., 2022)
  — Nova's deliberation arbiter implements both patterns.
- **Reflexion: Language Agents with Verbal Reinforcement Learning** (Shinn
  et al., 2023) — Nova's post-game reflection borrows from this lineage.

### 4.2 Affect modeling (the part that's actually science, not vibes)

- **Russell, J.A. (1980). "A circumplex model of affect."** *J. Personality
  and Social Psychology*, 39(6), 1161-1178. ~40 years of replication. The
  mood gauge in the brain panel renders this model literally.
- **Schultz, Dayan, Montague (1997). "A neural substrate of prediction and
  reward."** *Science*, 275(5306), 1593-1599. Justifies Nova's "we model
  dopamine" framing as literal reward-prediction-error rather than vibes.
- **Csikszentmihalyi's Flow** — engagement framework; informs the
  arbiter's "switch to deliberation under stress" boundary.

### 4.3 Player modeling

- **Bartle's Player Types** (1996) — Achievers / Explorers / Socializers /
  Killers — anchors the persona library at a high level.
- **Quantic Foundry's 12 Motivations** (Yee, ongoing empirical work) —
  more fine-grained, empirically-grounded motivation model. Each persona
  in the library is anchored to one or two of these motivations.
- **EA SEED's "Augmenting Automated Game Testing with Deep Reinforcement
  Learning"** (Bergdahl et al., 2020) — the strongest existing-industry
  citation for AI playtesting; deep-RL not LLM-cognitive, so distinct from
  Nova's approach.

### 4.4 What's genuinely novel about Nova

The combination of:

- **Trauma tagging as implemented** — no published paper combines an LLM
  agent + episodic store + explicit aversive tagging + elevated retrieval
  weight + LLM-narrated trauma memory. Closest cousins (McGaugh on amygdala-
  modulated memory, prioritized experience replay in RL, fear conditioning
  in animal cognition) are conceptual analogues, not implementations. This
  is publishable as an engineering contribution.
- **Affect-conditioned policy in LLM agents** — most LLM-agent papers omit
  affect entirely or treat it as flavor text. Nova treats valence/arousal/
  dopamine as first-class signals that bias retrieval (aversive weight
  modulation) and arbiter routing (anxiety-triggered ToT). No academic
  comparison exists yet.
- **"Cognitive playtesting" as a product category** — there isn't a peer-
  reviewed literature on synthetic playtesting that reports introspective
  affect curves. Nova can define the category.

---

## 5. Persona library

Full library (12 personas) lives in `docs/product/personas-and-use-cases.md`.
Each persona maps to a specific AffectVector configuration + decision biases
+ memory seeds + motivation tag (Bartle/Yee citation).

| Persona | Primary motivation | Affect baseline highlight | Trigger threshold |
|---------|-------------------|----------------------------|---------------------|
| **Casual Carla** | Completionist, escapism | Low arousal, moderate confidence | Quits at 5+ minutes stuck |
| **Hardcore Hana** | Mastery, achievement | High arousal, high confidence, low frustration ceiling | Plays through trauma; doesn't quit until objectively defeated |
| **Whale Wei** | Power, status, social | Variable; high spend tolerance | Spends to bypass frustration peaks |
| **Returning Rishi** | Nostalgia, social | Memory pre-seeded with old version | Confused by changes; high quit risk if onboarding doesn't acknowledge |
| **First-Time Felix** | Discovery, curiosity | Empty memory; slow decisions; tutorial-dependent | Quits if tutorial confuses |
| **Speedrunner Sam** | Mastery, time-attack | Optimizer; pre-seeded with strategies | Frustrated by RNG, not by difficulty |
| **Social Sasha** | Connection, sharing | Cares about scores worth bragging about | Quits if outcomes feel unsharable |
| **Killer Kai** (Bartle's Killer) | Domination of others | Aggressive, exploitative | Drops single-player content fast |
| **Casual Curious Carlos** | Mid-engagement explorer | Tries everything once | Bored by repetition |
| **Achievement Hunter Aiko** | Completion of objectives | Methodical | Gives up if completion criteria unclear |
| **Accessibility Anya** *(specialty)* | Equal access | Various impairment profiles | Cannot progress past inaccessible UI |
| **Returning Lapsed Rae** *(specialty)* | Re-engagement | Faded memory of mechanics | Quits if re-onboarding is missing |

The persona library is one of three competitive moats (alongside validation
data accumulated over time, and the cognitive-architecture-as-shown-on-
brain-panel story).

---

## 6. Use case catalog

Full catalog (10 use cases with industry data) in
`docs/product/personas-and-use-cases.md`. Top three by revenue potential:

### 6.1 Tutorial / FTUE validation (the wedge)

**Pain:** mobile games' median D1 retention is 26.5–27.7% (top quartile,
GameAnalytics 2025) and *worsening*. Studios spend $5K–50K on UA per
launch; a 5% improvement in D1 from fixing a tutorial cliff is millions in
LTV. Today's process: human playtesters via PlaytestCloud ($30–80/test,
24-48h turnaround, N≤5 in early stages) + Firebase funnel analysis after
launch. Both are too slow for iteration.

**Nova solution:** 50 Casual + 50 First-Time + 20 Returning personas run
the FTUE in parallel overnight. Report: where each cohort hit anxiety
peaks, how many failed each tutorial step, what they "thought" while stuck.

**Buyer:** UA Manager or Live Ops PM at a mobile studio.

**Pricing target:** $250–500 per FTUE-test report; $5K–25K/year subscription
for studios doing weekly content drops.

### 6.2 Live-ops content validation

**Pain:** gacha/live-service studios ship weekly content. QA cycles are 2–
3 days per drop; bugs that ship cost real revenue and player goodwill.

**Nova solution:** overnight runs of N personas through the new content;
report by morning. Catches difficulty curves, economy imbalances, and
narrative pacing issues before live deployment.

**Buyer:** Live Ops Director.

**Pricing:** subscription tier — recurring weekly value justifies $10K–
50K/year contracts.

### 6.3 A/B test pre-screening

**Pain:** mobile A/B tests need 2–4 weeks of real users (10K+ for stat
sig). Bad variants get exposed to real players + cost goodwill.

**Nova solution:** 50 personas through variant A vs 50 through variant B,
1-hour turnaround, statistical comparison output. Filter the bad variants
out before exposing to real users.

**Buyer:** Product Manager / Data Scientist.

**Pricing:** per-comparison ($500–2K) or subscription.

Other catalogued use cases: difficulty-curve verification, economy balance
testing, accessibility QA (with EU EAA 2025 regulatory tailwind),
localization sanity checks, soft-launch synthetic preview, competitive
teardown (gray-zone, pitch carefully), live-ops change rehearsal,
narrative pacing review.

---

## 7. Competitive landscape

Full breakdown (12 sections, source-cited) in
`docs/product/competitive-landscape.md`. Key actors:

### 7.1 Direct competitors

- **modl.ai** (Copenhagen) — most direct competitor. Products: Test, Play,
  Create. Customer roster thin in public data (Riot is the only confirmed
  name). Approach: RL-based bug-finding + coverage automation. **Nova
  differentiation:** persona-based introspective affect reporting; brain-
  panel as trust artifact; LLM-cognitive architecture vs RL-coverage focus.
- **Razer Cortex AI Playtest + Razer QA Co-AI** — hybrid AI+human via
  Razer's ~55M MAU hardware ecosystem (player-recruitment funnel) +
  AWS Marketplace listing for Bedrock-based QA agent. Distribution
  advantage; positioned for hybrid tests, not pure synthetic.
- **General Intuition** (Oct 2025, $133.7M seed) — wildcard. Trained on
  Medal's 2B+ video-game-clips/year corpus. Aimed at NPCs not playtesting,
  but the war chest + corpus mean they could pivot. Watch their hiring.

### 7.2 Adjacent

- **Crowd-playtesting:** PlaytestCloud, Antidote, Applause — paid human
  playtester marketplaces. Nova augments rather than replaces (10× cycle
  speed for early signals; humans for nuanced edge cases).
- **General LLM agents:** Anthropic computer use, Devin/Cognition, Adept,
  Imbue — could pivot in but lack game-specific cognitive architecture.
- **AI character platforms:** Inworld AI, Convai — adjacent, focused on
  NPC AI not synthetic players.

### 7.3 Demand-side signals

- **Square Enix** publicly committed to 70% of QA via genAI by end-2027,
  with University of Tokyo partnership (Matsuo-Iwasawa Lab). Open door
  for cognitive-architecture vendors.
- **EA, Ubisoft, Epic, miHoYo** all have internal AI-playtesting tooling
  (per secondary sources), but capability + maturity unclear.
- VC investment in game tech / AI agents continues to flow; AI playtesting
  specifically is under-funded relative to the apparent market.

### 7.4 Where Nova fits

The white space: **synthetic playtesting that reports introspective affect
curves and persona-specific narrative reflections.** Nobody ships this
today. Nova is the only one with a working cognitive architecture demo
that could be extended into this category in 6 months.

---

## 8. Roadmap (summary; full detail in `product-roadmap.md`)

| Phase | What | Duration | LLM cost gate |
|-------|------|----------|----------------|
| 0 | Finish v1.0.0 cognitive architecture demo on 2048 | 2 weeks | ~$50 |
| 0.5 | Lightweight validation (5 friends-and-family) + repositioning | 1 week | $0 |
| 1 | `GameAdapter` extraction + Tetris port | 4–6 weeks | ~$50 |
| 2 | Exploration learning + general perception ("any game") | 8–12 weeks | ~$200 |
| 3 | Persona system (4 personas v1, 10 personas v2) | 2–3 weeks (parallel with 2) | ~$100 |
| 4 | Reporting + A/B comparison layer | 4–6 weeks | ~$200 |
| 5 | Production infrastructure (headless emulator farm, multi-tenant, billing) | 8–12 weeks | $500–2K cloud |
| 6 | First 3 paid pilots, real-user validation, iterate | open-ended | revenue from here |

**MVP-as-product:** ~6 months from today, ~$600 in LLM credits.
**Polished v1:** ~9 months from today.

The architecture decisions made today (CoALA-style cognitive layer + LLM-
agnostic adapter pattern + bus-based event system) are designed to support
this trajectory. The 2048-specific code is deliberately localized so the
GameAdapter extraction in Phase 1 is a refactor, not a rewrite.

---

## 9. Strengths (the case for Nova)

### 9.1 Technical strengths

- **The cognitive architecture works end-to-end today.** Memory, affect,
  ToT deliberation, reflection, brain-panel viewer all functional on a
  real game in a real emulator. Not a paper, not a demo video — running
  code with 187 passing tests.
- **The brain-panel UI is genuinely novel.** Visible cognitive reasoning
  per-move, type-coded affect crossings, ToT branch evaluation with
  winner highlighted, first-person voice. This is the trust artifact the
  category lacks.
- **The architecture is game-agnostic above the perception/action interface.**
  GameAdapter extraction is a refactor of localized code, not a redesign.
  This isn't a 2048-specific system pretending to be general; it's a
  general system that happens to play 2048 first.
- **LLM-provider abstraction is in place.** Already supports Gemini and
  Anthropic via a `build_llm` factory. Adding OpenAI / local LLMs is
  straightforward.

### 9.2 Strategic strengths

- **Demand-side signals are real.** Square Enix's 70%-by-2027, mobile
  retention worsening into 2025, accessibility regulatory tailwind via
  EU EAA — multiple independent forces pushing the market.
- **No direct competitor ships the persona-based introspective approach.**
  modl.ai (RL coverage), Razer (hybrid distribution), General Intuition
  (NPCs) — all adjacent, none head-on.
- **Cognitive science citations legitimize the pitch.** 41 papers in the
  foundations dossier; the most load-bearing (Schultz dopamine, Russell
  circumplex, CoALA) connect Nova to 40+ years of established science. Not
  vibes-based AI.
- **The trauma-tagging mechanism is a publishable contribution.** Genuine
  novelty + a credible academic write-up is both scientific legitimacy
  and a moat.

### 9.3 Practical strengths

- **Capital-efficient.** ~$600 in LLM credits gets to MVP-as-product over 6
  months. Single engineer can sustain through Phase 4. Doesn't need a seed
  round to validate the thesis.
- **Multiple potential exits.** Acquisition target for a larger AI-agent
  player (Anthropic, Inworld, modl.ai itself); standalone SaaS at $5K-50K
  ARR per studio; open-source-with-paid-hosting model.

---

## 10. Weaknesses and risks (the honest cons)

### 10.1 Technical risks

- **The "Nova predicts real players" claim is empirically untested.** No
  validation data exists yet. The lightweight Phase 0.5 (N=5 friends-and-
  family) is directional, not statistically significant. Studios who buy
  on prediction-accuracy claims will eventually demand harder evidence.
- **Real-time games are out of scope.** The screenshot-per-step
  architecture cannot handle action games, shooters, racing, or anything
  with sub-second decision windows. Roughly 30-40% of the gaming market by
  revenue is unaddressable without architectural overhaul.
- **3D and complex action spaces are out of scope.** Even slower-paced 3D
  games (RPGs, adventure, simulation) need 3D scene understanding that
  current vision-LLMs do imperfectly. Nova realistically addresses 2D
  puzzle, strategy, narrative, and turn-based games — a substantial but
  not universal slice.
- **Pro/Flash quota dependency.** Currently dependent on Gemini paid tier;
  Pro has a 1000 RPD per-model daily cap that we exhausted in heavy
  testing. Production needs either higher-tier quotas (paid request to
  Google) or multi-provider failover.
- **The OCR palette is 2048-specific.** Each new game needs perception
  rework — not architectural, but real engineering per game family.
- **Exploration learning is unproven for Nova specifically.** Voyager
  works on Minecraft; SIMA works on instruction-following. Whether Nova's
  cognitive architecture extends gracefully to "drop in any game and
  learn it" in Phase 2 is the biggest open architectural question.

### 10.2 Strategic risks

- **General Intuition's $133.7M raise.** If they pivot from NPCs to
  synthetic playtesting, Nova is racing against a much larger team with
  proprietary training data and a substantial corpus. The differentiator
  becomes persona-based cognitive introspection (Nova's lane) vs
  statistical NPC-modeling (their lane) — different shapes, possibly
  coexisting, but Nova is the smaller fish.
- **modl.ai's existing studio relationships.** They've been in the market
  for years, have customer relationships, and already understand the
  studio sales motion. If they add personas + affect on top of their
  existing distribution, Nova is fighting from behind.
- **Studio sales cycles are slow.** AAA studios have 6-12 month
  procurement cycles; mobile mid-tier studios are faster but still
  cautious. The wedge has to be cheap enough to "just try" — likely a
  free or $5K pilot to land the first 5 logos. Not enterprise SaaS
  pricing for at least a year.
- **Trust and IP concerns with pre-launch builds.** Studios will not
  upload pre-launch APKs to a third party without strong NDA + data
  handling guarantees. SOC 2, on-prem deployment options, opt-out
  training data — all real product requirements that add cost and time.
- **No revenue traction yet.** Architecture-first pitch resonates with
  technical advisors; non-technical investors want to see ARR or LOIs.
  First 12 months are unfunded thesis-validation territory.

### 10.3 Operational risks

- **Solo founder bus factor.** Single engineer carrying the full stack.
  Vacation, illness, burnout — all single points of failure. Hire #2
  triggers (likely Phase 4) need to be planned for.
- **LLM cost trajectory uncertain.** Gemini Flash is cheap today; pricing
  could change. Multi-provider abstraction mitigates but doesn't eliminate
  the risk.
- **Market timing.** AI agents are hot in 2026; could cool by 2027 if a
  general "agent winter" hits. Nova's architectural depth and category
  novelty are partial hedges but not immunity.

### 10.4 Conceptual risks

- **The "personas are real" claim is contested.** Player taxonomies
  (Bartle, Yee) are useful frameworks but their empirical validity is
  debated. Nova's personas are designer-tuned configurations, not
  measurements of real player segments. Buyers may push back.
- **"Predicts how real players react" is a strong claim that may be
  unprovable at the level of individual game decisions.** Nova may
  predict aggregate cohort metrics (drop-off rates, frustration peaks)
  more reliably than per-move decisions. The marketing should reflect
  this.
- **The emotional-reading aspect is anthropomorphic.** "Nova feels
  frustrated" is a useful metaphor that may oversell what the system
  actually computes (a number going up). Some critics will object on
  philosophical grounds.

---

## 11. Open questions

These are real unresolved questions the team will need to answer in the
next 6 months:

1. **Does Nova's persona-conditioned predictions correlate with real
   human play?** Resolved: Phase 0.5 lightweight + first-pilot real-user
   data. Outcome shapes pricing and positioning.
2. **Which game genres does the architecture extend to gracefully?**
   Resolved: Phase 1 (Tetris) + Phase 2 (3 unseen-genre games). Outcome
   defines the addressable market.
3. **Does the brain-panel "show your work" UI actually drive purchase
   decisions, or is it a nice-to-have?** Resolved: first 5 pilot
   conversations. Outcome shapes the dashboard's importance vs back-end
   reporting.
4. **What's the right pricing model?** Per-session / per-report /
   subscription / freemium-with-enterprise. Resolved: first paid pilot
   + competitive benchmarking. Outcome shapes the entire business model.
5. **Does the "cognitive playtesting" category exist in studios' minds,
   or do we need to create it?** Resolved: pilot conversations. Outcome
   shapes marketing narrative + sales cycle length.
6. **Open-source vs proprietary core?** Open-core (architecture open,
   personas + reporting + hosting paid) is the recommended path but the
   decision affects sales motion + community-building strategy. Resolve
   before Phase 4.
7. **Single-provider vs multi-provider LLM strategy?** Studios may want
   on-prem or specific providers. Resolve before first enterprise pilot
   conversation.
8. **Hire #2 timing?** Phase 4 by default. Earlier if seed funding lands;
   later if bootstrapping. Resolve at Phase 1 demo + funding decision.
9. **Partnership vs competition with modl.ai?** Could be a complement-
   their-coverage-with-Nova's-personas play, or head-on. Resolve in early
   pilot conversations.
10. **Does the trauma-tagging mechanism actually improve agent performance
    measurably?** It's elegant and publishable, but unproven that it
    improves outcomes vs a non-trauma baseline. Could be ablated in
    Phase 0.5+.

---

## 12. Where the project stands as of 2026-05-02

**Shipped:**
- Cognitive architecture (memory, affect, ToT deliberation, reflection)
  end-to-end on 2048
- 187 passing tests across agent + viewer
- Brain-panel viewer with thinking stream, mood gauge, dopamine bar,
  memory feed
- Real-time WebSocket event bus
- 5-document product dossier (~1,800 lines, 41 citations, 12 personas,
  10 use cases)

**In progress / next 2 weeks:**
- Final v1.0.0 polish + demo recording (Task 41-56 of original plan)
- AgentEvent type system cleanup (technical debt)
- Anthropic Sonnet integration for production reflection

**Next 6 months:**
- Phase 0.5 lightweight validation
- Phase 1 GameAdapter + Tetris port
- Phase 2 exploration learning
- Phase 3 persona system v1
- Phase 4 reporting layer
- First studio pilot conversations

---

## 13. Reviewer prompt — what kind of review I want

You've now read the briefing. **I want a comprehensive, honest critique.**
Specifically, please address:

### Technical critique
1. Are there architectural choices in Nova's cognitive layer (memory,
   affect, deliberation, reflection) that I'm getting wrong? Anything
   you'd structure differently?
2. Is the screenshot-per-step + LLM-driven decision pipeline a
   fundamental constraint, or are there ways to extend to faster-paced
   games that I'm not seeing?
3. Is the OCR + ADB + emulator stack the right shape for this product,
   or should I be thinking about a different game integration approach
   (e.g., direct game-engine SDK integration, browser-based games)?
4. Is the trauma-tagging mechanism actually doing useful work, or is it
   architectural cosmetics that doesn't improve outcomes? How would I
   measure this empirically?

### Scientific critique
5. Are there papers I'm missing that would either strengthen or undermine
   Nova's foundations? Specifically: any work on LLM-agent affect
   prediction vs human behavior, or any negative results on cognitive
   simulation that I should know about?
6. Is the "Russell circumplex + Schultz RPE" affect framing
   scientifically defensible, or am I misappropriating these models?
7. Would academic reviewers accept the claim that Nova represents a
   novel publishable contribution (specifically the trauma-tagging
   mechanism)? What would the right venue be?

### Product / market critique
8. Is "synthetic playtesting" a real product category, or am I creating
   a "we're a Slack-but-for-X" framing that doesn't have a buyer?
9. Is the wedge use case (FTUE validation for mobile studios) the right
   wedge, or is there a better entry point I'm missing?
10. Is the persona library a real moat, or will competitors clone it in
    a quarter? What would make the library defensible?
11. Is the brain-panel "show your work" UI actually a competitive
    differentiator, or is it a nice-to-have that doesn't drive purchase?
12. Pricing model: any of (per-session, per-report, subscription)
    sound right? Or am I missing a model that fits better?

### Competitive critique
13. Am I underweighting modl.ai or General Intuition? Either of them
    could shut Nova down — what would I need to see in their roadmap
    to know I should pivot?
14. What other competitors am I missing that the research didn't
    surface?
15. Is "complement existing tools" or "head-on competition" the right
    framing? Why?

### Strategic critique
16. Is the 6-month MVP timeline realistic, or am I underestimating
    something specific?
17. Is bootstrap vs seed-funding the right framing? What would change
    your answer?
18. What's the strongest argument *against* building this product? If
    you had to convince me to abandon it, what would you say?
19. What's the failure mode I'm most likely to walk into without
    realizing it?
20. If you were me, what would you do *differently* in the next 30 days?

### Format I'd like the response in

A structured markdown document mirroring sections 9-13 of this briefing
(Strengths I missed; Weaknesses I'm underweighting; Open questions I
should add; Specific actions for the next 30 days). Be specific. Cite
sources where you can. Don't pad with generic AI-industry context — I've
already done that research. **The most useful response is one that
disagrees with me on 2-3 specific load-bearing claims and explains
why.**

Thank you for taking this seriously.
