# Pre-Commit Checklist

> Before EVERY commit, work through this list and check each item.
> The pre-commit framework runs `scripts/check-claude-checklist.sh`
> which **blocks the commit** if any item is left unchecked.
>
> After a successful commit, `scripts/reset-checklist.sh` runs at the
> post-commit stage and resets every box back to `[x]` so the next
> commit starts fresh.
>
> If a step doesn't apply, write a one-sentence reason after the
> bracket (e.g. mark `[x]` and add `/review — skipped, doc-only change`)
> and check the box. Silent skipping is forbidden.

## Branch + scope
- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — 2 modified files: baseline.py (~90 lines: import time + Usage, refactored decide/call_with_api_retry + new _emit helper) + test_decision_baseline.py (+82 lines: _CapturingBus + 3 new telemetry tests); well within 500-line limit
- [x] Atomic commit — single coherent unit: Task 6 telemetry events via EventBus.publish

## Verification
- [x] `git diff --cached` scanned for secrets — only Python source and test code; no API keys, no env values, no secrets
- [x] `nova-agent/` — pytest 227 passing (was 224 prior; +3 new telemetry tests), mypy strict clean, ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — TDD implementation of approved plan Task 6 (docs/superpowers/plans/2026-05-05-baseline-bot.md); telemetry is a pure additive side-effect path with no new seams; security-reviewer dispatch is reserved for the controller per Task 6 spec
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, Task 6 is isomorphic/mechanical TDD; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: controller will dispatch security-reviewer post-commit per Task 6 spec §step-5; payload fields are narrowed per security.md contract (indices, action enum, token counts, latency, error class name, 200-char excerpt only)

## Documentation
- [x] LESSONS.md — N/A: no new lesson from this task; telemetry pattern is additive and well-understood
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: ADR-0007 covers Baseline Bot; telemetry contract is captured in spec §3.4

## Commit message
- [x] Conventional Commits format: `feat(baseline): add telemetry events for Test Runner consumption`
- [x] Body explains why — five new bus event types (bot_call_attempt, bot_call_success, bot_call_api_error, bot_call_parse_failure, bot_trial_aborted); Test Runner spec §3.4
- [x] Co-author tag present
