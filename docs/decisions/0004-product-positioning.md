# ADR-0004: Product positioning — cognitive audit & prediction platform (not a QA tool)

**Status:** Accepted
**Date:** 2026-05-02
**Deciders:** Founder + AI red-team brainstorm

---

## Context

Nova plays game builds end-to-end and reports on what happens. That
description fits at least four product categories:

1. **QA tool** — sells to QA Director; competes with modl.ai; deliverable
   is bug reports / coverage metrics.
2. **Developer tool** — sells to Engineering Manager; integrates into
   IDE/CI; deliverable is debug context.
3. **Product / design tool** — sells to Product Director / Live Ops
   Director; deliverable is design-decision validation; competes with
   PlaytestCloud + internal designer playtesting.
4. **Marketing / UA tool** — sells to UA Manager; deliverable is
   retention / LTV predictions; competes with attribution platforms
   (which it doesn't really, but the buyer overlap exists).

Initial positioning was ambiguous, leaning toward "AI playtesting" which
puts Nova adjacent to category #1 (QA). The AI red-team flagged this as
a category trap: QA budgets are smaller (cost center), QA buyers care
about coverage metrics (not affect signatures), and modl.ai already owns
the QA category with 5+ years of studio relationships.

## Decision

Position Nova explicitly as a **product-decision tool** (category #3).
Specifically:

- Headline: "**Project Nova: The Cognitive Audit & Prediction Platform**"
- Subtitle: "**A product-decision tool to test game design and economy
  hypotheses with simulated player personas.**"
- Buyer: Product Director / Live Ops Director / Studio Director
- User: Game Designer / Live Ops PM / Senior Engineer (SDK integrator)
- Outcome consumer: UA Manager (their KPIs justify the budget upstream)

Lock the category claim in the first 50 words of the README and in the
methodology page. Add a "What this is NOT" section that explicitly
disclaims:

- QA bug-finding (route users to modl.ai)
- Real-time / 3D game testing (out of scope)
- Replacement for human playtesting (Nova augments, doesn't replace)
- Attribution / marketing platform (UA platforms sit downstream)

## Alternatives considered

- **QA tool positioning (rejected).** Strengths: existing category, no
  buyer education needed. Rejected because: head-on with modl.ai, smaller
  budgets (cost center), wrong language for the deliverable (bug reports
  vs persona introspection).
- **Developer tool positioning (rejected).** Strengths: Brain Panel as
  developer-facing artifact resonates with engineers. Rejected because:
  developers don't make retention/economy decisions; they integrate the
  SDK and consume reports but don't pay. They're users, not buyers.
- **Marketing / UA tool positioning (rejected).** Strengths: outputs
  (retention, LTV, churn predictions) are exactly what UA cares about.
  Rejected because: UA buyers buy attribution + creative tools, not
  game-internals tools. They're the *outcome consumer* (predictions
  matter to them), not the *direct buyer*.
- **Ambiguous / multi-category positioning (rejected).** "Lets buyers
  define the category" sounds flexible but is actually fatal: QA
  buyers project QA expectations onto Nova and find it lacking compared
  to modl.ai. The category lock-in is a feature, not a bug.

## Consequences

**Positive:**

- Clear buyer profile makes sales motion executable for a solo founder.
- Product/Live-Ops budgets are larger (profit center) than QA budgets
  (cost center).
- Recurring revenue is more natural — live-ops studios drop content
  weekly, so subscription pricing makes sense.
- Nova differentiates cleanly from modl.ai (different category) and
  from CasterAI / General Intuition (different deliverable shape).
- Methodology publication becomes a moat — studios learn the
  Signature vocabulary, Nova becomes the industry benchmark.

**Negative:**

- Smaller addressable market than "AI for game studios broadly." The
  category is more focused but more constrained.
- Sales cycle for product/live-ops is longer than for QA (more
  approvals; bigger budget = more scrutiny).
- Lose access to "AI testing budget" line items at studios that bucket
  AI tooling under QA.

**Neutral:**

- The technical architecture is unchanged. Same cognitive layer, same
  Brain Panel, same Signatures. Only the marketing/positioning changed.

**Reversibility:**

- Hard to reverse cleanly. Once positioned in a category, repositioning
  later requires brand work + sales-motion re-tooling. But: the
  underlying tech can plausibly be repositioned to QA later if the
  product-decision-tool category fails to monetize. Better to start
  focused than start ambiguous.

## References

- `docs/product/README.md` strategic positioning section + the
  side-by-side table contrasting Product Decision Tool vs QA Tool
  positioning.
- `docs/product/competitive-landscape.md` for the full competitive
  analysis that informed the rejection of QA-adjacent positioning.
- `LESSONS.md` "Category positioning matters more than feature parity"
  entry.
- ADR-0002 (State-Transition Signatures) — the analytical primitive that
  makes the product-decision-tool deliverable possible.
- ADR-0003 (Hybrid local + API inference) — supports the "studios with
  IP-sensitive builds can self-host the System 1 path" argument that
  product/live-ops sales need.
