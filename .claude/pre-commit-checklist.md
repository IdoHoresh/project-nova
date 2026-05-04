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
- [x] `git diff --cached --stat` reviewed — 1 new file: `docs/superpowers/plans/2026-05-05-cliff-test-scenarios.md` (~917 lines, doc-only)
- [x] Atomic commit — single logical change: add the cliff-test scenarios implementation plan

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens (markdown only)
- [x] `nova-agent/` not touched — N/A pytest/mypy/ruff (doc-only)
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint (doc-only)
- [x] Docs / config — `docs/superpowers/plans/` only

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: doc-only`. Plan markdown with no code surface, no security surface.
- [x] `code-reviewer` subagent — N/A, doc-only
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; this is itself a doc deliverable
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; the plan implements the cliff-test scenarios spec at the dataclass + library layer

## Commit message
- [x] Conventional Commits format: `docs(plans): add Phase 0.7 cliff-test scenarios implementation plan`
- [x] Body explains *why* — see commit body
- [x] Co-author tag present
