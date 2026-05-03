# ADR-0001: Cognitive architecture as the product moat (not RL, not pure prompting)

**Status:** Accepted
**Date:** 2026-05-02
**Deciders:** Founder (Ido) + AI red-team brainstorm

---

## Context

Project Nova is an LLM-driven agent that plays games end-to-end with a
cognitive architecture (memory, affect, deliberation, reflection,
trauma-tagging). At several points in the build, alternative
architectural approaches were considered:

1. **Pivot to reinforcement learning (PPO, DQN).** RL would master 2048
   in an hour and produce a perfect player at zero per-move cost, since
   the game is mathematically simple.
2. **Pivot to pure prompt-engineering with persona templates.** Skip
   the affect math entirely; just prompt the LLM with persona
   descriptions and let it produce decisions.
3. **Stay with the cognitive architecture as designed.** LLM-driven
   ReAct + ToT decisions, episodic + semantic memory, affect vector
   updated via reward-prediction-error dynamics, post-game reflection,
   trauma-tagging of catastrophic-loss memories.

The decision-forcing question: what is Nova's *product* — a game-
playing optimizer or a player simulator?

## Decision

**Stay with the cognitive architecture as designed.** Specifically:

- Reject the RL pivot. RL produces optimizers; Nova produces simulators.
  RL outputs probability distributions over actions; Nova outputs
  reasoning text + affect trajectory + reflection lessons. Without the
  reasoning text, there is no Cognitive Audit Trace, no persona
  narrative, no Brain Panel, and no commercial product distinct from
  modl.ai's existing RL coverage testing.
- Reject pure prompt-only persona simulation. Prompt-only personas
  produce inconsistent affect dynamics across sessions and have no
  basis for the State-Transition Signatures (see ADR-0002) that the
  product depends on. The affect math is what makes Nova falsifiable.
- Keep all components: episodic + semantic memory, RPE-driven affect,
  ToT deliberation arbiter, post-game reflection, trauma-tagging.

## Alternatives considered

- **Reinforcement learning (rejected).** Strengths: dramatically faster
  inference, zero per-move marginal cost after training, can become
  superhuman at the game. Rejected because: it solves the wrong problem.
  Nova's value proposition is *introspection* (visible reasoning, persona
  narratives, post-game reflection lessons) — not win-rate. RL produces
  a black box that wins games; that's not what game studios buy. Also
  puts Nova in head-on competition with modl.ai who has a 5-year head
  start on RL coverage testing.

- **Pure prompt-only persona simulation (rejected).** Strengths: simpler
  architecture, no affect math to validate, faster to build. Rejected
  because: without the affect math, the persona library is just
  prompt-engineered descriptions that any competitor can clone in a
  weekend. The State-Transition Signatures (ADR-0002) require
  quantified affect dynamics, which require the affect vector + RPE
  updates + memory retrieval. Pure prompts cannot produce falsifiable
  Signatures.

- **Hybrid LLM + shallow RL (deferred for future consideration).** RL for
  action selection within an LLM-narrated reasoning frame. Could
  preserve introspection while gaining inference speed. Not pursued
  now because the additional complexity doesn't pay back at our scale
  (2000 ablation runs in Phase 0.8 are fast enough on the Python sim).
  Worth revisiting if Phase 1+ exposes a real latency or cost wall.

## Consequences

**Positive:**

- Nova is a unique product category (cognitive playtesting) rather than
  a competitor in an existing one (QA automation).
- The cognitive architecture is publishable — the trauma-tagging
  mechanism specifically has no clear academic precedent
  (see `docs/product/scientific-foundations.md`).
- The Brain Panel becomes a credible "show your work" artifact that
  buyers can audit, which is a defensible trust mechanism.

**Negative:**

- LLM inference cost scales with traffic (mitigated by the hybrid
  local + API stack — see ADR-0003).
- Per-move latency is much higher than RL would produce (1-2s vs
  <100ms). Restricts Nova to turn-based / strategy / narrative games;
  real-time and action games are out of scope.
- The affect mechanism MUST validate empirically (Phase 0.7 cliff test +
  Phase 0.8 trauma ablation) — if it doesn't, the entire architecture
  needs repair or repositioning.

**Neutral:**

- Inference architecture choices (which LLMs, hybrid vs all-API)
  remain flexible — the cognitive layer is provider-agnostic via the
  `LLM` protocol abstraction.

**Reversibility:**

- Hard to reverse. The cognitive architecture shapes the entire
  codebase (memory, affect, reflection, brain panel). Pivoting to RL
  later would require rewriting most of the agent and abandoning the
  brain-panel viewer.
- This is the right kind of "hard to reverse" — it commits us to a
  defensible category position rather than a fungible technical
  approach.

## References

- `docs/product/methodology.md` §3.3 ("What we are NOT doing — RL pivot
  rejected") for the full rationale in product-facing language.
- `docs/product/README.md` strategic positioning section.
- `LESSONS.md` "Don't pivot to RL" entry under Architecture decisions.
- ADR-0002 (State-Transition Signatures) — depends on the cognitive
  architecture being in place.
- ADR-0003 (Hybrid local + API inference) — mitigates the cost downside
  of this decision.
