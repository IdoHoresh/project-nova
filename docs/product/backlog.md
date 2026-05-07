# Project Nova — Strategic Backlog

> **Purpose:** navigation aid for backlog items captured outside the
> roadmap. Each item is tagged with its status against the existing
> methodology, roadmap, and ADRs so we don't double-design or lose
> context. This file is **not** a source of truth — it points at the
> docs that are.
>
> **Read alongside:** [`product-roadmap.md`](./product-roadmap.md) for
> phase definitions, [`methodology.md`](./methodology.md) for the
> technical foundation, [`personas-and-use-cases.md`](./personas-and-use-cases.md)
> for cohort definitions.
>
> **Status tags:**
> - `[planned]` — already in roadmap or methodology, named here for cross-reference
> - `[NEW]` — not yet captured in any spec; needs writing-plans or spec authorship
> - `[partial]` — architecture exists, surface or generalisation gap remains
> - `[deferred]` — interesting but off-current-thesis; revisit post-Phase 4
>
> **Origin:** captured 2026-05-07 from a strategic backlog draft, cross-walked against
> existing methodology + roadmap + LESSONS by Opus session.

---

## High-priority — pull into Phase 1–2 spec work

### Memory Decay & Summarization Engine `[partial]`

Background agent that runs between simulated sessions, compresses the
prior game into high-level insights ("this level requires long-term
planning"), and purges redundant tactical vectors from LanceDB.
Enables D30/D90 retention simulation without unbounded context growth.

**Already covered:** Three-channel memory decay (episodic 24h /
semantic 7d / affective 30d) is specified in `methodology.md` §1.6 and
LESSONS "Three-channel memory decay matched to cognitive psychology".

**Gap:** The summarisation step — a background agent that produces
session-level abstractions and prunes redundant tactical memory — is
not yet specified. Needed to make Phase 4 long-horizon simulation
tractable per `methodology.md` §1.6.2.

**Action:** Phase 1 or Phase 2 spec. Bundle with hybrid local+API
inference work since the summariser is a natural fit for the local
Qwen 14B path.

---

### Quantitative A/B Testing Simulator `[NEW]`

Run the cliff-test runner (or its successor) on Version A vs Version B
of the same game build, in parallel, and produce a comparative report:
"this change reduces average session anxiety by 15% and delays the
churn cliff by 8 moves."

**Already covered:** Phase 6 paid-pilot framing in `product-roadmap.md`
implicitly enables this (a studio brings two builds, Nova compares
them). Cliff Test paired-arm structure (ADR-0007) is the right
primitive — it just needs to scale from "Carla vs Bot" to
"build-A-Carla vs build-B-Carla."

**Gap:** Not named anywhere as a product feature. The studio sales
pitch leans on this output ("this delay is worth $X in retained UA")
but no spec defines the comparative-report format, the seed-pairing
discipline across builds, or the statistical test for delta
significance.

**Action:** Phase 4 spec, alongside KPI Translation Layer. The output
is a one-page differential report similar to the paid-pilot format.

---

### Live-Ops & Twist Engine + Meta-Economy Emotions `[NEW]`

Two related items, bundle as a single Phase 2 spec §:

1. **Live-Ops Twist Engine** — handle external interruptions
   (pop-ups, sales, energy gifts) by recalculating RPE in real time.
   Detects whether the twist resets boredom or is perceived as a
   predatory paywall (Rage Quit Signature).

2. **Distance-to-Reward RPE** — extend the affect/RPE math to long
   sessions where reward is multiple sessions away. Adds psychological
   triggers: Grind-wall Anxiety, Inventory/Space Anxiety (the urge to
   destroy items to make room).

**Already covered:** `methodology.md` §1 affect dimensions exist but
are board-spatial only. `methodology.md` §3 inference architecture
sees board state.

**Gap:** No game-state schema extension for resource counts, energy
timers, item prices, or live-ops events. No reasoning pathway that
weighs "I paid $5 and didn't get the item" against "the board is
locked." See LESSONS entry "Economic-frustration layer for
meta-economy games should be designed in Phase 2, not retrofitted in
Phase 3" (2026-05-07).

**Action:** Phase 2 spec § "Economic-frustration layer." Defines new
game-state fields, new System 1/2 reasoning prompts, and a new
Signature (Epsilon? — economic churn distinct from board-geometry
churn) with its own falsification criterion.

---

### Qualitative Post-Churn Exit Interviews `[partial]`

When a persona churns mid-session, freeze its memory and emotional
state and open a chat interface. Game Designer asks "why did you
leave?" and gets a reasoned answer grounded in game context: "the boss
was easy, but I ran out of energy and the sales pop-up felt
predatory."

**Already covered:** Reflection module exists in `nova-agent`
(post-game reflection lessons are produced; CLAUDE.md "memory + affect
+ ToT deliberation + reflection"). The persona's frozen state is
already serialisable through the bus protocol.

**Gap:** Designer-facing chat UI in `nova-viewer` does not exist.
Reflection currently emits a single post-game JSON event, not an
interactive query interface.

**Action:** Phase 2 or Phase 3 nova-viewer feature. Cheap to prototype
on top of existing reflection module — primarily a UX layer + a thin
chat-completion wrapper that injects the frozen persona state as
system context. Strong sales-demo asset; consider prioritising even
ahead of full Phase 2 economic-layer work for pitch leverage.

---

## Medium-priority — fold into existing Phase specs

### Affect-Driven Persona Library — Whale, Min-Maxer `[planned]`

Concrete cohort definitions beyond Casual Carla:
- **Whale** — high tolerance for grind, low anxiety on failure, driven
  by rare achievements and social status.
- **Min-Maxer** — easily bored by low difficulty, highly frustrated by
  inconsistent mechanics or efficiency loss.

**Already covered:** `methodology.md` §1 specifies 12-persona library
with per-persona signatures. `personas-and-use-cases.md` is the
authoritative cohort doc. Phase 3 explicitly does v1 (4 personas) → v2
(10 personas).

**Gap:** None at the architecture level. The named cohort definitions
above are useful **input** for the Phase 3 persona-calibration spec —
fold them into `personas-and-use-cases.md` when that spec is written.

---

### Persona Matrix — population-scale simulation `[planned]`

Run a synthetic population of diverse emotional and historical
profiles in parallel. State Injection Layer loads different game
snapshots per persona. Narrative Persona Layer injects ToT system
prompts. Monte Carlo statistical weighting matches real market
distribution (10% Whales / 40% Casual / 50% Grinders). Output: 3
agents on the same map simultaneously, each with different Anxiety
based on injected history; final report shows Weighted Retention Rate
across segments.

**Already covered:** This **is** Phase 4. `methodology.md` §1.6.2
specifies "cohort distributions across N≥50 personas." LESSONS
"Cohort-distribution reporting > single-trajectory point predictions"
(2026-05-02).

**Gap:** The operational specifics (3-profile parallel run, weighted
retention report format, state-injection mechanism) are sharper in
this backlog item than in the methodology. Fold into the Phase 4 spec
when written.

---

### Vision-Action Abstraction (generalised VLM) `[partial]`

Mediation layer that takes screenshots, uses a Vision Model to
interpret state, and returns screen-action commands. Enables
plug-and-play deployment to any Unity 2022.3+ game without custom
integration code.

**Already covered:** 2048 Unity build uses ADB + OCR + VLM today
(Carla is a VLM persona). `methodology.md` §3 covers VLM observation.

**Gap:** Generalisation beyond 2048's specific OCR palette (LESSONS
"OCR palette must match every tile color the game can produce") and
fixed ADB DPAD-keyevent input layer (LESSONS "Unity 2048 fork ignores
adb shell input swipe; only DPAD keyevents work"). Phase 1 Unity SDK
+ GameAdapter abstraction is where this lifts to a named architecture
goal.

**Action:** Already in `product-roadmap.md` Phase 1 ("Unity SDK +
GameAdapter abstraction"). Surface it explicitly as the
"Vision-Action layer" sales talking point in `README.md` so studios
understand the plug-and-play promise.

---

### Economy Shift Detection `[NEW]`

Test scenario (not architecture): does a bot with memory detect a
nerf in generator efficiency or item value, and adapt its strategy?
Success metric: bot abandons the "old path" within K moves after the
change takes effect.

**Already covered:** Trauma-tagging architecture (Phase 0.8) tests
within-game adaptation to negative experiences. The mechanism is the
same; the trigger is different (economy nerf vs board-geometry trap).

**Gap:** The Phase 2 economy-layer test corpus doesn't yet include
this scenario. Add it once economy-layer schema lands.

**Action:** Phase 2 test corpus. Bundle with the Live-Ops & Twist
Engine spec — same affect/RPE pathway exercised by a different
trigger.

---

## Deferred — off-current-thesis, revisit post-Phase 4

### Adversarial "Boredom" Explorer `[deferred]`

Bot instructed to maximise boredom or stress the system: seeks map
edges, repetitive unplanned actions, economic exploits born of a
persona's "boredom." Behavioural QA capability for security and
economy balancing.

**Why deferred:** Pulls Nova back toward the QA-tool category that
the dossier explicitly repositioned away from. See LESSONS "Category
positioning matters more than feature parity" — Nova's category is
**Cognitive Audit & Prediction** (Product/Live-Ops budget), not
**Automated QA** (where modl.ai has 5-year head start).

The boredom-explorer concept is interesting and may have legitimate
use as a stress-test mode for Phase 5+ production infra. But adding
it before Phase 4 product-fit work risks diluting the category
positioning at the worst possible moment (right before commercial
pilots).

**Action:** Park. Revisit if a paid pilot specifically asks for
adversarial economy-exploit testing. Until then, the existing
Bot/Carla paired arm is sufficient adversarial coverage.

---

### Instruction Alignment Score + Tutorial Friction Measurement `[partial]`

Nova acting as a first-time human player is **already planned** in Phase 2
(2.1 visual perception → 2.2 action discovery → 2.3 tutorial-watching →
2.4 skill induction → 2.5 unseen-game validation). The architecture is
covered. Two concrete measurement additions are missing from Phase 2's
work units:

**Gap 1 — Instruction Alignment Score (IAS):** Track how quickly and
accurately the agent follows a new UI-driven command during the
onboarding phase. Operationalisation: ratio of tutorial steps completed
correctly on first attempt vs total tutorial steps, per-session.
Complements the Phase 2.3 cause-effect log but makes the compliance rate
a named, exportable metric rather than a post-hoc derivation.

**Gap 2 — Tutorial Friction via Anxiety + ToT stacks:** Use the existing
Anxiety and ToT deliberation signals to surface "confusing" tutorial
steps — defined as moves where the agent required multiple VLM passes,
showed elevated Anxiety, or entered ToT mode on a step that should be
trivial. This is an interpretation layer on top of Phase 2.3 logs, not
a new architecture. Candidate game: Gossip Harbor (merge-2 genre).
Acceptance criterion stub: agent completes a 5-step Gossip Harbor
tutorial cold, IAS ≥ 0.8, and flags ≥1 friction point where Anxiety
> threshold or ToT fired.

**Already covered:** Phase 2.1 (OCR generalisation), 2.2 (action
discovery), 2.3 (tutorial pipeline), 2.4 (semantic rule induction),
2.5 (unseen-game validation). Do **not** re-spec those.

**Action:** At Phase 2.3 spec-authorship time, add IAS as a named DV
and Tutorial Friction as a logged secondary metric. No architecture
changes needed — both are measurement additions on top of the planned
pipeline. Link spec here when written.

---

## Maintenance

- This file is updated when new backlog items surface. Keep entries
  brief — point at the authoritative spec/methodology section, don't
  duplicate content.
- When an item moves from `[NEW]` → spec authored, update the tag to
  `[planned]` and link the spec.
- When an item is implemented, prune it from this file and rely on
  the methodology/roadmap as the canonical record.
