# Project Nova — Product Dossier

> **For:** the team building Nova into a synthetic-playtesting product for game studios.
> **Source:** three parallel deep-research sweeps + the cognitive architecture
> already shipped on `claude/practical-swanson-4b6468`.
> **Scope:** strategy, positioning, market, evidence — and the research file
> index. The accompanying [`product-roadmap.md`](./product-roadmap.md) covers
> the build phases.

---

## TL;DR

Nova-as-product is a **synthetic-playtesting service**: studios upload a build,
pick a persona mix, and get back a report describing how each persona segment
emotionally arc'd through the experience — where they got stuck, where they
churned, where they'd spend, and what they reflected back about the game
afterward. The architecture we shipped this week (memory + affect + ToT
deliberation + reflection + brain-panel viewer) is the substrate. Eight to
twelve months from today gets us a polished v1; an MVP is reachable in 4–6
months.

The market signal is real and accelerating — **Square Enix has publicly
committed to 70% of QA via genAI by end-2027**, **General Intuition raised
$133.7M in Oct 2025** (one of the largest AI seed rounds ever) on a video-game
agent corpus, and **Razer is shipping AI playtesting on AWS Marketplace**
through their hardware distribution channel. Mobile retention has *worsened*
into 2025 (D1 26.5%, D7 3.4–3.9% per GameAnalytics), which means studio
willingness-to-pay for tools that catch retention problems before launch is
rising. The category exists; nobody has yet shipped what Nova proposes —
"synthetic playtesting that reports introspective affect curves and persona-
specific narrative reflections."

The wedge: **tutorial / FTUE validation** is the lowest-trust-bar, fastest-
sale use case (it ties directly to D1 retention which gates UA payback).
Combined with the **Casual** and **Returning** personas it can be sold to
mobile UA and live-ops PMs as "find your tutorial drop-off cliff before you
spend $100K on UA against a leaky funnel." That's the pitch for the first 5
pilots. Live-ops content validation and A/B-test pre-screening expand from
there.

---

## Research index

| File | Length | What it answers |
|---|---|---|
| [`competitive-landscape.md`](./competitive-landscape.md) | ~3K words, 12 sections | Who already exists, who could pivot in, where the white space is |
| [`scientific-foundations.md`](./scientific-foundations.md) | ~4.3K words, 41 citations | Which papers Nova draws on, which legitimize the pitch, what's genuinely novel |
| [`personas-and-use-cases.md`](./personas-and-use-cases.md) | ~4.5K words, 12 personas, 10 use cases | Persona library, concrete use cases with industry data, market sizing |
| [`product-roadmap.md`](./product-roadmap.md) | this directory | Build phases, dates, dependencies, what to do this week vs not |

Read in order: this README → roadmap → drill into the three research files for
detail when needed.

---

## Strategic positioning

### The category Nova is creating

There are three adjacent product categories today. Nova sits at the
intersection of all three but is fully inside none.

| Category | Examples | What they do | What they don't |
|---|---|---|---|
| **AI playtesting agents** | modl.ai, Razer QA Co-AI | Run automated agents that play game builds, report bugs/coverage | Don't simulate distinct **player personas**; don't surface **introspective affect**; report bugs not experiences |
| **Crowd-playtesting** | PlaytestCloud, Antidote, Applause | Real humans paid to playtest, video + survey | Slow (24–48h), expensive ($30–80/playtest), small N, can't simulate edge personas (whales, accessibility, returning) |
| **General LLM agents** | Anthropic computer use, Devin, Cognition | Drive arbitrary computer interfaces via LLM | Not specialized for games; no cognitive architecture; no persona framework |

**Nova's wedge:** a synthetic playtester that's distinctly *cognitive* — has
memory, has feelings, deliberates under stress, reflects after the session,
and can do all of this in N parallel persona configurations. The deliverable
isn't "did the agent crash the build" or "did it find a bug" — it's "here's
what 50 simulated Casuals went through, here's where each one hit an
emotional wall, here's what they 'said' about it in their post-game
reflection." That's the unique artifact.

### What the research reveals about defensibility

From the **academic foundations** dossier:
- Nova's combination of CoALA-style cognitive architecture + Russell circumplex
  affect + Schultz dopamine RPE + explicit trauma-tagging is **not present in
  the published agent literature**. The trauma-tagging mechanism specifically
  has no clear precedent — it's a novel engineering contribution worth a
  research write-up.
- The literature gives Nova citations for every component (CoALA legitimizes
  the architecture; Russell legitimizes the affect model; Schultz legitimizes
  the dopamine framing; Voyager / Generative Agents / Reflexion legitimize
  the LLM agent shape) — Nova is provably "in the tradition" rather than
  "vibes-based AI."
- The **gap**: there's no academic evidence yet that affect-conditioned LLM
  agents *predict* human player behavior better than non-affect-conditioned
  ones. That's the empirical study Nova should publish to lock in the
  scientific position. (See "Validation study" in the roadmap.)

From the **competitive landscape**:
- modl.ai is the only direct competitor at scale, and they're focused on bug-
  finding / coverage automation, not persona-based experiential reports.
  Their public customer roster is thin (Riot is the only confirmed name).
- General Intuition is the wildcard — $133M raise, video-game corpus, but
  pointed at NPC AI not playtesting today. They could pivot. Watch their
  hiring.
- Razer Cortex's distribution advantage (~55M MAU through their hardware
  ecosystem) is a real moat for them in a hybrid AI+human product, but doesn't
  apply to Nova's fully-synthetic category.
- Square Enix's 70%-by-2027 commitment is a demand-side gift. They have an
  open partnership with University of Tokyo's Matsuo-Iwasawa Lab — a vendor
  with a credible cognitive-architecture story has a real shot at being
  a partner, not a competitor.

From the **personas + use cases** research:
- The persona library has 10 well-defined archetypes plus 2 specialty slots
  (Accessibility, Returning Lapsed). Each maps to Nova's existing
  AffectVector, decision biases, and motivation taxonomy with grounded
  citations (Bartle, Yee/Quantic Foundry, Marczewski HEXAD, BrainHex).
- Three use cases stand out for revenue potential:
  1. **Tutorial/FTUE validation** — recurring quarterly, tied to D1 retention,
     low trust bar.
  2. **Live-ops content validation** — weekly cadence, recurring revenue,
     huge gacha/live-service market.
  3. **A/B test pre-screening** — augments rather than replaces existing
     processes; sells to data-science buyer who already trusts statistical
     claims.
- Underrated: **accessibility QA** has a regulatory tailwind (EU EAA 2025
  enforcement) that creates a "we have to do this" budget unlock that the
  pure-discretionary use cases lack.

### Where the moat is

Three layers, in increasing defensibility:

1. **Persona library + tuning data** (months to replicate). Each persona is a
   specific AffectVector configuration + decision biases + reflection prompt
   tuning. Replicable in principle; expensive in practice. First-mover advantage.
2. **Validation data: do Nova's persona predictions correlate with real
   player behavior?** (years to replicate). Once Nova has 6-12 months of paid
   pilots, the dataset of "Nova predicted X, real users did Y" becomes the
   moat. Studios will pay for accuracy guarantees.
3. **The cognitive architecture story** (the most durable). "Memory + affect
   + deliberation + reflection, grounded in cited cognitive science, with
   visible reasoning per persona" is a category that nobody else has shipped.
   The brain-panel UI is part of this — it's the "show your work" artifact
   that makes the predictions trustable. Not technically hard to copy; very
   hard to copy *credibly* without the architectural lineage.

### Where Nova is genuinely vulnerable

- **General Intuition with $133M can outhire and outscale.** If they pivot
  toward synthetic playtesting, Nova is racing against a much larger team
  with proprietary training data. Moat: persona-specific cognitive
  introspection vs their statistical NPC-modeling. Different shape; might
  coexist.
- **modl.ai already has the studio relationships.** If they add personas +
  affect on top of their existing distribution, Nova has a tougher uphill
  climb. Moat: their architecture is RL/coverage-focused, not LLM-cognitive.
  Pivoting cleanly is non-trivial.
- **The "predicts real players" study is unproven.** Nova's pitch depends on
  the claim that cognitive simulation produces actionable forecasts. Without
  validation data, the pitch is theoretical. **First pilot needs to include
  measurement** (e.g., Nova's predictions for tutorial drop-off vs the
  studio's actual drop-off in the same week).
- **Studios are conservative buyers.** Long sales cycles. The wedge has to
  be cheap enough to "just try" — likely a free or $5K pilot to land the
  first 5 logos, not enterprise SaaS pricing.

---

## What this means for the next 6 months

In priority order (the roadmap doc has the full schedule):

1. **Finish v1.0.0 of the cognitive architecture demo** (current 57-task
   plan, ~2 weeks remaining). The demo IS the proof-of-architecture for the
   product pitch. Don't pivot mid-build.

2. **Lightweight validation + repositioning** (post-v1.0.0, ~1 week, $0).
   Five friends-and-family play 2048 in the emulator; compare directional
   alignment with Nova's Casual + Hardcore personas. Reframe the pitch
   around the **cognitive-architecture-as-design-tool** story (visible
   brain-panel reasoning, persona variety) rather than statistical
   prediction claims. Defer rigorous validation to the first pilot — the
   first studio engagement bundles a 30-day measurement window where
   their real users do the validation work for free. See Phase 0.5 in
   the roadmap for the full reframe.

3. **Build the GameAdapter abstraction + port to Tetris** (~4-6 weeks). Two
   games proves the architecture. Tetris is well-known, simple action space,
   completely different scoring — perfect contrast to 2048.

4. **Implement the persona system** (~2-3 weeks). 4 personas to start
   (Casual, Hardcore, Whale, Returning). Tune their AffectVector defaults +
   decision-biasing prompts. Use the persona library doc as the spec.

5. **Build the reporting layer** (~4 weeks). Run-N-personas → aggregate →
   report. This is the user-facing artifact.

6. **First studio pilot** — likely free, mobile studio, tutorial-validation
   wedge. Goal: testimonial + measurement data, not revenue.

By end of 6 months: pilot deck with one paid customer, validation data,
persona library, two-game proof. Enough to raise a seed round if going that
direction, or land 5–10 pilots if staying bootstrapped.

---

## Honest open questions

These are real risks the research surfaced that the team should be deliberate about:

1. **Does cognitive simulation actually predict human behavior?** Untested
   for LLM-affect agents specifically. **Decision (2026-05-02):** the
   product is positioned from day one as "**design tool with visible
   cognitive reasoning**" rather than "**statistical predictor of real
   players**." The brain-panel UI is the trust artifact. Rigorous
   correlation data accrues from real pilot users in the first paid
   engagement (free 30-day measurement window bundled into pilot terms),
   not from upfront paid playtests.

2. **Is the "persona report" deliverable actually what studios buy?** Studios
   want answers, not data. The first pilot has to involve a hands-on
   workshop with the buyer to learn what report format they actually act on.

3. **Will the LLM cost scale?** Today: ~$0.05–0.10 per game on Gemini Flash.
   At 50 personas × 100 sessions/month per pilot studio × 10 studios = 50K
   sessions/month. ~$2.5K-5K/month in API costs for production at modest
   scale. Not a blocker but worth modeling against pricing.

4. **Pricing model.** Per-session ($1-5)? Per-report ($500-5K)? Subscription
   ($10K-50K/year)? Different shapes have different sales cycles + viable
   customer profiles. The first paid pilot answers this.

5. **Does Nova compete with existing tools or complement them?** A
   "complement modl.ai by adding persona introspection on top of their
   coverage testing" positioning is easier to sell than head-on competition.
   Worth a partnership conversation early.
