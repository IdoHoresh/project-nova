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
- [x] `git diff --cached --stat` reviewed — 2 modified files: types.ts (+38 lines: 5 new interfaces + 5 AgentEvent union arms) + eventGuards.ts (+57 lines: 5 guard functions + 5 switch cases + 5 imports); well within 500-line limit
- [x] Atomic commit — single coherent unit: mirror bot telemetry event types in nova-viewer per bus contract (required by pre-push hook)

## Verification
- [x] `git diff --cached` scanned for secrets — only TypeScript type definitions and guard functions; no API keys, no env values, no secrets
- [x] `nova-agent/` — N/A: not touched in this commit; still 227 passing from prior commit
- [x] `nova-viewer/` — vitest 98 passing, tsc --noEmit clean, eslint clean
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — mirror-only change; adds type interfaces + guards matching exact Python payload spec from Task 6; no logic, no new seams
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, mirror-type change is mechanical; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: no secrets paths, no LLM calls, no env vars; guard functions validate exact payload shapes (type(exc).__name__ maps to error_type: string, 200-char excerpt maps to raw_response_excerpt: string)

## Documentation
- [x] LESSONS.md — N/A: no new lesson; bus contract mirroring is established pattern
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: bus contract says "both types.ts and eventGuards.ts updated in same PR"; this commit satisfies that requirement

## Commit message
- [x] Conventional Commits format: `feat(viewer): mirror bot telemetry event types in AgentEvent union`
- [x] Body explains why — pre-push hook requires matching viewer types for any new bus event shape; five types added per spec §3.4 telemetry contract
- [x] Co-author tag present
