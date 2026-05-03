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
- [x] `git diff --cached --stat` reviewed — 6 lines added to `nova-viewer/package.json` (pnpm overrides block) + `nova-viewer/pnpm-lock.yaml` regen
- [x] Atomic commit — single logical change: pin esbuild + postcss minimum versions to resolve dependabot moderate alerts

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; package.json + lockfile only
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — gate trio green: `pnpm test` (98 tests passed), `npx tsc --noEmit` (clean), `pnpm run lint` (clean). esbuild now 0.28.0 (was 0.21.5), all postcss instances now 8.5.13 (was mix of 8.4.31 / 8.5.13). vite stays 5.4.21 — blocked by vitest 2.1.9 peer-dep on vite ^5; deferred to follow-up commit alongside vitest 3.x bump.
- [x] Docs / config — `nova-viewer/package.json` adds `pnpm.overrides` block; lockfile regen.

## Review

- [x] `code-reviewer` subagent — N/A, single-file pin to package.json with no executable code change
- [x] `security-reviewer` — N/A in the Nova-threat-model sense (no secrets / env / LLM / bus paths touched). This commit IS the security upgrade — closes 2 of 3 dependabot moderate alerts.

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the override syntax is standard pnpm
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a security patch, not an architectural decision

## Commit message

- [x] Conventional Commits format: `chore(viewer): pin esbuild/postcss minimums for dependabot alerts`
- [x] Body explains *why* — GitHub flagged 3 moderate dependabot alerts on default branch (esbuild dev-server CORS, vite path traversal, postcss XSS). All transitive npm deps. Pinning esbuild ≥0.25.0 and postcss ≥8.5.10 via `pnpm.overrides` resolves 2/3 without touching direct deps. Vite deferred — bumping to 6.4.2 requires vitest 3.x (peer-dep coupling) and is its own commit.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
