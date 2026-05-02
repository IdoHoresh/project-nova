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
- [x] `git diff --cached --stat` reviewed — `nova-viewer/lib/__tests__/eventGuards.test.ts` (+137 LOC test additions) + `nova-viewer/lib/eventGuards.ts` (+1 LOC comment) + this checklist; ~153 insertions total, all additive, zero deletions in production code
- [x] Atomic commit — single logical change is "close coverage gaps in eventGuards predicate tests after 0f57f98 review"; the comment in eventGuards.ts ships in the same commit because the corresponding test asserting prototype-pollution rejection is the consumer of that comment

## Verification

- [x] `git diff --cached` scanned for secrets — pure TS test cases + one source-comment line, no env / API keys / tokens / URLs
- [x] `nova-agent/` not touched — N/A, viewer-only addition
- [x] `nova-viewer/` — pnpm test green (93/93, including 46 eventGuards tests up from 31), `npx tsc --noEmit` clean, `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes; the test additions are self-documenting via describe-block names

## Review

- [x] `code-reviewer` subagent — N/A, this commit IS the response to code-reviewer + spec-reviewer feedback on 0f57f98; their NEEDS_FIX / SHOULD-FIX items are addressed verbatim
- [x] `security-reviewer` — N/A by trigger, but the predicate file IS bus-surface; the change tightens test coverage on the prototype-pollution allowlist (new comment + already-passing test) and adds NaN-reject assertions, so the security delta is non-negative

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson is the property of Task 9 (the final commit in this plan) per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9 once `useNovaSocket` consumes `parseAgentEvent`
- [x] ARCHITECTURE.md — N/A, system topology unchanged; this is a test-coverage and one-line comment refinement
- [x] New ADR — N/A, no architectural decision; review-feedback-driven test additions only

## Commit message

- [x] Conventional Commits format: `test(viewer): close coverage gaps in eventGuards predicate tests`
- [x] Body explains *why* — three predicates (memory_write, mode, trauma_active) routed but untested; NaN reject paths for tot_selected.chosen_value and tot_branch.complete.value were not exercised; duplicate body in unknown-event-name `it` removed; one-line allowlist comment on isToTSelectedData clarifies the prototype-pollution guard
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
