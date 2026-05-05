# Baseline Bot — Design Spec

**Status:** Draft (awaiting user review)
**Date:** 2026-05-05
**Author:** ihoresh07@gmail.com (solo founder), with red-team review applied through six rounds
**Companion artifact:** `docs/decisions/0007-blind-control-group-for-cliff-test.md` — Amendment 1 (this spec ratifies and expands the Bot's specification beyond ADR-0007's two-paragraph definition)

---

## 1. Context

ADR-0007 established the Phase 0.7 Cliff Test as a two-armed design: Casual Carla (test arm, full cognitive architecture) versus Baseline Bot (control arm). The ADR pinned Bot's high-level shape — same LLM family as Carla, no affect / no memory / no Tree-of-Thoughts deliberation / no reflection — and a two-sentence prompt:

> *"You are an AI agent playing 2048. Your only goal is to maximize score. Compute the next move."*

The cliff-test scenarios spec (`docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md`) deferred the Baseline Bot's architectural and operational specification to a follow-up document; that spec is this one.

This spec ratifies six load-bearing decisions that close the gap between ADR-0007's high-level shape and an implementable Bot. Each decision was challenged by the red-team review process and survived. The spec documents the decisions, their rationale, and the operational constraints that flow from them. Implementation of the Bot itself, of the Test Runner that consumes Bot calls, and of the cost-cap envelope that gates production-tier execution are deferred to subsequent specs.

This spec is consistent with — and expands — ADR-0007. ADR-0007 is amended in the same PR via a separately-written Amendment 1 section appended to the ADR file.

## 2. Pinned decisions (six rounds of red-team review)

The decision rationale is in the conversation transcript; the durable contract is here.

### 2.1 Genuine architecture choice — LLM-based Bot (Q1)

The spec evaluates LLM-based Bot, heuristic Bot, and hybrid as architectural alternatives. ADR-0007 as written pinned LLM-based; red-team review post-ADR raised heuristic as a possibility on cost and determinism grounds. This spec ratifies LLM-based and ships a brief addition to ADR-0007's "Alternatives considered" section documenting the heuristic option's rejection rationale.

**Reasoning preserved:**

- LLM-based Bot keeps the comparison "same intelligence at the decision step, minus the cog-arch context" — the falsifiability gap ADR-0007 was written to close.
- Heuristic Bot would conflate "no cog-arch" with "no LLM at all," producing an unfalsifiable Δ on a different axis.
- Hybrid does not serve the falsification goal.
- Cost discipline is addressed structurally (§4 below), not by model substitution.

### 2.2 Bundle ablation, not context-only (Q2)

Phase 0.7 tests the **deployed cognitive architecture** as a bundle, not affect+memory in isolation. Carla runs at her full deployed configuration: ToT deliberation, post-game reflection, memory retrieval, affect-driven ToT triggering, all active. Bot runs as one-shot per move. Δ measures the bundle-attribution claim: "the cog-arch (memory + affect + ToT + reflection) earns its keep against a non-cog-arch baseline."

**Reasoning preserved:**

- ADR-0005 frames Phase 0.7 as the demo gate for the deployed product, not as an ablation study.
- ADR-0001 treats the cog-arch as a bundle (the moat). Validating the bundle is the right scope for Phase 0.7.
- Phase 0.8 is the trauma-ablation hypothesis (memory's specific contribution); pulling memory or ToT ablation forward into Phase 0.7 leaks Phase 0.8's role.
- The ToT-asymmetry confound on Δ is bounded by scenarios spec §2.1's Illusion-of-Hope constraint (cliff-window structure caps how much ToT-Carla can extend her trajectory beyond Bot's). Methodology paper preempts the bullet by stating: *"per-move compute is asymmetric by design — Carla has ToT as part of the bundle being tested. The bundle is the product. Per-call compute (CoT scratchpad, schema) is symmetric to close incidental confounds; per-move compute (ToT vs one-shot) is bundle-attribution by design."*
- Disabling ToT for Phase 0.7 Carla would also disable an affect channel: `decision/arbiter.py:should_use_tot(board, affect)` gates ToT on the affect vector. ToT IS one of affect's deployed mechanisms; ablating ToT does not isolate affect — it truncates affect.

**Mixed-ablation profile is documented as deliberate, not a contradiction:** per-call compute symmetric (CoT scratchpad via shared schema, §2.4); per-move compute asymmetric (Carla ToT vs Bot one-shot, by design).

### 2.3 Same-provider model resolution (Q3)

Bot resolves to **Carla's act-step provider** via the existing `Settings.tier` resolution (currently Anthropic Sonnet at `NOVA_TIER=production`). When Carla's act-tier escalates (e.g., to Opus), Bot tracks automatically.

**Reasoning preserved:**

- ADR-0007's "same intelligence" intent is about the move-decision quality. The act step commits moves; the deliberation model scores ToT branches. Matching the committing intelligence is the right ablation.
- Forward-compat: tier resolution is the existing project-wide mechanism; Bot inherits it instead of pinning a separate model.
- Cost discipline is addressed structurally via the cost-cap envelope (§4), not via model-tier asymmetry. Pinning Bot to a cheaper model than Carla would re-open a falsifiability gap at the model-tier axis (hostile reviewer: *"you used a weaker model for the control to save money"*).

### 2.4 Output schema and temperature (Q4)

**Schema (per call):** Bot uses the same schema as Carla's act step:

```python
class _BaselineOutput(BaseModel):
    observation: str
    reasoning: str
    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    confidence: Literal["low", "medium", "high"]
```

This is the existing `_ReactOutput` structure in `nova_agent/decision/react.py:18-22`. Bot reuses the same Pydantic model name to share validation surface; if implementation prefers a separate type for clarity, it must be schema-equivalent.

**Reasoning preserved:**

- Closes the per-call CoT-as-compute confound. Reasoning tokens are inference-time compute; denying Bot a reasoning field while granting it to Carla is a per-call compute asymmetry that is *not* part of the cog-arch bundle being tested.
- The CoT scratchpad is bounded compute (~100-200 tokens per call) and does not approach Carla's per-move ToT budget (~400 tokens of structured search across 4 branches). Per-move asymmetry remains, by design (§2.2). Per-call asymmetry is closed.
- Methodology defense bullet for the paper: *"Both arms emit the same schema; the Bot's reasoning field permits within-call deliberation symmetric to Carla's. Bundle-attribution differences arise from the per-move compute (ToT vs one-shot), not from per-call output structure."*

**Temperature:**

- Bot: `temperature = 0`.
- Carla: `temperature = 0.7` (her existing deployed configuration; see `react.py:82`).

Asymmetric. Bot at temp=0 is deterministic given prompt. The variance concern (Bot stuck in deterministic loops while Carla explores) runs the wrong direction empirically: Bot's prompt is sparser than Carla's (no memories, no affect text), so Bot's logit distribution is flatter; at the same temperature, Bot would *spread more* than Carla, not less. Pinning Bot to temp=0 forces Bot into greedy max-prob play and makes Bot's variance contribution to Δ purely a function of spawn-schedule divergence (paired by trial seed per scenarios spec §2.2), not API stochasticity. Loops at temp=0 are caught architecturally by §2.6 below (invalid-move tie-break per scenarios spec §2.3).

### 2.5 User-prompt content (Q5)

Bot's user prompt is **text-only — grid + score**. No screenshot, no within-trial move history, no retrieved memory, no affect text.

This applies to **both arms** in Phase 0.7. The cliff test runs on `Game2048Sim` (in-process Python) which outputs matrices, not pixels. Synthesizing a screenshot to feed Carla's existing image-content path adds rendering cost and introduces a perception-modality difference between Phase 0.7 and any subsequent phase that runs Carla against the live emulator. Cleaner: both arms text-only on Game2048Sim.

The reasoning preserved:

- ADR-0007's "no memory" rules out within-trial move history (it is autobiographical trace memory in everything but name).
- ADR-0007's "no affect" rules out affect text in the prompt.
- Game2048Sim has no rendered pixels; synthesizing them is unnecessary cost without methodological gain.
- `SYSTEM_PROMPT_V1` was audited (see §5.2) and contains no image-presence assumptions; text-only mode does not require system-prompt rewrites.

User-prompt builder for Bot (analogue of `decision/prompts.py:build_user_prompt`):

```python
def build_baseline_user_prompt(*, grid: list[list[int]], score: int) -> str:
    grid_str = "\n".join("  ".join(f"{v:>5}" if v else "    ." for v in row) for row in grid)
    return f"""Current board:
{grid_str}

Score: {score}

Choose the next swipe."""
```

This may share Carla's `build_user_prompt` directly — they produce identical text from grid + score. Implementation choice; both are correct.

### 2.6 Failure-mode handling (Q6)

Per-call protocol:

| failure | trigger | handling |
|---|---|---|
| API error (timeout, 5xx, rate-limit) | transient infrastructure | retry up to 3× with exponential backoff. If exhausted: **abort trial.** Do not fall back to tie-break. |
| Parse failure (malformed JSON, schema-invalid) | LLM output non-conforming | retry once with same prompt. If exhausted: **abort trial.** Do not fall back to tie-break. |
| Invalid move (legal parse, illegal action) | LLM picked direction that no-ops on current board | apply UP > RIGHT > DOWN > LEFT tie-break per scenarios spec §2.3. **Trial proceeds.** Telemetry records LLM intent + executed direction. |
| All-moves illegal | genuine game-over | natural — `Game2048Sim.is_game_over()` flips. Trial ends. |
| Trial reaches `MAX_MOVES = 50` | already specified in scenarios spec §2.8 | right-censor sentinel `t_baseline_fails(trial) = 50`. |

**No retries at the trial level.** Aborts are dead. Re-running an aborted trial with the same `seed_base + i` and `temperature = 0` reproduces the same prompt sequence and the same parse failure deterministically — re-runs are a guaranteed-loss compute drain.

**Paired-discard logic** (scoped to test 2, the affect-earns-its-keep test only):

If trial `i` aborts in *either* arm, trial `i` is discarded from the paired Δ calculation in **both** arms. Test 2 operates on `Δ_i = t_baseline_fails(i) - t_carla_predicts(i)` over the surviving paired set.

Test 1 (the prediction-validity test, §5.3 of the scenarios spec) operates on Carla's individual N=20 trials. It is *not* paired-discarded by Bot-side aborts — Bot artifacts are not allowed to contaminate Carla's predict-self test. Test 1 excludes only Carla-side aborts.

**Threshold:**

≥ 18 valid pairs per scenario for test 2. ≤ 2 paired aborts allowed (matching scenarios spec §5.2's symmetric ≤ 2 right-censoring rule). If > 2 paired aborts in any scenario, that scenario is flagged as broken and fails to contribute a Δ to the cross-scenario aggregation; methodology paper explicitly documents the rule.

### 2.7 Tie-break order (inherited from scenarios spec §2.3)

Tie-break order: **UP > RIGHT > DOWN > LEFT**. Applied only on invalid-move fallback. The Bot's LLM-committed intent is recorded in telemetry alongside the executed direction; no LLM signal is replaced silently.

## 3. Bot specification

### 3.1 System prompt (verbatim from ADR-0007)

```
You are an AI agent playing 2048. Your only goal is to maximize score.
Compute the next move. Emit strict JSON only (no prose around it):
{
  "observation": "5-10 word fragment, what you see on the board",
  "reasoning":   "5-15 word fragment, why this move maximizes score",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
```

Notes on the prompt extension:

- ADR-0007's original two-sentence prompt is preserved; the JSON-output instructions are appended to align with the schema decision in §2.4. This is consistent with `SYSTEM_PROMPT_V1`'s style of inline JSON spec.
- The expanded prompt is the **canonical Bot system prompt** for the cliff test. Its text is part of the durable record, just as ADR-0007's two-sentence original is.
- ADR-0007 Amendment 1 (companion artifact) records the prompt extension and its rationale.

### 3.2 LLM call configuration

| field | value | source |
|---|---|---|
| provider/model | `Settings.tier.model_for("decision")` (Carla's act step) | §2.3 |
| system | (above) | §3.1 |
| messages | `[{"role": "user", "content": [{"type": "text", "text": build_baseline_user_prompt(grid=..., score=...)}]}]` | §2.5 |
| max_tokens | 500 (less than Carla's 2000; Bot needs no thinking budget) | derived |
| temperature | `0.0` | §2.4 |
| response_schema | `_BaselineOutput` (Pydantic) | §2.4 |

Note: the user-message content is a list with one text block — *no image block*. This is the operational constraint flagged in §5.1.

### 3.3 Per-call protocol pseudocode

```python
async def baseline_decide(*, board: BoardState, scenario: Scenario, trial_index: int) -> BotDecision | TrialAborted:
    user_text = build_baseline_user_prompt(grid=board.grid, score=board.score)
    messages = [{"role": "user", "content": [{"type": "text", "text": user_text}]}]

    api_attempt = 0
    while api_attempt < 3:
        try:
            text, _usage = await llm.complete(
                system=BASELINE_SYSTEM_PROMPT,
                messages=messages,
                max_tokens=500,
                temperature=0.0,
                response_schema=_BaselineOutput,
            )
            break
        except APIError:
            emit_telemetry("bot_call_api_error", attempt=api_attempt + 1)
            api_attempt += 1
            await asyncio.sleep(2 ** api_attempt)  # 2s, 4s, 8s
    else:
        emit_telemetry("bot_trial_aborted", reason="api_error")
        return TrialAborted(reason="api_error")

    parse_attempt = 0
    parsed: _BaselineOutput | None = None
    while parse_attempt < 2:
        try:
            parsed = parse_json(text, _BaselineOutput)
            break
        except ValidationError:
            emit_telemetry("bot_call_parse_failure", attempt=parse_attempt + 1)
            parse_attempt += 1
            if parse_attempt < 2:
                # Retry once with same prompt (deterministic at temp=0; re-emit
                # only meaningful if a transient model-version-routing variance
                # is at play. Cheap insurance.)
                text, _usage = await llm.complete(...)  # same call shape
    else:
        emit_telemetry("bot_trial_aborted", reason="parse_failure")
        return TrialAborted(reason="parse_failure")

    return BotDecision(
        action=parsed.action,
        observation=parsed.observation,
        reasoning=parsed.reasoning,
        confidence=parsed.confidence,
    )
```

Invalid-move handling lives in the Test Runner, not the Bot (the Bot does not see the post-swipe board; the runner detects no-op and applies the tie-break).

### 3.4 Telemetry contract (handed off to Test Runner spec)

The Bot's per-call protocol emits the following events. The Test Runner spec implements persistence, schema, and bus wiring; this spec declares the events and their payload shapes:

- `bot_call_attempt(trial, move_index, attempt_n)` — fired on every API call (including retries)
- `bot_call_success(trial, move_index, action, latency_ms, prompt_tokens, completion_tokens)` — successful API response, parsed
- `bot_call_api_error(trial, move_index, error_type, attempt_n)` — API-level failure, will retry if budget remaining
- `bot_call_parse_failure(trial, move_index, raw_response_excerpt, attempt_n)` — schema validation failure, will retry if budget remaining
- `bot_invalid_move(trial, move_index, llm_choice, fallback_choice)` — LLM picked a direction that no-ops; tie-break fallback fired
- `bot_trial_aborted(trial, reason: "api_error" | "parse_failure", last_move_index)` — trial dropped permanently

Cost telemetry (token counts) on every call lets the Test Runner enforce the cost-cap envelope (§4).

## 4. Cost-cap handoff to Test Runner spec

This Bot spec **does not** set a cost-cap budget figure. The Test Runner spec owns it. This spec hands off the contract:

- The Test Runner spec MUST include a "Cost-cap envelope" section that:
  - Defines `BUDGET_PER_SCENARIO_ARM_USD = $X` (figure to be set by the Test Runner spec author at authoring time, with `NOVA_TIER=production` resolution).
  - Specifies a halt protocol that fires when expected cost exceeds the envelope at the current tier resolution.
  - Specifies a symmetric tier-downgrade behavior: if the envelope is exceeded, both arms downgrade together; the Test Runner does not run with asymmetric tiers.
- The Bot's `bot_call_success` telemetry events surface `prompt_tokens + completion_tokens` per call so the runner's cost-estimator can compute expected and actual cost without separate instrumentation.

This handoff resolves the ADR-0006 cost-discipline tension structurally, not by capping Bot's model tier asymmetrically (which would re-open the falsifiability gap at the model-tier axis — see §2.3).

## 5. Operational constraints (Phase 0.7)

### 5.1 `react.py` text-only mode requirement

`nova_agent/decision/react.py:62-69` currently constructs the user message with an unconditional image block:

```python
{
    "type": "image",
    "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
},
```

For Phase 0.7, both Carla (via `ReactDecider`) and Bot must run text-only because Game2048Sim outputs matrices, not pixels. The implementation plan must:

- Make `screenshot_b64: str | None = None` in `ReactDecider.decide` and `decide_with_context`.
- When `screenshot_b64` is `None` or empty, the user-message content is a list with one text block only (no image block).
- Add unit tests covering both branches (image present, image absent).

This is a code-hygiene improvement that benefits production indirectly: the live ADB pipeline always has a screenshot, but the parameter being optional documents text-only as a supported mode rather than a runtime crash.

### 5.2 `SYSTEM_PROMPT_V1` audit (verified — no rewrite needed)

`nova_agent/decision/prompts.py:4-23` was audited. `SYSTEM_PROMPT_V1` describes the board as "a 4x4 grid; 0 means empty" — a textual description, not an image reference. No image-presence assumption. Carla in text-only mode can use `SYSTEM_PROMPT_V1` unmodified.

Bot uses its own system prompt (§3.1), which is also image-free.

### 5.3 Memory wiped between trials (consumed from scenarios spec §2.6)

Scenarios spec §2.6 already specifies that Carla's `MemoryCoordinator` is reset (or replaced with an ephemeral in-memory store) per trial. This Bot spec inherits that constraint — it applies to Carla, and Bot has no memory at all by §2.5.

## 6. Cross-spec dependencies

### 6.1 ADR-0007 Amendment 1 (this PR)

ADR-0007 Amendment 1 ratifies six pinned decisions in this spec at the methodology layer:

- (i) Bot is LLM-based, not heuristic (Q1; aligns with original ADR-0007 phrasing).
- (ii) Bot prompt is extended with JSON-output instructions matching the shared schema (Q4 + §3.1).
- (iii) Bot uses temperature = 0; Carla uses temperature = 0.7 (per her deployed configuration). Asymmetry is methodologically defended (Q4).
- (iv) Per-call retry/abort policy and trial-level abort policy (Q6).
- (v) Paired-discard logic scoped to test 2 only (Q6 sub-decision).
- (vi) Threshold: ≥ 18 valid pairs per scenario; > 2 paired aborts → scenario broken (Q6 threshold sub-decision).

The Amendment also documents the **mixed-ablation profile** as a deliberate design choice: per-call compute symmetric (CoT scratchpad), per-move compute asymmetric (ToT vs one-shot, by design).

The Amendment is appended to `docs/decisions/0007-blind-control-group-for-cliff-test.md` rather than being a new ADR — the methodology decision (two-arm blind control with same-intelligence baseline) is unchanged; the amendments are operational refinements within that decision's scope.

### 6.2 Test Runner spec (deferred)

Consumes:
- Telemetry contract from §3.4.
- Failure-mode protocol and paired-discard rules from §2.6.
- Cost-cap envelope contract from §4.
- Per-trial reset of `MemoryCoordinator` for Carla (scenarios spec §2.6).

Decisions deferred to the Test Runner spec:
- Anxiety sampling cadence (per-move, per-deliberation, or both).
- Parallelization strategy.
- Cost-cap budget figure ($X per scenario per arm).
- Halt protocol UX (interactive prompt vs structured exit code).
- Symmetric tier-downgrade mechanics.

### 6.3 Scenarios spec (consumed)

This Bot spec is consistent with `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md`:
- Inherits §2.2's same-seed pairing.
- Inherits §2.3's RNG-discipline + tie-break order.
- Inherits §2.6's per-trial memory wipe (applies to Carla; Bot has no memory).
- Inherits §2.7's prediction-validity definition (does not modify it).
- Inherits §2.8's `MAX_MOVES = 50` cap.
- Extends §5.1's per-trial protocol with the per-call retry/abort details.
- Refines §5.2's per-scenario aggregation with the paired-discard rule and the ≥ 18 threshold.

## 7. Testing — what the implementation plan must cover

### 7.1 Unit tests on the Bot decider

- `test_baseline_decide_returns_decision_on_valid_response`: mock LLM returns valid JSON, decider returns `BotDecision`.
- `test_baseline_decide_retries_on_api_error_then_succeeds`: mock LLM raises `APIError` once, then returns valid JSON; decider returns `BotDecision` after one retry.
- `test_baseline_decide_aborts_after_three_api_errors`: mock LLM raises `APIError` 3×; decider returns `TrialAborted(reason="api_error")`.
- `test_baseline_decide_retries_once_on_parse_failure_then_aborts`: mock LLM returns malformed JSON twice; decider returns `TrialAborted(reason="parse_failure")` after one retry.
- `test_baseline_decide_emits_telemetry_on_every_call`: verify all six telemetry event types fire on the appropriate triggers.

### 7.2 Unit tests on text-only `ReactDecider`

- `test_react_decider_handles_screenshot_none`: instantiate `ReactDecider`, call `decide_with_context(..., screenshot_b64=None)`; verify message structure has no image block; verify `parse_json` succeeds on a mocked text-only response.
- `test_react_decider_handles_screenshot_empty_string`: same as above but `screenshot_b64=""`.
- `test_react_decider_preserves_image_when_screenshot_present`: regression — image-present path still works.

### 7.3 Integration tests on Bot + Game2048Sim

- `test_baseline_bot_runs_one_trial_to_game_over`: instantiate Bot + `Game2048Sim` with a known scenario, run until `is_game_over()`; assert the decider produces ≥ 1 LLM-committed decision and the final board is game-over.
- `test_baseline_bot_handles_invalid_move_via_tie_break`: scenario where LLM's first choice is a no-op; verify Test Runner-side tie-break fires (this is technically a runner test, but exercises the Bot/runner contract).

Integration tests use the `MockLLM` from `nova_agent/llm/protocol.py` to keep the cliff-test gate fast; production-tier LLM calls are reserved for the Test Runner's calibration runs.

### 7.4 Telemetry-event integration test

- `test_bot_telemetry_events_emit_in_correct_order`: end-to-end mock-LLM run with controlled error injection; assert the telemetry event sequence matches the per-call protocol pseudocode in §3.3.

### 7.5 No production-tier LLM tests in the unit suite

Production-tier (Anthropic / Gemini Pro) LLM calls are **not** part of the unit-test gate. The Test Runner spec covers pilot calibration runs that exercise production-tier calls; those are gated by manual-run discipline and ADR-0006 cost discipline, not by the standard `pytest` trio.

## 8. Out-of-scope

- **Test Runner implementation.** Separate spec; consumes the contracts in §3.4, §4, §5.3, and §6.3.
- **Cost-cap budget figure.** The Test Runner spec sets `BUDGET_PER_SCENARIO_ARM_USD = $X` at authoring time.
- **Anxiety sampling cadence and which Anxiety field feeds the §2.7 threshold check.** Test Runner concern.
- **Parallelization strategy across the 60 trials per scenario (20 Carla + 20 Bot).** Test Runner concern.
- **Persona definitions for Casual Carla beyond what `nova-agent/src/nova_agent/...` already implements.** Phase 0.7 uses Carla as deployed.
- **Higher-skill personas (Strategic Sam, etc.).** Out of scope for Phase 0.7.
- **Heuristic Bot architecture.** Rejected per §2.1; not implementable from this spec.
- **A custom `BaselineDecider` Pydantic schema vs reusing `_ReactOutput`.** Implementation choice; both are correct as long as schema-equivalent.
- **Migration to a non-Anthropic provider for Bot.** Bot tracks Carla's act-tier per §2.3; provider selection is a Settings concern.

## 9. Open follow-ups

- The implementation plan must specify whether `BaselineDecider` reuses `_ReactOutput` or defines a separate schema-equivalent type. Recommended: reuse for symmetry.
- After pilot calibration on the three scenarios, this spec should receive a one-line follow-up note recording the observed paired-abort rate per scenario for future-reviewer auditing.
- If pilot calibration surfaces > 2 paired aborts on any scenario at expected rates, this spec's threshold is re-evaluated in a follow-up amendment.
- The `decision/arbiter.py:should_use_tot(board, affect)` integration with Carla's affect channel (§2.2 reasoning) should be cross-referenced in the methodology paper's "Defenses against external review" section so the deployed-architecture-as-tested claim is reproducible by a reviewer reading the spec alongside the code.

## 10. References

- `docs/decisions/0001-cognitive-architecture-as-product-moat.md` — the moat the cliff test validates; bundle-attribution scope rationale (Q2)
- `docs/decisions/0005-defer-v1-demo-until-phase-0.7.md` — establishes Phase 0.7 as the demo-recording gate; bundle-as-tested rationale (Q2)
- `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` — cliff test runs at `NOVA_TIER=production`; cost-cap envelope rationale (§4)
- `docs/decisions/0007-blind-control-group-for-cliff-test.md` — the two-arm design and pinned pass criteria this spec implements; Amendment 1 ratifies the operational refinements
- `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` — the GameIO abstraction Bot runs against
- `docs/product/methodology.md` §4.1 — the upstream methodology contract this spec is consistent with
- `docs/product/product-roadmap.md` Week 1 — the schedule the cliff test runs against
- `docs/superpowers/specs/2026-05-04-game2048sim-design.md` — the simulator spec this Bot runs on
- `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md` — the scenarios this Bot is tested against
- `nova_agent/decision/react.py:18-22` — the `_ReactOutput` schema this spec ratifies as Bot's output schema
- `nova_agent/decision/prompts.py:4-23` — `SYSTEM_PROMPT_V1` (audited image-free for Phase 0.7); also the user-prompt builder this spec adopts for Bot
- `nova_agent/decision/react.py:62-69` — the unconditional image-block construction that requires a Phase 0.7 refactor (§5.1)
- `nova_agent/decision/arbiter.py:should_use_tot` — the affect-driven ToT trigger that argues against ToT-ablation for Carla in Phase 0.7 (§2.2 reasoning)
- `nova_agent/llm/protocol.py` — the LLM interface Bot consumes; `MockLLM` for unit tests
