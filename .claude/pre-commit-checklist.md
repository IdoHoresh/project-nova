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
- [x] `git diff --cached --stat` reviewed — `nova-viewer/lib/stream/__tests__/fixtures.ts` (+ImportTypeAdd, +14 lines for the new fixture), `nova-viewer/lib/stream/__tests__/deriveStream.test.ts` (+1 fixture import, +14 lines for the new test) plus this checklist; small, additive
- [x] Atomic commit — single logical change: "add tot_branch.api_error fixture + deriveStream test that asserts the api_error variant collapses to parse_error in ToTBranchEntry"

## Verification

- [x] `git diff --cached` scanned for secrets — pure test additions; no env / API keys / tokens / URLs touched
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (98/98, +1 from the new test), `npx tsc --noEmit` clean (fixture returns the tightly-typed `{event:"tot_branch"; data: ToTBranchApiErrorData}` so the union narrowing is exercised end-to-end), `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes

## Review

- [x] `code-reviewer` subagent — N/A, this is Task 8 of an in-flight plan; the plan-level review pass runs at Task 9 alongside the LESSONS update
- [x] `security-reviewer` — N/A by trigger; test-only addition, no security surface touched

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands in Task 9 per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; Task 8 is regression coverage for Task 1 (union narrowing) and Task 6 (explicit api_error → parse_error collapse in `applyBranch`)

## Commit message

- [x] Conventional Commits format: `test(viewer): cover tot_branch api_error rendering`
- [x] Body explains *why* — nova-agent's `tot.py:166` emits `tot_branch.api_error` when an LLM call fails. The old `AgentEvent` catch-all silently dropped these into `unknown` so they never rendered as failed-branch cards. With Task 1's union narrowing + Task 6's explicit `applyBranch` collapse to `parse_error`, the api_error variant now renders alongside parse_error branches; this test pins that behavior so a regression in either spot fails fast.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
