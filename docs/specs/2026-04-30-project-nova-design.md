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

**Differentiation against the closest prior art (Webb et al. 2025, Modular Agentic Planner / MAP).** MAP is brain-inspired modular planning for LLMs — also a structured cognitive architecture with module-level decomposition. Nova differs in three concrete ways: (1) Nova adds **session-persistent affect** as a slow variable that modulates reasoning across hundreds of moves; MAP is planning-only and stateless across episodes. (2) Nova adds **episodic memory + reflection-distilled semantic memory** (Park 2023 + Shinn 2023 lineage); MAP does not retain experience. (3) Nova adds **a transparent real-time brain-panel UI** that makes internal state legible to a human viewer; MAP is evaluated on benchmark scores, not introspective UX. Pre-empts the "this is just MAP with mood" line.

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
| 3 | Long-term memory | Episodic event log + semantic rules + aversive memory tags / informal "trauma" (Park 2023, Tulving 1972, LeDoux 1996) |
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
  "tags": ["aversive", "loss_precondition", "tight_board"],
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

**Side effect on retrieval.** Every returned record has its `last_accessed` field written back to `now()` so recency decay actually resets. Without this write-back, memories surfaced repeatedly remain "old" forever and the recency term degrades into a no-op.

**Aversive Memory Tag (informal: "trauma") records** get a wider similarity threshold and a multiplier on relevance (so they surface on loosely-similar boards). Capped to prevent pathological over-avoidance — see §3.6. Per the Lost-in-the-Middle phenomenon (Liu et al. 2023), retrieved memories are inserted at the **top OR bottom** of the active context section of the prompt, never in the middle.

**Concurrency.** Tree-of-Thoughts spawns N parallel branch evaluators (§3.8). Branches are **read-only** with respect to memory: they query, they never write. All memory writes (move records, importance updates, `last_accessed` write-back, aversive-tag updates) happen on the single decision-loop thread after the chosen branch executes. SQLite uses WAL journaling (`PRAGMA journal_mode=WAL`) for non-blocking concurrent reads.

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
| `anxiety` | [0, 1] | Game-over proximity, aversive memory surfaced (`aversive_triggered`) | "nervous", "wants to play safe" |
| `confidence` | [0, 1] | Recent success rate vs expectation | "sure" / "hesitant" |

**Update rules.** All variables share one form:
```
x ← clip(decay · x + δ_x, range)              (per move-step)
```
Per-move-step decay rates (units: per move, NOT per second):

| Variable | decay (1 − λ) | λ | Notes |
| --- | --- | --- | --- |
| dopamine | 0.6 | 0.4 | Fast — dopamine is a phasic spike |
| valence | 0.95 | 0.05 | Slow — valence is the session-persistent slow variable |
| arousal | 0.90 | 0.10 | Medium |
| anxiety | 0.85 | 0.15 | Medium — drains as boards loosen |
| frustration | 0.90 | 0.10 | Medium — accumulates across low-RPE streaks |
| confidence | 0.95 | 0.05 | Slow |

`δ_x` deltas, computed each move:
```
RPE_norm     = clip(δ_t / σ_δ, −1, +1)               where σ_δ is running stdev of |δ_t| over last 100 moves; σ_δ ← max(σ_δ, ε)
δ_valence    = +0.7  · RPE_norm
δ_arousal    = +0.6  · (1 − empty_cells/16) + 0.2 · |RPE_norm|
δ_dopamine   = +1.0  · max(0, RPE_norm)
δ_frustration = +0.3 · max(0, −RPE_norm)
δ_anxiety    = +0.5  · game_over_proximity + 0.3 · aversive_triggered
δ_confidence = +0.4  · sign(RPE_norm) · |RPE_norm|^0.5
```
Ranges: `valence ∈ [−1, +1]`; `arousal, dopamine, frustration, anxiety, confidence ∈ [0, 1]`.

**Frustration cap.** `frustration ≤ 0.8` enforced after the clip step. Engineering hack to prevent runaway-spiral feedback (negative RPE → frustration → riskier action → more negative RPE). Acknowledged as a hack; load-bearing for stability.

**Stylized, not human-fit.** All coefficients above are **illustrative / tuned for demo legibility**. They are not fit to human-subject data and make no claim of replicating affective dynamics. The *form* (linear update with exponential decay) is grounded in computational-affect modeling (Bach & Dayan 2017); the *constants* are engineering choices.

**Translation to natural language for the VLM prompt.** A small templating function turns the vector into a sentence: *"You feel anxious and frustrated. Last few moves disappointed you. The board is tight."* This is the **appraisal step** from Croissant et al. (2024) Chain-of-Emotion (with cognitive-appraisal grounds in Lazarus 1991 and Scherer's 2001 Component Process Model): emotion is computed, then verbalized into the prompt.

**Convergence monitoring.** Per-game `mean(|δ_t|)` is logged to the brain-panel stats footer. Across games 1→50 it should shrink (V is learning, RPE is no longer pure noise). If it does not shrink, V is not learning and the entire RPE/Schultz-grounded claim is empirically broken — that is the test, not a vibe.

**Citations.** Russell (1980) circumplex; Schultz, Dayan, Montague (1997) RPE; Sutton & Barto (2018) TD-learning algorithm anchor; Croissant et al. (2024) appraisal-driven affective LLM game agents; Lazarus (1991), Scherer (2001) appraisal theory; Forgas (1995) affect-infusion model; Bach & Dayan (2017) for the form of linear-with-decay affect dynamics; Eysenck et al. (2007) and Derakshan & Eysenck (2009) Attentional Control Theory for the anxiety variable's gating role on System 2 (§3.8).

#### 3.6 Aversive Memory Tag (informal: "trauma")

**Naming convention.** Throughout the codebase and technical documentation the term is **Aversive Memory Tag** (`aversive_*` identifiers in code: `aversive_radius`, `aversive_decay`, `aversive_tag`). The brain-panel UI label, LinkedIn post copy, and demo narration use the punchier "Trauma" — that is a marketing surface, not the technical surface. This split keeps the engineering rigorous and the demo watchable.

**Ethical hedge.** "Trauma" here is engineering shorthand for an importance-weighted memory of a catastrophic in-game outcome. It is **not** a model of clinical PTSD, fear conditioning, or any human pathology.

**Responsibility.** After a catastrophic loss, identify the *precondition* boards (3–5 moves before death) and tag them as aversive.

**Tagging rule.** When a game ends with `final_score < expected` and the loss was on a contested board (e.g., `empty_cells ≤ 2` for several moves before death), the boards from move `(t−5)` to `(t−1)` are written back to episodic memory with:

- `importance += 3` (capped at 10)
- `aversive_tag = True`
- `aversive_radius`: an embedding-similarity threshold looser than normal retrieval
- `aversive_weight = 1.0` (initial — decays via extinction; see below)

**Effect at retrieval.** Aversive-tagged memories surface on boards within `aversive_radius` (vs. normal `relevance_threshold`). When surfaced, they boost `anxiety` (`aversive_triggered = 1` in §3.5) and bias the appraisal prompt: *"You remember losing on a board like this."* This pre-deliberative bias is the engineering analogue of Damasio's somatic-marker hypothesis (Damasio 1994; Bechara et al. 1994) — emotional memories shape choice *before* explicit reasoning runs (and before §3.8's optional ToT branch evaluation begins).

**Spiral defenses.** Four-layer defense against the trauma-death-spiral failure mode (the "Nova panics on every board" pathology):

| # | Defense | Mechanism | Load-bearing? |
| --- | --- | --- | --- |
| A | **Active-tag cap** | Maximum **1** aversive memory surfaced per move (the highest-`aversive_weight` match). | Yes |
| B | **Exposure-extinction halving** | Each survival on an aversive-radius-similar board: `aversive_weight ← aversive_weight · 0.5`. After ~6 survivals the memory's aversive contribution is < 0.02 and effectively inert. | **Yes — primary deterministic guarantee.** Defense B alone bounds the spiral mathematically. |
| C | Semantic override | Reflection (§3.11) may write a `trauma_outdated` semantic-memory rule after N successful traversals. | **Best-effort, NOT load-bearing.** LLMs reliably underweight abstract textual rules against dominant visual context (the current tight-board screenshot). Treat as a nice-to-have. |
| D | Cross-game affect reset | On `game_start`: anxiety, frustration, dopamine reset to baseline. Valence retains 30% (slow-variable design). Prevents game N+1 starting in saturated-anxiety state. | Guardrail, not a defense |

The architecture relies on **A and B** for correctness. C is best-effort. D is hygiene. This is intentional: deterministic mechanisms first, LLM-mediated mechanisms as a bonus.

**Honest theoretical hedges.** This module is **engineering-inspired** by amygdala-modulated emotional memory consolidation (LeDoux 1996; Phelps & LeDoux 2005; Phelps 2004; McGaugh 2013); it makes **no claim of replicating the underlying circuit**. The implementation does not include reconsolidation, time-based extinction, context-dependent retrieval, or fear generalization gradients. Trauma generalization circuits in the actual literature are debated; frame this entire module as a stylized design metaphor.

**Citations.** LeDoux (1996); Phelps & LeDoux (2005); Phelps (2004) for amygdala-modulated emotional memory and the wider-similarity retrieval radius; McGaugh (2013) for emotional tagging during consolidation; Damasio (1994) and Bechara et al. (1994) for the somatic-marker rationale that motivates pre-deliberative biasing of the prompt.

#### 3.7 Outcome evaluator (TD-error / RPE)

**Responsibility.** Compute the prediction-error signal that drives dopamine and emotion updates.

**Update rule — TD(0) with online learning.**

```
δ_t   = r_t + γ · V(s_{t+1}) − V(s_t)              (TD error)
V(s_t) ← V(s_t) + α · δ_t                          (online linear update)
V(s_terminal) ≡ 0
r_t   = score(s_{t+1}) − score(s_t)                (raw 2048 score gain)
```

Constants:

- **`γ = 0.99`** — 2048 has a long horizon (winning games run 1000+ moves); γ = 0.99 gives an effective half-life of ~69 moves, correctly valuing early-game setup. (γ = 0.95 was rejected — half-life of 14 moves undervalues setup.)
- **`α ∈ [0.005, 0.02]`** — start at 0.01; the longer-credit window from γ = 0.99 motivates the lower α range.

This is **proper TD(0), not bandit-baseline.** Earlier drafts used `δ = actual_score_delta − V(board_before)`, which collapses RPE to "did this move merge well?" and severs the temporal-credit-assignment claim that justifies citing Schultz/Dayan/Montague (1997) and Sutton & Barto (2018).

**Function approximator — linear, on 6 hand-engineered features.**

```
φ_empty          = empty_cells / 16
φ_adjacent_pairs = adjacent_identical_tile_count / 24    # immediate merge potential
φ_mono           = monotonicity_score / max_mono         # row+column monotonicity
φ_smooth         = 1 − Σ_{adj a,b} |log₂(a) − log₂(b)| / norm
φ_maxcorner      = 1 if max_tile in any corner else 0
φ_logmax         = log₂(max_tile) / 17

V(s) = wᵀ φ(s) · score_scale            (score_scale ≈ 50)
```

`φ_adjacent_pairs` is the dominant short-term-value feature for 2048 — without it, V cannot distinguish a "ready-to-merge" board from a "frozen" board of equal sparsity.

**Bootstrapping prior `V₀`** (solves the move-1 game-1 question — RPE is meaningful from the first action):

```
w₀ = [4.0, 5.0, 3.0, 2.0, 2.0, 1.5]
     [empty, adjacent_pairs, mono, smooth, maxcorner, logmax]
```

`adjacent_pairs` carries the highest weight because it's the most predictive of immediate score gain.

**Why linear, not GBT.** Spec earlier offered "tiny gradient-boosted regressor" as an alternative. **Rejected.** GBT (xgboost/lightgbm) is batch-trained, not online; there is no incremental leaf update that preserves TD semantics. Linear function approximation has standard convergence guarantees under on-policy sampling (Sutton & Barto 2018, ch. 9), runs in O(d) per update, is interpretable for the brain panel ("which feature drove that prediction?"), and adds no tuning overhead at this feature dimension (d = 6).

**Per-move flow.**

1. Before action: compute `V(s_t) = wᵀ φ(s_t) · score_scale`. Save it.
2. After action: read new score; compute `r_t`, `V(s_{t+1})`.
3. Compute `δ_t`, update `w ← w + α · δ_t · φ(s_t)`.
4. Pass `δ_t` (and its normalized form `RPE_norm`, see §3.5) to the affect module.

**Convergence test.** Per-game `mean(|δ_t|)` is logged. Across games 1→50 it should monotonically shrink (V is learning the true value). If it doesn't, V has bug or feature-set is inadequate, and the RPE/dopamine claim is empirically broken — see §8 acceptance.

**Citations.** Schultz, Dayan, Montague (1997) — neuroscience anchor for dopamine = RPE. Sutton (1988) and Sutton & Barto (2018) — algorithm anchor for TD-learning and linear function approximation; pairs with Schultz '97 to ground both the *what* (dopamine encodes prediction error) and the *how* (TD-learning is the computational mechanism). Wu (2014) for the 2048 monotonicity heuristic in `φ_mono`.

#### 3.8 Decision module — appraisal, retrieval, deliberation

**Responsibility.** Given the current board, decide which way to swipe.

**Dual-process framing.** The default-vs-ToT switch maps onto Kahneman's dual-process theory (Kahneman 2011): default ReAct = System 1 (fast intuition, "cognitive ease"); Tree-of-Thoughts = System 2 (slow deliberation, "cognitive strain"). The **arbiter** module (`decision/arbiter.py`) is the explicit System-1/System-2 selector. High anxiety lowers cognitive ease (Eysenck et al. 2007 Attentional Control Theory; Derakshan & Eysenck 2009) and forces the switch to System 2.

**Loop per move:**

1. **Appraise.** Compute current affect from §3.5. Translate to natural-language description.
2. **Retrieve.** Query long-term memory with current board → top-5 relevant memories (§3.4). Update `last_accessed` on each returned record. Memories inserted into the prompt at top OR bottom of active context, never middle (Liu et al. 2023 Lost-in-the-Middle mitigation).
3. **Build prompt.** Compose: board state + recent moves + retrieved memories + affect description + sub-goal if any.
4. **Arbiter — System 1 or System 2?**
   - **Default path (System 1, low uncertainty):** single ReAct call. VLM emits `Observation`, `Reasoning`, `Action`, `Confidence`, `memory_citation` (see §8). Parse and validate.
   - **Deliberate path (System 2, high uncertainty / high anxiety / high stakes):** Tree-of-Thoughts. Generate 3–4 candidate moves; evaluate each in **parallel read-only branches** ("imagine the board after this move; rate the position"); pick highest-value branch.
   - **Trigger for ToT:** `anxiety > 0.6` AND (`max_tile >= 256` OR `empty_cells <= 3`). Tunable.
5. **Branch streaming (ToT only).** Each branch's evaluation streams to the brain-panel's Reasoning panel as it completes — candidate move + estimated value + brief justification. Rejected branches grey out; the chosen branch highlights. The 2–4 second deliberation reads on screen as visible thinking, not a freeze. Branches are **read-only** with respect to memory (§3.4 concurrency); they query, never write.
6. **Validate output.** Action must be one of `{swipe_up, swipe_down, swipe_left, swipe_right}`. If parse fails: retry once with a stricter format prompt; on second failure, fall through to the heuristic policy (Take-The-Best, §3.10). This retry-then-fallback chain is **wired into the decider entrypoint** — not just spec text. Every decision returns a valid action or raises a logged exception that the loop catches and falls back from.

**Citations.** Yao et al. (2022, ICLR 2023) ReAct; Yao et al. (2023) Tree of Thoughts; Sumers et al. (2024) CoALA; Kahneman (2011) for the System 1 / System 2 framing of the arbiter; Eysenck et al. (2007) and Derakshan & Eysenck (2009) Attentional Control Theory for the anxiety→System-2 trigger; Liu et al. (2023) Lost-in-the-Middle for the prompt-position rule.

#### 3.9 Action executor

**Responsibility.** Translate `swipe_up` etc. to ADB commands and execute them.

**Implementation.** `adb shell input swipe x1 y1 x2 y2 duration_ms`. Coordinates calibrated once per emulator config.

**Reliability concerns.** ADB swipe latency varies 50–200ms; occasional drops. Mitigation:

- **Visual stability check (replaces hardcoded 300ms wait).** After issuing a swipe, take screenshots in a 50ms-interval pixel-diff loop until two consecutive frames are identical (board is static), with a hard cap of ~600ms then force-read + log. Hardcoded waits break on emulator frame drops; the stability loop is robust to lag.
- **No-op detection and dead-board handling.** If the post-stability pixel-diff against the pre-swipe screenshot shows no change, retry the swipe once. If the second attempt also shows no change AND all four swipe directions have been tried with no change in this position, fire `game_over` (the board is dead). Without this rule the loop can record phantom moves and burn budget swiping at a finished game.
- **Concurrency.** The decider's VLM call (§3.8) is a sync, blocking call wrapped in `asyncio.to_thread` so the event bus can continue serving the brain panel during the 500ms–2s decision window. Without this wrap the viewer freezes on every move.

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

**Step 3 — Appraisal.** Affect updates: anxiety rises (game-over proximity + `aversive_triggered=1`) to 0.7. Valence drops slightly. Frustration is at 0.4 from a streak of low-RPE moves. The state is verbalized: *"You feel anxious. The board is tight. You remember losing on a board like this."*

**Step 4 — Decide.** Anxiety + max-tile-256 trigger ToT. Three candidate moves are generated; each is mentally simulated and scored. Swipe-down scores worst (matches trauma pattern). Swipe-up scores best (clears two 16s, frees a cell). Final action: swipe-up.

**Step 5 — Execute.** ADB swipe-up. ~150ms latency. Tiles slide, two 16s merge into 32. Score 1840 → 1872.

**Step 6 — Outcome evaluation.** Expected gain from V(board_before) was ~28. Actual was +32. RPE δ = +0.07. Dopamine ticks up. Anxiety slightly relaxes.

**Step 7 — Memory write.** Importance score: programmatic = 6 (saved from a tight board), LLM rating = 7. Stored with `tags=["aversive_avoided"]`. The original aversive memory's `aversive_weight` is **halved** by exposure-extinction (§3.6 defense B) — Nova survived a similar board, so that memory's grip on her loosens deterministically.

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
- **ToT branch panel (System 2 mode only).** When the arbiter switches to Tree-of-Thoughts, this replaces the single-block Reasoning view: a vertical stack of branch cards, one per candidate move, each showing direction + estimated value + brief justification. Cards stream in as branches complete (parallel evaluation). Rejected branches grey out; the chosen branch highlights and persists. Turns the 2–4 second deliberation into visible thinking on screen, not a freeze.
- **Mode badge.** "INTUITION" (default, System 1) or "DELIBERATION" (ToT engaged, System 2) with snappy transition animation.
- **Action arrow.** Large directional arrow that animates on swipe. Briefly persistent.
- **Trauma indicator.** A subtle red border / glow around the screen when an aversive-tag memory is active in working memory. Fades after a few moves. (UI label is "Trauma"; technical surface is Aversive Memory Tag — see §3.6.)
- **Convergence indicator.** Small dot/sparkline in the stats footer showing per-game `mean(|δ_t|)` trend across the session — visual confirmation that V is learning. Required for §8 acceptance.
- **Stats footer.** Score, move count, total games played, current mood trajectory sparkline, V-convergence indicator, current `NOVA_TIER`.

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
| VLM provider — primary | Google AI (Gemini family) | Strong vision + JSON output at significantly lower per-token cost than Anthropic for the high-volume tasks |
| VLM provider — secondary | Anthropic Claude | Used where Anthropic's long-form structured output advantage matters (reflection) and for the polished demo recording |
| Model — default decisions (90% of moves) | `gemini-2.5-flash` | $0.30 / $2.50 per 1M tokens; MMMU 79.7 — comfortably above the bar for 4×4 grid reasoning |
| Model — Tree-of-Thoughts deliberation | `gemini-2.5-pro` | $1.25 / $10 per 1M; best step-wise reasoning per dollar |
| Model — OCR fallback + cheap classification | `gemini-2.5-flash-lite` | $0.10 / $0.40 per 1M; trivially cheap for "read these digits" / "rate 1–10" |
| Model — post-game reflection | `claude-sonnet-4-6` | $3 / $15 per 1M; Anthropic's strength is long-form structured prose |
| Model — Week 6 demo recording | `claude-sonnet-4-6` | $3 / $15 per 1M; matches the production-tier reflection model so the demo's memory store is style-consistent. (Opus 4.7 was rejected — same demo-viewer experience, ~5× the cost.) |
| Realistic 6-week dev cost | **~$80** total ($100 hard cap) | See §6.6 for the full cost rollup and tier-by-tier breakdown. |
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

### 6.5 Security — top-priority requirement

The repository is public. Any leaked secret is publicly exposed within minutes. Security is therefore a first-class requirement, not an afterthought.

#### Five-layer defense (defense-in-depth)

| Layer | Mechanism | Catches |
| --- | --- | --- |
| 1 | `.gitignore` blocks all standard secret filename patterns | `.env`, `*.key`, `*.pem`, `secrets.*`, `credentials.*`, `*api_key*`, etc. |
| 2 | Code loads secrets ONLY from environment variables — never hardcoded, never from committed JSON | Secrets baked into `.py` or `.ts` source |
| 3 | Local `gitleaks` pre-commit hook scans staged changes before each commit | Accidental staging of secrets in source files |
| 4 | GitHub-side: **secret scanning** + **push protection** + **dependabot security updates** (verified enabled on this repo) | Anything that slips past layers 1–3; pushes containing detected secrets are BLOCKED at the GitHub edge |
| 5 | Anthropic Console daily-spend cap + in-code `NOVA_DAILY_BUDGET_USD` guardrail | Bounds blast radius if a key leaks despite all other layers |

#### Hard rules — non-negotiable

1. **No secret ever appears in source code.** All API keys, tokens, and credentials are loaded from `os.environ` (Python) or `process.env` (Node) at runtime.
2. **`.env` is never committed.** A `.env.example` template lives at the repo root with all keys present but no values.
3. **Browser-exposed env vars contain no secrets.** Next.js `NEXT_PUBLIC_` prefix variables are public — they go into the bundle. Secrets stay server-side.
4. **The brain-panel viewer in v1 needs no secrets.** The viewer talks to the local agent over WebSocket; the agent owns all credentials.
5. **`SECURITY.md` is the canonical reference.** Read it before any commit involving credentials or auth.

#### Required artifacts (committed in repo root)

- `.gitignore` — extended secret-pattern blocklist
- `.env.example` — template with all keys, no values, with a security checklist at the bottom
- `SECURITY.md` — full security policy, leak response procedure, and milestone-review checklist

#### Milestone security reviews

At each major milestone (end of week 1, week 3, week 6), run the security review checklist from `SECURITY.md` §"Security review — required before each milestone":

1. `gitleaks detect --redact` (full git-history scan)
2. Verify nothing matching `*.env`, `*secrets*`, `*credentials*` has ever been committed
3. Check the GitHub Security tab for secret-scanning alerts
4. Confirm `.env.example` contains no real values
5. Confirm push protection + secret scanning + dependabot are still enabled

A milestone is not done until all five pass.

#### Leak response — fast path

If a secret is committed (whether or not it has been pushed):

1. **Rotate the key immediately** at the provider console — DO NOT wait, DO NOT try to git-rebase first.
2. Update `.env` with the new key.
3. Optionally scrub git history with `git filter-repo`.
4. Run `gitleaks detect --redact` to find anything else exposed.

Full procedure in `SECURITY.md` §"What to do if a key is leaked".

#### Threat model — in/out of scope for v1

| In scope | Out of scope |
| --- | --- |
| Accidental key commits (most common case) | Compromised dev machine — OS keychain owns these |
| Public-repo exposure | Adversarial supply-chain dep — partial mitigation only |
| Cost-amplification attacks via leaked key | Network-level attacks — v1 is local only |
| Credential leaks in logs / recordings / screenshots | Production deployment hardening (deferred to v2/v3 when deployment exists) |

When v2 / v3 add a deployed/cloud component, this section gets a follow-up covering at-rest encryption, transport TLS, auth on the WebSocket, and rate limiting.

---

### 6.6 Cost discipline — three model tiers, one env var

Hard total budget for v1: **~$80**. Hard cap: **$100**. Per-run cap: **$0.50**. The strategy is three model tiers selected by a single environment variable, plus seven cost levers, plus a hard distinction between "plumbing tests on Mock LLM (free)" and "behavior tests on real Flash (cheap)" — see §6.7.

#### Three tiers

```python
# nova-agent/src/nova_agent/llm/tiers.py
TIERS = {
    "dev": {                                        # default — daily dev work
        "decision":            "gemini-2.5-flash",
        "tot":                 "gemini-2.5-flash",
        "tot_branches":        3,
        "reflection":          "gemini-2.5-flash",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
    "production": {                                 # Week 5–6 §8 acceptance
        "decision":            "gemini-2.5-flash",
        "tot":                 "gemini-2.5-pro",
        "tot_branches":        4,
        "reflection":          "claude-sonnet-4-6",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
    "demo": {                                       # Week 6 LinkedIn recording (5 games)
        "decision":            "claude-sonnet-4-6",
        "tot":                 "claude-sonnet-4-6",
        "tot_branches":        4,
        "reflection":          "claude-sonnet-4-6",
        "perception_fallback": "claude-sonnet-4-6",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
}
TIER = os.environ.get("NOVA_TIER", "dev")
```

**Tier rationale:**

- **`dev` uses Flash, not Flash-Lite.** Flash-Lite has documented structured-output reliability problems (malformed JSON, fence-wrapped responses, schema-ordering bugs); using it as the daily-dev decision model would burn days on parser-bug rabbit holes that are actually model bugs. Flash 2.5 has reliable JSON-schema adherence. The minor cost difference is dwarfed by the time saved.
- **Flash-Lite kept ONLY for `importance_rating`** — single-purpose, simple "rate 1–10" schema, low risk.
- **`demo` uses Sonnet 4.6, not Opus.** Opus 4.7 was dropped — saves ~$40 with no demo-viewer-visible quality difference. Sonnet 4.6 also matches the production-tier reflection model, so the demo's memory store is internally style-consistent (no canonicalization pass needed across tier boundaries).

#### Seven cost levers

| # | Lever | Mechanism |
| --- | --- | --- |
| L1 | **Fixture-replay cache** | Cache key is `sha256(rendered_prompt_string, model_name, temperature, response_schema_hash)`. **Keying on the rendered prompt string itself, not a `prompt_template_version`** — so any change to the board, retrieved memories, affect text, or template structure produces a different hash automatically. Writes gated on smoke-pass (no cache pollution from buggy builds). `NOVA_CACHE=off` debug switch. Hit-rate logged on every call + dashboarded in the brain panel. |
| L2 | **MockLLMClient default for tests** | Deterministic responses keyed off input. All unit + integration tests use it by default. Real LLM is opt-in via `NOVA_LLM_REAL=1`. See §6.7. |
| L3 | **Tier downshift via `NOVA_TIER`** | Default `dev`. `production` only Weeks 5–6 + ~3 mid-dev checkpoints. `demo` only Week 6 recording. |
| L4 | **3-game smokes by default** | Iteration default is 3 games, not 50. Full N-game eval is a manual flag, used 2–3× across the project. |
| L5 | **Per-run hard cap $0.50** | Replaces per-day cap during dev. A single run cannot exceed this without explicit override. Bounded blast radius. |
| L6 | **Importance LLM-rating off in dev** | In `dev` tier, importance is programmatic-only. LLM-rating fires only in `production`/`demo` and only when `\|RPE_norm\| > 0.5 OR terminal OR new max-tile`. |
| L7 | **Headless ADB-recorded perception replay** | A `RecordedRunner` feeds saved (frame, score) tuples through the loop for pure-logic dev sessions (memory/affect/RPE/ToT work). No emulator needed. Cuts cost AND iteration time. |

#### Cost rollup — verified

| Phase | Workload | Cost |
| --- | --- | --- |
| Daily `dev` work (Gemini free tier + paid Flash overflow + cache) | Weeks 1–6 | ~$5 |
| Week-1 Flash-Lite vs Flash diagnostic | one-shot, 100 prompts each | ~$1 |
| L2 behavior checkpoints × 2 (15 games each on Flash) | Weeks 2 + 3 | ~$15 |
| Week-4 mini-acceptance (Flash, 10 games) | one-shot | ~$3 |
| `production` tier acceptance (20 games) | Week 5 | ~$20 |
| `production` re-run after bug fixes (10 games) | Week 6 | ~$10 |
| `demo` tier recording (Sonnet 4.6, 5 games) | Week 6 | ~$10 |
| Buffer | unforeseen re-runs | ~$15 |
| **Total** | | **~$80** |

Hard cap **$100**. Per-run cap **$0.50** (env-var-overridable). The Anthropic Console daily-spend cap remains the outer ceiling (§6.5).

#### Memory-rule heterogeneity safeguard

When tiers switch (e.g. dev → production), the reflection model changes (Flash → Sonnet 4.6). The two models write semantic-memory rules in different styles. To prevent the memory store from looking mid-run like two different agents wrote it:

- **Every memory rule and reflection record carries `writer_model` on write.**
- During L3/production runs and demo recordings, retrieval-time filtering excludes records written by other tiers' reflection models.
- Optional: a one-shot **canonicalization pass** at start of a tier-switched session re-runs the last N reflections through the new tier's model so the store displays consistently in the demo.

---

### 6.7 Three test layers — answering "is it the model or my code?"

The single biggest risk of running daily dev on a cheaper model is **wasted time chasing fake bugs** — failures that look like architecture issues but are actually just the model being weak on a given prompt. The three-layer test strategy makes the answer deterministic.

| Layer | LLM | What it proves | Gates merge for | Cost |
| --- | --- | --- | --- | --- |
| **L1 — Plumbing tests** | MockLLMClient (deterministic, scripted) | Wires connect, schemas match, events fire in order, error paths fire | **Plumbing modules only** (perception, bus, memory IO, retrieval, action exec, ADB) | $0 |
| **L2 — Behavior tests** | Real Gemini Flash | Architecture produces intended signal under real LLM noise | **Behavior modules only** (affect, trauma/aversive, ToT, reflection) — must pass on real Flash before merge | ~$0.50/run |
| **L3 — Quality runs** | `production` tier (Flash + Pro + Sonnet 4.6) | §8 acceptance numbers | Final gate before demo | ~$1/game |

**Smoke gauntlet** (universal gate): a 30-second canned scenario that runs end-to-end on Mock LLM, asserting every bus event fires in the right order with the right schema. Runs every commit. $0. Catches ~90% of integration regressions.

**The merge gate split is critical.** Behavior modules (affect, aversive-tag, ToT, reflection) **never** rely on Mock-only tests for merge approval. Mock proves the bus event fires; it cannot prove that the ToT branch comparator picks the affect-weighted branch correctly when the affect signal is subtle. Behavior modules merge only after a real-Flash L2 run on a paired-scenario test set. This is the trade — slower merge cycle on behavior code, immunity from "Mock green, prod broken."

**The "is it the model or my code?" decision tree:**

```
Behavior looks wrong (e.g., Nova doesn't get more cautious when anxious).
  │
  ▼
1. Run L1 plumbing test for that path on Mock.
     ├─ FAILS  → bug in code. Fix. $0 spent.
     └─ PASSES → continue.

2. Run L2 behavior test on real Flash.
     ├─ FAILS  → real architecture issue (coefficients, prompt, ToT trigger).
     │           Fix, re-run. ~$0.50 each iteration.
     └─ PASSES → continue.

3. (If concern remains) run on production tier for one game.
     ├─ Behavior shows up → tier-sensitivity issue. Document in §8 caveats.
     └─ Still no behavior change → real coupling bug. Back to design.
```

You **never** debug behavior on dev-tier model output alone. You debug **plumbing** on Mock (model-independent) and **behavior** on real Flash (model strong enough to register the architecture's intended signal).

#### Week-1 diagnostic (cheap immunization)

End of Week 1: 100 identical decision prompts × {Flash-Lite, Flash}. Compare malformed-JSON rate, schema conformance, key-set divergence. Cost ~$0.50. Output: a baseline that lets you tell, for any future weird parser failure, whether it's the model or your code.

#### Mid-dev "tuning" checkpoints

Three real-LLM checkpoints during Weeks 2–4:

| Week | Scenario | Cost |
| --- | --- | --- |
| End of Week 2 | Affect coupling — paired anxious-vs-calm Nova, 15 games | ~$15 |
| End of Week 3 | Aversive-tag retrieval + ToT trigger, 15 games | ~$15 |
| End of Week 4 | Mini-acceptance on `production` tier, 10 games — surfaces emergent bugs (spiral, drift, memory pollution) before Week-5 final | ~$15 |

This is what catches issues that only emerge across many games (trauma death-spiral, affect drift, semantic-rule pollution). 10-game checkpoints would not be enough; ~30 games across the three checkpoints is the minimum useful sample.

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

Acceptance criteria for "v1-FULL is done." Final acceptance is run on the **`production`** tier (§6.6) over **n=20 games**. n=20 with sign / McNemar's tests at α=0.10 is an **honest budget-bounded constraint** for an industry portfolio piece — not an academic-grade sample. If real budget allows n=30, run n=30; below n=20 is underpowered and will be flagged.

### 8.1 End-to-end functionality

1. **Game-over to game-over.** Nova plays a complete game from start to terminal state without manual intervention, with all eight cognitive modules active. No phantom moves on dead boards (no-op detection §3.9). No crashes on DB-write failure (try/except wrap). No viewer freeze during VLM calls (`asyncio.to_thread` wrap §3.9).

### 8.2 Architectural proof — "is the architecture doing work, not theatre?"

2. **Affect ablation.** Same model, same memory store, same starting board seed: Nova-with-affect (full §3.5) vs Nova-with-affect-pinned-to-baseline. McNemar's paired test on **n=20 paired contested boards**, α=0.10. Affect must change the action distribution ≥30% of the time, with high-anxiety Nova selecting the more conservative action significantly more often. If affect ablation shows no behavioral difference, the affect module is theatre and the spec says so.

3. **Aversive-tag (trauma) replication.** Across **N=30 paired episodes** (not curated): Nova loses on a board pattern, the precondition is tagged, and on a future similar board the action distribution differs from the baseline-without-tag run. The exposure-extinction half-life (§3.6 defense B) is verified by the action distribution converging back to baseline after ~6 survivals on aversive-radius-similar boards.

4. **Memory-utilization measurement (Lost-in-the-Middle test).** Three methods, all run:

   **Method 1 — Counterfactual ablation.** Same contested board × {real retrieved memories, random/irrelevant memories drawn from store at low cosine similarity}. Measure action-divergence rate over n=30 paired runs. Targets: divergence ≥30% on contested boards; divergence ≈0% on open boards.

   **Method 2 — Structured citation.** The decision response schema includes `memory_citation: {memory_id, how_it_influenced} | null`. Measure, over n=50 sampled contested moves: citation rate (≥40%), citation validity (must be 100% — IDs must exist in the retrieved set, no hallucinated IDs), and citation grounding (manual audit, mean ≥3.5/5 — does the cited memory actually relate to the cited reasoning?).

   **Method 3 — Position-invariance test.** Same contested board × {memories at top, middle, bottom of context}. If middle-position behavior matches the no-memory baseline, Lost-in-the-Middle (Liu et al. 2023) is biting and the prompt's top-OR-bottom mitigation is justified. n=30 one-shot test, end of Week 4.

   Total memory-utilization measurement budget: ~$2.

### 8.3 Learning-system correctness

5. **V function convergence.** Per-game `mean(|δ_t|)` is logged across the 20-game acceptance run. Trend across games 1→20 must be monotonically decreasing (or flat-from-converged). If it is not, V is not learning, and the Schultz/Sutton RPE claim is empirically broken — fix V before claiming the architecture in the LinkedIn post.

6. **Reflection produces real semantic rules.** After 20 games, the semantic-memory store contains ≥10 distinct lessons. Manual review (1-5 sensibility scale) shows mean ≥3.5/5. Style consistency: all rules in the acceptance run have the same `writer_model` (§6.6 heterogeneity safeguard).

### 8.4 Perception robustness

7. **Fast-OCR FP/FN rates measured, not asserted.** A held-out tile-sprite test set (≥200 frames covering tiles 2–8192 across the game's color schemes). Measure: digit-misread rate (FP), missed-tile rate (FN), VLM-fallback trigger rate. Report numbers, not "near-100%."

### 8.5 Reproducibility

8. **Determinism harness.** Same emulator state + same `NOVA_TIER` + same seeds → identical move trace (within stochastic-tile-spawn limits — see caveat). Required pins:
   - Gemini decision call: `temperature=0`, `seed` parameter passed through SDK.
   - ToT branch evaluation: `temperature=0.3` is acknowledged as nondeterministic (multi-branch diversity is intentional). Variance bounded by branch-count cap.
   - Embedding model + version pinned in `pyproject.toml`; LanceDB schema asserts dimensionality on connect.
   - 2048 game RNG seed: **punted to v1.x** (forking `stdbilly/2048_Unity` for seed control is non-trivial). Trauma-replication test instead matches by *board state* rather than RNG-replay. Documented as an honest limitation.

### 8.6 Demo and presentation

9. **Brain panel quality.** A non-technical viewer can watch a 30-second clip and explain what Nova is "feeling" and "remembering" without needing the design doc. Tested on 3 non-technical viewers; all 3 pass.

10. **Demo recording.** A 60–90 second clip suitable for LinkedIn, on `demo` tier (Sonnet 4.6), with on-screen narration / labels where helpful. Memory store written entirely by `claude-sonnet-4-6` (style-consistent — see §6.6 heterogeneity safeguard).

11. **VLM faithfulness audit.** Sample n=50 moves from the production-tier acceptance run. For each, check whether the VLM's `reasoning` text predicts the action it actually returns. Faithfulness rate ≥80% is the bar. Lower means the model is rationalizing, not reasoning — disclosed honestly in the post if it fails.

### 8.7 Cost & latency receipts

12. **Per-game token-budget receipts.** The §6.6 ~$80 total budget is verified by logged actual cost from each tier's runs. If actual exceeds budget, the spec is updated to honest numbers — not the budget retroactively justified.

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
- Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences*, 24, 87–185. *(Note: Cowan's "4" is framed as focus-of-attention capacity, not a hard storage cap. Nova's hard cap is a design simplification, not a literal claim.)*
- Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). Lost in the Middle: How Language Models Use Long Contexts. *TACL 2024*. arXiv:2307.03172.
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
- Derakshan, N., & Eysenck, M. W. (2009). Anxiety, processing efficiency, and cognitive performance: New developments from Attentional Control Theory. *European Psychologist*, 14(2), 168–176. **[Tighter cite for the anxiety→System 2 trigger.]**
- Lazarus, R. S. (1991). *Emotion and Adaptation.* Oxford UP. **[Source theory for cognitive appraisal — verbalization of affect into the prompt (§3.5).]**
- Scherer, K. R. (2001). Appraisal considered as a process of multilevel sequential checking. In *Appraisal Processes in Emotion: Theory, Methods, Research* (pp. 92–120). Oxford UP. **[Component Process Model — alternative appraisal frame.]**
- LeDoux, J. (1996). *The Emotional Brain.* Simon & Schuster.
- Phelps, E. A., & LeDoux, J. E. (2005). Contributions of the amygdala to emotion processing. *Neuron*, 48, 175–187.
- Phelps, E. A. (2004). Human emotion and memory: interactions of the amygdala and hippocampal complex. *Current Opinion in Neurobiology*, 14(2), 198–202. **[Justifies wider similarity threshold for aversive-tag retrieval (§3.6).]**
- Bach, D. R., & Dayan, P. (2017). Algorithms for survival: a comparative perspective on emotions. *Nature Reviews Neuroscience*, 18, 311–319. **[Form of linear-with-decay affect dynamics (§3.5).]**

### Reinforcement learning (TD-error and value functions)

- Sutton, R. S. (1988). Learning to predict by the methods of temporal differences. *Machine Learning*, 3, 9–44. **[Algorithm anchor for TD-learning, paired with Schultz et al. 1997 as the neuroscience anchor.]**
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press. **[Standard reference for online linear function approximation; Ch. 9 covers TD(0) convergence under on-policy sampling — the regime Nova's V operates in.]**
- Wu, K. (2014). 2048 AI — heuristic-based search. *Open-source notes.* **[Source for `φ_mono` (monotonicity) heuristic in V's feature set, §3.7.]**

### LLM agents

- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *UIST 2023*. arXiv:2304.03442. **[Memory-stream blueprint.]**
- Yao, S., Zhao, J., Yu, D., et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*. arXiv:2210.03629.
- Yao, S., Yu, D., Zhao, J., et al. (2023). Tree of Thoughts. *NeurIPS 2023*. arXiv:2305.10601.
- Shinn, N., Cassano, F., Berman, E., et al. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*. arXiv:2303.11366.
- Wang, G., Xie, Y., Jiang, Y., et al. (2023). Voyager: An Open-Ended Embodied Agent with Large Language Models. arXiv:2305.16291.
- Packer, C., Wooders, S., Lin, K., et al. (2023). MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560.
- Croissant, M., Frister, M., Schofield, G., & McCall, C. (2024). An Appraisal-Based Chain-of-Emotion Architecture for Affective Language Model Game Agents. *PLOS ONE*. **[Closest prior art for the affect module.]**
- Li, C., Wang, J., Zhang, Y., et al. (2023). Large Language Models Understand and Can Be Enhanced by Emotional Stimuli (EmotionPrompt). arXiv:2307.11760.
- Webb, T., Mondal, S., & Momennejad, I. (2025). A brain-inspired agentic architecture to improve planning with LLMs (Modular Agentic Planner). *Nature Communications*, **16:8633**. arXiv:2310.00194. *(Differentiation note: Nova adds affect + episodic memory; MAP is planning-only.)*

---

*End of design specification, draft 1.*
