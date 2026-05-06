# LESSONS.md — engineering & product retrospective

> **What this file is:** an append-only log of hard-won lessons from
> Project Nova's development. Every meaningful gotcha, design pivot,
> failure mode, and "I won't make that mistake again" insight gets
> captured here so the team doesn't re-learn the same lesson twice.
>
> **Format:** newest entries at the top within each section. Each
> lesson has: what happened, what we learned, how to apply it.
>
> **Audience:** future-you, future contributors, future Claude sessions
> reading this for orientation. Read this BEFORE starting work that
> touches an area covered below.
>
> **Maintenance:** add a lesson the moment you've learned something
> that cost time. Better to over-capture than under-capture. Periodically
> (monthly?) prune entries that have been formalized into automated
> guardrails (hooks, tests, docs).

---

## Engineering / debugging gotchas

### Carla anxiety firing at move 0–1 is "fast reaction," not "predictive lead-time"

**Date:** 2026-05-06 | **Cost:** would have been ~$50 + a damaged external-review pitch if we'd shipped Phase 0.7 against the current scenarios. Caught by the red-team round on the first pilot CSV.

**What happened:** The 2026-05-06 pilot at production tier produced a Δ = `t_baseline_fails - t_predicts` ≥ 2 in 15/15 paired trials. On paper that's a perfect methodology pass (per ADR-0007 Amendment 1, ≥3/3 scenarios with ≥3/5 trials at Δ ≥ 2). But Carla's `t_predicts` was 0 or 1 in nearly every trial — anxiety crossed threshold on the first move that had affect signal. Bot's `t_baseline_fails` averaged 4–5 moves on corner-abandonment-256 (window 12–17). Reframed: identifying a cliff at move 1 when Bot dies at move 4 is *fast reaction to a catastrophic state*, not *predictive lead-time over a developing decline*. An external reviewer (per scenarios spec §2.4 "external review credibility is load-bearing") would correctly say "Carla just panics on hard-looking boards; this isn't prediction."

The §7.4 calibration check ("Bot game-over within `expected_cliff_window` for ≥3/5 trials") is what catches this: all 3 scenarios failed Bot calibration in the pilot (snake-collapse-128: 1/5; corner-abandonment-256: 0/5 — Bot crashes too fast; 512-wall: 1/5 — Bot survives slightly past window). The §7.4 check exists precisely to prevent the failure mode of "Carla wins because the scenarios are so harsh that the cliff is at move 1, so any anxiety signal beats Bot."

**Lesson:** Methodology-pass-with-Δ-clean is necessary but not sufficient. `t_predicts` near 0 is a *red flag*, not a green light — it means Carla is reacting, not predicting. Calibration is the load-bearing gate; never ship a Phase 0.7 run on scenarios that fail §7.4. The methodology and the calibration are separable contracts, both must pass.

**How to apply:**

- When inspecting cliff-test CSV output, before computing Δ, check the `t_predicts` distribution per scenario. If the median is 0 or 1, the scenarios are mis-calibrated regardless of what Δ says.
- Re-author scenarios so Bot's game-over move falls inside `expected_cliff_window` for ≥3/5 trials before re-running the formal Phase 0.7.
- Keep the §7.4 calibration check as a separate validation step in the analysis pipeline (`analyze_results.py` follow-up spec) — don't fold it into the Δ test.
- When framing Phase 0.7 results for external review, lead with `t_baseline_fails - t_predicts ≥ 2 AND t_predicts is meaningfully past move 0`, not just Δ. The "predictive" claim has to survive the move-0 attack.

### Gemini Pro 2.5 has a hard 1000 RPD daily quota that is shared across the whole repo's API key

**Date:** 2026-05-06 | **Cost:** ~$0.30 wasted on a second pilot whose data was unusable; ~30 min misdiagnosing concurrency as the root cause; 1 commit revert.

**What happened:** First pilot consumed 956 Gemini Pro calls (4 ToT branches × N moves × 5 trials × 3 scenarios). Triggered a hypothesis that 20% Carla abort rate was due to concurrency=8 hitting transient 429s. Lowered DEFAULT_CONCURRENCY to 4 and re-piloted — abort rate jumped to **88% per-branch** (74/84 ToT branches `RetryError[ClientError]`). The cause was not concurrency: cumulative Pro calls across both pilots exceeded the 1000 RPD daily quota and Pro was hard-throttling for the rest of the UTC day. The c=4 commit (`60ac3bf`) had to be reverted because its data was confounded — we have no quota-clean evidence on whether concurrency=4 actually helps versus concurrency=8.

CLAUDE.md gotcha #2 documents the 1000 RPD limit and a workaround (`NOVA_DELIBERATION_MODEL=gemini-2.5-flash` env override). Initially I thought cliff-test should respect that override, but `main.py:148-152` shows the override is *only* read when `Settings.tier` is unset. Cliff-test requires `NOVA_TIER=production` (per spec §6.1 + ADR-0006), so `model_for("tot")` returns `gemini-2.5-pro` regardless of the env override. The documented workaround does not apply in tier mode.

**Lesson:** Under NOVA_TIER=production, cliff-test runs at the strict tier mapping with no env-override escape hatch. A single full pilot (~3 scenarios × 5 trials × 4 branches × ~30 moves) burns ~1000 Pro calls — basically the entire daily RPD quota. Plan the daily Gemini Pro call budget before starting any pilot. The 4-branches-per-ToT multiplier is the dominant cost factor.

**How to apply:**

- Before starting a cliff-test pilot, count today's prior Pro calls. If `prior_calls + estimated_run_calls` ≥ 1000, do not start; wait for UTC-midnight reset.
- Do not change concurrency or runner parameters in response to mid-day Carla aborts without first confirming the Pro quota state. Throttle-cluster aborts and quota-exhaustion aborts produce the same `RetryError[ClientError]` payload — they are not distinguishable from the Carla telemetry alone.
- For Phase 0.7 N=20 formal run, the per-day budget allows ~1 scenario/day at production tier with Pro for ToT, OR switch to NOVA_TIER=demo (Sonnet for ToT, no Pro RPD limit, ~5× per-call cost).
- The `tot_branch` event with `status=api_error error="RetryError ... ClientError"` is the diagnostic signature for both rate-limit clustering AND quota exhaustion. Disambiguate by counting Pro calls in the day's logs, not by inspecting the error payload.
- Long-term: the cliff-test runner should track a `pro_calls_today` counter against the 1000 RPD ceiling and refuse to start if a pilot/full-run would exceed it. Captured as a follow-up rather than implemented.

### `thinking_budget=None` on Gemini Flash silently truncates JSON output

**Date:** 2026-05-06 | **Cost:** ~30 min wall + ~$0.05 burned on a hosed pilot calibration before diagnosis. Caught during the first real-LLM cliff-test run; every Bot trial parse-failed at move 0 and every Carla react trial silently aborted (the `except Exception` in `_run_carla_trial` swallowed it).

**What happened:** `nova_agent/lab/cliff_test.py:_build_llms()` shipped without forwarding a `thinking_budget` to `build_llm()` for the Gemini Flash decision/bot LLMs. Default is `thinking_budget=None`, which `gemini_client.py:53-58` documents as "model decides — Flash burns the entire budget on thinking." With `BASELINE_MAX_TOKENS=500`, the model spent all 500 tokens on hidden reasoning and emitted only 8 visible tokens (`{\n  "observation": "Large` — same prefix every time). `parse_json` couldn't find a closing `}` → `StructuredOutputError` → 1 retry (deterministic at temp=0, identical failure) → `TrialAborted(reason="parse_failure")`. Bot side telemetry showed it; Carla react side hit the same wall but silently aborted before publishing any bus events, so no `events_*_carla_*.jsonl` files were created — making it look like Carla "didn't run" when in fact every trial died at move 0.

The canonical fix already existed in `main.py:165-193` — `thinking_budget=0` for Flash, `thinking_budget=1024` for Pro (Pro rejects 0). The cliff-test runner shipped without mirroring it because the Task 10 manual smoke ran on the `fresh-start` scenario, which evidently produced a small enough JSON payload to squeak through under whatever thinking the model chose; the production scenarios (snake-collapse-128, corner-abandonment-256, 512-wall) all failed.

**Lesson:** Every Gemini call site must explicitly set `thinking_budget`. The factory's `thinking_budget=None` default is a footgun, not a sane default — Flash interprets None as "go wild on thinking" and Pro interprets None as "dynamic budget." Both starve visible-token output under tight `max_output_tokens` limits. Never let a new code path pass through `build_llm` for a Gemini model without picking a value. Diagnostic fingerprint: `tokens_out` very small (≤10), response is a JSON prefix, parse failure is deterministic across retries, and the failure happens on every move.

**How to apply:**

- For any new `build_llm(model="gemini-flash-...", ...)` call site: pass `thinking_budget=0`.
- For `gemini-pro`: pass a positive cap (1024 is the established value for ToT branches; tune for your output size).
- Add a regression test asserting the kwargs at the construction site (see `test_build_llms_passes_thinking_budget_for_gemini_models`). Mocked-LLM tests can't catch this because mocks ignore `thinking_budget`; the assertion has to be at the factory boundary.
- If a manual smoke "passes" but the call site differs from `main.py`, run the real scenario corpus before declaring victory. `fresh-start` is not representative of cliff-test scenarios.
- Long-term: consider making `thinking_budget` a required kwarg on the Gemini side of `build_llm` (no None default). Documented as a follow-up in this entry rather than implemented — would be a small ADR.

### Pydantic-settings silently drops field-name kwargs when aliases exist + `extra="ignore"`

**Date:** 2026-05-04 | **Cost:** ~10 min during Task 5 of the Game2048Sim build (factory test failed before the spec reviewer flagged the same issue independently).

**What happened:** Project Nova's `Settings` (`nova-agent/src/nova_agent/config.py`) declares fields with aliases (e.g. `io_source` aliased to `NOVA_IO_SOURCE`) and `model_config` has `extra="ignore"` but NOT `populate_by_name=True`. Consequence: constructing `Settings(io_source="sim")` (kwarg by field name) silently drops the value — pydantic treats the field-name kwarg as an unknown extra and the field stays at its default. Only `Settings(NOVA_IO_SOURCE="sim")` (kwarg by alias) actually populates. The production env-var loading path is unaffected; this is a test-construction trap only, but the failure is silent (no exception, just default values).

**Lesson:** With aliases + `extra="ignore"` and without `populate_by_name=True`, pydantic-settings forces a strict alias-only API for kwargs. The `ignore` policy makes field-name kwargs look like noise and discards them without an error. The next engineer reaching for `Settings(my_new_field=...)` in a test will hit a confusing failure mode where their assertion is way downstream of the actual cause.

**How to apply:** Test helpers that construct `Settings` directly should always pass kwargs by **alias** (`NOVA_IO_SOURCE`, `GOOGLE_API_KEY`, …) and document this in the helper's docstring. Reference pattern: `nova-agent/tests/test_main_build_io.py:11-19`. Optional follow-up: setting `populate_by_name=True` in `Settings.model_config` would allow both forms — defer until a future Settings change naturally touches `model_config`, not worth a standalone PR.

### Pillow 12.2 type stubs reject `list` literals for `ImageDraw` geometry args

**Date:** 2026-05-04 | **Cost:** ~5 min during Task 3 of the Game2048Sim build, caught immediately by mypy strict.

**What happened:** Pillow 12.2.0's type stubs require `tuple` for `ImageDraw.rectangle((x0, y0, x1, y1), fill=...)` — `list` literals (`[x0, y0, x1, y1]`) are rejected. Older Pillow versions (10.x, 11.x) accepted either. Idiomatic Python (and most StackOverflow examples) reach for the list form first, so this is an easy paste-from-snippet trap.

**Lesson:** When a library tightens type stubs across a major version, mypy strict surfaces the regression but ruff and runtime don't. Default to tuples for any `ImageDraw` geometry args (rectangle bounds, polygon points, ellipse bbox, line endpoints) regardless of what the snippet you copied uses.

**How to apply:** Reference pattern: `nova_agent/lab/render.py:52` uses `(x0, y0, x1, y1)`. If you see `Argument 1 to "rectangle" of "ImageDraw" has incompatible type "list[int]"; expected "tuple[float, float, float, float] | ..."`, swap the brackets, don't argue with the stubs.

### TDD only catches direction-mapping bugs when BOTH axes are pinned

**Date:** 2026-05-04 | **Cost:** ~3 minutes; the bug shipped in the plan template but caught at first GREEN run.

**What happened:** Task 2 of the Game2048Sim build had the rotation count for swipe-UP and swipe-DOWN swapped in the plan template (`UP=1, DOWN=3` instead of correct `UP=3, DOWN=1`). The bug surfaced because the test suite pinned BOTH `test_merge_leftmost_priority_swipe_up` AND `test_merge_leftmost_priority_swipe_down`. A single-direction test on the same axis would have passed for the wrong reason — the rotation maps the test fixture into the right slide-left case anyway when both ends are wrong by the same amount.

**Lesson:** Direction-symmetric or axis-symmetric code (rotations, mirroring, signedness, byte-order, transpose) needs both ends pinned. One end alone is not a useful test — it can pass by chance for the wrong reason. The cost of the second test is trivial; the cost of NOT having it is a silently-wrong sim that produces plausible-looking games.

**How to apply:** When writing tests for symmetric APIs, write the test for one direction, then mirror it for the opposite direction in the same commit. If you find yourself writing "I'll add the other direction later," stop and add it now. Reference pattern: `nova-agent/tests/test_lab_sim.py` pairs every direction test (`*_swipe_up` ↔ `*_swipe_down`, `*_swipe_left` ↔ `*_swipe_right`).

### `claude-code-action@v1` cannot self-review PRs that modify the review workflow

**Date:** 2026-05-04 | **Cost:** ~10 minutes of "why did the action fail with a 401?" before reading the error message carefully.

**What happened:** PR #3 modified `.github/workflows/claude-review.yml` (bumping the Layer 2 model from Sonnet to Opus). When the action ran on PR #3, the OIDC step succeeded but the App Token Exchange step failed three times with `401 Unauthorized — Workflow validation failed. The workflow file must exist and have identical content to the version on the repository's default branch.`

**Lesson:** The Claude GitHub App's security model **requires the workflow file on the PR branch to be byte-identical to the version on `main`**. This is anti-tampering: it prevents a PR from modifying the workflow during the review run to leak secrets, escalate permissions, or self-approve. The action's own error message acknowledges this is "normal" for a PR that adds or modifies the workflow file. There is no fix on our end — it is structural.

**How to apply:** When a PR touches `.github/workflows/claude-review.yml` (or any other workflow file the action validates against `main`):

- Expect Layer 2 to fail on that PR with the 401 / validation error. **Don't panic.**
- CI still runs in parallel and validates correctness.
- Manually review the diff yourself before merge — Layer 2 cannot help here, that's the trade-off.
- After merge, the new workflow becomes canonical on `main`, and the NEXT PR that doesn't touch the workflow gets full Layer 2 review using the new version.
- **Do not** try to "split" the workflow change into a separate PR to fix it — every PR that modifies the workflow hits the same constraint.
- For sensitive workflow changes, dispatch the manual `/security-review` skill on the diff to add a security-tier review even though Layer 2 cannot.



**Date:** 2026-05-03 | **Cost:** ~2 hours of audit-trail work; surfaced one real api_error → parse_error rendering bug that had been live in the agent for weeks.

**What happened:** `nova-viewer/lib/types.ts` had a `{event: string; data: unknown}` catch-all arm at the bottom of the `AgentEvent` discriminated union. It was added "for safety" so the union would accept any frame the agent might emit, even shapes the viewer hadn't modelled yet. Removing it surfaced a third `tot_branch.status` variant — `"api_error"`, emitted from `nova_agent/decision/tot.py:166` whenever an LLM call fails — that the viewer had never typed. The catch-all routed those frames through `e.data as ToTBranchData` casts that compiled fine because TypeScript saw both arms (complete and parse_error) as assignable from the catch-all's `unknown`. The bus protocol was permissive enough that the bad shape rendered weirdly instead of throwing — a silent UX bug.

**Lesson:** A union arm of `{ tag: string; data: unknown }` defeats discriminated narrowing in every consumer. It also defeats `grep` — you can't audit which variants are handled because the catch-all matches everything. Hand-written runtime predicates per variant + a top-level `parse(raw): T | null` is worth the boilerplate, because TypeScript narrowing then becomes a real consistency check between producer and consumer.

**How to apply:** When mirroring an external protocol (Python bus → TS viewer), don't use a string-keyed catch-all "for safety." Either type every variant explicitly or fail closed (return `null`) for unknown tags. Every catch-all is a bug-hider. The validator implementation lives at `nova-viewer/lib/eventGuards.ts` (see `parseAgentEvent`); use it as the template when adding new event types.

### macOS UF_HIDDEN flag silently breaks Python venvs on Desktop

**Date:** 2026-05-02 | **Cost:** ~1 hour of "why does pytest work but `uv run nova` fail?"

**What happened:** Repo lives at `~/Desktop/a/`. macOS Sequoia's App Management auto-applies the `UF_HIDDEN` file flag to everything under `~/Desktop`. Python 3.14's site loader explicitly skips `.pth` files marked hidden. The editable install `_editable_impl_nova_agent.pth` was hidden → Python couldn't find `nova_agent` → CLI failed with `ModuleNotFoundError`. Pytest worked because `pytest.ini` declares `pythonpath = src` explicitly, bypassing the `.pth` mechanism.

**Lesson:** When Python imports mysteriously fail on macOS, run `ls -lO` on the relevant `.pth` file to check for the `hidden` flag. Don't trust that a venv is healthy just because some entry points work.

**How to apply:** Workaround is `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"` to put the venv outside `~/Desktop`. Better long-term: don't put repos under `~/Desktop` on macOS.

### Empty exported environment variables shadow `.env` files

**Date:** 2026-05-02 | **Cost:** ~30 min of "the API key IS in .env, why does the SDK say no auth?"

**What happened:** Pydantic-settings reads process env first, `.env` second. If a parent shell exports `ANTHROPIC_API_KEY=""` (empty string), it shadows the populated `.env` value, and `Settings.anthropic_api_key` becomes empty even though the file has the key.

**Lesson:** Empty exported env vars are a real shadowing risk. They behave differently from "unset" but pydantic treats them identically to unset for FALLBACK purposes — except the process-env-precedence rule fires first.

**How to apply:** In any pydantic-settings config, use `env_ignore_empty=True` so empty exports are treated as unset. When debugging "key not found" errors with a populated `.env`, run `printenv | grep YOUR_KEY` to check for shadowing.

### Anthropic API requires actual paid credits, not just grant credits

**Date:** 2026-05-02 | **Cost:** ~45 min of "the dashboard shows $20, why does the API say credit balance too low?"

**What happened:** Anthropic distinguishes "Credit grant" (free promotional balance) from "Credit purchase" (real Stripe-charged credits). The `/v1/messages` API gates on actual paid credits. Grant credits sit on the balance but don't unlock the API until at least one paid purchase has been made on the account.

**Lesson:** Anthropic dashboard balance ≠ API-eligible credits. Check the invoice history for a row labeled "Credit purchase" with status "Paid" — that's the indicator the API will work.

**How to apply:** Before any production deploy that depends on Anthropic, verify by hitting `/v1/models` (works without credits) AND `/v1/messages` (requires credits). If `/models` works but `/messages` 400s with "credit balance too low," the account needs a real Stripe purchase.

### Gemini Pro has a per-model 1000 RPD daily quota that's separate from your overall paid tier

**Date:** 2026-05-02 | **Cost:** ~30 min of "why are we hitting 429 on Pro when our Google Cloud billing is enabled?"

**What happened:** Even on the paid tier, `gemini-2.5-pro` has a default 1000 requests-per-day-per-model cap. ToT runs 4 parallel branches per call; ~250 ToT calls/day exhausts the quota. Other Gemini models (Flash) are unaffected.

**Lesson:** Per-model quotas exist independently of the project's billing tier. Pro is treated as a "premium" model with tighter defaults. To raise the limit, file a quota-increase request with Google Cloud.

**How to apply:** When designing an architecture that calls Pro frequently, either (a) request quota uplift before launch, (b) cap Pro calls in the application layer, or (c) configure a fallback to Flash for the same logical role. Currently using (c) via `NOVA_DELIBERATION_MODEL=gemini-2.5-flash` override in `.env`.

### Unity 2048 fork ignores `adb shell input swipe`; only DPAD keyevents work

**Date:** 2026-05-01 | **Cost:** ~15 min of "the swipe command runs but nothing happens"

**What happened:** The forked Unity 2048 game's input layer apparently handles only keyboard / DPAD events, not synthetic touch swipes. `adb shell input swipe x1 y1 x2 y2` reports success but the game doesn't move. `adb shell input keyevent 19/20/21/22` (DPAD up/down/left/right) does work.

**Lesson:** Game-engine input handling varies. Don't assume `adb shell input swipe` works just because it's the "obvious" way to send a swipe to an Android app.

**How to apply:** Test all input methods up front when integrating a new game. `nova_agent.adb.swipe()` already wraps DPAD keyevents internally; don't revert to the touch-swipe API.

### `pm clear` doesn't reset Unity 2048 save state

**Date:** 2026-05-02 | **Cost:** ~20 min of "I cleared the app data but the score is still where I left off"

**What happened:** Unity stores game state in external storage (or PlayerPrefs at the system level) that `adb shell pm clear` doesn't touch. The app re-launches with the prior session's save intact.

**Lesson:** Unity persistence ≠ standard Android app data. Cold-boot the AVD (`adb emu kill` + restart) for a true fresh state.

**How to apply:** When experiments need a clean game state, cold-boot the emulator. For ablation studies that need true randomness, this is non-negotiable.

### OCR palette must match every tile color the game can produce

**Date:** 2026-05-02 | **Cost:** ~1 hour of "why is nova playing terribly and the score not changing?"

**What happened:** The 2048 OCR uses a fixed RGB palette to classify tile colors. When tile values appeared (16, 32, 128) that weren't in the palette, the nearest-neighbor classifier mapped them to wrong values (often "empty"). Nova's perception silently produced wrong board state; decisions became no-ops; affect stayed flat (RPE = 0); the game appeared "stuck" but Nova had no idea.

**Lesson:** Nearest-neighbor color classification fails silently. There's no error, just wrong answers. Critical to either (a) sample exhaustively before deployment, (b) add a max-distance threshold that flags unknown colors, or (c) add a fallback OCR (tesseract) for cells that don't match any palette entry within tolerance.

**How to apply:** Currently sampled colors: empty/2/4/8/16/32/128. **64 and 256 are still unsampled** and will silently misread when nova reaches them. Either pre-sample those colors or implement the max-distance fallback before Phase 0.7's cliff test runs in production.

### Plan-template bugs caught only during execution

**Date:** 2026-05-02 | **Cost:** ~3 separate sub-agent retries

**What happened:** During the 12-task subagent-driven implementation of the thinking stream, three plan-template bugs surfaced at execution time:

1. The `rewordFirstPerson` regex rule order produced "I merges down" (failed test 6); rule order needed reorganization.
2. The `truncate` function's `slice.trimEnd() + ELLIPSIS` produced `"fox…"` which matched the test's `not.toMatch(/\w…$/)` — needed to keep the trailing space.
3. `as never` for the `prevAffect` spread failed strict tsc; needed `as AffectVectorDTO`.

In each case, the implementer subagent correctly caught the bug at execution time and chose tests-as-truth.

**Lesson:** Plan templates are a useful starting point but cannot be assumed correct. TDD discipline — writing the test first and treating it as the spec — is what catches plan bugs cheaply. If the plan and the test disagree, the test is usually right because it's more specific.

**How to apply:** When dispatching subagents with plan-provided code blocks, explicitly instruct them to treat the tests as the spec. If the plan code fails the plan tests, fix the code, not the tests.

### TypeScript discriminated-union catch-all defeats narrowing

**Date:** 2026-05-02 | **Cost:** ~30 min of "why isn't `e.event === 'decision'` narrowing `e.data`?"

**What happened:** The `AgentEvent` union in `nova-viewer/lib/types.ts` ends with a catch-all `{event: string; data: unknown}` arm. TypeScript's discriminated-union narrowing fires only when EVERY arm matches a literal — the catch-all matches any string, so narrowing on `e.event === "decision"` doesn't narrow `e.data` to the decision arm's shape. We worked around it with `as data as { ... }` casts everywhere.

**Lesson:** A catch-all in a discriminated union turns it into a non-discriminated union for narrowing purposes. Either drop the catch-all and handle unknowns explicitly with type predicates, OR don't expect narrowing to work.

**How to apply:** Day 1 Task 2 of Week 0 fixes this: remove the catch-all, add hand-written runtime predicates in `useNovaSocket`, replace `as data as` casts with proper narrowing. After this, the type system actually catches typos in field-name access.

### ToT branch failure mode needs explicit per-branch exception handling

**Date:** 2026-05-02 | **Cost:** ~45 min of "why is ToT raising 'no valid candidates' when Pro should be working?"

**What happened:** `ToTDecider._evaluate_one` originally only caught `StructuredOutputError` from `parse_json`. When the underlying `self.llm.complete()` call threw (e.g., 429 quota exhaustion, network error, tenacity RetryError), the exception propagated silently into `gather(return_exceptions=True)`. All 4 branches "failed" with nothing visible, then `decide()` raised the generic "ToT produced no valid candidates" with no clue to the underlying cause.

**Lesson:** `gather(return_exceptions=True)` swallows exceptions in a way that hides root causes. Per-task exception handling is mandatory, not optional. AND the consolidating function that raises on "no successes" should include per-task failure summaries in its error message.

**How to apply:** Already fixed in commit `89e1a7c`. Pattern to repeat elsewhere: catch `Exception` (not just specific subclasses) at the per-task level, publish a structured failure event, return the exception. The aggregator includes failure summaries in its consolidated error.

### `as never` doesn't work for object spreads in TypeScript strict mode

**Date:** 2026-05-02 | **Cost:** ~5 min, caught immediately by tsc

**What happened:** Plan template used `as never` for a `prevAffect` spread (`{...affectEv({}).data as never}`). Strict tsc rejected with `TS2698: Spread types may only be created from object types`.

**Lesson:** `as never` is for unreachable code paths, not for "force this through type checking." For object spreads, use the actual type (`as AffectVectorDTO`).

**How to apply:** When tempted to write `as never`, ask "is this code actually unreachable?" If yes, OK. If no, find the right type.

---

## Architecture / design decisions

### Sim cost ≡ live cost — record-replay rationale (ADR-0006) intact, cliff-test budget bounded by LLM not ADB

**Date:** 2026-05-04 | **Context:** Task 6 calibration smoke for the Game2048Sim build (sim 50-move vs live 50-move).

**What happened:** Task 6 measured a 50-move run on `Game2048Sim` against a 50-move run on the live emulator path with the same cognitive layer. LLM-call shape was **byte-identical**: $0.0159 vs $0.0159, 50 calls each, ~531-568 tokens-in. PR #2's code review had flagged a per-event `asyncio.to_thread` cost concern in `RecordingEventBus.publish` — sim's higher event cadence does NOT amplify this; total LLM cost dominates by orders of magnitude.

**Lesson:** Sim is the *same* cognitive workload as live — same prompts, same model, same token shape. The wall-clock speedup (~1.7× on the calibration run) comes entirely from removed ADB latency, not cheaper inference. This confirms ADR-0006's record-replay rationale: replay sidesteps LLM cost entirely; sim does NOT. Phase 0.7's cliff test (N=20 trials × 2 arms × 3-5 scenarios = 120-200 games × $0.016 ≈ $2-3 LLM cost) is bounded by LLM cost, which sim does not change. Sim's value is iteration cadence, not cheaper experiments.

**How to apply:** When budgeting any future cliff-test or ablation that uses `Game2048Sim`, multiply LLM-call cost by trial count — don't expect sim to reduce it. Use the recorder for UI-iteration loops (where replay actually IS free) and the sim for cognitive-validity loops (where cost is the same as live but wall-clock is faster). Calibration data lives in the Task 6 commits; re-run if the cognitive layer's prompt shape changes materially.

### Don't pivot to RL — it kills the cognitive moat

**Date:** 2026-05-02 | **Context:** brainstorm with the AI red-team

**What happened:** During the architecture review, the natural question came up: why pay for LLM inference when RL (PPO, DQN) could master 2048 in an hour at zero per-move cost?

**Lesson:** RL produces optimizers; cognitive simulation produces explainers. The product is the *introspection* (visible reasoning, persona narratives, post-game reflection lessons) — not the win-rate. Trading the cognitive architecture for inference speed kills the differentiator and puts us in modl.ai's lane (where they have a 5-year head start).

**How to apply:** When inference cost / latency feels painful, the answer is hybrid local+API LLMs (System 1/2 routing) — not RL. The cognitive layer is the moat; preserve it. Documented in `docs/product/methodology.md` §3.3.

### State-Transition Signatures > 1:1 affect→KPI mappings

**Date:** 2026-05-02 | **Context:** brainstorm session on validation methodology

**What happened:** Original methodology proposed mapping single affect snapshots to KPIs ("anxiety > 0.6 → spend trigger"). The AI red-team pointed out: a single anxiety spike could mean fun challenge, annoying puzzle, or about-to-quit. Indistinguishable from the snapshot.

**Lesson:** Behavioral prediction needs compositional patterns, not threshold snapshots. Multi-step state machines (e.g., Confidence ↓ → Anxiety ↑ → Frustration plateau = Churn Signature) are scientifically defensible AND harder for competitors to clone trivially.

**How to apply:** Defined the four named Signatures (Alpha/Churn, Beta/Conversion, Gamma/Engagement, Delta/Bounce) in `docs/product/methodology.md` §1. Each signature has a state-machine pattern, falsification criterion, and KPI mapping.

### Cohort-distribution reporting > single-trajectory point predictions

**Date:** 2026-05-02 | **Context:** brainstorm on long-horizon (Day-N retention) prediction

**What happened:** Original framing implied Nova would predict "32.4% Day-30 churn." Compounding error in any multi-day simulation makes single-point predictions noise by Day 30 — the same fundamental limit that caps weather forecasting at ~10 days regardless of model quality.

**Lesson:** When dealing with compounding-error systems, report distributions, not points. The widening confidence interval IS the prediction. Honest format: "Median 28% Day-30 churn (95% CI [22%, 38%]), driven by accumulated affective baseline drift." Studios use the distribution shape (variance) to make decisions; tight CI = ship with confidence, wide CI = run more human playtests first.

**How to apply:** All long-horizon predictions in Phase 4+ MUST be cohort distributions across N≥50 personas. Specified in `docs/product/methodology.md` §1.6.2.

### Hybrid local+API inference > all-API or all-local

**Date:** 2026-05-02 | **Context:** brainstorm on production inference architecture

**What happened:** The naive options at scale are (a) all-API (latency + cost + rate limits) or (b) all-local (~70B+ model needed for reasoning depth, expensive hardware). Both have real downsides.

**Lesson:** Routing by cognitive load is the right architecture, mirroring Kahneman's System 1 / System 2. ReAct (90% of moves, fast intuitive) → local 14B-class (Qwen 2.5 14B + vLLM `guided_decoding` for zero JSON parse errors). ToT branches + Reflection (rare, deliberate) → frontier API. ~95% of inference moves local; API cost stays bounded.

**How to apply:** Phase 1 builds the `LocalLLMAdapter`. The `LLM` protocol abstraction in `nova_agent/llm/protocol.py` already supports this; adding the local adapter is a 1-week port, not a rewrite.

### Variance reduction is the on-thesis test for trauma-tagging, not mean shift

**Date:** 2026-05-02 | **Context:** designing the trauma ablation study

**What happened:** Initial instinct was to test "does trauma improve average score?" — the standard "did the intervention work" test.

**Lesson:** Trauma in the cognitive architecture is *avoidance learning* — the agent remembers what killed it and avoids similar situations. The empirical signature of avoidance learning is **reduced variance under similar stimuli** (more consistent play, fewer catastrophic outliers in the lower tail), not higher mean performance. Testing on mean would be the wrong test for the mechanism.

**How to apply:** Phase 0.8 uses Levene's W test for equality of variances (full math in `docs/product/methodology.md` §4.2). Pass criterion: W significant at p<0.05 AND Var(Y_on) < Var(Y_off). Failure → demote trauma from core feature to UI flavor.

### Three-channel memory decay matched to cognitive psychology

**Date:** 2026-05-02 | **Context:** designing long-horizon (Day-N) simulation

**What happened:** Naive answer to "should memory fade between simulated sessions?" is "yes, single half-life." But this is wrong: real human memory has at least three distinct channels (episodic / semantic / affective) with very different decay rates.

**Lesson:** Don't add tunable parameters without literature anchoring. The three-channel decay model (Tulving 1972) gives Nova:
- Episodic: ~24h half-life (Ebbinghaus, Murre & Dros 2015)
- Semantic: ~7d half-life (Bahrick 1984)
- Affective baseline: ~30d with floor (Yehuda et al.)

Each rate is citable; the model is scientifically defensible; Day-3 frustration legitimately compounds into Day-17 churn risk via the slow-decaying affective channel.

**How to apply:** Implementation gates on Phase 0.7 + 0.8 passes. Spec'd in `docs/product/methodology.md` §1.6.

---

## Workflow / process learnings

### Test-runner spec drift — collector creeping into analyzer

**Date:** 2026-05-05 | **Cost:** ~0 minutes (caught in Q6 of Test Runner spec brainstorm), but pattern compounds across spec evolution if uncaught.

**What happened:** Brainstorming "what artifacts does the cliff-test runner produce?" my initial proposal was a 3-tier JSON hierarchy: per-trial + per-scenario aggregate (mean Δ, prediction-validity %) + run-level verdict (pass/fail per methodology §5.3). The red team flagged it as a Separation-of-Concerns violation: the per-scenario and run-level tiers were no longer "data the runner collected" — they were *statistical analysis* hardcoded into the orchestrator. If the analysis methodology evolves (e.g., switch from paired-mean Δ to bootstrap CI, or change the prediction-validity threshold post-pilot), the runner code would have to change in lockstep. Conceded; final shape is flat CSV row-per-trial + JSONL events, with all aggregate stats and pass/fail logic deferred to a separate `analyze_results.py` (out of Test Runner spec scope).

**Lesson:** When designing an experiment-runner spec, the natural drift is: "runner produces data" → "runner produces summary" → "runner produces verdict." Each step feels like it's serving the consumer (the analyst eventually wants pass/fail, so why not just include it?). But the consequence is methodology-orchestrator coupling: any future change to the stats has to thread through the runner code. Specs that conflate collection with analysis are harder to evolve and harder to defend in methodology review (the runner becomes part of the experimental method). Hold the line: runner = collector. Analyzer = separate artifact.

**How to apply:** When drafting an experiment-runner spec, draw an explicit boundary in the Out-of-Scope section: "the runner does NOT compute aggregate statistics, summary means, pass/fail verdicts, or cross-trial comparisons. Those live in a downstream analysis script that consumes the runner's flat per-trial output." The boundary survives only if it's stated. Per-trial *derived flags* (e.g., "did this trial meet threshold X?") are acceptable in the runner output because they're per-trial observations, not cross-trial aggregations. The line is at "across-trial / across-arm / across-scenario math" — anything inside one trial is data; anything across trials is analysis.

### Verify red-team cost-leakage claims numerically before accepting framing

**Date:** 2026-05-05 | **Cost:** ~0 minutes (caught in-loop), but pattern-cost across the brainstorm system is large if uncaught.

**What happened:** During the Test Runner spec brainstorm (Q2, parallelism strategy), the red team flagged "critical budget leakage" from independent arm scheduling under the paired-discard rule (Bot spec §2.6) — claim being that Bot tokens spent before a paired Carla abort would be wasted. Running the actual numbers (Bot abort rate <2% at temp=0 + 3× API retry, Carla abort rate ~3-5%, Bot per-trial cost ~$0.10, Carla ~$1-2, N=20 × 3 scenarios) showed expected wasted-pair leakage was **~$2-3 over the entire cliff test** — not "critical." Accepted the structural change (paired-trial as unit-of-concurrency) on independent code-clarity grounds, explicitly rejected the cost-leakage framing in the analysis. If the framing had been accepted as-stated, the spec would have anchored the budget envelope discussion around a phantom $-figure problem and downstream calibration runs would have over-engineered for it.

**Lesson:** A red-team claim that sounds rigorous (units, percentages, "wasted tokens", "leakage") may still be 10× over-calibrated. The rigor of the *structure* (named units, percentages quoted) is independent of the rigor of the *magnitudes*. Always run the actual numbers — abort rates × per-trial costs × N — before accepting either the proposed fix or the framing that motivates it. The fix may still be correct on other grounds (in this case, paired bookkeeping is a real code-clarity win); separating "is the fix right?" from "is the framing right?" keeps the spec honest and prevents spec text from anchoring on a phantom problem.

**How to apply:** When a `/redteam` analysis surfaces a quantitative claim (cost leakage, latency overhead, error rate, overshoot percentage), §3 of the protocol output ("Where the red team is weaker than they framed") MUST include explicit math — quote the inputs, compute the magnitude, compare to the threshold of "critical." If the math shows the magnitude is small, accept the fix only on its other merits (or reject) and call out the framing miscalibration. This is now part of how the redteam slash command is meant to be exercised; no skill-file change needed, but next round's §3 should treat numerical-claim verification as mandatory not optional.

**Addendum (2026-05-05, same-session reinforcement):** The same rule extends to **code-state claims**, not just numerical claims. In Q3 of the same Test Runner brainstorm (Anxiety sampling mechanism), the red team flagged "EventBus async race conditions at trial teardown" and proposed direct state poll over bus subscription. My initial pushback assumed the bus had an in-process subscriber pattern. Verifying the code (`nova_agent/bus/websocket.py:52-59`) showed the bus is **WebSocket-broadcast-only with silent drop on no-client connected** — my mental model of the architecture was wrong, and the red team's MODIFY was correct (though their framing about "race conditions" was also imprecise; the actual problem is dropped events at the publish site, not race windows on receive). The right answer turned out to be even cleaner than the red team framed: the runner can capture the post-decision anxiety from the synchronous return value of `affect.update()`, no bus involvement at all. Lesson generalizes: when the red team makes a code-state claim ("X has property Y"), verify by reading X before defending or conceding. The cost of the read is small; the cost of arguing from a wrong mental model compounds across the rest of the brainstorm and downstream into the spec.

### Open PR on the active long-lived branch silently swallows new commits

**Date:** 2026-05-05 | **Cost:** ~5 minutes of cleanup at end of session + a non-trivial methodology hit (PR #7's scope misrepresented for several hours)

**What happened:** Project Nova uses a long-lived feature branch (`claude/practical-swanson-4b6468`) and a one-PR-per-coherent-unit cadence (workflow.md). PR #7 was opened with the cliff-test scenarios unit (8 commits) and left open awaiting review. A new session started and shipped a second coherent unit (Baseline Bot decider — spec + ADR amendment + 7-task implementation = 13 more commits) on the same branch. Every push auto-updated PR #7 because GitHub tracks branches not commits, so PR #7 silently grew from 8 commits to 21 — but its title/body still described only the cliff-test unit. The "one-big-PR drift trap" workflow.md explicitly warns about. Caught only at PR-creation time when the finishing-a-development-branch skill asked which option to take.

**Lesson:** Long-lived feature branches + open PRs are a hidden mode: you cannot open a "new" PR from the same branch — you can only update the existing one. Any work committed before the prior PR merges stacks under that PR's title/body. Without an explicit check at session start, the stack can grow several units deep before anyone notices, and at that point the choices are (a) update PR meta to encompass everything, (b) force-push branch surgery (destroys in-flight Layer 2 review). Both are recoveries; neither is the cadence the workflow rule wants.

**How to apply:**

1. **SessionStart hook in `.claude/settings.json`** — runs `gh pr list --head $(git branch --show-current) --state open --json number,title` at every session start and emits a `systemMessage` warning listing any open PRs on the current branch with a reminder to confirm the new work belongs in the same unit before committing. Hook beats discipline; landed in this same commit. Note: the hook only registers after `/hooks` reload or session restart in the session that introduced it (settings watcher catches new files at session start only).
2. **Memory entry on the same topic** in user-scope auto-memory so future-me checks PR state at session start across `/clear` boundaries.
3. **If the stack already happened**: prefer (A) updating the existing PR's title/body to honestly describe both units over (B) force-pushing branch surgery — (A) is reversible, preserves the in-flight Layer 2 review (which is now reviewing the combined diff anyway), and avoids a force-push on a branch tracked by an open PR. (B) only makes sense if the two units are genuinely unrelated; coupled units (where the second's spec depends on the first's) ship cleanly under one combined PR.

### `# type: ignore` staging across multi-task plans creates a peel-as-you-go cleanup chain

**Date:** 2026-05-04 | **Context:** the 7-task Game2048Sim build (Tasks 1, 2, 4, 5).

**What happened:** Task 1 introduced three `# type: ignore[import-untyped]` comments on lazy imports of modules (`nova_agent.lab.io`, `nova_agent.lab.sim`, `nova_agent.lab.scenarios`) that didn't exist yet. Tasks 2, 4, and 5 each had to PEEL the corresponding ignore once the underlying module materialized, because mypy strict's `unused-ignore` rule fires the moment the module import resolves. Forgetting to peel causes mypy strict to fail at task N rather than task 1, which is confusing because the failing line wasn't touched in task N's diff.

**Lesson:** Cross-task plans that stage forward-references via `# type: ignore` create a chain of cleanup obligations across tasks. Each task that resolves a placeholder must remember to peel its specific ignore. The plan must document the staging explicitly or the obligation gets lost when sub-agents read tasks in isolation.

**How to apply:** Two patterns for forward-references in multi-task plans:

1. **Document the staging in a top-level table** in the plan doc (e.g. "Task 1 stages 3 `type: ignore` comments at file:line; Task 2 peels A, Task 4 peels B, Task 5 peels C"). The Game2048Sim plan documented this in Step text but not as a table — adequate but easy to miss when sub-agents read tasks in isolation.
2. **Use `if TYPE_CHECKING:` + string-literal annotations** for forward-references instead of runtime imports + `type: ignore`. More verbose at the import site but no cleanup obligation, and `unused-ignore` doesn't apply because there's no runtime import to resolve.

### "Did I review?" must be a binary check on file paths, not a judgment

**Date:** 2026-05-04 | **Context:** PR #1 closed, Week 0 Day 2 review-system port

**What happened:** PR #1 (10-commit AgentEvent validator + nunu.ai dossier rewrite + CI trim) shipped with the Claude pair skipping reviewer dispatches twice. The mistake wasn't "I decided not to review" — it was "I never asked the question." When invocation depends on the operator remembering to ask "should I review this?", the answer drifts toward "no" under fatigue or context pressure. Looking back at the diff after merge, the missed reviews would have caught nothing critical, but the pattern is unsafe.

**Lesson:** A path-matched trigger taxonomy in `REVIEW.md` plus a binary line in `.claude/pre-commit-checklist.md` ("`/review` dispatched on staged diff (or N/A: <reason>)") removes the judgment call entirely. The reviewer's first job becomes inspecting the diff's file paths against a 9-row table; the answer is yes, no, or "yes for code-reviewer + yes for security-reviewer." No vibes. Pattern adopted from the Gibor app's `/review` skill.

**How to apply:** Three layers, each catching a different failure mode:

- **Layer 1** (in-session, before commit): `/review` orchestrator at `.claude/skills/review/SKILL.md` — manual, Sonnet/Opus, runs while context is hot; the `/code-review` and `/security-review` skills are direct entry points when the orchestrator is overkill
- **Layer 1.5** (auto, on push): `PreToolUse` agent hook in `.claude/settings.json` — Haiku, fires on `git push:*`, blocks only on critical findings
- **Layer 2** (auto, PR-time): `.github/workflows/claude-review.yml` — `claude-code-action@v1`, Sonnet, advisory PR comments only (NOT a required check until ≥10 PRs of signal data exist)

The hook is the safety net for "I forgot Layer 1," and Layer 2 is the safety net for both the human-fast layers when the diff grew across commits. Promoting Layer 2 to a required check is a future ADR — too early to gate merges on it now.

### Brainstorm-then-plan-then-implement actually works

**Date:** 2026-05-02 | **Context:** the thinking-stream feature build

**What happened:** Used the `superpowers:brainstorming` skill (5 visual+conceptual questions) → `superpowers:writing-plans` skill (12-task TDD plan) → `superpowers:subagent-driven-development` skill (sequential task dispatches with reviews). Total: ~4 hours to ship a real feature with 47 passing tests.

**Lesson:** The discipline pays back. Brainstorm catches design issues cheap (5 min each). Plan catches scope creep (every task gates on the next). Subagent execution preserves coding context per task.

**How to apply:** For any non-trivial feature (new component, new data flow, new external integration), invoke the three skills in sequence. Don't skip ahead to "just build it" — the wrong abstractions emerge from undisciplined building and cost 10x to refactor later.

### Self-judged gates work when the criteria are explicit and binary

**Date:** 2026-05-02 | **Context:** dropping the "hostile reviewer" requirement from Week 3

**What happened:** Original plan made Week 3 (KPI mockup) gated on showing it to a hostile reviewer (a specific industry contact who'd be cruel). User dropped that requirement (no available contacts). Replaced with self-judged criteria: "looks like Firebase dashboard, not sci-fi UI" + "leads with KPIs, not affect curves" + "CSV export is first-class."

**Lesson:** External validators are nice-to-have but should never be on the critical path for solo founders. Self-judged gates work IF the criteria are explicit and binary. "Looks professional" is too vague; "leads with KPI predictions, includes CSV export, every prediction footnoted" is testable.

**How to apply:** When defining a self-judged gate, write the specific yes/no questions you'll ask. If the questions are subjective ("does it look good?"), reframe until they're observable ("does it have CSV export? does it lead with KPIs?").

### Update memory before logging off

**Date:** 2026-05-02 | **Context:** end of long brainstorm + dossier session

**What happened:** Almost cleared chat with significant strategic work uncaptured in memory files. The prior `project_nova_resume_point.md` was from much earlier in the session (pre-pivot) and would have given next-session-me a stale picture.

**Lesson:** Memory update is a deliberate ritual at end-of-session, not an afterthought. Treat it like git-commit: nothing's "saved" until it's in the resume_point file.

**How to apply:** Last 10 minutes of every productive session: read the current `project_nova_resume_point.md`, update with any state changes, verify next-session pickup task is at the top, commit if memory is in a tracked repo. Then clear chat or log off.

### TDD subagents catch plan bugs better than human review

**Date:** 2026-05-02 | **Context:** the 12-task thinking-stream build

**What happened:** Three separate plan-template bugs were caught by subagents during TDD execution (rule ordering, truncate trim behavior, `as never` invalid). A human reviewer reading the plan ahead of time would likely have missed at least one of these.

**Lesson:** TDD with the test as spec is an organizational technology, not just an engineering one. The subagent has no incentive to "make the test pass cleverly"; it just runs the test, sees the failure, fixes the impl. Human reviewers often ignore tests when the impl looks plausible.

**How to apply:** Trust subagent TDD output more than ahead-of-time plan review for verification. Use plan review for *strategy* (is this the right thing to build?), not *correctness* (will this code work?).

---

## Strategic / product learnings

### Within-game adaptation ≠ cross-game speedrunning — check faithful-simulation framing before stripping behavioral DVs

**Date:** 2026-05-06 | **Cost:** ~20 min of two /redteam rounds to converge on the right §4.2 design

**What happened:** Designing the methodology §4.2 trauma-ablation rewrite, a first red-team round challenged the avoidance-recurrence behavioral DV as "anti-product — agent learns to skip the trap, becoming a speedrunner instead of a playtester." I accepted it and proposed Option D (affective-only DV). A second red-team round identified the conflation: a human player who hits a brutal trap mid-session plays more cautiously for the remaining moves of that session. That within-session adaptation IS the faithful-simulation signal studios pay for. The speedrunner critique correctly targets cross-session optimization (RL-style: "next game, skip the trap"). It does not apply to within-game adaptation. Stripping the behavioral DV based on the first round's framing would have removed a product-valuable observation and coupled Phase 0.8's pass criterion to the Anxiety pathway — which the C1 ablation had already shown was weak.

**Lesson:** "Avoidance is anti-product for a playtester" is only true for cross-game behavioral learning. Within-game adaptation (playing more cautiously after hitting a trap in the same session) is exactly what the product should simulate. The two are easily conflated under a surface-level "speedrunner" framing. When a red-team challenges a behavioral DV as anti-product, the load-bearing question is temporal scope: within-session or cross-session?

**How to apply:** Before accepting an "anti-product" critique on a behavioral test: (1) Identify whether the behavior is within-game or cross-game. (2) Ask "would a real human player show this behavior in the same session?" — if yes, it IS the playtester signal. (3) Keep the behavioral DV as primary when it tests the mechanism's function; demote only if it tests optimization-across-sessions. Also: the existing LESSONS entry "Variance reduction is the on-thesis test for trauma-tagging" (2026-05-02, Architecture / design decisions) is superseded by the §4.2 rewrite — the on-thesis test is now within-game trap-recurrence rate (behavioral primary) + Anxiety lift (affective secondary, descriptive).

### Category positioning matters more than feature parity

**Date:** 2026-05-02 | **Context:** dossier writing decision on Nova's positioning

**What happened:** Originally framed Nova as "AI playtesting" (adjacent to modl.ai, a QA tool). After review, repositioned as "Cognitive Audit & Prediction Platform" — a product-decision tool. Same architecture, fundamentally different sales motion.

**Lesson:** What category you claim determines your buyer, your pricing, your conferences, your competitors. QA = cost center, smaller budgets, head-on with modl.ai. Product/Live-Ops = profit center, larger budgets, less direct competition. The same product can be sold into different categories with very different outcomes.

**How to apply:** When positioning a product, ask "which department's budget pays for this" and "what KPIs does that department care about." The answer determines the category. Optimize for the larger budget + less-crowded category, even if the technical feature set is identical.

### Don't invent dollar figures in reports

**Date:** 2026-05-02 | **Context:** the bug-handling spec

**What happened:** Initial framing proposed "fix this bug or lose $10K UA spend tomorrow." Rhetorically powerful, quantitatively unsupported (we don't know the studio's CAC, cohort size, or LTV).

**Lesson:** Fabricated numbers destroy credibility with sophisticated buyers. Hand them observable cohort data and let them compute the dollar impact with their own inputs. They'll trust you more for it.

**How to apply:** No invented metrics in any Nova-generated report. Format: "100% of Casual cohort abandoned at level 5; translated to your real users: D1 retention drops by [X% of your D1 cohort that is Casual]. Apply your own CAC + LTV to compute UA-spend impact."

### Naming determines urgency

**Date:** 2026-05-02 | **Context:** bug-handling deliverable design

**What happened:** Initial proposal: "Catastrophic Churn Event" warning when Nova detects a bug. The AI red-team pointed out that "churn" implies "the player would have quit anyway," producing a "shrug" reaction from Product.

**Lesson:** Headline language determines the urgency the report creates. "Catastrophic Churn Event" → shrug. "Forced Abandonment Event (likely build issue)" → "OH GOD FIX THIS NOW." Same data, completely different outcome.

**How to apply:** When naming a report event, ask "does this name signal preventability and urgency?" If not, rename. Documented in `docs/internal/v2.2-epsilon-spec.txt` §4.

### Methodology publication is a moat, not a leak

**Date:** 2026-05-02 | **Context:** open-source vs proprietary deliberation

**What happened:** Initial instinct: keep the affect→KPI math proprietary so competitors can't clone it. Reviewer counter: publish the methodology, become the industry benchmark, force competitors to explain why their math differs.

**Lesson:** In B2B technical sales, transparency attracts the kind of buyers who pay enterprise pricing (data scientists, technical leads who audit your math). Hidden methodology attracts skeptical buyers who treat you as black-box AI vibes. The methodology moat is not "we have secret math" — it's "we have the validated math + the industry vocabulary + the calibration corpus from real pilots."

**How to apply:** Publish `docs/product/methodology.md` openly. Cite literature. Show the Levene's Test formula. Explain the Signatures. Hide nothing about HOW it works; protect the WHO has been validated against (per-pilot calibration corpus).

---

## Failure-mode handling

### Always define what failure looks like before running the test

**Date:** 2026-05-02 | **Context:** Phase 0.7 cliff test design

**What happened:** Initial plan had "weak pass" zone (50-80% trial pass-rate) where we'd "lower the marketing claim." Reviewer flagged: 55% is essentially a coin flip. A "weak pass" zone is rationalization, not signal.

**Lesson:** Define hard floors for falsifiable tests BEFORE running them. Vague "pass/fail/maybe" zones invite confirmation bias. Solo founders especially need this discipline because there's no one else to challenge the rationalization.

**How to apply:** Phase 0.7 hard floor: ≥70% (above chance + sample noise). Below that triggers the 2-week affect-rework branch unconditionally. No "directional alignment" marketing on a coin-flip result.

### Failed validations are publishable, not project-end

**Date:** 2026-05-02 | **Context:** discussing what to do if cliff test fails

**What happened:** Reviewer asked "are you prepared to kill the project if Phase 0.7 fails?" Reframed: failure isn't binary "kill or pivot." There are at least 4 responses: tune, reposition, pivot architecture, or kill. And even "kill" produces a publishable negative result.

**Lesson:** A negative result from a well-designed experiment is more valuable than no experiment. The downside of running Phase 0.7 isn't $50 in LLM credits; it's the time cost. The upside (knowing definitively whether the architecture predicts) is enormous in either direction.

**How to apply:** Frame validation experiments as "we're going to learn either way." A pass means we proceed with confidence; a fail means we save 6 months of building the wrong thing. Both outcomes are wins relative to "not running the experiment."

### Don't trust "zero new architecture" claims without questioning

**Date:** 2026-05-02 | **Context:** the bug-handling brainstorm

**What happened:** Initial framing of bug-handling claimed "zero new architecture — the existing Frustration accumulator handles this perfectly." On second look: false. The Frustration accumulator triggers on score-delta dynamics, which can't distinguish "bad move" from "bug-frozen game." A new `StateUnchangedAfterAction` detector is required (~50 lines).

**Lesson:** "Zero new architecture" claims are seductive (no work needed!) and almost always wrong. When something seems to handle a new case for free, double-check the actual mechanism. Usually some small but real addition is needed.

**How to apply:** When proposing that an existing system handles a new case, write down the minimal test that would prove it. Often the test reveals the gap.

---

## Maintenance notes

- This file is read manually; no auto-maintenance.
- Periodically (monthly?) prune entries that have been formalized into:
  - Pre-commit hooks → no longer a "lesson," it's a guardrail
  - CI checks → no longer a "lesson"
  - CLAUDE.md gotchas section → no longer a "lesson," it's part of orientation
  - Documented architecture decisions (ADRs) → reference the ADR, then prune
- New lessons go at the top of their section.
- Date format: YYYY-MM-DD.
- "Cost" estimates are rough — they exist to convey "this was painful" not for precise accounting.
