# ADR-0002: State-Transition Signatures over 1:1 affect-to-KPI mappings

**Status:** Accepted
**Date:** 2026-05-02
**Deciders:** Founder + AI red-team brainstorm

---

## Context

Nova predicts player behavior from internal affect signals. The original
methodology proposed mapping single affect snapshots to KPIs:

> "anxiety > 0.6 → predicted spend trigger"
> "frustration > 0.5 → predicted abandonment"

Each is a single-threshold mapping from an affect dimension to an
outcome.

The AI red-team flagged a problem: a single anxiety spike could mean
"fun challenge," "annoying puzzle," or "about to quit." The snapshot
doesn't disambiguate. Threshold mappings produce false positives at
scale and aren't scientifically defensible — sophisticated buyers
(data scientists, technical leads) will reject them.

## Decision

Replace 1:1 affect-to-KPI mappings with **State-Transition Signatures**:
named multi-step compositional patterns over the affect vector
trajectory. Each Signature is a state-machine pattern that, when matched,
predicts a specific player outcome.

Four Signatures cover the commercially actionable cases:

- **Alpha (Churn):** Confidence ↓ → Anxiety ↑ → Frustration plateau
- **Beta (Conversion):** Frustration ↑ + Dopamine starvation near
  monetization touchpoint
- **Gamma (Engagement):** Confidence ↑ + Dopamine ↑ across consecutive
  moves with low Anxiety
- **Delta (FTUE Bounce):** Anxiety spike within first 60 seconds of
  fresh session in empty-memory persona

Each Signature has:

- A pattern definition (state machine)
- A KPI mapping (with citation)
- A falsification criterion
- A literature anchor

Full specs in `docs/product/methodology.md` §1.

## Alternatives considered

- **Stay with 1:1 mappings (rejected).** Simpler to implement, easier
  to explain in pitches. Rejected because not scientifically
  defensible — single thresholds produce noise that sophisticated
  buyers will reject.
- **Use ML classifier instead of named Signatures (rejected).** Train
  a classifier on trial data to predict outcomes from affect vectors.
  Rejected because: requires labeled training data we don't have,
  produces a black-box prediction that violates the Cognitive Audit
  Trace transparency principle, and competitors with the same data
  could clone it. Named compositional Signatures are interpretable +
  literature-anchored.
- **More than four Signatures (deferred).** Could add Epsilon
  (bug-triggered abandonment), Zeta, etc. Deferred because adding
  Signatures requires evidence that the existing four don't cover
  an outcome category. Epsilon has a documented spec in
  `docs/internal/v2.2-epsilon-spec.txt` gated on Phase 0.7 + 0.8
  passes before promotion.

## Consequences

**Positive:**

- Scientifically defensible — each Signature is a falsifiable state-
  machine pattern, not a vibes-based threshold.
- Harder for competitors to clone trivially. Compositional patterns
  carry more design intent than single-number thresholds.
- Each Signature gets its own validation criterion + KPI mapping —
  modular methodology.
- Becomes the industry vocabulary if Nova publishes the methodology
  early (see ADR-0004 strategic positioning).

**Negative:**

- More complex to implement than threshold checks. Each Signature
  needs a state-tracking detector with timing windows.
- More to validate empirically — each Signature has its own
  falsification criterion that must pass.
- Pitching them requires educating the buyer on what a "state-
  transition signature" is. Higher cognitive load on first
  conversation.

**Neutral:**

- The underlying affect vector machinery is unchanged; Signatures are
  derived from it.

**Reversibility:**

- Reversible. If Phase 0.7/0.8 validation reveals that the named
  Signatures don't actually predict, we can fall back to threshold
  mappings as a weaker product offering. The cognitive architecture
  supports both.

## References

- `docs/product/methodology.md` §1 for the full Signature specs.
- `docs/product/methodology.md` §2 for the Signature → KPI translation
  table.
- ADR-0001 (cognitive architecture as moat) — Signatures depend on
  the affect math being in place.
- ADR-0004 (product positioning) — the methodology publication that
  makes Signatures the industry vocabulary.
- `docs/internal/v2.2-epsilon-spec.txt` for the future fifth Signature
  (Bug-Triggered Abandonment).
