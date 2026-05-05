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
- [x] `git diff --cached --stat` reviewed — 1 line added to a single test file (regression-test text-block assertion)
- [x] Atomic commit — single coherent unit: code-quality reviewer Should-1 fix on Task 1's regression test

## Verification
- [x] `git diff --cached` scanned for secrets — only test assertion strings, no API keys / env values
- [x] `nova-agent/` — pytest 213 passing, mypy + ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` (one-line test assertion fix from upstream code-quality review)
- [x] `code-reviewer` subagent — N/A: this IS the code-reviewer follow-up fix; no new review needed per memory feedback_subagent_dispatch_selectivity (skip re-review on verbatim fixes)
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A this commit
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A

## Commit message
- [x] Conventional Commits format: `test(react): assert text block presence in screenshot regression test`
- [x] Body explains why — code-quality reviewer Should-1 finding on commit 5534028; the regression test asserted image-block presence but not text-block presence, masking a future drop of the text block
- [x] Co-author tag present
