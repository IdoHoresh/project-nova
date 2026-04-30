# 01 — What is Project Nova?

> Beginner-friendly. No jargon assumed. Read this first.

## The one-line version

**Project Nova is an AI that plays the mobile game 2048 — but it has feelings, memories, and a kind of dopamine system. You can watch it think.**

## Meet Nova

Imagine a person sitting down to play 2048 on their phone. Let's call her Nova.

When Nova plays:

1. She **looks** at the board.
2. She **remembers** similar boards she's seen before.
3. She **feels** something — calm, anxious, frustrated, excited.
4. She **thinks** about which way to swipe.
5. She **swipes**.
6. She **sees the result** and feels something about it (good move felt rewarding, bad move felt frustrating).
7. She **writes the experience down in her memory** for later.
8. She loops back to step 1.

That's the whole project.

The catch is: Nova is not a person. She's software. But she's built so that every one of those steps actually happens — visibly — and you can watch them on a screen as she plays.

## What you'll see when Nova plays

The screen is split in two:

```
┌────────────────────────┬────────────────────────────────┐
│                        │                                │
│   Live 2048 game       │   Nova's mind                  │
│   running in the       │                                │
│   Android emulator     │   - mood (anxious / calm)      │
│                        │   - dopamine pulse (just got   │
│                        │     a good merge!)             │
│                        │   - memory she just retrieved  │
│                        │     ("I lost on a board like   │
│                        │      this two games ago...")   │
│                        │   - what she's thinking right  │
│                        │     now                        │
│                        │   - her next move (with arrow) │
│                        │                                │
└────────────────────────┴────────────────────────────────┘
```

You see the game on the left. You see Nova's mind on the right. As she plays, both panels update live.

## Why does this exist?

Three reasons:

### 1. It's a portfolio piece

The author of this project (Ido) is using it for a job hunt aimed at mobile game studios. "I built an AI that plays mobile games like a human would" is a strong story for studios that work on casual games (Superplay, Sparkplay, Playtika, Playrix, King, and similar).

### 2. It's actually useful for game studios

Casual game studios run constant testing on new content: new levels, new tutorials, new ads, weekly updates. They need bots that can play their games like a human player would, not just rigid scripts.

A regular bot can tell you "this level is winnable." Nova can tell you "this level made me frustrated by move 12 because I kept missing merges, and that frustration is what would cause real players to quit." That's useful in a way that a regular bot isn't.

(Studios use this kind of data for QA, difficulty tuning, tutorial validation, and even ad-creative testing. See the design spec for the full list.)

### 3. The architecture is genuinely interesting

Nova is built using ideas from cognitive science and from recent research on AI agents — combined into one working system. The point isn't to invent new science; it's to take well-tested ideas and put them together cleanly. This is called an **applied synthesis** in research-speak.

## Why 2048?

2048 was picked because:

- The board is simple (4×4 grid, just numbers). Easy for the AI to "see" reliably.
- The action space is tiny (4 directions: up, down, left, right). Easy to act.
- It's instantly recognizable. A recruiter watching a 5-second clip immediately knows what game it is.
- Open-source Unity versions exist with a permissive (MIT) license, so we can fork one and run it on Android.
- It's turn-based — Nova has time to think between moves. No real-time twitch pressure.

It's the friendliest possible target for showing off a brain-inspired AI. Fancier games come in v2 and v3.

## What "brain-inspired" means here

Important: Nova is **not** a brain simulation. Real brain simulation is a multi-decade research project that nobody has solved.

What Nova *is* is a software system whose modules are **inspired by** real findings about how human brains work:

- Real brains have a reward signal (dopamine) that responds to surprise. Nova has a software variable called `dopamine` that does something similar.
- Real brains have memories of bad experiences that bias future caution. Nova has memory entries tagged as "trauma" that bias her future decisions.
- Real brains have moods that shift over time and shape decisions. Nova has mood variables that shift over time and shape her decisions.

The science isn't being faked — every component is anchored in published, well-cited research. But the metaphor is "stylized like the brain," not "actually a brain."

This honest positioning matters: claiming "I built a real human brain in Python" would be ridiculed. Claiming "I built a software system inspired by cognitive science research, and here are the papers" is a strong, defensible portfolio piece.

## Where this fits in the bigger picture

Nova isn't the first AI to play games. She isn't the first AI with memory. She isn't the first AI with simulated emotions. All three have been published.

What makes this project worth building:

- **Synthesis.** All three put together cleanly in one system.
- **Visibility.** A polished UI that makes the AI's internal state legible to a viewer in real time. Most published research papers don't ship a demo this watchable.
- **Application.** Aimed at a specific domain (casual mobile games) where the architecture has plausible commercial value.

## What's next

If you want to understand how Nova actually works:

- **[02 — The Pieces](02-the-pieces.md)** — what an emulator, ADB, VLM, and vector database are, and why we need each
- **[03 — Memory Explained](03-memory-explained.md)** — how Nova remembers things
- **[04 — Emotion Explained](04-emotion-explained.md)** — how Nova feels things
- **[05 — The Decision Loop](05-the-decision-loop.md)** — how a single move happens, step by step
- **[06 — Brain Panel Tour](06-brain-panel-tour.md)** — every element on the UI explained
- **[08 — Glossary](08-glossary.md)** — a quick reference for jargon
- **[09 — Security](09-security.md)** — why keys must never leak, and how the project defends against it
