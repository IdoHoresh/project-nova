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
- [x] `git diff --cached --stat` reviewed — 1 file, 3 lines changed (palette error message only)
- [x] Atomic commit — single logical change: improve palette validator error message

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` — pytest + mypy + ruff all green (200 passed, mypy clean, ruff clean)
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint
- [x] Docs / config — none touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy mechanical; 2-line error message fix, no logic change
- [x] `code-reviewer` subagent — N/A; mechanical change, Layer 1.5 pre-push hook covers it
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths

## Documentation
- [x] LESSONS.md — N/A this commit
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; 2-line error message improvement, no architectural decision

## Commit message
- [x] Conventional Commits format: `fix(lab): include offending tiles in Scenario palette error`
- [x] Body explains why — symmetry with other validator branches; actionable for Tasks 2-5 scenario authors
- [x] Co-author tag present
