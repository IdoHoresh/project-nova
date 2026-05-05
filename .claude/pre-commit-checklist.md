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
- [x] `git diff --cached --stat` reviewed — 2 modified files: baseline.py (+24 lines impl) + test_decision_baseline.py (+54 lines new test); well within 500-line limit
- [x] Atomic commit — single coherent unit: happy-path BaselineDecider.decide implementation + test

## Verification
- [x] `git diff --cached` scanned for secrets — only Python source and test code; no API keys, no env values, no secrets
- [x] `nova-agent/` — pytest 220 passing (was 213 + 7 baseline), mypy strict clean, ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — TDD implementation of approved plan Task 3 (docs/superpowers/plans/2026-05-05-baseline-bot.md); no new architectural seams, no new bus paths, no secrets paths; single LLM call per spec
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, Task 3 is isomorphic/mechanical TDD; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: no new LLM adapter, no env/secrets paths, no bus events; single call to existing self.llm.complete() with no PII

## Documentation
- [x] LESSONS.md — N/A: no new lesson from this task; implementation was straightforward
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: ADR-0007 already covers the Baseline Bot design

## Commit message
- [x] Conventional Commits format: `feat(baseline): implement happy-path BaselineDecider.decide`
- [x] Body explains why — single LLM call per move with text-only prompt; retries and telemetry deferred to Tasks 4-6 per the plan
- [x] Co-author tag present
