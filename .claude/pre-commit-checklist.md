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
- [x] `git diff --cached --stat` reviewed — `nova-viewer/package.json` adds vite 6.4.2 + bumps vitest to 3.2.4 + adjusts @vitejs/plugin-react to 5.2.0; `nova-viewer/pnpm-lock.yaml` regen
- [x] Atomic commit — single logical change: bump vitest+vite to resolve dependabot alert #2 (vite path traversal)

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; package.json + lockfile only
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — gate trio + build green: `pnpm test` (98 tests pass on vitest 3.2.4), `npx tsc --noEmit` (clean), `pnpm run lint` (clean), `pnpm run build` (Next 16 production build succeeds, 4 static pages prerendered). Versions resolved: vite 6.4.2 (was 5.4.21), vitest 3.2.4 (was 2.1.9), @vitejs/plugin-react 5.2.0 (was 4.7.0). No peer-dep warnings.
- [x] Docs / config — `vitest.config.ts` unchanged, fully compatible with vitest 3.x; CJS deprecation warning from previous build also resolved.

## Review

- [x] `code-reviewer` subagent — N/A, dep-bump-only commit; no executable code touched
- [x] `security-reviewer` — N/A in the Nova-threat-model sense; this commit IS the security upgrade. Closes the last of 3 dependabot moderate alerts (vite path-traversal in optimized-deps `.map` handling).

## Documentation

- [x] LESSONS.md — N/A; the vitest/vite peer-dep coupling pattern is documented in this commit's body and is standard ecosystem behavior
- [x] CLAUDE.md "Common gotchas" — N/A, no new Nova-specific gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, security patch not architectural decision

## Commit message

- [x] Conventional Commits format: `chore(viewer): bump vitest+vite to resolve dependabot vite alert`
- [x] Body explains *why* — closes the deferred dependabot alert #2 (vite <=6.4.1 path traversal). Required vitest 3.x in tandem because vitest 2 peer-deps vite ^5; @vitejs/plugin-react also stepped down from 6 to 5 because plugin-react 6 wants vite ^8 (vite 8 is alpha at time of writing). Net result: all three dependabot moderate alerts now closed on this branch.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
