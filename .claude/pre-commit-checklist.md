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
- [x] `git diff --cached --stat` reviewed — 2 files: `LESSONS.md` (5 new entries from the Game2048Sim build's cross-task sweep), `.claude/pre-commit-checklist.md` (refilled for this commit)
- [x] Atomic commit — single logical change: capture Game2048Sim implementation lessons from Tasks 1-6

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; only the alias name `GOOGLE_API_KEY` appears as a documentation reference, no values
- [x] `nova-agent/` not touched in this commit — N/A pytest/mypy/ruff (would still pass at HEAD; doc-only change)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — LESSONS.md updated with cross-task entries

## Review
- [x] `/review` dispatched — N/A: doc-only, REVIEW.md taxonomy `N/A: doc-only`
- [x] `code-reviewer` subagent — N/A, doc-only
- [x] `security-reviewer` — N/A, doc-only

## Documentation
- [x] LESSONS.md — UPDATED in this commit (the entire commit)
- [x] CLAUDE.md "Common gotchas" — N/A (lessons are sub-gotcha-level; the Pydantic alias trap COULD be promoted to gotcha #10 in a future commit if it bites again)
- [x] ARCHITECTURE.md — N/A (already updated in Task 5)
- [x] New ADR — N/A (no new architectural decisions)

## Commit message
- [x] Conventional Commits format: `docs(lessons): record Game2048Sim implementation lessons (Tasks 1-6)`
- [x] Body summarizes the 5 lessons captured + references the Task 6 calibration data point that informed lesson 2
- [x] Co-author tag present
