# 05 — The Decision Loop

> What actually happens between two consecutive moves. Step by step, with a real example.

This doc shows you exactly what Nova does from the moment she finishes one move until she starts the next. Every step is something a real piece of code does. Read it once and you'll understand the whole system.

We'll walk through one move in two settings:
- **Easy case** — early in a game, board is open, nothing exciting.
- **Hard case** — mid-game, board is tight, Nova has trauma history.

## The eight steps

```
       1. PERCEIVE
            ↓
       2. RETRIEVE MEMORIES
            ↓
       3. APPRAISE EMOTION
            ↓
       4. BUILD PROMPT
            ↓
       5. DECIDE (VLM call, possibly with ToT)
            ↓
       6. EXECUTE (ADB swipe)
            ↓
       7. EVALUATE OUTCOME (RPE)
            ↓
       8. WRITE TO MEMORY
            ↓
         (loop)
```

---

# Easy case: opening move

## State

It's the start of a new game. The board:

```
.  .  .  .
.  2  .  .
.  .  .  2
.  .  .  .
```

Score: 0. Empty cells: 14. Nova has no trauma memories triggered (board is too generic).

## Step 1 — Perceive

The agent sends `adb exec-out screencap` to capture a PNG of the emulator screen. The PNG is passed to the **fast OCR module**, which scans the 4×4 grid and reads off the tiles. ~8 milliseconds. Output:

```python
board_state = {
    "grid": [[0,0,0,0],[0,2,0,0],[0,0,0,2],[0,0,0,0]],
    "score": 0,
    "empty_cells": 14,
    "max_tile": 2,
}
```

## Step 2 — Retrieve memories

Nova computes an embedding (numeric fingerprint) of the board. She queries her vector database: "give me the top 5 memories most similar to this one, weighted by recency, importance, and relevance."

The result is mostly irrelevant noise — this is the start of a new game, not a hard situation. Top hit:

> *"Last game you started with a similar empty board and made a swipe-right opener. It worked fine. Importance: 3/10."*

That memory gets attached to working memory.

## Step 3 — Appraise emotion

The system updates Nova's affective state. Since it's the start of a fresh game and nothing has happened yet:

```
valence:     +0.1  (mild positive — fresh start)
arousal:     +0.2  (alert but not tense)
dopamine:     0.0
frustration:  0.0
anxiety:      0.0
confidence:   0.5
```

These numbers get translated into a sentence:

> *"You feel calm and a little curious. Nothing is at stake yet."*

## Step 4 — Build prompt

The agent constructs the prompt for the VLM. It looks something like:

```
SYSTEM:
You are Nova, an AI playing 2048. You see the board, decide which way
to swipe, and explain your reasoning. Output strictly in JSON with
fields: observation, reasoning, action, confidence.

USER:
[image of the board]

Current state:
  Score: 0
  Empty cells: 14
  Max tile: 2

Recent memory:
  "Last game you started with a similar empty board and made a swipe-right
   opener. It worked fine."

Your mood:
  You feel calm and a little curious. Nothing is at stake yet.

Decide your next move.
```

## Step 5 — Decide

Anxiety is low and the board is easy, so the system uses the **default ReAct path** — a single VLM call. ~1 second.

Claude returns:

```json
{
  "observation": "Two 2s on the right side. If I swipe right they merge into a 4.",
  "reasoning": "Easy opener. Builds the right column. Low risk.",
  "action": "swipe_right",
  "confidence": "high"
}
```

The action is parsed and validated. ✓ One of the four valid swipes.

## Step 6 — Execute

The agent runs:

```
adb shell input swipe 900 800 100 800 100
```

(The coordinates are calibrated to the emulator's screen size; this swipes from the right side of the screen to the left, i.e., a swipe-right gesture.)

The emulator responds. Tiles slide right. The two 2s merge into a 4. A new tile appears.

Instead of waiting a fixed ~300ms (emulator lag breaks fixed waits), the agent runs a **visual stability loop**: take a screenshot, take another 50ms later, compare pixel hashes. If they match, the board is static — capture the result. If they don't, wait and try again, up to a hard cap of ~600ms. Robust to dropped frames, doesn't waste time when the animation finishes early. The agent also pixel-diffs the result against the pre-swipe frame: if nothing changed, retry the swipe once; if still nothing, and all four directions have been tried with no change, fire `game_over` (the board is dead). Without that no-op detection the loop could record phantom moves and burn budget swiping at a finished game.

## Step 7 — Evaluate outcome

The outcome evaluator compares:

- Expected score gain (from the value function): `expected = 4` (we predicted one merge)
- Actual score gain: `actual = 4` (one merge happened)
- RPE: `δ = actual − expected = 0` (no surprise)

Since RPE is zero, no dopamine spike. Mood barely changes. Confidence ticks up slightly because the prediction matched reality.

## Step 8 — Write to memory

The system computes an importance score for this event:

- Was it surprising? No (RPE = 0).
- Was it a big merge? No (a 2+2 = 4).
- Was it near game over? No.
- Programmatic importance: 1.
- LLM-rated importance: not requested for low-stakes events.

Final importance: **1/10**. The memory is written to the episodic store with low importance. It will fade fast.

## Loop

Back to step 1 with the new board state.

---

# Hard case: tight board, trauma triggered

Same eight steps. Different content. This is the scenario from earlier in the brainstorm.

## State

Mid-game. 50 moves in. Board:

```
4   8  16  32
2  64 256   4
16  4   8   2
2   8   4   .
```

Score: 1840. Empty cells: 1. There's a 256 stuck in the middle. The board is dangerously full.

## Step 1 — Perceive

Fast OCR reads the board. ~8ms.

## Step 2 — Retrieve memories

Embedding query against the vector database. The top hit comes back with a special tag:

> 📕 **TRAUMA TAG.** *"Two games ago, you had a 256 stuck in the middle with one empty cell. You swiped down impulsively and lost the game three moves later. Importance: 9/10."*

This memory is high-importance and high-relevance, and it's tagged as trauma. The retrieval system gives it extra weight and a wider similarity threshold (which is how it surfaces here even though the board isn't an exact match — it's just *similar enough*).

Two more memories also come back: a near-miss from this same game, and a successful corner play from last game. All three are attached to working memory.

## Step 3 — Appraise emotion

The trauma tag triggers an automatic anxiety bump. The full state update:

```
valence:     -0.3   (tense, slight unease)
arousal:     +0.8   (highly alert — game over near)
dopamine:    -0.1   (last few moves earned little)
frustration: +0.4   (no good merges in a while)
anxiety:     +0.7   (rising — recalling past loss)
confidence:  +0.3
```

Translated to text:

> *"You feel anxious. The board is tight. You remember losing on a board like this. You don't fully trust your strategy. You want to play safe."*

## Step 4 — Build prompt

The prompt now contains the tight board, the trauma memory (rendered as "you remember losing on a board like this two games ago by swiping down"), and the anxiety-laden mood description.

## Step 5 — Decide

Anxiety is `0.7` and `max_tile = 256`. The trigger condition for **Tree-of-Thoughts deliberation** fires:

```
anxiety > 0.6  AND  (max_tile >= 256  OR  empty_cells <= 3)
```

The system enters ToT mode (System 2 — slow, deliberate). It evaluates 4 candidate moves **in parallel**, and each evaluation streams a card to the brain panel as it completes — so the viewer sees Nova's thinking unfold in real time, not a 3-second freeze:

> *"If I swipe up — the bottom-row 16 merges with the row-above 16. Good. The 256 stays stuck. Slight improvement."* → value 0.62 (card appears, blue border)
>
> *"If I swipe down — like last time, like the trauma. The bottom row's 4s and 2s would merge but the 256 sinks deeper. **Bad. Same shape that killed me.**"* → value 0.18 (card appears, neutral)
>
> *"If I swipe left — the right column collapses, I lose access to the 256 from the right. Reduces my options. Bad."* → value 0.31 (card appears)
>
> *"If I swipe right — small merges, doesn't free the 256 but doesn't make things worse either. Cautious option."* → value 0.45 (card appears)

When all four branches have streamed in, the chosen branch (`swipe_up`, value 0.62) highlights with a cyan border; the rejected three grey out. Each ToT branch is **read-only with respect to memory** — branches query past episodes but never write — so we don't have to worry about race conditions on the SQLite/LanceDB store. Writes happen on the main loop *after* the chosen branch is committed.

Total ToT wall-clock time: ~2–4 seconds. Visually, that reads as deliberation, not as a crash.

Final output:

```json
{
  "observation": "Board is critical. 256 stuck. One empty cell.",
  "memory_invoked": "Trauma — lost on a similar board after swiping down.",
  "reasoning": "Anxiety is high. Avoid the move that killed me. Up gives a real merge AND avoids the trauma pattern.",
  "action": "swipe_up",
  "confidence": "medium"
}
```

## Step 6 — Execute

ADB swipe up. Tiles slide. 16+16 merges into 32. Score 1840 → 1872. A new tile appears in the now-empty cell.

## Step 7 — Evaluate outcome

- Expected score gain: ~28 (we predicted one merge of two 16s)
- Actual: +32 (slightly better — the 8s also reorganized into a more efficient shape)
- RPE: `δ = +0.07` (small positive surprise)

Updates:

```
dopamine:    0.2  (small spike)
valence:     -0.1 (still tense, but slightly relieved)
anxiety:     0.5  (eased — trauma move was avoided)
confidence:  0.45 (small bump — prediction was approximately right)
```

The brain panel **pulses the dopamine bar** and the anxiety meter dips visibly.

## Step 8 — Write to memory

Importance check:
- Was it surprising? Mildly (board was scary, found a safe move).
- Was it near game over? Yes.
- Did it echo a past trauma successfully avoided? **Yes.**

Programmatic importance: 6. LLM-rated importance: 8. Average: **7/10**.

The memory is written with high importance and tagged: `["trauma_avoided", "tight_board"]`. Next time Nova sees a similar board, this *success* memory will surface alongside the trauma, with a "you've handled this before" framing.

The original trauma-tagged memory's weight is slightly reduced (regulatory decay) — successful avoidance softens the trauma over time.

## Loop

Back to step 1 with the new board state.

---

## Latency budget

For each move:

| Step | Latency target |
| --- | --- |
| Perceive | < 50ms |
| Retrieve memories | < 100ms |
| Appraise emotion | < 5ms |
| Build prompt | < 5ms |
| Decide (default) | < 1500ms |
| Decide (ToT) | < 4000ms |
| Execute (ADB swipe + animation) | ~400ms |
| Evaluate outcome | < 50ms |
| Write to memory | < 50ms |

Default-path total: under 2 seconds per move.
ToT-path total: under 5 seconds per move.

A full game runs ~200–800 moves, so ~7–40 minutes of wall-clock time depending on how often ToT fires. Watchable on a livestream, recordable for a demo clip.

## What viewers see

Throughout all 8 steps, the brain panel viewer is updating in real time. Every internal state change — perception, retrieval, mood update, reasoning, action, outcome, memory write — is broadcast over WebSocket and rendered live. The next doc, [06 — Brain Panel Tour](06-brain-panel-tour.md), walks through every UI element.

## Summary in one sentence

Nova looks → remembers → feels → thinks → acts → sees the result → updates her feelings → writes it down → repeats.
