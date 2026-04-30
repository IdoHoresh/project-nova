# 03 — Memory Explained

> How Nova remembers things, and why memory is interesting in an AI system.

## The naive way to give an AI memory

The simplest thing you can do is: every time the AI takes an action, append a line of text to a long log, and feed the entire log back to the AI on its next decision.

That breaks for two reasons:

1. **Cost and context limits.** AI models can only read so much text per call. After a few hundred moves, the log doesn't fit. You'd have to send a smaller and smaller fraction of it, which means losing information arbitrarily.
2. **Noise.** Most events in 2048 are boring. "I swiped right and merged two 2s into a 4." Repeated 500 times. If you feed all of that back in, the AI drowns in trivia and can't see the meaningful patterns.

A real memory system has to be **selective** — it has to know what's worth keeping, what's worth retrieving when, and what to forget.

## How human memory works (very simplified)

Cognitive science divides long-term memory into three kinds (Tulving 1972):

| Type | What it stores | Example for 2048 |
| --- | --- | --- |
| **Episodic** | Specific events, with time and context | "Last Tuesday I lost a game with a 512 stuck in the corner" |
| **Semantic** | General facts and rules | "Keeping the largest tile in a corner is generally good" |
| **Procedural** | Skills/motor patterns | The reflex of swiping a certain way without thinking |

Nova has all three.

There's also **working memory** — the small amount of information you can hold actively in your head right now. Cognitive scientists estimate it's about 4 things at a time (Cowan 2001). Nova has a working memory too, and it's deliberately kept small.

And finally there's **trauma**, which isn't a separate memory type but a *tag* on episodic memories — a marker that says "this one is especially important because it was a bad outcome." Trauma memories surface more readily and bias future decisions toward caution. Nova has these too.

## How Nova's memory works

### Working memory

The current board, the last few moves, what Nova just retrieved from long-term memory, and her current mood — all bundled together and fed to the AI for the next decision. This lives in the prompt that gets sent to Claude.

### Episodic memory

Every move Nova ever makes goes into a log. Each entry looks roughly like this:

```json
{
  "id": "ep_2026-04-30T12:34:56.789Z",
  "board_before": [[0,2,0,0],[0,0,0,2],[0,0,0,0],[0,0,0,0]],
  "action": "swipe_right",
  "board_after": [[0,0,0,4],[0,0,0,2],[0,0,0,0],[0,0,0,0]],
  "score_delta": 4,
  "rpe": 0.0,
  "importance": 1,
  "tags": [],
  "embedding": [0.12, -0.04, 0.88, ...]
}
```

The log is **append-only** — Nova never deletes a memory. She just retrieves the relevant ones when she needs them.

The crucial fields:

- **`importance`** (1–10). How memorable was this event? A boring opening swipe = 1. A catastrophic loss = 10. This is computed two ways: programmatically (e.g., a near-game-over move = high importance) and via an LLM rating ("on a scale of 1-10, how memorable is this?"). The two are averaged.
- **`tags`**. Special markers like `trauma`, `success`, `tight_board`. Used at retrieval time to bias which memories surface.
- **`embedding`**. A list of numbers that represents the "meaning" of the board. Used for similarity search.

### Semantic memory

After a game ends, Nova reflects (more on this in [05](05-the-decision-loop.md) and the spec). The reflection produces sentences like:

> *"When the corner anchor is broken, I tend to lose within ~10 moves."*
> *"Aggressive merging in the early game creates space but burns my big tile."*

These get stored as **semantic memory rules** — not tied to a specific game, but distilled wisdom. They're injected into Nova's prompt when relevant.

### Procedural memory

In v1 the procedural-memory role is filled by the **heuristic fallback policy** (Take-The-Best). The VLM itself is *not* procedural memory — its weights are general semantic/linguistic representations, and equating LLM weights with the amygdala/basal-ganglia substrate of human procedural memory is a stretch the spec deliberately avoids. The VLM is the **semantic / working-memory engine**; the heuristic is the procedural fallback. In v2 we may add an explicit "skill library" (Voyager-style — Wang et al. 2023) where Nova can write and store named strategies.

### Aversive memory tags (informally: "trauma")

After Nova loses a game *catastrophically* (low score, on a contested board), the system goes back through the last 3–5 moves and flags those board states as **aversive memories**. They get:

- `importance += 3` (so they survive forgetting longer)
- An `aversive` tag
- A wider similarity threshold for retrieval (so even *loosely* similar boards trigger them) — `aversive_radius`
- An `aversive_weight` initialized to `1.0`

Effect: next time Nova sees a board that's even somewhat reminiscent of where she died, the aversive memory surfaces, her anxiety rises, and she plays more cautiously.

**Why not "trauma"?** In code we use "aversive" because "trauma" is a clinical word and overclaiming the metaphor invites pushback. The brain-panel UI still says "Trauma" — that's the marketing surface, kept for the demo. The codebase identifiers (`aversive_tag`, `aversive_weight`, `aversive_radius`) keep the engineering rigorous.

**Four spiral defenses.** A "trauma death-spiral" — Nova panics on every board, plays badly, loses again, panics more — is a real risk. The architecture has four guards against it:

| | Defense | What it does |
| --- | --- | --- |
| A | **Active-tag cap** | At most ONE aversive memory surfaces per move (the highest-`aversive_weight` × relevance match). Nova never reads two aversive memories at once. |
| B | **Exposure-extinction halving** | Each survival on an aversive-radius-similar board halves that memory's `aversive_weight`. After ~6 survivals the weight is < 0.02 and the memory becomes inert. **This is the primary deterministic guarantee** — the spiral terminates mathematically, not because the LLM cooperates. |
| C | Semantic override | Reflection can write a `trauma_outdated` rule. Best-effort only — LLMs reliably underweight abstract textual rules against dominant visual context. Not load-bearing. |
| D | Cross-game affect reset | On `game_start`: anxiety, frustration, dopamine reset to baseline. Valence retains 30% (slow variable, by design). |

The architecture leans on **A and B** for correctness. C is a bonus; D is hygiene. This is intentional: deterministic mechanisms first, LLM-mediated mechanisms second.

This is metaphor inspired by amygdala-modulated emotional memory (LeDoux 1996; Phelps 2004; McGaugh 2013), **not** a literal model of any circuit. We make no claim of replicating reconsolidation, time-extinction, or context-dependent retrieval. The science justifies "biased retrieval after high-arousal events." The rest is engineering.

## How retrieval works (the important part)

When Nova is about to make a move, the system needs to surface a few relevant past memories. Naively, you'd just grab "the most recent ones" or "the most similar ones" — but that misses the point. Some old memories are still important; some recent ones are noise; some dissimilar memories are still relevant for other reasons.

The retrieval formula comes from Park et al.'s **Generative Agents** (2023). Each candidate memory gets scored:

```
score = α_recency · recency
      + α_importance · importance
      + α_relevance · relevance
```

- **`recency`**: how long ago was this memory accessed? More recent = higher.
- **`importance`**: the 1–10 rating stored with the memory.
- **`relevance`**: how similar is this memory's board to the *current* board? Computed via cosine similarity of embeddings.

All three are normalized to [0,1] and weighted (initially equal weights). Top 5 memories by total score are surfaced.

**Side note on `last_accessed`.** Every retrieved memory has its `last_accessed` field written back to "now" after retrieval. Without that write-back, retrieved memories would stay "old" forever and the recency term would become a no-op.

**Lost-in-the-Middle mitigation.** The retrieved memories are inserted into Nova's prompt at the **top OR bottom** of the active context section, never in the middle. Liu et al. (2023) showed LLMs systematically under-attend to context they encounter mid-prompt; placing memories at the edges sidesteps that.

**Are the memories actually being used?** That's a fair question — the VLM might be solving the board zero-shot and ignoring our retrieved context. We measure this directly in §8 of the spec via three methods: (1) counterfactual ablation (real memories vs random irrelevant memories — does the action change?), (2) structured citation (the response schema requires Nova to cite which memory ID influenced the move), and (3) position-invariance test (top vs middle vs bottom — is middle equivalent to no-memory?). If those tests fail, the memory subsystem is theatre and the spec says so honestly.

### Worked example

It's mid-game. Nova has a tight board with a 256 in the middle. She's about to make a move. The memory system runs retrieval:

| Memory | recency | importance | relevance | total | surfaced? |
| --- | --- | --- | --- | --- | --- |
| "Lost on a 256-stuck-mid board 2 games ago" (trauma-tagged) | 0.6 | 0.9 | 0.85 | **2.35** | ✅ top |
| "Made a great corner move 3 moves ago" | 0.95 | 0.4 | 0.3 | 1.65 | |
| "Won a game last session" | 0.1 | 0.8 | 0.5 | 1.4 | |
| "First swipe of this game" | 0.85 | 0.1 | 0.2 | 1.15 | |
| "Lost on a different board 5 games ago" | 0.3 | 0.7 | 0.4 | 1.4 | |

The trauma-tagged memory wins because it's high on both relevance (similar board) and importance (a loss). It surfaces, and Nova's next prompt includes:

> *"You remember losing on a board like this two games ago. You swiped down and lost three moves later."*

That information shapes her decision.

## What about forgetting?

In a strict sense, Nova never forgets — every memory stays in the log. But the **`recency`** component of retrieval decays over time using a **power-law curve** (Wixted & Carpenter 2007), which means very old memories rarely surface unless they have very high importance.

Why power-law instead of exponential? It matches human forgetting more closely. Humans don't forget at a constant rate — we forget quickly at first, then slowly. Park's original Generative Agents used exponential decay; Nova uses power-law as a small upgrade.

Eventually, very old memories with importance ≤ 1 can be pruned to keep the database tidy. This is a maintenance task, not a memory feature.

## Summary

| Concept | One-liner |
| --- | --- |
| Episodic memory | Append-only log of (board, move, outcome) tuples |
| Semantic memory | Distilled rules from post-game reflection |
| Procedural memory | Reflexes — Take-The-Best heuristic fallback. The VLM itself is the semantic engine, not procedural memory. |
| Aversive memory tags (UI: "Trauma") | Markers on episodic memories that bias retrieval and emotion; bounded by extinction-halving so the spiral terminates mathematically |
| Working memory | What Nova has "in mind" right now (the current prompt) |
| Importance | 1–10 score on each memory; combination of programmatic + LLM-rated |
| Retrieval | Top-k by `α·recency + α·importance + α·relevance` |
| Forgetting | Power-law decay on recency; high-importance memories survive longer |

## Further reading

- **Park et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior.** The blueprint we're using. arXiv:2304.03442.
- **Tulving, E. (1972). Episodic and Semantic Memory.** Foundational paper for the memory taxonomy.
- **Cowan, N. (2001). The magical number 4 in short-term memory.** Why working memory is small.
- **Wixted & Carpenter (2007). The Wickelgren power law.** Why forgetting is power-law.
- **LeDoux, J. (1996). The Emotional Brain.** Background on fear memory and trauma.
