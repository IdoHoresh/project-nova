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
- [x] `git diff --cached --stat` reviewed — 2 files: scenarios.py (+9 lines MAX_MOVES) + test_lab_scenarios.py (+86 lines corpus tests)
- [x] Atomic commit — single logical change: add MAX_MOVES constant + corpus invariant tests

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` — pytest (210 passed) + mypy (clean) + ruff (clean) all green
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint
- [x] Docs / config — none touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy mechanical; TDD new test file + constant addition, no logic change
- [x] `code-reviewer` subagent — N/A; mechanical TDD task, Layer 1.5 pre-push hook covers it
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths

## Documentation
- [x] LESSONS.md — N/A this commit
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; adding MAX_MOVES constant + corpus tests is not an architectural decision

## Commit message
- [x] Conventional Commits format: `feat(scenarios): add MAX_MOVES cap and corpus invariant tests`
- [x] Body explains why — closes cliff-test scenarios spec implementation; invariants catch authoring errors before agent runs
- [x] Co-author tag present
