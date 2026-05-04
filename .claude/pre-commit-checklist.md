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
- [x] `git diff --cached --stat` reviewed — 1 file: `.github/workflows/ci.yml` (pnpm 10 → 11 to match project; root-cause of PR #5's nova-viewer CI failure)
- [x] Atomic commit — single logical change: bump CI pnpm to 11 to match the project state set by commit e322872

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens (workflow YAML only)
- [x] `nova-agent/` not touched — N/A pytest/mypy/ruff
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint (the fix is in CI workflow, not viewer code; effect is the viewer trio will now pass on CI)
- [x] Docs / config — `.github/workflows/ci.yml` only

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: CI-config-only`. Single-line YAML version bump with explanatory comment; no code surface, no security surface.
- [x] `code-reviewer` subagent — N/A, CI-config-only
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; the CI-vs-local pnpm-version-skew gotcha could land as a future LESSONS entry if it bites again
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A (operational fix)

## Commit message
- [x] Conventional Commits format: `ci(viewer): bump pnpm 10 → 11 to match project lockfile encoding`
- [x] Body explains *why* — pnpm 10 in CI rejects pnpm 11's lockfile-overrides encoding with ERR_PNPM_LOCKFILE_CONFIG_MISMATCH; commit e322872 already moved the project to pnpm 11 (allowBuilds workspace config), CI was never updated. Surfaced as a failure on PR #5 (Game2048Sim).
- [x] Co-author tag present
