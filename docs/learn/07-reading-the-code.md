# 07 — Reading the Code

> A guide to navigating the Nova codebase once it's built.

**Status:** This document is a placeholder. It will be filled in as the code is written. The structure below reflects the planned architecture from the design spec.

## Repository layout

```
project-nova/
├── nova-agent/        ← Python: Nova's brain
├── nova-viewer/       ← Next.js: the brain panel UI
└── nova-game/         ← Forked Unity 2048 + Android build instructions
```

Each subdirectory is its own self-contained project with its own README, dependencies, and build process.

## nova-agent (Python)

Planned module layout:

```
nova-agent/
├── pyproject.toml
├── README.md
├── tests/
└── src/nova_agent/
    ├── __init__.py
    ├── main.py                    # entry point — runs the decision loop
    ├── config.py                  # settings, paths, API keys via env
    │
    ├── perception/
    │   ├── __init__.py
    │   ├── capture.py             # ADB screencap → PNG
    │   ├── ocr.py                 # fast tile-digit OCR (OpenCV)
    │   └── vlm_perception.py      # VLM fallback for unknown tiles
    │
    ├── memory/
    │   ├── __init__.py
    │   ├── episodic.py            # SQLite episodic event log
    │   ├── semantic.py            # SQLite semantic-rules table
    │   ├── vector_store.py        # LanceDB adapter
    │   ├── retrieval.py           # recency + importance + relevance scoring
    │   ├── importance.py          # programmatic + LLM-rated importance
    │   └── trauma.py              # trauma tagging + retrieval-radius logic
    │
    ├── affect/
    │   ├── __init__.py
    │   ├── state.py               # the affect vector + update rules
    │   ├── rpe.py                 # outcome evaluator, value function V
    │   └── verbalize.py           # turn affect vector into prompt sentence
    │
    ├── decision/
    │   ├── __init__.py
    │   ├── react.py               # default ReAct path (single VLM call)
    │   ├── tot.py                 # Tree-of-Thoughts deliberation
    │   ├── arbiter.py             # decide which path to use
    │   ├── prompts.py             # prompt templates
    │   └── heuristic.py           # Take-The-Best fallback
    │
    ├── reflection/
    │   ├── __init__.py
    │   └── postmortem.py          # post-game reflection, writes semantic rules
    │
    ├── action/
    │   ├── __init__.py
    │   └── adb.py                 # ADB swipe execution
    │
    ├── bus/
    │   ├── __init__.py
    │   └── websocket.py           # publish state events to the brain panel
    │
    └── llm/
        ├── __init__.py
        ├── anthropic_client.py    # Anthropic SDK wrapper
        ├── structured.py          # JSON parsing, retries, validation
        └── embeddings.py          # board → embedding
```

### Key entry point: `main.py`

The decision loop lives here. Pseudocode:

```python
async def main():
    components = bootstrap_all_modules()
    bus = components.bus
    
    while True:
        board = components.perception.capture_and_perceive()
        bus.publish("perception", board)
        
        memories = components.memory.retrieve(board, top_k=5)
        bus.publish("retrieval", memories)
        
        affect = components.affect.appraise(board, memories)
        bus.publish("affect", affect)
        
        decision = components.decision.decide(board, memories, affect)
        bus.publish("decision", decision)
        
        components.action.execute(decision.action)
        
        new_board = components.perception.capture_and_perceive()
        outcome = components.affect.evaluate_outcome(board, new_board, decision)
        bus.publish("outcome", outcome)
        
        components.memory.write(board, decision, outcome)
        bus.publish("memory_write", ...)
        
        if components.perception.detect_game_over(new_board):
            reflection = components.reflection.run(this_game)
            components.memory.write_semantic(reflection)
            bus.publish("reflection", reflection)
            components.action.restart_game()
```

Real code will be cleaner and async-await-styled, but the shape is this.

### How to run (planned)

```bash
cd nova-agent
uv sync                # install dependencies
cp .env.example .env   # configure API keys
uv run nova            # start the agent
```

## nova-viewer (Next.js)

Planned module layout:

```
nova-viewer/
├── package.json
├── README.md
├── tsconfig.json
├── tailwind.config.ts
├── public/
└── app/
    ├── layout.tsx
    ├── page.tsx                   # main brain panel page
    └── components/
        ├── GameStream.tsx         # left column: scrcpy stream
        ├── MoodGauge.tsx          # 2D circumplex gauge
        ├── DopamineBar.tsx        # vertical pulse bar
        ├── AffectLabel.tsx        # one-sentence affect text
        ├── MemoryFeed.tsx         # stack of memory cards
        ├── MemoryCard.tsx         # individual memory card
        ├── ModeBadge.tsx          # INTUITION / DELIBERATING
        ├── ReasoningText.tsx      # streaming reasoning text
        ├── ActionArrow.tsx        # animated swipe direction
        ├── TraumaIndicator.tsx    # red glow when trauma active
        └── StatsFooter.tsx
└── lib/
    ├── websocket.ts               # subscribes to the agent's WS channel
    └── types.ts                   # shared event types
```

### How to run (planned)

```bash
cd nova-viewer
npm install
npm run dev    # open http://localhost:3000
```

(The viewer expects the agent's WebSocket to be live at `ws://localhost:8765` or similar — configurable via env.)

## nova-game (Unity 2048 fork)

This directory contains:
- A README pointing at `stdbilly/2048_Unity` and instructions for forking it
- Custom build settings for Android export
- An installer script that builds the APK and installs it on a connected emulator

Likely most of the actual Unity project files won't be checked in here — the fork lives as a separate Unity workspace. The `nova-game` directory holds setup instructions, build scripts, and any custom scripts/asset overrides.

## Suggested reading order for the codebase

When the code exists, start here:

1. **`nova-agent/src/nova_agent/main.py`** — see the whole loop in 80 lines.
2. **`nova-agent/src/nova_agent/decision/prompts.py`** — see what Nova actually says to the VLM.
3. **`nova-agent/src/nova_agent/affect/state.py`** — see the affect update rules.
4. **`nova-agent/src/nova_agent/memory/retrieval.py`** — see the Park-style retrieval formula in code.
5. **`nova-viewer/app/page.tsx`** — see how the UI lays out.

After those five files you'll have a complete mental model of Nova.

## Update note

This document will be filled in with real code references, line numbers, and worked examples once implementation is underway. Until then, treat it as the planned skeleton.
