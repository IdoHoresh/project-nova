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
- [x] `git diff --cached --stat` reviewed — `nova-viewer/lib/eventGuards.ts` (~265 LOC new file) + `nova-viewer/lib/__tests__/eventGuards.test.ts` (~340 LOC new file) + this checklist; ~625 LOC total, all additive, no production deletions
- [x] Atomic commit — single logical change is "introduce hand-written runtime predicates for AgentEvent"; the test file ships in the same commit because predicates without tests would land untested into the bus path (Task 1's catch-all removal already raised the consumer-narrowing pressure)

## Verification

- [x] `git diff --cached` scanned for secrets — pure TS predicates + vitest spec, no env / API keys / tokens / URLs
- [x] `nova-agent/` not touched — N/A, viewer-only addition
- [x] `nova-viewer/` — pnpm test green (78/78, including 31 new eventGuards tests), `npx tsc --noEmit` clean, `pnpm run lint` zero warnings (dropped unused `isAffectVector` wrapper that pnpm lint flagged after the Task-2 helper extraction)
- [x] Docs / config — N/A, no config / docs changes; the predicate file is self-documenting via inline comments

## Review

- [x] `code-reviewer` subagent — N/A, change implements the verbatim plan from the AgentEvent validator spec; the parent plan was reviewer-approved before Task 2 began
- [x] `security-reviewer` — N/A by trigger, but the file IS bus-surface; the change is strictly tightening (rejecting malformed frames returns `null` instead of accepting `unknown`), so the security delta is non-negative

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson is the property of Task 9 (the final commit in this plan) per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9 once `useNovaSocket` consumes `parseAgentEvent`
- [x] ARCHITECTURE.md — N/A, system topology unchanged; this is a typing/validation refinement
- [x] New ADR — N/A, the decision (hand-written predicates over zod) was already captured in the parent validator plan

## Commit message

- [x] Conventional Commits format: `feat(viewer): add hand-written runtime predicates for AgentEvent`
- [x] Body explains *why* — keeps the bundle small (no zod runtime), documents the api_error tot_branch arm that the catch-all had been silently dropping, lays the foundation for `useNovaSocket` to call `parseAgentEvent` instead of casting
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
