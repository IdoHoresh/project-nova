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
- [x] `git diff --cached --stat` reviewed — 2 modified files: baseline.py (~15 lines: import + constant + decide loop) + test_decision_baseline.py (+42 lines: 2 new parse-retry tests); well within 500-line limit
- [x] Atomic commit — single coherent unit: parse-failure retry loop (1x, then TrialAborted) + 2 TDD tests per Task 5

## Verification
- [x] `git diff --cached` scanned for secrets — only Python source and test code; no API keys, no env values, no secrets
- [x] `nova-agent/` — pytest 224 passing (was 222 prior; +2 new parse-retry tests), mypy strict clean, ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — TDD implementation of approved plan Task 5 (docs/superpowers/plans/2026-05-05-baseline-bot.md); parse-retry wraps existing parse_json call; no new architectural seams, no new bus paths, no secrets paths
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, Task 5 is isomorphic/mechanical TDD; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: no new LLM adapter, no env/secrets paths, no bus events

## Documentation
- [x] LESSONS.md — N/A: no new lesson from this task; parse-failure retry is straightforward try/continue pattern
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: ADR-0007 already covers the Baseline Bot design; parse-retry policy is captured in spec §3.3 / A1.5

## Commit message
- [x] Conventional Commits format: `feat(baseline): add parse-failure retry (1x, then abort)`
- [x] Body explains why — wraps parse_json in 2-iteration loop; StructuredOutputError caught specifically; spec ref A1.5 / §3.3
- [x] Co-author tag present
