# Architecture Decision Records (ADRs)

> **What this is:** a permanent log of significant architectural decisions
> made on Project Nova. Each ADR captures the *context*, the *decision*,
> the *consequences*, and the *alternatives considered*.
>
> **Why ADRs matter:** future-you (or future contributors) will inherit
> a codebase shaped by hundreds of decisions, most of which are invisible.
> Without a written record, every "why is it like this?" question becomes
> archeology. ADRs make the reasoning durable.

---

## When to write an ADR

Write an ADR when a decision:

1. **Is hard to reverse.** Choosing a database, a primary language, a
   protocol, an architectural pattern. Things that have downstream
   consequences across the codebase.
2. **Affects multiple components.** Cross-cutting concerns like the bus
   protocol, persona schemas, the LLM adapter pattern.
3. **Has non-obvious alternatives.** If "why did you do it this way?"
   has multiple defensible answers, document why the chosen one won.
4. **Has been contested or revisited.** If you've already had the
   discussion twice, the third time write the ADR.

Don't write an ADR for:

- Routine implementation choices (which library? trivial code style?)
- Anything that's already in the methodology page or README
- Decisions that are easily reversible (file naming conventions,
  internal helper APIs)

---

## ADR template

Copy `0000-template.md` to `00NN-short-kebab-title.md`, fill in, commit.

Each ADR has:

- **Status:** Proposed / Accepted / Deprecated / Superseded by ADR-NNN
- **Context:** What's the situation that requires a decision?
- **Decision:** What did we choose to do?
- **Alternatives considered:** What did we reject and why?
- **Consequences:** What follows from this choice — both good and bad?
- **References:** Related ADRs, methodology sections, external papers.

---

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| 0001 | [Cognitive architecture as the product moat (not RL, not pure prompting)](./0001-cognitive-architecture-as-product-moat.md) | Accepted | 2026-05-02 |
| 0002 | [State-Transition Signatures over 1:1 affect-to-KPI mappings](./0002-state-transition-signatures.md) | Accepted | 2026-05-02 |
| 0003 | [Hybrid local + API inference (System 1 / System 2 routing)](./0003-hybrid-local-api-inference.md) | Accepted | 2026-05-02 |
| 0004 | [Product positioning: cognitive audit & prediction platform (not a QA tool)](./0004-product-positioning.md) | Accepted | 2026-05-02 |
