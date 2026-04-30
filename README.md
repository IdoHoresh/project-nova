# Project Nova

A brain-inspired AI agent that plays mobile games — with memory, mood, dopamine, and trauma. Watch the AI think in real time.

> *Most game AIs are pure decision machines. Nova has feelings.*

## What this is

Project Nova is a vision-language-model agent that plays the mobile game **2048** running in an Android emulator. The agent operates strictly black-box — it sees the screen, sends touches and swipes. No code instrumentation, no memory access, no game-state hooks.

What makes Nova different from "GPT-4V plays a game" demos:

- **Episodic memory** — remembers past games and retrieves analogous past situations.
- **Affect** — tracks mood (valence × arousal), dopamine, frustration, anxiety as persistent state across the entire play session.
- **Reward prediction error** — a TD-error signal modeled on the dopamine system in mammalian brains.
- **Trauma** — catastrophic losses leave high-importance, high-persistence memories that bias future caution.
- **Reflection** — after each game, Nova writes a verbal postmortem and distills lessons into semantic memory.
- **Transparent reasoning** — every internal state is visible in real time on a side-by-side brain panel.

This is an **applied synthesis** of recent cognitive-architecture-for-LLM-agents research, not a research-novel contribution. See the [design spec](docs/specs/2026-04-30-project-nova-design.md) for citations.

## Status

Early development. Currently in design phase. No runnable code yet.

## Repository layout

```
project-nova/
├── docs/
│   ├── specs/         # Architecture and design documents
│   └── learn/         # Beginner-friendly primers explaining every concept
├── nova-agent/        # Python — perception, memory, affect, decision loop, reflection
├── nova-viewer/       # Next.js — the brain panel UI
└── nova-game/         # Forked Unity 2048 build (target game)
```

## Documentation

- **[Design specification](docs/specs/2026-04-30-project-nova-design.md)** — full architecture, citations, scope, validation plan.
- **[Beginner primers](docs/learn/)** — read these first if you want to understand the project end-to-end.
  - [01 — What is Project Nova](docs/learn/01-what-is-project-nova.md)
  - [02 — The Pieces](docs/learn/02-the-pieces.md)
  - [03 — Memory Explained](docs/learn/03-memory-explained.md)
  - [04 — Emotion Explained](docs/learn/04-emotion-explained.md)
  - [05 — The Decision Loop](docs/learn/05-the-decision-loop.md)
  - [06 — Brain Panel Tour](docs/learn/06-brain-panel-tour.md)
  - [07 — Reading the Code](docs/learn/07-reading-the-code.md)
  - [08 — Glossary](docs/learn/08-glossary.md)

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

The forked 2048 base game uses [stdbilly/2048_Unity](https://github.com/stdbilly/2048_Unity) (MIT).

Architectural inspiration cited in full in the design spec. Key references:

- Sumers et al. (2024) — Cognitive Architectures for Language Agents (CoALA)
- Park et al. (2023) — Generative Agents: Interactive Simulacra of Human Behavior
- Croissant et al. (2024) — Appraisal-Based Chain-of-Emotion for Affective LLM Game Agents
- Schultz, Dayan, Montague (1997) — A Neural Substrate of Prediction and Reward
- Shinn et al. (2023) — Reflexion: Language Agents with Verbal Reinforcement Learning
