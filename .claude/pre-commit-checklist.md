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
- [x] `git diff --cached --stat` reviewed — one new test file `nova-viewer/lib/__tests__/websocket.test.ts` (~85 LOC, 4 tests covering FakeWebSocket-driven validator path) plus this checklist; ~85 insertions / 0 deletions on the test file
- [x] Atomic commit — single logical change: "add useNovaSocket vitest coverage for the validator + rate-limited warn path"

## Verification

- [x] `git diff --cached` scanned for secrets — pure vitest test file with FakeWebSocket stub and JSON.stringify fixtures; no env / API keys / tokens / URLs
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (97/97, up from 93 with the four new tests), `npx tsc --noEmit` clean (test file uses imported types only), `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes; the new test self-documents via the same inline comments as the production hook

## Review

- [x] `code-reviewer` subagent — N/A, this is Task 5 of an in-flight plan; the plan-level review pass runs at Task 9 once the LESSONS update lands
- [x] `security-reviewer` — N/A by trigger, but worth noting: tests are pure unit tests with no network, no env, no IO; FakeWebSocket is in-memory only

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands in Task 9 per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; Task 5 just adds test coverage for behavior already implemented in Task 4

## Commit message

- [x] Conventional Commits format: `test(viewer): cover useNovaSocket validator + rate-limited warning`
- [x] Body explains *why* — Task 4 wired parseAgentEvent into useNovaSocket; this test locks in the four behaviors (valid frame stamped + appended, invalid frame dropped with one warn, repeated invalid frames rate-limited per event name, malformed JSON dropped without throwing) so future refactors of the hook can't regress silently
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
