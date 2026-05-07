# Project Nova: The Cognitive Audit & Prediction Platform

> **A product-decision tool to test game design and economy hypotheses with
> simulated player personas.**

Nova is **not** a QA bug-finder, an automated test runner, or an
attribution platform. It is a decision-support system for the people who
own the design, economy, and live-ops decisions inside game studios. Nova
plays game builds end-to-end with a library of cognitively-modeled player
personas (Casual, Hardcore, Whale, First-Time, Returning, etc.), produces
quantified KPI predictions per cohort (predicted D1 retention delta,
churn-cliff location, spend-trigger position, engagement-window duration),
and ships an auditable reasoning trace ("Cognitive Audit Trace") that lets
the buyer verify *why* each prediction was made.

The output is a one-page validation report in the morning, not a
three-week human-playtest cycle.

---

## Who this is for

| Role | What they get from Nova |
|------|--------------------------|
| **Product Director** | Pre-launch validation of design hypotheses; confidence in retention forecasts before exposing real users |
| **Live Ops Director** | Overnight validation of weekly content drops; predicted player reaction per persona segment; A/B variant pre-screening |
| **Game Designer** | Per-level affect arcs per persona; specific identification of where Casual personas frustrate vs Hardcore personas engage |
| **Studio Director** | Cross-game economic-hypothesis testing; competitive teardown evidence (on builds you have rights to) |

The **buyer** is the Product Director or Live Ops Director (their budget,
their KPIs). The **users** are Game Designers, Live Ops PMs, and Senior
Engineers who integrate the SDK. The **outcome consumer** is the UA
Manager — they never log into Nova, but the retention predictions Nova
produces are exactly what their CAC payback math depends on.

## What this is *not*

We are explicit about scope to prevent buyers from projecting wrong
expectations onto Nova:

- **Not a QA bug-finder.** Nova does not detect crashes, memory leaks,
  rendering issues, or compatibility bugs. For coverage testing,
  modl.ai and traditional QA automation are the right tools.
- **Not a real-time game tester.** The current architecture handles
  turn-based puzzle, strategy, narrative, and slow-paced live-service
  content. Action games, racing, shooters, and any title with sub-second
  decision windows are out of scope.
- **Not a replacement for human playtesting.** Nova produces directional
  evidence in 30 minutes for hypotheses that would otherwise need 3-4
  weeks of human playtesting to investigate. Humans remain essential for
  qualitative experience design and for validating Nova's own predictions.
- **Not an attribution or marketing platform.** Nova predicts retention
  and engagement; UA platforms (AppsFlyer, Adjust, AppLovin) handle
  attribution and creative testing. They sit downstream of Nova's
  outputs, not as competitors.

---

## Core deliverable

Nova ships a **Validation Report** per game-version under test. The
report is the executive-readable artifact; the underlying Cognitive Audit
Trace is the per-prediction evidence layer.

A Nova report leads with KPI predictions and ends with reasoning:

```
═══════════════════════════════════════════════════════════
  PROJECT NOVA — Validation Report
  Game: [studio's game build, version under test]
  Cohort: 50 personas across 4 archetypes
  Wall-clock: 38 minutes
═══════════════════════════════════════════════════════════

  PREDICTED D1 RETENTION DELTA: +4.2% vs baseline    [1]
  PREDICTED CHURN CLIFF: Level 7 (47% of Casual cohort)
  PREDICTED SPEND TRIGGER: Post-level-9 hard paywall
  PREDICTED ENGAGEMENT WINDOW: Levels 3-6 (Hardcore cohort)

  TOP REFLECTION LESSONS:
  • Casual cohort: "the dragon level needs more healing pickups"
  • Hardcore cohort: "boss patterns repeat, getting predictable"
  • Whale cohort: "the gold gate at level 9 feels fair"

  ─── DRILL-DOWN ────────────────────────────────────────
  • Per-persona affect arcs over the session
  • Signature firing rates (Alpha/Beta/Gamma/Delta)
  • Cognitive Audit Trace: per-move reasoning + chosen action
  • CSV/JSON export for downstream analysis

  [1] Methodology: Signature Alpha firing rate × validated
      coefficient from corpus (n=37 prior pilots).
      See methodology.md for full math.
═══════════════════════════════════════════════════════════
```

Every prediction line is footnoted to a specific signature methodology in
[`methodology.md`](./methodology.md). No black box.

---

## How Nova works (one paragraph)

Nova is a **CoALA-shaped LLM agent** (Sumers et al., 2024) with persistent
episodic + semantic memory, a 6-dimensional affect vector grounded in
Russell's circumplex model (1980) and Schultz dopamine-RPE dynamics
(1997), Tree-of-Thoughts deliberation triggered by anxiety thresholds, and
post-game reflection that extracts semantic rules from catastrophic
losses. The cognitive layer routes compute by load, mirroring Kahneman's
dual-process cognition: System 1 (fast, intuitive ReAct decisions) runs
on a local 14B-class model with vLLM `guided_decoding` for zero-parse-error
JSON; System 2 (slow, deliberate ToT branches + post-game reflection)
runs on frontier APIs (Claude Haiku for branches, Sonnet for reflection).
Nova plays the studio's actual game build via a Unity SDK (production) or
OCR/ADB on emulator (pre-launch builds without SDK integration), driven by
a persona-conditioned policy that simulates 12 distinct player archetypes.

Full architecture detail in [`methodology.md`](./methodology.md). Full
scientific lineage in [`scientific-foundations.md`](./scientific-foundations.md).

---

## Strategic positioning

The most consequential category decision Nova makes is to **explicitly not
be a QA tool.** QA is historically a cost center; product/live-ops are
profit centers. Nova's pricing, sales motion, conferences, and
distribution channels are all anchored to product/design budgets.

| Element | Nova (Product Decision Tool) | Contrast: if we'd been a QA Tool |
|---------|------------------------------|--------------------------------|
| Headline metric | Predicted D1 retention delta | Bug coverage % |
| Buyer | Product Director / Live Ops Director | QA Director |
| Pricing model | Per-active-game subscription, $5K-25K/year mid-size, $50K+ enterprise | Per-test or per-session |
| Distribution | Unity Asset Store + GDC + product-design Slack communities | DevOps tooling marketplaces, QA conferences |
| Brand voice | "Validate before you ship" | "Find bugs faster" |

This category lock-in shapes everything downstream. The architecture
choices documented in [`methodology.md`](./methodology.md) — State-Transition
Signatures, hybrid local+API inference, KPI Translation Layer — only make
sense for a product-decision tool. They would be over-engineering for a
QA tool and under-specced for a marketing tool.

---

## Research index

| Document | What it answers |
|----------|------------------|
| [`README.md`](./README.md) (this file) | Product positioning. Read first. |
| [`methodology.md`](./methodology.md) | Technical foundation: 4 Signatures, KPI translations, hybrid inference, dual-DV trauma ablation. The load-bearing technical doc. |
| [`product-roadmap.md`](./product-roadmap.md) | Build phases 0-6, timing, gates, dependencies. |
| [`competitive-landscape.md`](./competitive-landscape.md) | modl.ai, General Intuition, Razer, Square Enix demand signals, white space analysis. |
| [`scientific-foundations.md`](./scientific-foundations.md) | 41 cited papers across LLM agents, cognitive architectures, affect models, player modeling. |
| [`personas-and-use-cases.md`](./personas-and-use-cases.md) | 12-persona library + 10 catalogued use cases with industry data. |
| [`external-review-brief.md`](./external-review-brief.md) | Self-contained briefing for outside reviewers (advisors, investors, technical critics). |

---

## Status

**v1.0.0 of the cognitive architecture demo** is in final polish on
`claude/practical-swanson-4b6468`. Memory, affect, ToT deliberation,
post-game reflection, and the brain-panel viewer all functional on a
running 2048 game in an Android emulator.

The 30-day validation sprint that follows v1.0.0 is detailed in
[`product-roadmap.md`](./product-roadmap.md). Phase 1 (Unity SDK +
GameAdapter abstraction + Tetris port as proof of generality) starts after
the validation gates pass.

**Realistic timeline from today:** MVP-as-product in ~6 months, polished
v1 in ~9 months, on a single-engineer build pace.

---

## Honest open questions

The full question list is in [`external-review-brief.md`](./external-review-brief.md).
The five most consequential:

1. **Does Nova's predicted churn cliff coincide with documented human
   churn cliffs?** Resolved by Phase 0.7 cliff test (Week 1 of the
   30-day sprint). Falsifiable. If no, we reposition.
2. **Does trauma-tagging produce within-game avoidance learning at
   trap-similar states?** Resolved by Phase 0.8 ablation (Week 2).
   Primary DV: within-game trap re-engagement rate (Cohen's `d ≥ 0.3`,
   95% CI excluding 0). If primary nulls, demote trauma to UI flavor.
3. **Will the local-LLM hybrid inference stack ship reliable JSON via
   `guided_decoding`?** Verified in Phase 1 SDK build (Week 6-7). High
   confidence based on vLLM's documented behavior, but the integration
   itself is the test.
4. **Is the persona library a moat or table stakes?** Honest answer:
   table stakes. The moat is the validation corpus (predictions vs real
   outcomes from paid pilots) plus the published methodology that defines
   the industry vocabulary. Personas are necessary, not sufficient.
5. **Does the brain panel actually drive purchase decisions?** TBD —
   will be validated when the first paid pilot's buyer either asks "can I
   embed this in our Slack" (signal: theater not product) or "can you
   give me CSV export" (signal: serious tool). Designed for the second.

---

## Branch + commit cadence

Active branch: `claude/practical-swanson-4b6468`. Every product doc + code
commit is pushed to this branch immediately. Draft PR open at
https://github.com/IdoHoresh/project-nova/pull/1 (will be retargeted at
v1.0.0 cut).
