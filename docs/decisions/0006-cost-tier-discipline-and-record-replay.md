# ADR-0006: cost-tier-discipline-and-record-replay

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** ihoresh07@gmail.com (solo founder), principal engineer (red-team review)

---

## Context

Nova spends real money on LLM API calls during development. The 6-week sprint budget per the design doc is ~$110-130 total (verified against provider pricing pages May 2026). Three forces compound this:

1. **Iteration overhead.** Every UI tweak (CSS padding on the brain panel, animation timing on the dopamine pulse, layout on the ToT branch tooltip) currently requires running the full agent end-to-end to generate fresh AgentEvents. A 50-move game burns ~$0.50 in decision + reflection calls. Twenty CSS iterations = $10 just to look at the layout.
2. **Test coverage.** Integration tests that hit real LLMs cost money on every CI run. CI on every push to a feature branch = ~$2-5/week of test cost alone.
3. **Phase 0.8 ablation.** The trauma-on/trauma-off Levene's-test run is N=2000 games. At full production model cost, that's the single most expensive day of the sprint.

The principal engineer red-teamed an initial cost-saving plan (vcrpy cassettes, NOVA_DEV_MODE, Ollama, batch API, record-and-replay). Outcomes:

- **Reject vcrpy / cassettes.** LLM prompts are too volatile in early dev — every persona tweak invalidates recorded fixtures. Maintenance burden exceeds the savings. Use simple hardcoded JSON dictionaries for unit-test mocks; the `MockLLMClient` already exists for this.
- **Reject Ollama for Week 0.** Local LLM quality won't pass the cliff test, and the integration cost (provider abstraction, latency variance, model-quality calibration) doesn't pay back in Week 0.
- **Defer batch API.** Right tool for Phase 0.8 ablation specifically — 50% discount on 24h-latency runs. Implement it when Phase 0.8 starts (Week 2-3), not now.
- **Approve record-and-replay.** Highest ROI. Saves all LLM cost on UI iteration; one-time per-game investment.
- **Approve tier system + schema enforcement.** Route every non-scientific run to cheap models. Mandate `response_schema` on every Gemini JSON callsite so the cheapest tier doesn't crash on JSON drift.

Three concerns the principal engineer flagged about the cheap-tier approach:

- **Format risk (resolved by enforcement).** Gemini 2.5 Flash-Lite natively supports `response_schema` (OpenAPI 3.0 enforcement at generation time). Pass the consuming pydantic model and the API guarantees structural validity. Not the old "JSON mode" that just begs the model to output brackets.
- **Reasoning risk (real, must respect).** Flash-Lite is fast and cheap but cognitively shallow — it trims multi-step deliberation. ToT branch evaluation, Arbiter threshold tuning, State-Transition Signature evaluation, and any cliff-test-relevant judgment work CANNOT use Flash-Lite. The structure will be perfect; the logic inside the structure will degrade.
- **Tier-discipline risk (procedural).** A solo dev with one knob will leave it in the cheapest position by accident. The tier system must make the cost/quality trade explicit and easy to flip per-task, not a hidden default.

## Decision

**Adopt a four-tier model-routing system with explicit `response_schema` enforcement on every Gemini JSON callsite, plus a record-and-replay mode for the AgentEvent bus to enable UI iteration without paying LLM cost.**

### The four tiers (`nova_agent.llm.tiers`)

| tier         | decision         | tot              | reflection        | tot_branches | use case                                                        |
|--------------|------------------|------------------|-------------------|--------------|-----------------------------------------------------------------|
| `plumbing`   | flash-lite       | flash-lite       | flash-lite        | 2            | UI work, bus plumbing, integration smoke tests                  |
| `dev`        | flash            | flash            | flash             | 3            | daily development; cognitive logic tweaks within the cheap tier |
| `production` | flash            | pro              | sonnet-4-6        | 4            | cliff test, ablation, real cognitive evaluation                 |
| `demo`       | sonnet-4-6       | sonnet-4-6       | sonnet-4-6        | 4            | Week 6 demo recording (per ADR-0005, post-Phase-0.7)            |

`plumbing` mode is **safe only because** every JSON-required callsite passes a pydantic `response_schema` to the Gemini API (see commit `feat(llm): add response_schema enforcement to LLM protocol`). Flash-Lite drifts on prompt-only JSON mode; OpenAPI 3.0 generation-time enforcement is what makes the cheap tier viable.

`plumbing` mode is **dangerous** for any cognitive-judgment work — Arbiter threshold tuning, ToT branch quality evaluation, anything that touches State-Transition Signatures. Use `dev` or `production` for that work.

### Selection: NOVA_TIER env var

`NOVA_TIER=<plumbing|dev|production|demo>` selects the tier at process start. Read via `Settings.tier` (pydantic-settings — single env-var chokepoint per `.claude/rules/security.md`); `main.py` consults it before constructing the three LLM clients (decision, deliberation, reflection). When `NOVA_TIER` is unset, `Settings.tier = None` and `main.py` falls back to the per-task `decision_model` / `deliberation_model` / `reflection_model` Settings fields (the historical shape) for backward compatibility.

### Schema enforcement: `response_schema` on every Gemini JSON callsite

`LLM.complete()` Protocol gains an optional `response_schema: type[BaseModel] | None = None` kwarg. `GeminiLLM` forwards it to `GenerateContentConfig.response_schema` for OpenAPI 3.0 enforcement. `AnthropicLLM` and `MockLLMClient` accept-and-ignore (Anthropic Messages API has no native equivalent; `MockLLMClient` has its own role-based deterministic generation).

Three callsites (`decision.react.decide_with_context`, `decision.tot._evaluate_branch`, `reflection.run_reflection`) pass their consuming pydantic model. `parse_json` post-validation is preserved at every callsite as defense-in-depth — generation-time enforcement is a guarantee, but the validation step also catches cross-provider drift if a future routing change moves a callsite from Gemini to Anthropic.

### Record-and-replay (`nova_agent.bus.recorder` + `nova_agent.bus.replayer`)

`RecordingEventBus` subclasses `EventBus` and appends every published event to a JSONL file in addition to the live broadcast. Each line: `{"t": <monotonic seconds>, "event": <name>, "data": <payload>}`. Activation: `NOVA_BUS_RECORD=path` (read via `Settings.bus_record_path`).

`ReplayServer` reads a JSONL file and broadcasts via WebSocket with original spacing (optional `time_warp`). CLI: `python -m nova_agent.bus.replayer --file game.jsonl`. Allows the viewer to render a recorded session as if it were live, no agent process required.

Disk writes are offloaded via `asyncio.to_thread` so the agent's event loop never blocks on filesystem latency. Disk failures are logged but do NOT break the live broadcast — recording is best-effort, broadcast is load-bearing.

### What we explicitly are NOT doing

- **No vcrpy / cassette tests.** Maintenance burden exceeds savings during early-dev prompt volatility. Continue using `MockLLMClient` and hand-crafted JSON fixtures for unit tests.
- **No Ollama integration in Week 0.** Re-evaluate when refactoring infra in Week 2+.
- **No batch API yet.** Right tool for Phase 0.8 (Week 2-3) ablation; implement at that time.
- **No tier auto-detection.** `NOVA_TIER` must be set explicitly. A solo dev with implicit tier inheritance will leave it in the cheapest position by accident — the cost of accidentally tuning Arbiter thresholds on Flash-Lite is much higher than the cost of typing one env var.

## Alternatives considered

- **Single `NOVA_DEV_MODE=true` boolean flag** instead of four tiers. Rejected — doesn't capture the cliff-test (`production`) and demo-recording (`demo`) cost profiles, and a boolean has only two states which can't represent the real cost/quality landscape (plumbing vs dev is a meaningful distinction inside the "dev" boolean's "true" state).

- **Use VCR / cassette tests instead of `MockLLMClient` for integration tests.** Rejected per principal engineer's red team — prompt volatility in early dev makes cassette maintenance a treadmill. Re-evaluate when prompts stabilize (post-Phase-0.7).

- **Run Ollama locally for plumbing-tier calls.** Rejected for Week 0 — Ollama integration is its own infra project (provider abstraction, model loading, latency variance). Not on the critical path for the cliff test. Re-evaluate post-Phase-0.7 if API spend becomes a constraint.

- **Fail-closed on missing schema enforcement** (i.e., raise if a Gemini call is made without `response_schema`). Rejected for now — would break callsites that don't return JSON (e.g., natural-language reflection summaries). The Protocol's optional kwarg is the right shape; enforcement is at the callsite-author's discretion guided by the rule "if you call `parse_json` on the output, you must pass `response_schema`."

- **Generate `response_schema` automatically from the `parse_json` target type.** Rejected — too clever. The explicit `response_schema=_ReactOutput` arg makes the contract obvious at the callsite. Implicit derivation hides the cost-discipline relationship.

- **Use `tools` instead of `response_schema` on Anthropic for symmetric enforcement.** Deferred — would require restructuring callsites to consume tool_use output instead of message text. Worth doing if Anthropic JSON drift surfaces in the cliff-test or production runs; capture as a future ADR if so.

## Consequences

**Positive**

- ~80% cost reduction on plumbing-tier runs (Flash-Lite vs Flash for decision and reflection; Flash-Lite vs Pro for ToT). Translates to ~$15-20/week saved during UI-heavy phases.
- Record-and-replay makes UI iteration zero-cost after one real game per session. Brain-panel polish (Week 5-6) becomes practical without burning the budget.
- `response_schema` enforcement means all four tiers produce structurally-valid JSON. No more hand-crafted "if the model returns wrong shape, retry with more emphatic prompt" defenses.
- Backward-compatible: existing `.env` files continue to work unchanged because `NOVA_TIER` defaults to None and main.py falls back to the per-task model fields.
- ADR-driven discipline: tier choice is explicit at process start, recorded in logs (`nova.tier_routing`), reviewable.

**Negative**

- Adds a new dimension of "did you set NOVA_TIER correctly?" to the reviewer mental model. Mitigation: log the tier on agent start; surface it in the brain-panel session-info pane (future commit).
- Plumbing tier is a footgun. Setting it during cognitive-judgment work produces shallow reasoning that looks structurally correct — the most dangerous failure mode. Mitigation: tiers.py docstring + this ADR + main.py log line + future linter check that `NOVA_TIER=plumbing` aborts the cliff-test runner.
- Anthropic schema enforcement is asymmetric — Sonnet+ runs without generation-time schema enforcement. Acceptable for now (Sonnet is reliable on JSON-mode); future ADR if drift surfaces.
- Recording/replay file format is a new wire shape — must stay backward-compatible if users keep recordings around. Mitigation: the JSONL shape is intentionally minimal (`t / event / data`).

**Neutral**

- Per-task model env vars (`NOVA_DECISION_MODEL` etc.) still work. Power users can mix-and-match, e.g. plumbing tier with Sonnet for reflection only.
- The four-tier system maps to an obvious Phase plan: plumbing in Week 0 polish + Week 5-6 UI work; dev in cognitive-tweak phases; production for cliff test + ablation; demo for the recording.

**Reversibility**

- Highly reversible. Removing the tier system means removing one Settings field, ~20 lines of main.py, and reverting the tiers.py addition. Schema enforcement is also reversible — drop the kwarg from the protocol and the callsites; runtime behavior reverts to current state. Record-and-replay is fully optional (env-var-gated); leaving it in place costs nothing.

## References

- ADR-0001 — cognitive architecture as product moat (the moat is what plumbing tier MUST NOT degrade)
- ADR-0002 — state-transition signatures (the cognitive evaluation that plumbing tier cannot run)
- ADR-0003 — hybrid local + API inference (the broader provider strategy this tier system implements)
- ADR-0005 — defer v1 demo until Phase 0.7 passes (demo tier maps to Week 6 demo recording, gated by Phase 0.7)
- `nova_agent.llm.tiers` — the four-tier definition
- `nova_agent.llm.protocol` — the `LLM.complete()` Protocol with `response_schema` kwarg
- `nova_agent.bus.recorder` + `nova_agent.bus.replayer` — record-and-replay implementation
- Recent commits: `feat(bus): add record-and-replay for AgentEvent streams`, `feat(llm): add response_schema enforcement to LLM protocol`, and the commit accompanying this ADR adding the `plumbing` tier and `NOVA_TIER` wiring in main.py.
- Principal engineer red-team summary recorded in conversation transcript 2026-05-04.
