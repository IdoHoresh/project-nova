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
- [x] `git diff --cached --stat` reviewed — three small viewer-source touch-ups (`nova-viewer/lib/websocket.ts`, `nova-viewer/lib/stream/deriveStream.ts`, `nova-viewer/lib/eventGuards.ts`) plus this checklist; comment + identifier rename only, no behavior change
- [x] Atomic commit — single logical change: "apply review followups across validator chain (websocket comment + array-edge guard, drop misleading `_prevAffect` underscore, augment applyBranch parse/api_error collapse comment, confirm prototype-pollution allowlist comment)"

## Verification

- [x] `git diff --cached` scanned for secrets — comment edits + a local-variable rename + an `!Array.isArray` guard; no env / API keys / tokens / URLs touched
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (98/98, no test files modified), `npx tsc --noEmit` clean (rename is local to `deriveStream` body and tests reference the public `DeriveOptions.prevAffect` field which is unchanged), `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes

## Review

- [x] `code-reviewer` subagent — N/A, this commit applies deferred LOW-severity findings from prior `code-reviewer` passes on Task 4 + Task 6
- [x] `security-reviewer` — N/A by trigger; the array-edge guard tightens an already-validated path, and the prototype-pollution comment confirms an existing allowlist guard

## Documentation

- [x] LESSONS.md — N/A, no new lesson; the meta-lesson about review followups lands in Task 9
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 stays open until the catch-all is fully removed in a later commit
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; this is a cleanup pass over Tasks 4 + 6

## Commit message

- [x] Conventional Commits format: `refactor(viewer): apply review followups across validator chain`
- [x] Body explains *why* — the sentence-fragment comment in `websocket.ts` was unclear about what condition fires the warn; the `evName` extraction relied on `"event" in raw` to save it from arrays passing `typeof === "object"` and an explicit `!Array.isArray` makes the guard read correctly; `_prevAffect` carried a "deliberately unused" underscore even though it IS used by `initThresholdState`; the `applyBranch` parse/api_error collapse comment now points future work at `lib/stream/types.ts ToTBranchEntry.status` widening so the handoff is mechanical; the `branch_values` allowlist comment was double-checked against the security-reviewer LOW finding from the original plan.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
