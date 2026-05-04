# Project Nova — Architecture Overview

> **Audience:** new contributors, technical reviewers, future-you. Read
> this for the system shape; read [`docs/product/methodology.md`](./docs/product/methodology.md)
> for the load-bearing technical detail (4 Signatures, KPI translations,
> Levene's Test math, multi-rate decay).
>
> **Why this exists:** the codebase has multiple subprojects + a complex
> cognitive architecture. Without an overview, every new contributor (or
> session) has to reconstruct the topology from individual files. This
> doc is the topology.

---

## High-level shape

Nova is a CoALA-shaped LLM agent (Sumers et al., 2024) that plays games
in an Android emulator and renders its internal state to a live browser
viewer. Three subprojects + a sequence of well-defined data flows.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────┐                                                    │
│  │ Pixel 6 AVD      │                                                    │
│  │ (Android Studio) │                                                    │
│  │                  │  perception (screencap)                            │
│  │ com.idohoresh.   │ ◄─────────────────────────┐                        │
│  │ nova2048         │                            │                       │
│  │ (Unity 2048      │  action (adb keyevent)    │                       │
│  │ fork)            │ ───────────────────────►   │                       │
│  └──────────────────┘                            │                       │
│                                                   │                       │
│                                          ┌────────┴──────────┐            │
│                                          │ nova-agent        │            │
│                                          │ (Python)          │            │
│                                          │                   │            │
│                                          │ Cognitive arch:   │            │
│                                          │ - Memory          │            │
│                                          │ - Affect          │            │
│                                          │ - Arbiter         │            │
│                                          │ - Reflection      │            │
│                                          └─────────┬─────────┘            │
│                                                    │                       │
│                                          ┌─────────▼──────────┐           │
│                                          │ EventBus           │           │
│                                          │ (WebSocket :8765)  │           │
│                                          └─────────┬──────────┘           │
│                                                    │                       │
│                                          ┌─────────▼──────────┐           │
│                                          │ nova-viewer        │           │
│                                          │ (Next.js :3000)    │           │
│                                          │                    │           │
│                                          │ Brain Panel:       │           │
│                                          │ - Cognition Stream │           │
│                                          │ - Mood gauge       │           │
│                                          │ - Dopamine bar     │           │
│                                          │ - Memory feed      │           │
│                                          └────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Subprojects

### `nova-agent/` — Python cognitive architecture

The agent. Reads game state via OCR on emulator screencaps, decides moves
via LLM (Gemini Flash for ReAct, Gemini Pro for ToT branches), executes
via ADB keyevents, updates internal state (memory + affect), and after
game-over runs reflection to extract semantic rules.

**Stack:** Python 3.11+, pydantic-settings, anthropic + google-genai SDKs,
LanceDB (vector store), SQLite (episodic store), opencv-python-headless +
pytesseract (OCR), fastapi + websockets (event bus), structlog +
tenacity (logging + retries).

**Test infrastructure:** pytest (140+ tests), mypy strict, ruff
(linting + formatting). See `nova-agent/pyproject.toml` for full
dependency manifest. Run `/check-agent` slash command for the full
gate trio.

**Key modules:**
- `nova_agent.adb` — ADB wrapper for input/output
- `nova_agent.affect` — affect vector + RPE update logic + verbalize
- `nova_agent.bus.websocket` — event bus server
- `nova_agent.config` — pydantic-settings (with `env_ignore_empty=True`
  to handle empty-shell-export shadowing; see LESSONS.md)
- `nova_agent.decision.react` — fast-thinking ReAct decider
- `nova_agent.decision.tot` — Tree-of-Thoughts deliberation with
  parallel branch evaluation
- `nova_agent.decision.arbiter` — routes between ReAct and ToT based
  on anxiety + board state
- `nova_agent.llm` — provider-agnostic LLM adapters (Gemini, Anthropic,
  Mock); `LLM` protocol in `protocol.py`
- `nova_agent.memory` — episodic (SQLite + LanceDB) + semantic
  (separate SQLite); aversive tagging for trauma; retrieval coordinator
- `nova_agent.perception.ocr` — board OCR (palette-based; see LESSONS.md
  for the gotcha about new tile colors)
- `nova_agent.reflection.postmortem` — post-game lesson extraction
- `nova_agent.main` — orchestrator (run loop, mode dispatch, event
  publishing)

### `nova-viewer/` — Next.js + React brain panel

The browser-based observer. Connects to the agent's WebSocket bus,
renders a three-column brain panel that shows nova's internal state in
real time: live thinking stream (first-person reasoning, ToT branches
with winner highlight, mode flips, memory recalls, affect crossings),
mood radar (Russell circumplex), dopamine bar, memory feed, and footer
telemetry.

**Stack:** Next.js 16.2.4, React 19.2.4, Tailwind 4, Framer Motion 12.
Test infra: vitest + React Testing Library + jsdom. Use `pnpm`, NOT
`npm` (see CLAUDE.md gotchas).

**Key modules:**
- `app/page.tsx` — top-level layout, WebSocket subscription, derives
  view-state from event stream
- `app/components/ThoughtStream.tsx` — the cognitive thinking stream
  (newest-on-top, sticky scroll, type-coded entries, fade-in motion)
- `app/components/BrainPanel.tsx` — right column with affect visuals
- `app/components/MoodGauge.tsx` — Russell circumplex valence × arousal
- `app/components/DopamineBar.tsx` — RPE bar
- `app/components/ModeBadge.tsx` — INTUITION (ReAct) vs DELIBERATION (ToT)
- `app/components/TraumaIndicator.tsx` — overlay when trauma fires
- `lib/types.ts` — typed `AgentEvent` discriminated union (currently
  has a catch-all that defeats narrowing — slated for fix in Week 0
  Day 1; see LESSONS.md)
- `lib/websocket.ts` — `useNovaSocket` hook
- `lib/stream/deriveStream.ts` — pure-function reducer that walks events
  and produces the stream entries
- `lib/stream/reword.ts` — first-person rewording helper
- `lib/stream/types.ts` — `StreamEntry` discriminated union

### `nova-game/` — Unity build artifacts

Build outputs for the Unity 2048 fork (`com.idohoresh.nova2048`). The
fork itself lives at `~/Desktop/2048_Unity/`; this directory holds APKs
+ reproducible build metadata. Mostly gitignored.

---

## GameIO seam (added 2026-05-04, ADR-0008)

The cognitive loop in `main.run()` reads the world via a `GameIO`
protocol (`nova_agent.action.game_io`) with three methods:
`read_board() -> BoardState`, `apply_move(SwipeDirection) -> None`,
`screenshot_b64() -> str`. Two implementations exist:

- `LiveGameIO` (`nova_agent.action.live_io`) — wraps `Capture` +
  `BoardOCR` + `ADB` for the live emulator path.
- `SimGameIO` (`nova_agent.lab.io`) — wraps `Game2048Sim` + a
  brutalist PNG renderer for in-process play; no emulator dependency,
  no OCR latency, deterministic via seeded `Scenario`.

Pick via `Settings.io_source = "live" | "sim"` (env: `NOVA_IO_SOURCE`);
sim scenarios are loaded by id from `nova_agent.lab.scenarios`
(env: `NOVA_SIM_SCENARIO`, default `"fresh-start"`). The cognitive
layer (decision / affect / memory / reflection) is source-agnostic
above this seam — same code paths run for both. See
[ADR-0008](./docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md)
for the rationale + rejected alternatives.

---

## Data flow per move

For one move of the agent:

1. **Capture.** `nova-agent/main.py` calls `Capture.grab()` which
   shells `adb exec-out screencap -p` to get a PNG of the emulator
   screen.
2. **Perception.** PNG goes to `BoardOCR.read()` which palette-matches
   each cell to produce a `BoardState` (4×4 grid + score).
3. **Memory retrieval.** `MemoryCoordinator.retrieve_for_board()` queries
   the LanceDB vector store for top-K similar past situations, with
   aversive (trauma) records given elevated weight.
4. **Affect description.** Current `AffectVector` is rendered into a
   one-sentence `affect_text` via `affect.verbalize.describe()`.
5. **Mode decision.** `arbiter.should_use_tot()` checks
   `anxiety > 0.6 AND (max_tile >= 256 OR empty_cells <= 3)` — if true,
   route to ToT; otherwise ReAct.
6. **LLM call.**
   - **ReAct path:** single Gemini Flash call with the board image +
     retrieved memories + affect text. Returns structured JSON
     (action + reasoning + observation + confidence).
   - **ToT path:** 4 parallel Gemini Pro calls (one per swipe
     direction), each scoring its candidate. Highest-value branch wins.
     Branch events stream to the bus as they complete.
7. **Action execution.** `ADB.swipe()` sends a DPAD keyevent (the Unity
   fork ignores swipes; see LESSONS.md). Game state changes.
8. **Re-perception.** Next loop iteration captures the post-action
   state.
9. **RPE + affect update.** `AffectState.update()` computes reward
   prediction error from the score delta vs the prediction implied by
   the prior board, updates all 6 affect dimensions.
10. **Memory write.** `MemoryCoordinator.write_move()` persists the
    move to the episodic store with the affect snapshot. If the
    arbiter detected this as a precondition for catastrophic loss,
    it's tagged aversive.
11. **Bus publish.** All of the above (perception, decision, affect,
    memory_write, mode, tot_branch / tot_selected if applicable) get
    published as typed events on the WebSocket bus.
12. **Viewer renders.** `useNovaSocket` receives the events, the stream
    deriver produces the rendered entries, the brain panel updates.

On game-over: a separate `_run_post_game()` path runs reflection (LLM
call to extract a lesson), persists semantic rules, publishes `game_over`
event, and resets affect for the next game.

---

## Where the cognitive architecture lives in the code

| Concept | File(s) |
|---------|---------|
| **Memory** | `nova_agent/memory/` — episodic store, semantic store, retrieval, aversive tagging |
| **Affect vector** | `nova_agent/affect/` — types, state, RPE update, verbalize |
| **Tree-of-Thoughts** | `nova_agent/decision/tot.py` — parallel branch eval |
| **ReAct** | `nova_agent/decision/react.py` — single-call decision |
| **Arbiter** | `nova_agent/decision/arbiter.py` — routes between ReAct and ToT |
| **Reflection** | `nova_agent/reflection/postmortem.py` — post-game lesson |
| **Trauma** | `nova_agent/memory/aversive.py` — aversive tagging + halving |
| **Bus** | `nova_agent/bus/websocket.py` — WebSocket server |
| **Brain panel** | `nova-viewer/app/components/` — all React components |
| **Stream derivation** | `nova-viewer/lib/stream/deriveStream.ts` — event → entry reducer |

---

## How the planned product layer maps to today's architecture

The product (synthetic playtesting service) is roadmapped for Phases 1-6
in [`docs/product/product-roadmap.md`](./docs/product/product-roadmap.md).
The cognitive architecture today is the substrate. The product layer
adds:

| Future component | Built on top of |
|------------------|-----------------|
| **Unity SDK (Phase 1)** | New `Nova.Studio` C# package; talks to existing Python agent via WebSocket bus |
| **GameAdapter abstraction (Phase 1)** | Refactor of existing 2048-specific perception + action code behind a `Protocol` |
| **Local LLM adapter (Phase 1)** | New adapter using existing `LLM` protocol; vLLM + Qwen 2.5 14B |
| **Persona system (Phase 3)** | Parameterized constructors for existing `AffectState` + injection into existing prompts |
| **KPI Translation Layer (Phase 4)** | New module reading from existing event bus; renders Validation Reports |
| **Long-horizon simulation (Phase 4.6)** | Multi-rate decay extension on existing memory store + new SimulatedClock primitive |
| **Production infra (Phase 5)** | Cloud orchestrator wrapping existing single-process agent |

The cognitive architecture itself is **game-agnostic above the
perception/action interface.** GameAdapter extraction in Phase 1 is a
refactor of localized 2048-specific code, not a redesign.

---

## Pointers to deeper reading

| If you need... | Read... |
|----------------|---------|
| Full technical methodology (Signatures, KPI math, Levene's Test) | [`docs/product/methodology.md`](./docs/product/methodology.md) |
| Strategic positioning + market analysis | [`docs/product/README.md`](./docs/product/README.md) |
| Phase-by-phase build plan | [`docs/product/product-roadmap.md`](./docs/product/product-roadmap.md) |
| Why specific architectural choices were made | [`docs/decisions/`](./docs/decisions/) |
| Hard-won engineering lessons | [`LESSONS.md`](./LESSONS.md) |
| Common gotchas + build commands | [`CLAUDE.md`](./CLAUDE.md) |
| Per-subproject conventions | `nova-agent/README.md`, `nova-viewer/AGENTS.md` |
