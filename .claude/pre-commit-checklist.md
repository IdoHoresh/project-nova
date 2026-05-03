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
- [x] `git diff --cached --stat` reviewed — single-file rewrite of `.github/workflows/ci.yml` (~70 lines net deletion across job removals + restructure) plus the checklist update
- [x] Atomic commit — single logical change: trim CI workflow to phase-appropriate gates (PR-only triggers, drop redundant pre-commit job, fold pnpm audit into viewer, separate gitleaks)

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` not touched — N/A, CI-config-only change
- [x] `nova-viewer/` not touched — N/A, CI-config-only change
- [x] Docs / config — `.github/workflows/ci.yml` rewritten; new shape is 4 jobs (agent, viewer, gitleaks, all-green) instead of 5 (agent, viewer, security, pre-commit, all-green); triggers tightened from `push: branches: ["**"]` to `push: branches: [main]` so feature-branch pushes no longer fire CI duplicates alongside the PR run

## Review

- [x] `code-reviewer` subagent — N/A, infrastructure-only change with no executable logic touched in agent or viewer; the workflow itself is the change
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. gitleaks split into its own job (smaller surface, runs in parallel, no node_modules dependency)

## Documentation

- [x] LESSONS.md — N/A, infra plumbing
- [x] CLAUDE.md "Common gotchas" — N/A, the trade-offs (PR-only triggers, audit non-blocking until Phase 5+) are documented inline in the workflow YAML
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a phase-appropriate trim of CI scope, not a new architectural decision

## Commit message

- [x] Conventional Commits format: `ci: trim workflow to phase-appropriate gates`
- [x] Body explains *why* — every PR commit was firing 10 checks (5 jobs × push + pull_request) with the pre-commit job 90% redundant against the local pre-commit framework; folded pnpm audit into viewer to avoid double-installing pnpm; bumped audit threshold to high to stop training us to ignore moderate noise; added build artifact upload for visual smoke checks
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
