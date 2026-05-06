# Project Nova — Methodology

> **Status:** v1 (2026-05-02). This is the **load-bearing technical doc** for the
> commercial pitch. Every claim Nova makes about a game is traceable to one of
> the constructs defined here. Read this first if you're evaluating whether
> Nova's outputs deserve the trust the marketing implies.
>
> **Audience:** technical buyers (Product Director, Live Ops Director,
> in-house data scientist), academic reviewers, and any future engineer
> implementing or extending the analytical layer.

---

## 1. The four State-Transition Signatures

Nova does not predict player behavior from isolated affect snapshots. A single
spike in anxiety is too noisy — it could mean "fun challenge," "annoying
puzzle," or "about to quit," and the simulation can't distinguish them. Nova
predicts behavior from **multi-step compositional patterns** in the affect
vector trajectory. Four named signatures cover the commercially relevant
cases.

Each signature is defined as a **state-machine pattern**: a sequence of affect
transitions across consecutive moves that, when matched, predicts a specific
player outcome. Matching is operationalized so the same input produces the
same signature classification on every run.

### 1.0 Affect dimensions and signature anchors

Nova's affect vector has six dimensions: valence, arousal, anxiety,
frustration, confidence, dopamine. Two of those (*valence*, *arousal*)
take qualitative inspiration from Russell's circumplex model (1980).
The remaining four (*anxiety*, *frustration*, *confidence*, *dopamine*)
are **Nova-engineered operational primitives**, not literature-derived.
Their update rules and threshold values are calibrated against in-game
outcomes, not against psychometric data, and they fire at the per-move
timescale (~1–3s per update) rather than the minutes-to-hours timescale
at which Russell's instrument was validated. The Russell appropriation
on the two anchored dimensions is qualitative, not validated at our
timescale — see §7 caveat.

The four State-Transition Signatures defined in §1.1–1.4 below are
correspondingly **engineered conjunction predicates** over those six
dimensions. Each "Inspiration" line cited per signature names the work
that *inspired the qualitative shape* of the conjunction (e.g., that
confidence-decay after a stress event predicts disengagement). It is
not a claim that the specific thresholds, durations, or co-firing rules
are derived from that work. The thresholds are products of in-house
calibration; the literature framed the question, not the answer.

### 1.1 Signature Alpha (Churn)

**Pattern:** `Confidence ↓` across 3+ consecutive moves following an `Anxiety
↑` event, terminating in `Frustration plateau` (frustration > 0.5 sustained
for 5+ moves with score-delta < 0).

**What it predicts:** The player is in a confidence-decay loop and is
statistically likely to end the session within the next 8–12 moves without
progression.

**Why this works:** Decline in confidence after a stress event is the
classical setup for learned-helplessness behavior in human play. Frustration
plateau (sustained frustration with no score recovery) is the operational
signature of "the player has stopped trying."

**Falsification criterion:** If Signature Alpha fires in N sessions and the
player completes the level cleanly in > 50% of them, the signature is
mis-tuned (probably the confidence-decay window is too short). Tune,
re-validate.

**Inspiration:** Conjunction shape inspired by flow-disruption research
(Csikszentmihalyi, 1990) and model-based RPE updates at agentic
timescales (Daw, Niv, & Dayan, 2005; Niv, 2009). Phasic-dopamine RPE
(Schultz et al., 1997) is foundational *concept*, not the operational
anchor — Nova's per-move RPE update is model-based, not phasic. The
3-move confidence window, 0.5 frustration threshold, and 5-move plateau
duration are calibrated, not literature-derived.

### 1.2 Signature Beta (Spend Conversion)

**Pattern:** `Frustration ↑` (cross above 0.5) co-occurring with `Dopamine
starvation` (dopamine < 0.2 for 3+ consecutive moves), in proximity to a
visible monetization touchpoint (store UI element, paywall card, energy gate).

**What it predicts:** The player is in the "frustration-conversion moment"
where F2P spend is most likely. Studios use this signal to validate that
monetization touchpoints are placed where conversion psychology predicts
they'll convert — not just where they're convenient.

**Why this works:** Frustration-driven spending is a documented F2P pattern
— spend rates rise sharply when players hit a difficulty wall and a paid
shortcut is visible.

**Falsification criterion:** If Signature Beta fires in N sessions across a
test population and the real-world spend rate at that game position does
not differ from baseline, the signature is mis-tuned (probably the
dopamine-starvation threshold is too aggressive).

**Inspiration:** F2P monetization psychology research and Quantic
Foundry's empirical motivation work informed the
frustration + dopamine-starvation conjunction shape. The 0.5 frustration
crossing, 0.2 dopamine threshold, and 3-move duration are calibrated,
not literature-derived.

### 1.3 Signature Gamma (Engagement)

**Pattern:** `Confidence ↑` and `Dopamine ↑` co-rising across 3+ consecutive
moves, with `Anxiety` remaining below 0.4 throughout.

**What it predicts:** The player is in flow. This game position is
producing the engagement state designers explicitly aim for. If you're
reviewing a level for "is this fun," Signature Gamma is the green-light
indicator.

**Why this works:** Co-rising confidence and reward signals without anxiety
is the operational definition of Csikszentmihalyi's flow channel — the
match between challenge and skill that produces sustained engagement.

**Falsification criterion:** If Signature Gamma fires in N sessions and
Time-on-Task at that position is shorter than baseline (i.e., players leave
even though Nova says they're engaged), the signature is mis-tuned.

**Inspiration:** Csikszentmihalyi (1990), *Flow: The Psychology of
Optimal Experience* — the qualitative shape (rising confidence + reward
without anxiety) reflects flow-channel theory. The 0.4 anxiety ceiling
and 3-move co-rise duration are calibrated, not literature-derived.

### 1.4 Signature Delta (FTUE Bounce)

**Pattern:** `Anxiety ↑` (cross above 0.5) within the first 60 seconds of a
fresh session, in a persona with empty memory (First-Time Felix or Returning
Lapsed Rae).

**What it predicts:** The player is about to abandon the FTUE. This is the
"D1 retention killer" pattern that drives the largest single retention loss
in mobile games today.

**Why this works:** Tutorial confusion produces affect signatures distinct
from in-game frustration. A fresh-session anxiety spike with no prior
context indicates the FTUE is failing to scaffold the player into the
game's mental model.

**Falsification criterion:** If Signature Delta fires in N first-time
sessions and the studio's actual D1 retention at that point does not
differ from baseline, the FTUE is fine and the signature is firing on a
non-issue.

**Inspiration:** Tutorial-bounce as the dominant D1-retention killer is
documented in GameAnalytics 2025 mobile retention research (top-quartile
D1 = 26.5%, worsening trend) and Nielsen Norman Group user-onboarding
research — those works frame the *qualitative phenomenon* the signature
detects. GameAnalytics is also the KPI baseline source for Delta's
predicted-D1-delta mapping (§2). The 0.5 anxiety threshold and 60-second
window are calibrated, not literature-derived.

### 1.5 Why four (not 12, not 2)

Four signatures cover the commercially actionable outcomes (churn,
conversion, engagement, FTUE bounce) without overfitting the analytical
layer to specific games. Each signature has a clear falsification criterion
and a clear KPI mapping (next section). Adding a fifth signature requires
new evidence that an outcome category isn't covered by these four.

### 1.6 Future work: long-horizon simulation (Day-N retention prediction)

Phase 4 of the roadmap extends Nova from single-session prediction
("does this level frustrate Casual Carla?") to multi-session simulation
("does the difficulty curve in weeks 1-4 produce the Day-30 retention
curve the studio is forecasting?"). This is the question UA Managers and
Live Ops Directors actually buy answers to, and Nova is architecturally
positioned to answer it without taking 30 calendar days to do so.

The mechanism is **time compression** (via the Unity SDK's clock-advance
primitive, Nova plays 30 simulated days in ~15 minutes of wall-clock) plus
**cognitive carryover** — the agent's memory and affect baselines persist
across simulated sessions, so Day 3's frustration shapes Day 17's churn
risk via accumulated affective load.

#### 1.6.1 Multi-rate memory decay

Current Nova treats all memory channels as if they had the same temporal
persistence. Real human memory does not. For multi-day simulation, we
apply differentiated decay matched to the three established memory
channels (Tulving, 1972):

| Channel | What it stores | Half-life (simulated time) | Inspiration |
|---------|----------------|------------------------------|---------------------|
| **Episodic** | Specific past events (per-move board states, individual decisions) | ~24 hours | Forgetting-curve research (Ebbinghaus, 1885; Murre & Dros, 2015) — qualitative shape only; half-life value is engineered |
| **Semantic** | Generalized lessons from reflection (post-game extracted rules) | ~7 days | Long-term semantic retention research (Bahrick, 1984) — qualitative shape only; half-life value is engineered |
| **Affective baseline** ("the scar") | Persistent shifts in mood/anxiety from significant negative events | ~30 days, asymptotic floor (never returns to zero) | Nova-engineered (no specific literature anchor); the qualitative shape (slow exponential decay with non-zero floor) is inspired by general trauma-persistence research, but the half-life value, the floor parameter, and the exponential-decay rule are Nova design choices, not parameters extracted from any cited paper |

This is what makes the "Day-3 frustration → Day-17 churn" prediction
mechanism work. Affective scars persist long after episodic details fade,
so accumulated negative-experience weight raises baseline anxiety enough
to shorten the cognitive buffer for normal challenges later in the
simulated month.

The half-life values above are **engineered defaults**. The episodic
and semantic channels take qualitative inspiration from the named
forgetting-curve research (Ebbinghaus 1885, Murre & Dros 2015, Bahrick
1984), but the specific half-life values, the asymptotic-floor
parameter on the affective channel, and the channel-specific update
rules are Nova design choices calibrated against in-game outcomes —
not parameters lifted from the cited papers. They will be calibrated
further against real per-cohort retention data from paid pilots
(Phase 6 onwards). The calibrated values become part of the validation
corpus moat — every studio's pilot data refines our decay coefficients
against their actual user base.

#### 1.6.2 Cohort-distribution reporting (handling compounding error)

A single 30-day trajectory accumulates error exponentially. Small
inaccuracies in single-day affect dynamics compound into noise by Day
30. This is the same mathematical reality that limits weather forecasting
beyond ~10 days regardless of model quality.

**Mitigation:** Nova never reports a single-trajectory point prediction
for Day-N retention. Instead, every long-horizon prediction is reported
as a cohort distribution:

- Run N=50+ personas with the same baseline through the simulated 30-day
  arc
- Report the median, P25, P75, and 95% confidence interval of the
  Signature-Alpha firing rate at each day
- Honest 30-day prediction format: **"Median 28% Day-30 churn (95% CI
  [22%, 38%]), driven by accumulated affective baseline drift over the
  Day 3-7 difficulty band"**

The widening confidence interval *is* the prediction — it makes the
inherent uncertainty visible and actionable. Studios use the
distribution shape (not just the median) to make decisions: a wide CI
means "this design has high outcome variance, run it past more human
playtesters before shipping;" a tight CI means "this design produces
consistent player reactions across personas, ship with confidence."

#### 1.6.3 What needs to be built

The single-session machinery validated in Phase 0.7 / 0.8 supports the
single-day case. Long-horizon simulation requires three additional
implementation pieces:

- **Simulated-time clock primitive.** A `SimulatedClock` service that
  advances the virtual game clock and Nova's internal time counter in
  lockstep, exposed via the Unity SDK as a `FastForward(timedelta)`
  call. Decay functions consume the clock's elapsed-since-last-event
  reading per memory record.
- **Multi-rate decay function on memory records.** Each `EpisodicRecord`
  and `SemanticRule` gains a `last_decay_check_at_simulated_time` field.
  On retrieval, weight is recomputed via the channel's exponential decay
  function. Affective baseline state is similarly decayed between
  sessions.
- **Cross-session state persistence.** A `PlayerState` snapshot that
  captures `AffectVector` baselines + memory store state at session-end
  and restores them at next-session-start, with the decay applied for
  the elapsed simulated gap. Already partially supported by
  `AffectState.reset_for_new_game()` (Task 36); needs extension to soft-
  reset rather than hard-reset.

**Estimated implementation:** 1-2 weeks of focused work in Phase 4. See
the corresponding work unit in [`product-roadmap.md`](./product-roadmap.md)
§4.6.

#### 1.6.4 Why this isn't validated yet

Three reasons we ship this as future work, not as a current capability:

1. **The basics must validate first.** Phase 0.7 (cliff test) and Phase
   0.8 (trauma ablation) test the single-session machinery. If the
   single-session affect predictions don't track human pain (Phase 0.7
   fails), there's no point extending to multi-day. Long-horizon work
   gates on those two passes.

2. **Decay parameters need calibration data.** Half-lives are
   engineered defaults (see §1.6.1 reframing); per-game and per-genre
   calibration requires real-user retention curves to fit against. We
   get that data from paid pilots, not from internal validation.

3. **Compounding error needs validation too.** The cohort-distribution
   reporting principle is sound in theory; whether the actual confidence
   intervals stay narrow enough to be commercially useful at Day 30 is
   an empirical question. If the CI grows to ±25 percentage points by
   Day 30 across all personas, the prediction is too noisy to be
   actionable and we ship "5-day prediction with high confidence" rather
   than "30-day prediction with low confidence." The product framing
   adapts to whatever the empirical width turns out to be.

---

## 2. Signature → KPI Translation

Nova's reports lead with KPI predictions, not affect curves. The
translations below are the load-bearing math: every prediction in a Nova
report can be traced to a Signature firing rate in the per-cohort session
data.

| Signature | KPI mapping | Methodology |
|-----------|-------------|--------------|
| **Alpha (Churn)** | Predicted abandonment rate at this game position | (Sessions where Alpha fires within 5 moves of position) / (Total sessions reaching position). Reported per persona cohort. |
| **Beta (Conversion)** | Predicted spend trigger location + intensity | (Sessions where Beta fires near monetization touchpoint) / (Total sessions reaching touchpoint). Intensity = mean dopamine starvation duration. Reported per persona, weighted by persona's spend propensity prior. |
| **Gamma (Engagement)** | Predicted time-on-task / "flow window" duration | Mean duration of Gamma firing per session. Persona-specific. The "this level is fun" indicator. |
| **Delta (FTUE Bounce)** | Predicted D1 retention delta | (Sessions where Delta fires) / (Total first-time sessions). Mapped to retention via published correlation between FTUE confusion and D1 (cite at report-rendering time). |

**What we DO NOT publish without validation data:** absolute KPI values
(e.g., "predicted D1 retention is 27%"). What we DO publish: relative
deltas vs a baseline or A/B comparator (e.g., "version B shows 18% lower
predicted abandonment at level 5 vs version A"). Relative comparisons are
defensible without per-game calibration; absolute predictions require it.

---

## 3. Inference architecture

Nova routes compute by cognitive load, mirroring Kahneman's dual-process
cognition framework (Kahneman, 2011, *Thinking, Fast and Slow*). The
production stack is hybrid local + API:

| Path | Model | Where it runs | Why |
|------|-------|----------------|-----|
| **System 1 (ReAct)** — 90% of moves: routine, pattern-matching decisions | Qwen 2.5 14B Instruct or Phi-4 14B (vLLM) | Local GPU (consumer-grade RTX 4090 or M-series Mac, 12-16GB VRAM) | Fast, intuitive, ~250-500ms inference, zero marginal cost per move |
| **System 2 (ToT)** — 5-10% of moves: deliberative branching at high-stakes positions | Claude Haiku 4.5 (or Gemini Pro 2.5 if Anthropic unavailable) | Frontier API | Branches need real reasoning depth; rare enough that API cost is bounded |
| **System 2 (Reflection)** — 1 call per game-over | Claude Sonnet 4.6 | Frontier API | Postmortem narration benefits from frontier reasoning + longer context; fires once per game so cost is negligible |
| **Cheap vision** — OCR fallback for games without SDK | Gemini 2.5 Flash-Lite | Frontier API | Vision is the OCR fallback path only; production uses Unity SDK perception |

### 3.1 Why this works

- **System 1 is local.** 90% of moves never leave the studio's machine. Zero
  marginal cost. Sub-second latency. No data leaves the perimeter (important
  for studios with strict IP protection on pre-launch builds).
- **System 2 is API.** The 5-10% of moves that warrant deliberation get
  frontier-model reasoning. API cost stays bounded because deliberation is
  rare by design.
- **Reflection is API.** Once per game; the long-context narration LLM does
  this best.

### 3.2 The reliability mechanism that makes 14B local viable

Local 14B-class models historically suffer from inconsistent JSON output —
they drop closing brackets, hallucinate field names, miss enum values. This
breaks Nova's typed event bus.

**Solution:** vLLM's `guided_decoding` with JSON-schema constraints. Schema
constraints are enforced at sampling time — the model literally cannot emit
tokens that produce malformed JSON, because the sampler rejects them. Parse-
error rate drops to **literal zero** by construction, not "drastically
lower."

This is what makes the 14B-class local path practical. Without schema
constraints, we'd need 32B+ for acceptable JSON reliability. With
constraints, 14B is sufficient.

### 3.3 What we are NOT doing (RL pivot rejected)

A standard architectural temptation at this scale is to pivot from LLMs to
reinforcement learning (PPO, DQN). RL would master 2048 in an hour and
produce a perfect player at zero per-move cost.

**We are not doing this.** RL produces optimizers; Nova produces simulators.
RL outputs a probability distribution over actions; Nova outputs reasoning
text + affect trajectory + reflection lessons. Without the reasoning text,
there is no Cognitive Audit Trace, no persona narrative, no Brain Panel,
and no commercial product distinct from modl.ai's existing RL coverage
testing. The cognitive architecture is the moat; trading it for inference
speed kills the product.

---

## 4. Statistical foundation

Nova's claims about its own internal mechanisms are validated empirically.
Two specific tests anchor the methodology:

### 4.1 The Cliff Test (cognitive prediction validity)

**Hypothesis:** Nova's affect curve peaks *before* documented human
struggle points, AND the affect-driven prediction is more accurate or
earlier than a non-affective baseline. Both conditions must hold; either
alone is insufficient.

**Why two conditions, not one:** A single-arm test ("did Carla's anxiety
peak before failure?") cannot distinguish "affect predicts" from "any
agent fails at the same threshold because the game's mechanics get
harder past it." Without a non-affective control, an apparent pass is
unfalsifiable — Carla could be reading the geometry of the board, not
its cognitive load. The Blind Control Group fixes this by adding an
emotionless score-maximizing baseline and treating Carla's *delta over
baseline* as the load-bearing signal. See ADR-0007 for the full
falsification rationale.

**Method:** For each documented hard 2048 scenario (community-catalogued
"snake collapse," "1024-wall" patterns; 3-5 scenarios total):

1. **Test arm — Casual Carla persona** (N=20 per scenario). Cognitive
   architecture active: memory, affect, ToT deliberation, reflection.
   Record full affect-vector trajectories per move. Mark the move at
   which `Anxiety` first crosses `0.6` (the prediction event).

2. **Control arm — Baseline Bot persona** (N=20 per scenario). Single
   purely-logical prompt: *"You are an AI agent playing 2048. Your only
   goal is to maximize score. Compute the next move."* No affect, no
   memory retrieval, no ToT, no reflection. Record only the move
   sequence and game-over move index.

3. **Comparison.** For each scenario, compute:
   - `t_carla_predicts` = mean move index at which Carla's `Anxiety >
     0.6` precedes her game-over move
   - `t_baseline_fails` = mean move index at which Baseline Bot games
     end (effectively the failure rate's mode)
   - `Δ = t_baseline_fails - t_carla_predicts` (positive = Carla
     predicts the cliff *that many moves earlier* than the baseline's
     raw failure curve)

**Pass criteria (both must hold):**

- Affect peak precedes Carla's failure point by ≥ 2 moves in > 80% of
  her N=20 trials per scenario (the original prediction-validity test)
- AND `Δ ≥ 2` moves in ≥ 3 of the 3-5 scenarios (the affect-earns-its-keep
  test — Carla must predict the cliff materially earlier than a stupid
  score-maxer just runs out of options)

**Failure modes:**

- *Single-arm pass* (Carla predicts but `Δ < 2`): the affect layer is
  decorative — it tracks the cliff but doesn't precede it more than a
  baseline would by sheer mechanical exhaustion. The architecture-as-
  predictor claim is **demoted to architecture-as-narrator**; we
  reposition the demo around interpretability, not prediction.
- *Both-arm fail* (no early Anxiety peak in Carla): full failure of the
  prediction hypothesis. Per the original criterion, the affect-rework
  branch begins (re-derive RPE weights, ablate dimensions) before any
  pitch.
- *Both-arm pass* (Carla predicts AND `Δ ≥ 2`): the architecture earns
  its keep. The pitch line becomes "Baseline failed at move 100, Nova
  raised the alarm at move 96 — 4 moves of warning your studio can
  use," with the actual `Δ` from the corpus of scenarios.

**Apparatus:** Python `Game2048Sim` (in-process simulator, no emulator
overhead). Both arms run on the **same seeded board sequences** so the
mechanics are identical and the only varying factor is the cognitive
configuration. Removes perception/action layer noise; isolates the
cognitive layer for measurement.

**Cost:** ~100 extra games per scenario × 3-5 scenarios = +300-500 games
on the Cliff Test budget. At plumbing-tier pricing (~$0.05-0.10 per
game) that is <$50 of additional spend — negligible against the
scientific validity gain.

### 4.2 The Trauma Ablation (mechanism validity)

**Hypothesis (dual).**

- *Primary (behavioral):* Trauma-tagging reduces within-game re-engagement
  with trap-similar board configurations after a first trap encounter.
  An agent whose trauma mechanism is doing its job adapts within the same
  session — the same way a human player who hits a brutal trap mid-game
  plays more cautiously for the remaining moves.
- *Secondary (affective):* Trauma-tagging adds a measurable negative-state
  lift at trap-similar board states, over and above the no-trauma baseline.
  This validates that the mechanism's intended pathway (aversive memory →
  affect lift) is the one the architecture actually expresses.

The primary is the on-thesis behavioral signature of avoidance learning, which
is what trauma is engineered to implement. The secondary is the mechanism-
pathway validation: it tests *how* trauma works, not only *whether* it works.

**Method.** Run N=1000 games with trauma-tagging enabled (`Y_on`) and N=1000
with trauma-tagging disabled (`Y_off`) against the same seeded board sequence
in `Game2048Sim`. Both arms use the deployed cognitive architecture; trauma-
tagging is the only varied component. From every run record (a) the per-move
proximity of the current board to the closest documented trap pattern (the
Phase 0.7 scenario patterns: corner-abandonment, snake-collapse, high-tile-
wall) and (b) the per-move Anxiety value.

**Independent variable.** Trauma-tagging on vs. off. Same seeds across arms
to fix the spawn schedule, so the IV is the only difference between paired
games.

**Primary DV (gating) — within-game trap-recurrence rate.** For each game,
identify the first move whose board configuration matches a trap pattern
within proximity threshold T. After that move, count the fraction of
remaining moves that *also* enter trap-similar states (proximity ≥ T to any
documented pattern). This per-game rate is the within-game re-engagement
metric; trauma-on should produce systematically lower rates than trauma-off.

**Secondary DV (descriptive) — affective lift at trap-similar states.** For
each move whose board satisfies proximity ≥ T to any documented pattern,
record the Anxiety value. Compare the trauma-on and trauma-off distributions
at trap-similar states.

**Pre-registered pass criterion (gating, primary only).** Cohen's `d ≥ 0.3`
on the primary DV with 95% CI excluding 0, and trauma-on rate < trauma-off
rate. **Primary nulls = fail, regardless of secondary result.** This locks
the gate before pilot data exists, so we cannot drift to the DV that happened
to pass.

**Pre-registered descriptive criterion (secondary, non-gating).** Cohen's `d`
and 95% CI on the secondary DV are computed and reported alongside the
primary result. The secondary does not change the pass/fail outcome.

**Operational details deferred.** The trap-similarity metric, the proximity
threshold `T`, and the trap-pattern dictionary will be specified in the
Phase 0.8 implementation spec, not here. The methodology fixes the test
shape (primary behavioral, secondary affective, both pre-registered, primary
gates); the spec writes the operational definitions when Phase 0.8 begins.

**Failure modes (three branches).**

- *Primary nulls:* trauma is **demoted** from a core architectural feature
  to a UI flavor. The mechanism is preserved (already implemented, brain-
  panel visualization is compelling) but we stop marketing it as a
  competitive differentiator.
- *Primary passes, secondary nulls:* trauma works behaviorally but does
  *not* express through the affect pathway — i.e., the mechanism reaches
  the decision via planning / ToT / memory-conditioned routing rather than
  through Anxiety lift. This is an ADR-worthy architectural finding; document
  in a follow-up ADR amendment and reframe the affect-pathway claim
  accordingly. Does not invalidate trauma as a feature.
- *Both pass:* trauma is validated as a behavioral feature with affect-
  pathway expression. Pitch line: "Carla feels the cliff (affect lift) and
  adapts around it (trap re-engagement drops within session)."

**Why behavioral primary in a cognitive-architecture test.** Behavior is the
on-thesis test for *avoidance learning*, which is the mechanism trauma
implements. Affect is the proposed *pathway* by which the mechanism reaches
behavior. A cognitive-architecture validation that gated on the pathway
rather than the function would conflate "the mechanism works" with "the
mechanism works *via the specific channel we expected*." The architecture
is allowed to route trauma's effect through any of its decision pathways
(memory consultation, ToT branch evaluation, arbiter thresholding); the
primary DV tests the function, the secondary DV tests one specific pathway.

### 4.3 Why within-game adaptation, not cross-game optimization

Trauma in the cognitive architecture is *avoidance learning within a session*
— the agent remembers what killed it during the current playthrough and
shifts behavior for the remaining moves. The empirical signature is **reduced
within-game re-engagement with trap-similar configurations after a first
trap encounter**, not optimal play across separate games.

This distinction matters because Nova is a synthetic playtesting tool, not
an RL optimizer. The product value comes from faithfully simulating how a
human player experiences a level — including the realistic failure mode of
"player hits trap, adapts cautiously, runs out of options, quits." A cross-
game optimizer that learned to skip the trap entirely would be the wrong
tool for the job: studios pay for the failure signal, not for an agent that
no longer hits the failure. Within-session adaptation is faithful simulation;
cross-session optimization is not.

The expected behavioral signature is therefore: trauma-on agents engage with
trap-similar states *less* in the moves following a trap encounter *within
the same game* than trauma-off agents do, on the same seeded board. They
still hit the original trap (same seed, same first encounter). What changes
is what happens after — the within-session adaptation. That is the
playtester signal, and it is the on-thesis test for trauma as Nova
implements it.

Mean-performance tests (does trauma-on score higher?) are the wrong shape
for this hypothesis. Variance-on-score tests (does trauma-on play more
consistently?) were the originally proposed shape but failed three
independent ways: paired observations break under trauma-on retrieving
different memories per move, 2048 score is bounded above making
asymptotic-distribution assumptions invalid, and variance reduction can
arise from over-conservative play that is not avoidance learning. The
behavioral primary DV in §4.2 is the on-thesis replacement: it tests
within-game adaptation directly, controls for the spawn schedule via paired
seeds, and is robust to the observation that the affect pathway is not the
only channel through which trauma reaches behavior.

---

## 5. What this is NOT

Nova is a product-decision tool. To preserve clarity for sophisticated
buyers, we explicitly do not claim:

- **Nova is not a QA bug-finder.** We do not detect crashes, memory leaks,
  rendering bugs, or compatibility issues. For coverage testing, modl.ai
  and traditional QA automation tools are the right answer. Nova will not
  improve your bug-find rate.
- **Nova does not predict individual player behavior.** Nova predicts
  *cohort-level* signature firing rates, which translate to KPI
  predictions per persona. A specific human player will deviate; the
  prediction is about the persona aggregate, not a singular user.
- **Nova does not replace human playtesting.** Nova produces directional
  evidence in 30 minutes for design hypotheses that would otherwise take
  3-4 weeks of human playtesting to investigate. Human playtesting remains
  the right tool for nuanced edge cases, qualitative experience design, and
  validation of Nova's own predictions.
- **Nova does not currently support real-time games.** The screenshot-per-
  step + LLM-driven decision pipeline cannot test action games, racing,
  shooters, or any title with sub-second decision windows. v1 addresses
  turn-based puzzle, strategy, narrative, and slow-paced live-service
  content. Real-time coverage is a future architectural decision, not a
  current capability.
- **Nova is not affect detection in real human players.** Nova simulates
  affect in synthetic personas. We do not analyze real player webcam
  feeds, biometric data, or session telemetry to infer human emotional
  state. The synthetic affect is the product; the real affect is out of
  scope.

---

## 6. Validation corpus (the moat that grows)

Each paid pilot bundles a 30-day measurement window in which Nova's
signature predictions are compared against the studio's actual real-user
metrics post-launch. The dataset built from this:

```
For each (game, persona, signature) tuple:
  - Nova's predicted firing rate
  - Actual real-user behavior at that position
  - Calibration delta (predicted - actual)
  - Confidence interval
```

After 5-10 pilots, this corpus is the largest moat. Competitors with
prompt-engineered persona libraries can clone the surface behavior, but
they cannot clone the calibration data without doing their own pilots
first. The corpus, combined with the **published methodology** (this doc),
establishes Nova as the industry benchmark for cognitive playtesting math.

---

## 7. Citations bibliography

The full 41-citation list is in `scientific-foundations.md`. The most
load-bearing for this methodology:

- **Schultz, W., Dayan, P., & Montague, P.R. (1997).** "A neural
  substrate of prediction and reward." *Science*, 275(5306), 1593-1599.
  — Foundational phasic-RPE concept; cited for **conceptual lineage
  only**. Nova's per-move RPE update operates at agentic timescales
  (~1–3s per move), not the ~100ms phasic-dopamine timescale Schultz
  et al. measured. See Daw + Niv below for Nova's operational anchor.
- **Daw, N.D., Niv, Y., & Dayan, P. (2005).** "Uncertainty-based
  competition between prefrontal and dorsolateral striatal systems
  for behavioral control." *Nature Neuroscience*, 8(12), 1704-1711. —
  Model-based vs model-free RL framing; Nova's per-move RPE update is
  model-based, operating at agentic timescales rather than at phasic-
  dopamine timescales.
- **Niv, Y. (2009).** "Reinforcement learning in the brain." *J.
  Mathematical Psychology*, 53(3), 139-154. — RL learning rules at
  agentic timescales; companion citation to Daw et al. (2005) as
  Nova's operational RPE anchor.
- **Russell, J.A. (1980).** "A circumplex model of affect." *J.
  Personality and Social Psychology*, 39(6), 1161-1178. —
  Inspiration for **only two of Nova's six affect dimensions**
  (*valence* and *arousal*; rendered literally in the brain panel
  mood gauge). The other four dimensions (anxiety, frustration,
  confidence, dopamine) are Nova-engineered operational primitives,
  not Russell-derived. Russell's circumplex is also validated at
  minutes-to-hours self-reported timescales, not at the ~1–3s
  per-move timescale Nova fires; the appropriation on the two
  anchored dimensions is qualitative, not validated at our timescale.
- **Csikszentmihalyi, M. (1990).** *Flow: The Psychology of Optimal
  Experience.* Harper & Row. — Engagement signature foundation.
- **Kahneman, D. (2011).** *Thinking, Fast and Slow.* Farrar, Straus and
  Giroux. — System 1 / System 2 routing framework.
- **Sumers, T.R., et al. (2024).** "Cognitive Architectures for Language
  Agents." TMLR. — Architectural lineage; CoALA-shaped agent.
- **Bergdahl, J., et al. (EA SEED, 2020).** "Augmenting Automated Game
  Testing with Deep Reinforcement Learning." IEEE CoG 2020. — Adjacent
  industry precedent (deep-RL playtesting; distinct from Nova's LLM-
  cognitive approach).
- **GameAnalytics (2025).** Mobile gaming retention benchmarks report. —
  D1/D7 retention baselines used in Signature Delta KPI mapping.
- **Tulving, E. (1972).** "Episodic and semantic memory." In *Organization
  of Memory*, 381-403. Academic Press. — Foundation for Nova's
  three-channel memory model (§1.6).
- **Ebbinghaus, H. (1885).** *Über das Gedächtnis* (On Memory). —
  Original forgetting curve; inspires the *qualitative shape* of
  Nova's episodic-channel decay (exponential with rapid early drop).
  The specific 24-hour half-life is a Nova-engineered default, not
  an Ebbinghaus-derived value.
- **Murre, J.M.J., & Dros, J. (2015).** "Replication and analysis of
  Ebbinghaus' forgetting curve." *PLoS ONE*, 10(7), e0120644. — Modern
  replication confirming Ebbinghaus' qualitative shape; same caveat
  applies to Nova's half-life value.
- **Bahrick, H.P. (1984).** "Semantic memory content in permastore:
  Fifty years of memory for Spanish learned in school." *J.
  Experimental Psychology: General*, 113(1), 1-29. — Long-term
  semantic-retention research; inspires the *qualitative shape* of
  Nova's semantic-channel decay (much slower than episodic). The
  specific ~7-day half-life is a Nova-engineered default, not
  Bahrick-derived.
