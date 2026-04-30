# Project Nova — Design Specification

**Status:** Draft 1 — pending user review
**Author:** Ido Horesh
**Date:** 2026-04-30
**Scope:** v1-FULL (all 8 cognitive modules)

---

## 1. Vision and Framing

### What we are building

Project Nova is a vision-language-model (VLM) agent that plays the mobile puzzle game 2048 running in an Android emulator. The agent operates strictly black-box: it perceives the game through screenshots, decides through reasoning, and acts through ADB-injected swipes. It has no access to the game's code, memory, or state.

The defining feature is that Nova is built as a stylized cognitive architecture — not a literal brain simulation, but a software system whose modules are inspired by well-replicated findings in cognitive neuroscience and recent research on cognitive architectures for language agents. Nova has:

- **Persistent affect** that varies over the course of a play session
- **Episodic memory** of past games, with importance-weighted retrieval
- **Semantic memory** of distilled rules, written by post-game reflection
- **A dopamine-style reward signal** based on temporal-difference prediction error
- **"Trauma" memories** of catastrophic losses that bias future caution
- **Real-time transparent reasoning**, visible on a side-by-side brain panel

### Honest novelty positioning

Project Nova is **not** a research-novel contribution. The component techniques have all been published:

- LLMs and VLMs playing 2048 have been demonstrated publicly (AI Village, lmgame-org GamingAgent, VGRP-Bench).
- Memory streams with importance scoring and reflection are introduced by Park et al. (2023).
- Appraisal-based emotional architectures for LLM game agents are introduced by Croissant et al. (2024).
- Brain-inspired modular LLM planners are introduced by Webb et al. (2025).
- Verbal-reinforcement reflection is introduced by Shinn et al. (2023).

What this project contributes is an **applied synthesis** — a clean, end-to-end, working system that combines these techniques in a single VLM agent applied to a deterministic-stochastic puzzle, with mood as a session-persistent slow variable shaping play across hundreds of moves, and a transparent brain panel that makes the internal state legible to a human viewer.

The intended public framing is:

> An applied synthesis of recent cognitive-architecture-for-LLM-agents research (CoALA, Generative Agents, Chain-of-Emotion, Reflexion) into a working VLM agent that plays 2048 with persistent mood, episodic memory, and a reward-prediction-error-style dopamine signal.

This framing is defensible to a senior reviewer with relevant background. Claims to be avoided: "models human cognition," "implements consciousness," "neuroscience-grounded," "actual brain simulation." These overclaims invite warranted criticism and damage credibility.

### Goals for v1

In priority order:

1. **Transparent reasoning is the demo.** A viewer watching a 30-second clip should be able to see Nova's mood shift, watch a memory get retrieved, see the dopamine pulse on a good merge, and read the reasoning that produced each move.
2. **Real architectural depth.** All eight cognitive modules implemented, not just a VLM-in-a-loop with cosmetic UI.
3. **Defensible citations.** Every component backed by a real paper. The README and design doc cite ~15 foundational works.
4. **Shippable to a public LinkedIn post.** Clean, polished, recorded demo. Code reproducible by a competent reader.

Explicit non-goals:

- Optimal 2048 play. Nova does not need to win consistently. The demo lives in the *experience*, not the score.
- General-game generality in v1. We target one game and one game only. Multi-game generalization is v3.
- Production deployment. This is a portfolio piece.

### Audience

- Primary: hiring managers and engineers at casual / live-ops mobile game studios (Superplay, Sparkplay, Playtika, King, Playrix, Voodoo, Scopely, Moon Active, Peak Games, Plarium).
- Secondary: AI / agent-engineering practitioners on LinkedIn and Twitter.
- Tertiary: cognitive science and HCI readers who care about emotion in agent design.

### Commercial use cases (informs framing for the LinkedIn post and interviews)

The mood-and-memory architecture is what differentiates Nova from a commodity QA bot. Plausible commercial applications, ranked:

1. **Regression and smoke-test QA for live-service games.** Black-box VLM agents survive UI changes; scripted bots do not.
2. **Difficulty tuning and game balance.** Different mood profiles produce different frustration curves on the same level — pre-launch difficulty calibration without a real playtest panel.
3. **Tutorial and onboarding validation.** A "fresh" Nova with no semantic memory has to learn from the tutorial alone. If she gets stuck, real users will too.
4. **Procedurally generated content validation.** Filter unwinnable / softlocked levels before they ship.
5. **Marketing B-roll generation.** Different personas produce visually different gameplay footage on demand.
6. **Churn-prediction model training data augmentation.** Synthetic player traces with mood trajectories.
7. **Anti-cheat adversarial testing.** A humanlike bot is the hardest adversary for an anti-cheat system.

Honest caveats: at-scale VLM cost is real ($2.5K–25K per overnight test run with frontier models); black-box agents cannot test real-time twitch games; "humanlike" behavior is unvalidated against real telemetry until correlated.

---

## 2. v1 Scope — FULL

The full scope ships all eight cognitive modules from the architecture diagram, plus a Reflexion-style post-game reflection and Tree-of-Thoughts deliberation triggered on high-uncertainty board states.

### Included in v1 — eight modules

| # | Module | Brief description |
| --- | --- | --- |
| 1 | Perception | Screen capture from emulator → board state extraction |
| 2 | Working memory | Current board, recent moves, retrieved context, current affect |
| 3 | Long-term memory | Episodic event log + semantic rules + trauma tags (Park 2023, Tulving 1972, LeDoux 1996) |
| 4 | Affective state | Valence × arousal (Russell 1980) + dopamine + frustration + anxiety |
| 5 | Outcome evaluation | TD-error / RPE (Schultz 1997) — drives dopamine and emotion updates |
| 6 | Decision module | VLM call with appraisal + memory retrieval + optional ToT lookahead |
| 7 | Action executor | ADB-injected swipes |
| 8 | Brain panel viewer | Side-by-side live game + internal-state visualization |

Plus a post-game **reflection** subsystem (Reflexion-style) that writes back into long-term memory between games.

### Deferred to v2 and beyond

| Feature | Earliest version |
| --- | --- |
| Multiple swappable personas | v2 |
| Persona timing variation (fast tapper, cautious explorer) | v2 |
| **"Nova watches ads" — emotional reaction to mobile-game ads** | v2+ |
| Generalization to other casual mobile games | v3 |
| Imitation of a specific human player from recordings | v3 |
| Local/smaller VLMs for cost reduction at scale | v2+ |

### Timeline

Realistic budget: **5–6 weeks of focused work.** Plus 1 week of brain-panel polish on top. See section 7 for the time-sink breakdown.

### Portability — game-agnostic vs 2048-specific

v1 ships on 2048 only, but the architecture is deliberately designed so most of Nova ports cleanly to other games. This section makes that boundary explicit, so v3 ("Nova plays any casual mobile game") has a clear blueprint and so the repo signals architectural foresight to any reader.

**Game-agnostic in v1 (~80% of the code).** These modules work on any game without modification:

- Working memory (structured prompt assembly)
- Long-term memory + retrieval (embeddings + recency/importance/relevance)
- Affective state (valence, arousal, dopamine, frustration, anxiety, confidence)
- Outcome → affect mapping (the affect update rules don't care what the game is)
- Reflection (post-game verbal postmortem)
- Decision module (VLM call, ToT lookahead) — the prompt template is parametric on a game description
- Brain panel UI (mood gauges, memory feed, reasoning text — same regardless of game)
- WebSocket bus, SQLite, LanceDB, Anthropic SDK adapter, OBS recording

**2048-specific in v1 (~20% of the code).** These three modules need a per-game replacement to support a new game:

| Module | 2048 implementation | What changes for a new game |
| --- | --- | --- |
| **Perception fast path** | OpenCV template-matching tile digits on a 4×4 grid | Drop fast path; rely on VLM perception only. Cost rises (extra VLM call per frame); reliability drops slightly. |
| **Action vocabulary** | 4 swipes only (`swipe_up/down/left/right`) | Generalize to primitives: `tap(x,y)`, `swipe(x1,y1,x2,y2,duration)`, `drag(x1,y1,x2,y2,duration)`, `tap_and_hold(x,y,duration)`. ADB handles all four natively. |
| **Outcome evaluator** | Numeric `score_delta` from a known on-screen region | VLM-extracted reward signal per frame ("did things improve and by how much?"). Less precise but works on games without a numeric score. |

Plus minor game-specific items:
- Game-end detection (currently "no legal merge possible"; in v3 becomes a VLM classification of the screen)
- Heuristic fallback policy (currently Take-The-Best for 2048; in v3 either omit or replace with a game-specific heuristic only when one is cheap to write)

**Cost and reliability trade-offs for v3:**

| Dimension | v1 (2048) | v3 (any casual game) |
| --- | --- | --- |
| VLM calls per move | ~1 (decision only) | ~3–10 (perception + decision + outcome eval) |
| Cost per game (frontier model) | ~$1–5 | ~$15–100 |
| Perception accuracy | ~99.9% (template matching) | ~90–98% (VLM perception) |
| Game variety | one | broad — any casual mobile game |

**Migration path from v1 to v3.** The repo's `nova-agent/src/nova_agent/perception/` and `.../action/` directories are designed as pluggable layers. A new game ships as a new perception adapter (or a flag that disables the fast path) and a new action adapter (or a parametric action map). The rest of Nova does not change. Estimated work for the first additional game: **1–2 weeks** once v1 is stable.

**Honest constraints — what v3 does NOT cover.** Even with full generalization, Nova is bounded by black-box VLM perception:
- Real-time twitch games (FPS, runners, fighting games) — VLM latency is too slow.
- Games with critical hidden information that requires memorization across long sessions (e.g., card-counting in poker) — possible but harder than the v3 spec.
- Games with very dense HUDs where the relevant state changes in fine pixel detail.

The v3 sweet spot is the same as v1's — **casual / puzzle / merge / menu-driven mobile games**. That's also the commercial sweet spot, so the constraint and the goal align.

---

## 3. Architecture

### High-level diagram

```
                    ┌─────────────────────────────────────────┐
                    │          DECISION LOOP                  │
                    │    (CoALA — planning → execution)       │
                    └─────────────────────────────────────────┘
                                       │
   ┌───────────────────────────────────┼───────────────────────────────────┐
   ↓                                   ↓                                   ↓
┌────────────┐         ┌─────────────────────────┐         ┌──────────────────────┐
│ PERCEPTION │   →     │     WORKING MEMORY      │   ←     │   AFFECTIVE STATE    │
│ (VLM eyes) │         │   (current board,       │         │ (valence, arousal,   │
│            │         │    recent moves,        │         │  dopamine, frustr.,  │
│            │         │    retrieved context)   │         │  anxiety)            │
└────────────┘         └─────────────────────────┘         └──────────────────────┘
                                       │                                   ↑
                                       ↓                                   │
                            ┌──────────────────────┐                       │
                            │   LONG-TERM MEMORY   │                       │
                            │                      │                       │
                            │ • Episodic           │                       │
                            │ • Semantic           │                       │
                            │ • Trauma-tagged      │                       │
                            └──────────────────────┘                       │
                                       │                                   │
                            recency + importance + relevance               │
                                       ↓                                   │
                            ┌──────────────────────┐                       │
                            │  APPRAISAL + DECIDE  │                       │
                            │  (VLM with optional  │                       │
                            │   ToT on uncertainty)│                       │
                            └──────────────────────┘                       │
                                       │                                   │
                                       ↓                                   │
                            ┌──────────────────────┐                       │
                            │      EXECUTE         │                       │
                            │   (ADB swipe)        │                       │
                            └──────────────────────┘                       │
                                       │                                   │
                                       ↓                                   │
                            ┌──────────────────────┐                       │
                            │  OUTCOME EVALUATOR   │                       │
                            │   δ = score - V      │                       │
                            │  (RPE / TD-error)    │  ─────────────────────┘
                            │                      │
                            │  Write to memory     │
                            │  if significant      │
                            └──────────────────────┘
                                       │
                                       ↓
                       (Game over) → REFLECTION (Reflexion-style)
                       → semantic memory + optional trauma tag
```

### Module specifications

#### 3.1 Perception

**Responsibility.** Convert raw emulator screen to structured board state.

**Two implementations, fall-through:**

1. **Fast path — local digit OCR.** A small Python module reads the 4×4 grid using OpenCV template matching against the known set of 2048 tile values (2, 4, 8, …, 65536). Fast (~5–10ms per frame), deterministic, near-100% accurate on Nova's specific Unity-built game with its known tile sprites.
2. **Slow path — VLM perception.** If the fast path returns low-confidence (e.g., a tile sprite is unknown), the VLM is asked "what is on this board" as a fallback. Logs the failure for later improvement of the fast path.

**Output schema:**
```json
{
  "grid": [[0, 2, 0, 0], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]],
  "score": 0,
  "empty_cells": 14,
  "max_tile": 2,
  "perception_source": "fast" | "vlm"
}
```

**Citation.** No paper required for OCR. The fast/slow split is a standard CoALA-style **grounding** action (Sumers 2024).

#### 3.2 Working memory

**Responsibility.** Hold everything the VLM needs to make the next decision.

**Contents per cycle:**
- Current board state (from perception)
- Last 3–5 moves (board, action, outcome, score delta)
- Retrieved long-term memories (top-k, see §3.4)
- Current affect state translated to natural language (see §3.5)
- Current sub-goal if any (e.g., "build 512 chain in top-right corner")

**Capacity bound.** ~4 chunks of bound information, mirroring Cowan's revised working-memory limit (Cowan 2001). Implemented as a hard cap on the size of the prompt's "active context" section. The LLM context window is NOT the working memory — the active section is.

**Citation.** Baddeley & Hitch (1974); Cowan (2001); CoALA working-memory definition (Sumers 2024).

#### 3.3 Long-term memory — episodic store

**Responsibility.** Append-only log of every (board, move, outcome) tuple, with metadata.

**Record schema:**
```json
{
  "id": "ep_2026-04-30T12:34:56.789Z",
  "timestamp": 1714492496.789,
  "last_accessed": 1714492496.789,
  "type": "move" | "game_start" | "game_over" | "reflection",
  "board_before": [[...]],
  "board_after": [[...]],
  "action": "swipe_up",
  "score_delta": 32,
  "expected_score_delta": 28,
  "rpe": 0.07,
  "affect_snapshot": {"valence": -0.1, "arousal": 0.7, ...},
  "importance": 7,
  "tags": ["trauma_pre", "tight_board"],
  "embedding": [0.12, -0.04, ...],
  "source_reasoning": "..."
}
```

**Importance scoring.** Hybrid:
- **Programmatic:** combine |RPE|, terminality (game over), rarity (max-tile achievement), proximity-to-loss.
- **LLM-rated:** for non-trivial events, ask the VLM "rate this event 1–10 for memorability."

The two are averaged. Pure programmatic is too brittle; pure LLM-rated is too expensive.

**Storage.** SQLite for the structured columns. LanceDB for the embedding column with vector search (file-backed, no server, fast Rust core).

**Citation.** Park et al. (2023) memory stream. Tulving (1972) episodic-memory taxonomy.

#### 3.4 Long-term memory — retrieval

**Responsibility.** At decision time, surface the top-k most relevant past episodes.

**Formula** (Park 2023, normalized to [0,1] then weighted sum):

```
score(memory_i) = α_recency · recency_i
                + α_importance · importance_i
                + α_relevance · relevance_i
```

- `recency`: power-law decay since `last_accessed` (Wixted & Carpenter 2007 — slight upgrade over Park's exponential).
- `importance`: stored 1–10 score, normalized.
- `relevance`: cosine similarity between current-board embedding and stored-board embedding.

Initial weights `α = 1.0` each, tuned during evaluation.

**Trauma-tagged memories** get a wider similarity threshold and a multiplier on relevance (so they surface on loosely-similar boards). Capped to prevent pathological over-avoidance — see §3.6.

**Top-k.** Default k=5. Returned memories are appended to working memory as natural-language summaries plus the original board snapshot.

**Citation.** Park et al. (2023); Marr (1971) auto-associative pattern completion; McClelland et al. (1995) Complementary Learning Systems.

#### 3.5 Affective state

**Responsibility.** Maintain a small vector of scalar variables that represent Nova's "feelings" and modulate the prompt sent to the VLM.

**State variables**, all in [-1, 1] or [0, 1] as noted:

| Variable | Range | Updated by | Effect on prompt |
| --- | --- | --- | --- |
| `valence` | [-1, +1] | Cumulative RPE, recent outcomes | "feels good" / "feels bad" |
| `arousal` | [0, 1] | Empty-cell count, board volatility | "alert" / "calm" |
| `dopamine` | [0, 1] | Single-step RPE spikes (decays fast) | "just felt a hit" |
| `frustration` | [0, 1] | Streaks of low/negative RPE | "impatient", "wants a big play" |
| `anxiety` | [0, 1] | Game-over proximity, trauma triggers | "nervous", "wants to play safe" |
| `confidence` | [0, 1] | Recent success rate vs expectation | "sure" / "hesitant" |

**Update rule sketch** (full code in implementation phase):

```
δ_valence    = +0.7 · normalized_RPE − 0.05 · time
δ_arousal    = +0.6 · (1 − empty_cells/16) + 0.2 · |RPE|
δ_dopamine   = +1.0 · max(0, RPE)        ; fast decay
δ_frustration += +0.3 · max(0, −RPE)     ; reset on positive RPE
δ_anxiety    = +0.5 · (game_over_proximity) + 0.3 · trauma_triggered
δ_confidence = +0.4 · sign(RPE) · |RPE|^0.5
```

**Translation to natural language for the VLM prompt.** A small templating function turns the vector into a sentence: *"You feel anxious and frustrated. Last few moves disappointed you. The board is tight."*

This is the **appraisal step** from Croissant et al. (2024) Chain-of-Emotion: emotion is computed, then verbalized into the prompt.

**Citations.** Russell (1980) circumplex; Schultz, Dayan, Montague (1997) RPE; Croissant et al. (2024) appraisal-driven affective LLM game agents; Forgas (1995) affect-infusion model; Eysenck et al. (2007) attentional control theory for the anxiety variable.

#### 3.6 Trauma tagging

**Responsibility.** After a catastrophic loss, identify the *precondition* boards (3–5 moves before death) and tag them as traumatic.

**Tagging rule.** When a game ends with score < expected and the loss was on a contested board (e.g., empty_cells <= 2 for several moves before death), the boards from move (t-5) to (t-1) are written back to episodic memory with:

- `importance += 3` (capped at 10)
- `tags += ["trauma"]`
- `trauma_radius`: an embedding-similarity threshold that's looser than normal retrieval

**Effect at retrieval.** Trauma-tagged memories surface on boards within `trauma_radius` (vs. normal `relevance_threshold`). When surfaced, they boost `anxiety` and bias the appraisal prompt: *"You remember losing on a board like this."*

**Regulatory cap.** To prevent pathological over-avoidance (which would make Nova never play boldly), the system imposes a `trauma_decay` term: each retrieval slightly reduces the trauma weight, and reflective semantic-memory rules can override trauma in specific contexts.

**Citation.** LeDoux (1996) fear memory; McGaugh (2013) emotional tagging in consolidation; Phelps & LeDoux (2005). Honest hedge: trauma generalization circuits are debated — frame as design metaphor inspired by, not modeled on, fear-conditioning literature.

#### 3.7 Outcome evaluator (TD-error / RPE)

**Responsibility.** Compute the prediction-error signal that drives dopamine and emotion updates.

**Equation.**

```
δ = (actual_score_delta) − V(board_before)
```

where `V` is a **simple scalar value head** estimating expected score gain from a board state. v1 implements V as either:
- a hand-tuned heuristic (sum of expected merges given current pairs), or
- a tiny gradient-boosted regressor trained on a few hundred recorded games.

Either is fine; the choice is empirical.

**Mapping δ → affect update.** See §3.5 update rules.

**Citation.** Schultz, Dayan, Montague (1997). This is the most replicated finding in the entire stack — the safest claim in the project.

#### 3.8 Decision module — appraisal, retrieval, deliberation

**Responsibility.** Given the current board, decide which way to swipe.

**Loop per move:**

1. **Appraise.** Compute current affect from §3.5. Translate to natural-language description.
2. **Retrieve.** Query long-term memory with current board → top-5 relevant memories (§3.4).
3. **Build prompt.** Compose: board state + recent moves + retrieved memories + affect description + sub-goal if any.
4. **Decide.**
   - **Default path (low uncertainty):** single ReAct call. VLM emits `Observation`, `Reasoning`, `Action`, `Confidence`. Parse and validate.
   - **Deliberate path (high uncertainty / high anxiety / high stakes):** Tree-of-Thoughts. Generate 3–4 candidate moves, evaluate each ("imagine the board after this move; rate the position"), pick highest-value branch.
   - **Trigger for ToT:** `anxiety > 0.6` AND (`max_tile >= 256` OR `empty_cells <= 3`). Tunable.
5. **Validate output.** Action must be one of {swipe_up, swipe_down, swipe_left, swipe_right}. If parse fails, retry once with stricter format prompt; on second failure, fallback to a heuristic (Take-The-Best, §3.10).

**Citations.** Yao et al. (2022) ReAct; Yao et al. (2023) Tree of Thoughts; Sumers et al. (2024) CoALA.

#### 3.9 Action executor

**Responsibility.** Translate `swipe_up` etc. to ADB commands and execute them.

**Implementation.** `adb shell input swipe x1 y1 x2 y2 duration_ms`. Coordinates calibrated once per emulator config.

**Reliability concerns.** ADB swipe latency varies 50–200ms; occasional drops. Mitigation:
- Wait for tile-slide animation to complete (~300ms) before next perception cycle.
- Verify board changed after swipe; if not, retry once.

#### 3.10 Heuristic fallback (Take-The-Best for v1)

**Responsibility.** Provide a reliable fallback when VLM output is malformed, and provide a "fast-policy" baseline for evaluation.

**Implementation.** Hand-coded ranked rules (Gigerenzer & Goldstein 1996 Take-The-Best):
1. If a swipe direction would merge the largest pair on the board, prefer it.
2. Else, prefer a swipe that keeps the largest tile in a corner.
3. Else, prefer a swipe that maintains monotonicity along the longest row.
4. Else, swipe in a direction with the most expected merges.

**Citation.** Simon (1956); Gigerenzer & Goldstein (1996); Chase & Simon (1973) for chunk-based expertise.

#### 3.11 Reflection (post-game)

**Responsibility.** After a game ends, generate a verbal postmortem and distill it into semantic memory.

**Trigger.** `game_over` event.

**Prompt template.**

> *Nova just finished a game. Score: {final_score}. Last 30 moves: {move_list}. Reflections from prior games: {top-3 prior reflections}.*
>
> *Generate a short (3–5 sentence) postmortem. What strategy worked? What failed? What lesson should Nova carry into the next game? Output JSON with fields `summary`, `lessons` (array of strings), `notable_episodes` (memory IDs).*

**Output written to:**
- Episodic memory: the reflection itself, type=`reflection`, importance=8.
- Semantic memory: each lesson as a separate row in a `rules` table, with citations back to the source episodes.

**Citation.** Shinn et al. (2023) Reflexion; Park et al. (2023) reflection in Generative Agents.

#### 3.12 Brain panel viewer

See §5 for full UI specification. Architecturally: a separate Next.js process that subscribes to a WebSocket published by the agent. Receives every internal-state update and renders.

---

## 4. The decision loop — worked example

This section walks through Nova's processing of a single move, in plain language. The full developer-facing version of this story lives in [docs/learn/05-the-decision-loop.md](../learn/05-the-decision-loop.md).

**Setup.** Nova is mid-game. Score 1840. Board has 1 empty cell. A 256 is stuck in the middle.

**Step 1 — Perception.** Fast OCR reads the board into a 4×4 grid. ~8ms.

**Step 2 — Retrieval.** The current board's embedding is computed and queried against episodic memory. Top result is a trauma-tagged memory from two games ago: *"Lost the game on a similar tight board after swiping down."* Importance 9/10.

**Step 3 — Appraisal.** Affect updates: anxiety rises (game-over proximity + trauma triggered) to 0.7. Valence drops slightly. Frustration is at 0.4 from a streak of low-RPE moves. The state is verbalized: *"You feel anxious. The board is tight. You remember losing on a board like this."*

**Step 4 — Decide.** Anxiety + max-tile-256 trigger ToT. Three candidate moves are generated; each is mentally simulated and scored. Swipe-down scores worst (matches trauma pattern). Swipe-up scores best (clears two 16s, frees a cell). Final action: swipe-up.

**Step 5 — Execute.** ADB swipe-up. ~150ms latency. Tiles slide, two 16s merge into 32. Score 1840 → 1872.

**Step 6 — Outcome evaluation.** Expected gain from V(board_before) was ~28. Actual was +32. RPE δ = +0.07. Dopamine ticks up. Anxiety slightly relaxes.

**Step 7 — Memory write.** Importance score: programmatic = 6 (saved from a tight board), LLM rating = 7. Stored with `tags=["trauma_avoided"]`. The trauma weight on the original tagged memory is slightly reduced (regulatory decay).

**Step 8 — Brain panel update.** All of the above is broadcast over WebSocket and rendered in real time on the viewer.

Latency budget for this whole loop: target <2s for the ToT path, <500ms for the default path.

---

## 5. Brain panel UI design

The brain panel is the project's primary public artifact. It must be visually polished. See [docs/learn/06-brain-panel-tour.md](../learn/06-brain-panel-tour.md) for the user-friendly walkthrough.

### Layout

Single window, two columns:

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│                                     │                                     │
│       LIVE GAME (left column)       │    NOVA'S MIND (right column)       │
│                                     │                                     │
│   - scrcpy stream of emulator       │   - Mood gauge (valence × arousal)  │
│   - score                           │   - Dopamine pulse bar              │
│   - move count                      │   - Affect text label               │
│                                     │   - Memory feed (last 3 retrieved)  │
│                                     │   - Current reasoning text          │
│                                     │   - Mode badge (DEFAULT / ToT)      │
│                                     │   - Action arrow with animation     │
│                                     │   - Trauma indicator (when active)  │
│                                     │   - Game / session stats footer     │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

### Visual elements

- **Mood gauge.** A 2D point on a Russell-circumplex disk. Smooth animation as values change. Color-coded: green high-valence, red low-valence; saturation = arousal.
- **Dopamine bar.** Vertical bar that pulses upward and decays. Bright cyan on positive RPE, dim on negative.
- **Affect text label.** One-sentence English description, updated each tick (e.g., *"anxious, recalling past loss"*). Driven by §3.5 templating.
- **Memory feed.** Stack of recently-retrieved memory cards. Each shows: a tiny rendered board snapshot, a one-line summary, an importance badge, a tag list (`trauma`, `success`, etc.).
- **Reasoning text.** Live-streamed from the VLM as it generates. Typewriter animation if cheap; instant otherwise.
- **Mode badge.** "INTUITION" (default) or "DELIBERATION" (ToT engaged) with snappy transition animation.
- **Action arrow.** Large directional arrow that animates on swipe. Briefly persistent.
- **Trauma indicator.** A subtle red border / glow around the screen when a trauma-tagged memory is active in working memory. Fades after a few moves.
- **Stats footer.** Score, move count, total games played, current mood trajectory sparkline.

### Polish budget

This UI is the demo. Allocate at least one full week of focused work after the agent works end-to-end. Animations, color theory, typography all matter. Consider commissioning a small design review from a designer friend — non-negotiable for a portfolio piece.

### 5.5 Design language and tooling

#### Aesthetic principles

| Decision | Value |
| --- | --- |
| Vibe | Warm minimalist — calm, content-first, "neural / introspective" |
| Background | Deep warm dark (e.g., `#1a1614`) — the brain panel reads as quiet thought |
| Primary accent | Cyan (`#4FD1C5`) or violet (`#8B5CF6`) — synaptic/neural feel; deliberately distinct from Anthropic orange to give Nova her own identity |
| Reward / dopamine color | Bright cyan pulse — energy without harshness |
| Trauma / threat color | Muted dark red — slow pulse, never shouts |
| Mood gauge | Smooth gradient across the valence × arousal disk |
| Typography | One serif (display, gauge labels) + one sans (body, reasoning). E.g., Fraunces + Inter |
| Motion library | Framer Motion. Spring-based, no sharp easings. Dopamine spike is the only "punchy" animation; everything else flows. |
| Layout | Generous whitespace, subtle 1px borders, single-column right side stacked tightly |

#### Tooling — Claude Design

The project uses **Claude Design** (Anthropic Labs, research preview, launched 2026-04-17) for the static-visual phase of the brain panel build. Why:

- The author is not a designer. The brain panel is the demo. Polish gap is the largest single risk to the project.
- Claude Design's codebase-aware design-system feature keeps every component visually consistent without manual drift management.
- Cuts the static-layout phase from ~5 days hand-written to ~2 days assisted. Time saved goes into motion polish.

**Workflow split — what Claude Design does vs what stays hand-coded:**

| Phase | Tool | Output |
| --- | --- | --- |
| Visual identity exploration | Claude Design | 3–5 alternate brain-panel directions; pick one |
| Static layout — all panel states | Claude Design | Mockups of: calm Nova, anxious Nova, dopamine spike, trauma glow active, ToT mode, game over |
| Component code scaffolding | Claude Design export → React + Tailwind | Initial `nova-viewer/app/components/*.tsx` skeletons |
| Design-system enforcement | Claude Design (codebase-aware) | Consistent colors/typography/components across all panels |
| Motion / animation layer | Hand-coded with Framer Motion | Mood-gauge tween, dopamine pulse, memory feed slide-in, trauma glow, mode badge transition |
| WebSocket data binding | Hand-coded | All live-data wiring |
| Iteration on look-and-feel | Claude Design + manual tweaks | Continuous refinement |

#### When to use Claude Design — timeline anchors

Claude Design is invoked at three specific moments in the v1 build:

| Week | Trigger | What you do in Claude Design |
| --- | --- | --- |
| **Week 1, day 2–3** | After repo and emulator are running, before any UI code is written | **Direction exploration.** Generate 3–5 alternate brain-panel layouts from the same prompt (the Aesthetic Principles table above + the §5 element list). Pick one direction. Save mockups in `docs/design/v1/`. This locks the visual identity before any hand-coding. |
| **Week 5, day 1–3** | After the agent works end-to-end (perception → memory → affect → decision → action all wired) and the brain panel needs to become real UI | **Static states.** Generate one mockup per affect state (calm, anxious, frustrated, dopamine-spike moment, trauma-glow active, ToT mode, game-over screen). Export each as React + Tailwind. Scaffold them into `nova-viewer/app/components/`. |
| **Week 5, day 4–7** | After scaffolded components exist and the WebSocket is wired, you're tuning look-and-feel | **Iteration.** Use Claude Design to tweak component variants — try alternate mood-gauge styles, alternate memory-card layouts, alternate dopamine-bar shapes. Pull good variants back into the codebase. |

Outside those three windows, don't reach for Claude Design — the work is motion logic, data wiring, or animation tuning, none of which Claude Design covers well as of 2026-04.

#### Honest limits to plan around

Claude Design (research preview, April 2026) is strongest at static layouts and simple interactions. It is weak on:

- Live data-driven animations (dopamine pulse synchronized to RPE events)
- WebSocket subscription wiring
- State-machine logic (e.g., mode-badge transition rules)
- Per-frame motion tuning

These remain hand-coded with Framer Motion + standard React patterns. Plan for them in Week 5, days 4–7 and into Week 6.

#### Subscription requirement

Claude Design requires a Claude Pro / Max / Team / Enterprise subscription. Confirm the user has one before Week 1.

---

## 6. Tech stack and repository layout

### Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Agent language | Python 3.11+ | Standard for LLM/CV work; library ecosystem |
| VLM provider | Anthropic Claude (Opus or Sonnet) | Strong vision + structured outputs; provider-agnostic interface so swap is config-only |
| Vector DB | LanceDB | Local, file-backed, no server, fast Rust core |
| Structured store | SQLite | Local, zero-config, fits the data volume |
| Emulator capture | scrcpy + ADB | Open source, mature, mirrors device cleanly |
| Action injection | ADB shell input | Universal, no special permissions on emulator |
| Brain panel | Next.js (React + TypeScript) | Animation-friendly, screen-recordable in OBS |
| Real-time channel | WebSocket (FastAPI on agent side, native ws on viewer side) | Low-latency, broadcast pattern |
| Demo recording | OBS | Standard for software demos |
| Visual design tool | Claude Design (Anthropic Labs) | Static brain-panel layouts + design system; see §5.5 for the workflow split |

### Repository layout

```
project-nova/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── specs/
│   │   └── 2026-04-30-project-nova-design.md   ← this file
│   └── learn/
│       ├── 01-what-is-project-nova.md
│       ├── 02-the-pieces.md
│       ├── 03-memory-explained.md
│       ├── 04-emotion-explained.md
│       ├── 05-the-decision-loop.md
│       ├── 06-brain-panel-tour.md
│       ├── 07-reading-the-code.md
│       └── 08-glossary.md
├── nova-agent/
│   ├── pyproject.toml
│   ├── README.md
│   └── src/nova_agent/
│       ├── perception/
│       ├── memory/
│       ├── affect/
│       ├── decision/
│       ├── reflection/
│       ├── action/
│       ├── bus/
│       └── main.py
├── nova-viewer/
│   ├── package.json
│   ├── README.md
│   ├── app/
│   │   ├── page.tsx
│   │   └── components/
│   └── public/
└── nova-game/
    └── README.md  (instructions for forking stdbilly/2048_Unity)
```

---

## 7. Hardest problems and time-sinks

Realistic budget for v1-FULL is **5–6 weeks** of focused work. The dangerous time-sinks:

| Risk | Estimate | Mitigation |
| --- | --- | --- |
| ADB swipe reliability across emulator configs | 2 days | Calibrate once per emulator; verify post-swipe board change; one retry on no-op |
| Structured VLM output reliability | 2 days | Tight schema + provider's native structured-output mode + retry-with-stricter-prompt + heuristic fallback |
| Importance scoring tuning (programmatic vs LLM-rated balance) | 3 days | Iterate on a recorded set of games; aim for a memory feed that "feels alive" not noisy |
| Affect → decision coupling actually being visible in play | 4 days | Tune so that high anxiety produces visibly more conservative play in ~70%+ of contested boards |
| Trauma memory not over-firing | 3 days | Decay rule + regulatory cap; sample retrievals during testing |
| Tree-of-Thoughts cost and latency | 2 days | Cap branch count at 4; reuse perception across branches |
| Brain panel design quality | 7 days | Allocate explicitly; this is the demo |
| Demo composition / scenario scripting | 1 day | Curate a 2-minute reel showing trauma → avoidance → dopamine spike |
| OCR robustness on tile sprite edge cases | 1 day | VLM fallback path catches misses |
| Cost overruns during development | $50–200 | Budget; cap dev runs to ~50 games per iteration |

**Total realistic schedule:**

- Week 1: Game forked, emulator running, ADB capture + swipe loop wired end-to-end. Simple ReAct loop without memory or affect.
- Week 2: Episodic memory + retrieval + importance scoring. Memory feed in the brain panel.
- Week 3: Affective state + RPE + outcome evaluator. Mood gauges + dopamine pulse in the brain panel.
- Week 4: Trauma tagging + ToT deliberation + reflection. Mode badge + trauma indicator.
- Week 5: Polish pass on brain panel. Animations, color theory, typography.
- Week 6: Demo recording + writing + LinkedIn post + bug bash.

---

## 8. Validation plan

Acceptance criteria for "v1-FULL is done":

1. **End-to-end run.** Nova can play a complete game from start to game-over without manual intervention, with all eight modules active.
2. **Visible emotion-decision coupling.** In a curated set of 10 contested boards, high-anxiety Nova picks a more conservative move than low-anxiety Nova ≥7 times. Demonstrates the architecture is doing work, not theatre.
3. **Visible trauma effect.** Construct a scenario where Nova loses on a specific board pattern, then re-encounters a similar board in a later game. Brain panel shows trauma retrieval; Nova picks a different move. Recorded as a demo segment.
4. **Reflection produces real semantic rules.** After 5 games, the semantic memory contains at least 5 distinct lessons. Manual review confirms they are sensible.
5. **Brain panel quality.** A non-technical viewer can watch a 30-second clip and explain what Nova is "feeling" and "remembering" without needing the design doc.
6. **Demo recording.** A 60–90 second clip suitable for LinkedIn, with on-screen narration / labels where helpful, ready to post.

---

## 9. Future directions

### v2 — Personas

Multiple swappable Nova personas, each defined by:
- An **affect baseline** (e.g., the "anxious beginner" starts with arousal=0.5, anxiety=0.4, confidence=0.2).
- A **decision-style modifier** ("hardcore optimizer" always invokes ToT; "panicky tapper" never invokes ToT and has a tighter action delay).
- A **memory profile** ("forgetful" has faster decay; "brooder" has higher trauma persistence).
- A **timing profile** (action-delay distribution).

Demo: side-by-side, three Novas play the same level. Same brain architecture, three visibly different runs.

### v2+ — "Nova Reacts to Ads"

Same Nova brain, different stimulus. Instead of a 2048 board, Nova watches a mobile-game ad video (or playable ad). Affect runs continuously. Output:
- Moment-by-moment affect trace (valence + arousal over time)
- Engagement summary ("felt curious in first 3s, attention dropped at 7s, frustrated by deceptive CTA at 12s, did not feel motivated to install")
- Persona-tagged reactions (when v2 personas land, run the same ad through "casual player Nova" vs "hardcore Nova" → differential reactions)

**Commercial framing.** Ad creative testing currently relies on human focus groups + post-hoc CTR. A "synthetic player" emitting reactions in real time could be useful for ad-iteration pipelines at studios + ad networks (AppLovin, ironSource, Meta).

**Honest caveats.** The claim "Nova's reaction predicts real player reaction" is a hypothesis, not a proven result. Validation would require correlation with real campaign performance data. Until validated, frame as "stylized player-experience simulation," not "ad performance predictor."

### v3 — Generalization to other casual games

Goal: Nova plays an arbitrary casual mobile game (match-3, merge, solitaire, idle-clicker) using the same architecture. Requires:
- Game-agnostic perception (rely on VLM perception, drop the fast OCR path).
- Game-agnostic action vocabulary (tap (x,y), swipe (x1,y1,x2,y2), drag).
- Reward-signal abstraction (score, level-up, coin gain — discoverable from screen).

This is the "universal mobile game agent" north star from the original brief.

### v3 — Player imitation

Ingest recorded human gameplay and derive a Nova persona that imitates that specific player's style. Behavior cloning + persona-parameter inference. Hardest of the future directions.

---

## 10. Bibliography

### Cognitive architectures and dual-process

- Sumers, T. R., Yao, S., Narasimhan, K., & Griffiths, T. L. (2024). Cognitive Architectures for Language Agents. *Transactions on Machine Learning Research*. arXiv:2309.02427. **[Primary architectural reference for this project.]**
- Anderson, J. R., Bothell, D., Byrne, M. D., Douglass, S., Lebiere, C., & Qin, Y. (2004). An integrated theory of the mind. *Psychological Review*, 111(4), 1036–1060.
- Laird, J. E. (2012). *The Soar Cognitive Architecture.* MIT Press.
- Sun, R. (2016). *Anatomy of the Mind.* Oxford UP.
- Franklin, S., Madl, T., D'Mello, S., & Snaider, J. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. *IEEE TAMD*, 6(1), 19–41.
- Baars, B. J. (1988). *A Cognitive Theory of Consciousness.* Cambridge UP.
- Mashour, G. A., Roelfsema, P., Changeux, J.-P., & Dehaene, S. (2020). Conscious processing and the global neuronal workspace hypothesis. *Neuron*, 105(5), 776–798.
- Kahneman, D. (2011). *Thinking, Fast and Slow.* Farrar, Straus & Giroux.
- Evans, J. St. B. T., & Stanovich, K. E. (2013). Dual-process theories of higher cognition. *Perspectives on Psychological Science*, 8(3), 223–241.

### Bounded rationality and heuristics

- Simon, H. A. (1956). Rational choice and the structure of the environment. *Psychological Review*, 63(2), 129–138.
- Gigerenzer, G., & Goldstein, D. G. (1996). Reasoning the fast and frugal way. *Psychological Review*, 103(4), 650–669.
- Chase, W. G., & Simon, H. A. (1973). Perception in chess. *Cognitive Psychology*, 4(1), 55–81.

### Memory

- Tulving, E. (1972). Episodic and Semantic Memory. In Tulving & Donaldson (Eds.), *Organization of Memory* (pp. 381–403).
- Baddeley, A., & Hitch, G. (1974). Working Memory. In *Recent Advances in Learning and Motivation*, vol. 8.
- Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences*, 24, 87–185.
- Marr, D. (1971). Simple memory: a theory for archicortex. *Philosophical Transactions of the Royal Society of London. B*, 262, 23–81.
- McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex. *Psychological Review*, 102(3), 419–457.
- McGaugh, J. L. (2013). Making lasting memories: Remembering the significant. *PNAS*, 110(Suppl 2), 10402–10407.
- Wixted, J. T., & Carpenter, S. K. (2007). The Wickelgren power law and the Ebbinghaus savings function. *Psychological Science*, 18(2), 133–134.

### Emotion and reward

- Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, 275, 1593–1599. **[Anchor citation for the dopamine signal.]**
- Schultz, W. (2016). Dopamine reward prediction error coding. *Nature Reviews Neuroscience*, 17, 183–195.
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.
- Damasio, A. R. (1994). *Descartes' Error.* Putnam.
- Bechara, A., Damasio, A. R., Damasio, H., & Anderson, S. W. (1994). Insensitivity to future consequences following damage to human prefrontal cortex. *Cognition*, 50, 7–15.
- Maia, T. V., & McClelland, J. L. (2004). A reexamination of the evidence for the somatic marker hypothesis. *PNAS*, 101(45), 16075–16080.
- Forgas, J. P. (1995). Mood and judgment: The Affect Infusion Model. *Psychological Bulletin*, 117(1), 39–66.
- Eysenck, M. W., Derakshan, N., Santos, R., & Calvo, M. G. (2007). Anxiety and cognitive performance: Attentional Control Theory. *Emotion*, 7(2), 336–353.
- LeDoux, J. (1996). *The Emotional Brain.* Simon & Schuster.
- Phelps, E. A., & LeDoux, J. E. (2005). Contributions of the amygdala to emotion processing. *Neuron*, 48, 175–187.

### LLM agents

- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *UIST 2023*. arXiv:2304.03442. **[Memory-stream blueprint.]**
- Yao, S., Zhao, J., Yu, D., et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*. arXiv:2210.03629.
- Yao, S., Yu, D., Zhao, J., et al. (2023). Tree of Thoughts. *NeurIPS 2023*. arXiv:2305.10601.
- Shinn, N., Cassano, F., Berman, E., et al. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*. arXiv:2303.11366.
- Wang, G., Xie, Y., Jiang, Y., et al. (2023). Voyager: An Open-Ended Embodied Agent with Large Language Models. arXiv:2305.16291.
- Packer, C., Wooders, S., Lin, K., et al. (2023). MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560.
- Croissant, M., Frister, M., Schofield, G., & McCall, C. (2024). An Appraisal-Based Chain-of-Emotion Architecture for Affective Language Model Game Agents. *PLOS ONE*. **[Closest prior art for the affect module.]**
- Li, C., Wang, J., Zhang, Y., et al. (2023). Large Language Models Understand and Can Be Enhanced by Emotional Stimuli (EmotionPrompt). arXiv:2307.11760.
- Webb, T., Mondal, S., et al. (2025). A brain-inspired agentic architecture to improve planning with LLMs (Modular Agentic Planner). *Nature Communications*, 16. arXiv:2310.00194.

---

*End of design specification, draft 1.*
