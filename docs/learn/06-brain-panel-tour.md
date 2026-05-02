# 06 — Brain Panel Tour

> Every element on the UI, what it shows, and why it matters.

The brain panel is the project's most important artifact. The architecture matters, but what people will actually *see* on LinkedIn is this UI. Every pixel earns its place.

## The whole thing at a glance

Single window, two columns, side-by-side:

```
┌────────────────────────────────┬──────────────────────────────────────────┐
│                                │                                          │
│       LIVE 2048 GAME           │              NOVA'S MIND                 │
│       (left column)            │              (right column)              │
│                                │                                          │
│                                │   ┌─ MOOD GAUGE ─┐    ┌─ DOPAMINE ─┐    │
│                                │   │              │    │            │    │
│                                │   │   ●          │    │   ▮▮▮▮     │    │
│                                │   │              │    │            │    │
│                                │   └──────────────┘    └────────────┘    │
│       [scrcpy stream of        │                                          │
│        Android emulator        │   ┌─ AFFECT TEXT ───────────────────┐   │
│        running 2048]           │   │ "anxious, recalling past loss"  │   │
│                                │   └─────────────────────────────────┘   │
│                                │                                          │
│       Score: 1872              │   ┌─ MEMORY FEED ───────────────────┐   │
│       Move: 51                 │   │ 📕 [TRAUMA] Lost on similar     │   │
│                                │   │     board 2 games ago    9/10   │   │
│                                │   │ ✓ Corner play 3 moves ago 4/10 │   │
│                                │   │ ✓ Big merge last game     6/10  │   │
│                                │   └─────────────────────────────────┘   │
│                                │                                          │
│                                │   ┌─ MODE BADGE ────┐                   │
│                                │   │ 🔴 DELIBERATING │                   │
│                                │   └─────────────────┘                   │
│                                │                                          │
│                                │   ┌─ REASONING ─────────────────────┐   │
│                                │   │ "Trauma move was DOWN. Going UP │   │
│                                │   │  — merge the 16s, stay safe."   │   │
│                                │   └─────────────────────────────────┘   │
│                                │                                          │
│                                │   ┌─ ACTION ──┐   Game stats footer    │
│                                │   │     ↑     │   Games: 12  Best: 4096│
│                                │   │  SWIPE UP │   Mood trend: ▁▂▃▅▆▆▇▆ │
│                                │   └───────────┘                          │
└────────────────────────────────┴──────────────────────────────────────────┘
```

Now let's walk through each element.

## Left column — the live game

**What it shows.** A live, smooth video of the Android emulator running 2048. Updated at ~30 frames per second via scrcpy.

**Why this matters.** If we used screenshots that update once every 2 seconds, the demo would look frozen and dead between Nova's moves. With a live stream, viewers see the game running continuously — tile slide animations, new tiles appearing, etc. — even when Nova herself is "thinking."

**Above/below the game.**

- **Score** — current 2048 score, large, prominent.
- **Move count** — incremented after every confirmed swipe.

That's all on the left side. Keep it clean. The left column is the "game"; the right column is "Nova."

## Right column — Nova's mind

This is the differentiator. Every element below is a window into one of Nova's internal modules.

### 1. Mood gauge

A 2D point on a circular disk (Russell's circumplex):

```
       HIGH AROUSAL
            ↑
            ●  ←── Nova's current mood is here

   ←──── ──── ──── ──── ──→
NEG VAL              POS VAL
   ←──── ──── ──── ──── ──→

            ↓
       LOW AROUSAL
```

**What it shows.** Where Nova is right now on the valence × arousal map.

**Animation.** The point smoothly tweens to its new position whenever mood changes. No abrupt jumps.

**Color.** The point's color encodes the mood: red-orange when low valence + high arousal (anxious/angry); green when high valence + low arousal (calm); bright yellow when high valence + high arousal (excited); blue when low valence + low arousal (sad/withdrawn). Saturation scales with arousal so high-arousal moods look more "alive."

**Why this matters.** Mood is normally invisible. Showing it on a 2D gauge with smooth animation makes it watchable and intuitive. A viewer with no AI background can look at the gauge and immediately tell "Nova is feeling anxious right now."

### 2. Dopamine pulse bar

A vertical bar that pulses upward when dopamine spikes, then decays.

**What it shows.** The current dopamine level (the recent reward-prediction-error signal). Bright cyan when active, dim when at baseline.

**Animation.** When `dopamine` jumps (because Nova just got a better-than-expected outcome), the bar shoots up and then slowly decays. Visually punchy.

**Why this matters.** This is THE element that makes the "AI feels rewards" claim legible. A viewer sees the dopamine pulse on a satisfying merge and immediately understands: *"oh, the AI is being rewarded for that move."*

### 3. Affect text label

A single sentence describing Nova's current emotional state in plain English.

Examples:
- *"calm and curious — nothing at stake"*
- *"anxious, recalling past loss"*
- *"frustrated, wants a big play"*
- *"riding high — last few moves were great"*

**What it shows.** The output of the affect → natural-language templating function (see [04 — Emotion Explained](04-emotion-explained.md)).

**Animation.** Crossfades when the sentence changes, so it doesn't flicker.

**Why this matters.** Numbers are abstract. A sentence is immediate. This sentence is also the exact text injected into the VLM prompt, so the viewer knows exactly what Nova is being told about herself.

### 4. Memory feed

A vertical stack of memory cards, showing the top 3–5 memories currently in working memory.

Each card has:
- **A tiny rendered board snapshot** (an icon, ~40×40px, showing the board state of that memory)
- **A one-line summary** ("Lost on similar board 2 games ago")
- **An importance badge** (e.g., `9/10` in a colored pill)
- **Tags** (`📕 trauma`, `✓ success`, `tight_board`)

**Animation.** New memories slide in from the top with a subtle highlight; old memories drift off the bottom. Trauma-tagged memories pulse subtly.

**Why this matters.** This is where the project visibly does something most "AI plays game" demos don't — it shows the AI actively retrieving and using past experience. A viewer sees a trauma memory surface right before Nova plays cautiously and instantly understands the connection.

### 5. Mode badge

A single visual indicator of which decision path Nova just took:

- 🟢 **INTUITION** (default ReAct path — fast, single VLM call)
- 🔴 **DELIBERATING** (Tree-of-Thoughts active — multi-branch evaluation)

**Animation.** When the mode flips, a snappy transition (fade-and-slide). The badge stays visible while the move is being made.

**Why this matters.** This visualizes the dual-process aspect of the architecture (Kahneman's System 1 / System 2 mapping). Viewers see Nova switch from fast to deliberate mode on hard boards. Watchable proof that her behavior actually changes with situation difficulty.

### 6. Reasoning text (System 1 / INTUITION mode)

The raw `reasoning` field from the VLM's output, displayed live, on the default (System 1) path.

Examples:
> *"Trauma move was DOWN. Going UP — merge the 16s, stay safe."*
>
> *"Easy opener. Two 2s on the right, swipe right to merge. Low risk."*

**Animation.** Streaming text — appears character-by-character as the VLM generates it. Like a typewriter.

### 6b. ToT branch panel (System 2 / DELIBERATING mode)

When the mode badge flips to DELIBERATING, the Reasoning Text view is replaced by the **ToT branch panel** — a vertical stack of branch cards. One card appears for each candidate move as the VLM finishes evaluating it (parallel branches stream in over 2–4 seconds, in any order). Each card shows:

- The direction arrow (↑ ↓ ← →)
- The estimated value (0.00–1.00)
- A 1–2 sentence justification

When all branches complete, the **chosen branch highlights with a cyan border**; the rejected branches grey out (~35% opacity). The viewer sees Nova explicitly reject the bad futures and pick the best one — the deliberation reads as visible thinking, not as a frozen UI.

**Why this matters.** This is the literal "watch the AI deliberate" payoff. Without per-branch streaming, ToT mode would look like a 3-second crash. With it, ToT is the most compelling visualization in the whole demo — and the most direct possible answer to "but is this just one big API call?" (No: you can see the branches.)

### 7. Action arrow

A large directional arrow that animates each time Nova commits to a move.

**Animation.** Directional swoosh in the direction of the swipe (up/down/left/right), brief flash, fade. Persists for ~1 second after the action so viewers register what happened.

**Why this matters.** Combined with the live-game stream on the left, this lets a viewer correlate "Nova decided to go up" with the actual tile-slide on the game. Connection between intention and effect.

### 8. Trauma indicator (active state)

When an aversive-tagged memory is currently active in working memory, a subtle red glow appears around the right column. (The technical name is "Aversive Memory Tag" — see [03-memory-explained.md](03-memory-explained.md). The UI keeps the punchier "Trauma" label.)

**Animation.** Slow pulse. Fades when the aversive memory drops out of working memory (either by extinction-halving below the inert threshold, or by simply not being retrieved next move).

**Why this matters.** Adds an emotional weight to the demo. A viewer sees the red glow appear, looks at the memory feed, sees the trauma card, and connects: *"oh, she's playing under the shadow of a past loss right now."* Powerful demo moment.

### 9. Stats footer

A thin strip at the bottom of the right column showing session-level stats:

- Games played this session
- Best score
- Total moves
- A small mood-trend sparkline showing how valence has moved over the last ~50 moves

**Why this matters.** Context. Lets the viewer see that they're not watching a one-off lucky run; this is sustained behavior.

## Color and motion language

To keep the panel cohesive:

| Concept | Color | Motion |
| --- | --- | --- |
| Reward / dopamine | bright cyan | pulse up + decay |
| Trauma / threat | dark red | slow pulse |
| Reasoning / thinking | neutral white/gray | typewriter |
| Mood (positive) | green/yellow | smooth tween |
| Mood (negative) | red/blue | smooth tween |
| Mode change | bright accent | snappy slide |
| Memory retrieval | gentle violet highlight | slide-in from top |

Consistent language so a viewer learns the vocabulary in 10 seconds.

## What's NOT on the panel

A deliberate list. Things we leave off because they'd be noise:

- Raw numerical values for affect variables (use the gauges and text instead)
- Embedding vectors (meaningless to a human)
- VLM token counts, latency, cost (debug info, not demo info)
- Full memory database listing (the feed shows only what's relevant *now*)
- Game internals (tile spawn probabilities, AI difficulty settings — n/a for 2048)

The panel shows what makes the AI's behavior legible. Nothing else.

## How it's built

- **Framework:** Next.js (React, TypeScript)
- **Animation library:** Framer Motion (smooth tweens, spring animations)
- **Styling:** Tailwind CSS
- **Data:** Subscribes to a WebSocket endpoint published by the Nova agent. Each event the agent emits (perception, retrieval, mood update, reasoning chunk, action, outcome, memory write) is rendered as a state update.
- **Layout:** Two-column flexbox. Left column has fixed-aspect for the scrcpy stream. Right column scrolls if needed but ideally fits in viewport.

The whole thing renders at 60fps on any modern machine. Recordable cleanly via OBS as a single window.

## Polish budget

Allocate **at least one full week** of focused work on this UI after the agent works end-to-end. This is the demo. Animations, color theory, typography, micro-interactions all matter. If you have a designer friend, get a review.

This UI is what a recruiter sees. Most of the project's "wow" lives here.
