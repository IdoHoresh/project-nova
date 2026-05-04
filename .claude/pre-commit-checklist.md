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
- [x] `git diff --cached --stat` reviewed — 1 new file: `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md` (~310 lines, doc-only)
- [x] Atomic commit — single logical change: add the Phase 0.7 cliff-test scenarios design spec

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens (markdown only)
- [x] `nova-agent/` not touched — N/A pytest/mypy/ruff (doc-only)
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint (doc-only)
- [x] Docs / config — `docs/superpowers/specs/` only

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: doc-only`. Spec markdown with no code surface, no security surface.
- [x] `code-reviewer` subagent — N/A, doc-only
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; this is itself the documentation deliverable
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; no architectural decision changed (the spec implements ADR-0007's pinned design at the scenarios layer)

## Commit message
- [x] Conventional Commits format: `docs(specs): add Phase 0.7 cliff-test scenarios design spec`
- [x] Body explains *why* — Phase 0.7 cliff-test scenarios were deferred from the Game2048Sim spec; this spec resolves them with six rounds of red-team review (Illusion-of-Hope buffer, paired-seed protocol, RNG discipline, all-community-sourced, persona-calibrated magnitudes, fresh-memory-per-trial, noise-immune Anxiety threshold, MAX_MOVES=50 cap, minimum-implied-score validator).
- [x] Co-author tag present
