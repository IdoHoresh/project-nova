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
- [x] `git diff --cached --stat` reviewed — single-file change to `nova-viewer/lib/websocket.ts` (~30 LOC net additions: parseAgentEvent import, seenInvalidEventsRef, JSON.parse + schema-validation pipeline) plus this checklist; ~35 insertions / 6 deletions
- [x] Atomic commit — single logical change is "wire parseAgentEvent into useNovaSocket so invalid bus frames are dropped with rate-limited warn"

## Verification

- [x] `git diff --cached` scanned for secrets — pure TS hook refactor + console.warn formatting; no env / API keys / tokens / URLs
- [x] `nova-agent/` not touched — N/A, viewer-only change
- [x] `nova-viewer/` — `pnpm test` green (93/93, no test files touched in this commit), `npx tsc --noEmit` clean, `pnpm run lint` zero warnings
- [x] Docs / config — N/A, no config / docs changes; the new behavior is self-documented via inline comments in the new ws.onmessage block

## Review

- [x] `code-reviewer` subagent — N/A, this is Task 4 of an in-flight plan; the plan-level review pass runs at Task 9 once useNovaSocket + its tests + LESSONS update have all landed
- [x] `security-reviewer` — N/A by trigger, but worth noting: this commit *tightens* bus-surface security (every inbound frame is now schema-validated before being committed to React state) and adds a rate-limited console.warn that intentionally only logs the event name + raw object, with no secrets path

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands in Task 9 per the plan's "documentation lands at the wrap" convention
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 will be flipped to "resolved" in Task 9 once the full validator path is consumer-tested
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; Task 4 implements the design already locked in by Task 1's type cleanup

## Commit message

- [x] Conventional Commits format: `refactor(viewer): validate AgentEvent frames in useNovaSocket`
- [x] Body explains *why* — every parsed bus frame now flows through parseAgentEvent before reaching React state; invalid frames are dropped silently except for one rate-limited console.warn per event name (via useRef'd Set, persists per mount, no leak)
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
