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
- [x] `git diff --cached --stat` reviewed — single source file `nova-viewer/lib/stream/deriveStream.ts` (cast removal + applyBranch if/else expansion + isSwipeAction predicate guard) plus this checklist; ~30 insertions / ~25 deletions on the source file
- [x] Atomic commit — single logical change: "drop e.data casts in deriveStream now that the AgentEvent catch-all is gone"

## Verification

- [x] `git diff --cached` scanned for secrets — pure refactor of a derived-state reducer; no env / API keys / tokens / URLs touched
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (97/97, including the 29 deriveStream tests untouched), `npx tsc --noEmit` clean (cast removals are identity ops because Task 1 already dropped the catch-all), `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes; the rationale is captured in the source comment on the applyBranch else-branch

## Review

- [x] `code-reviewer` subagent — N/A, this is Task 6 of an in-flight plan; the plan-level review pass runs at Task 9 once the LESSONS update lands
- [x] `security-reviewer` — N/A by trigger, but worth noting: this refactor strictly tightens runtime checks (the bare `as SwipeAction` cast becomes an `isSwipeAction` predicate guard that drops malformed frames instead of letting them through)

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands in Task 9 per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; Task 6 is the cleanup pass that completes the catch-all-removal arc

## Commit message

- [x] Conventional Commits format: `refactor(viewer): drop e.data casts in deriveStream`
- [x] Body explains *why* — Task 1 dropped the AgentEvent catch-all so TS now narrows e.data automatically when we discriminate on e.event; the casts were redundant identity-casts hiding a real defect (the SwipeAction cast trusted the agent to emit only known directions). Replaces every `e.data as X` with the bare reference and turns the action cast into an `isSwipeAction` predicate guard that skips bad frames.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
