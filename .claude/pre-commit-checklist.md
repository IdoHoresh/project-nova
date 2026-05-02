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
- [x] `git diff --cached --stat` reviewed — single source file `nova-viewer/app/page.tsx` (six `e.data as X` cast removals + dependent body simplifications) plus this checklist; ~14 insertions / ~24 deletions on the source file
- [x] Atomic commit — single logical change: "drop e.data casts in app/page.tsx now that the AgentEvent catch-all is gone"

## Verification

- [x] `git diff --cached` scanned for secrets — pure refactor of memo selectors; no env / API keys / tokens / URLs touched
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (97/97), `npx tsc --noEmit` clean (cast removals are identity ops because Task 1 already dropped the catch-all), `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes

## Review

- [x] `code-reviewer` subagent — N/A, this is Task 7 of an in-flight plan; the plan-level review pass runs at Task 9 once the LESSONS update lands
- [x] `security-reviewer` — N/A by trigger; this refactor only removes redundant identity-casts in a memo derivation layer, no security surface touched

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands in Task 9 per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; Task 7 is the cleanup pass that mirrors Task 6 for app/page.tsx

## Commit message

- [x] Conventional Commits format: `refactor(viewer): drop e.data casts in app/page.tsx`
- [x] Body explains *why* — same reasoning as deriveStream cleanup (Task 6): with the AgentEvent catch-all gone (Task 1) the discriminator narrowing handles every accessor, so the casts were redundant identity-casts. Defensive guards (`Boolean(d.active)`, `typeof d.score === "number"`, `d.mode === "tot" || d.mode === "react"`) collapse to direct reads now that fields are exhaustively typed.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
