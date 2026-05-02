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
- [x] `git diff --cached --stat` reviewed — types.ts (~15 lines net) + pre-commit-config.yaml hook prefix fix + this checklist; well under the 500 threshold
- [x] Atomic commit — single logical change is the AgentEvent catch-all removal; pre-commit-config.yaml fix is bundled because the broken eslint-viewer hook blocks the commit (path-prefix mismatch — pre-existing bug surfaced by first viewer commit since hook was added)

## Verification

- [x] `git diff --cached` scanned for secrets — TS interface + comment + bash hook edits, no env / API keys / tokens
- [x] `nova-agent/` not touched — N/A, viewer-only types change
- [x] `nova-viewer/` — only `lib/types.ts` modified; tsc clean (existing casts narrow compatibly post-discrimination so the expected error cascade did not materialise — flagged in Tasks 6/7 territory)
- [x] Docs / config — `.pre-commit-config.yaml` hook prefix-strip fix included to unblock the commit; covered in commit body

## Review

- [x] `code-reviewer` subagent — N/A, change is mechanical and matches the verbatim plan from Task 1; reviewer ran on the parent plan
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus surface touched; pure TS type narrowing

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson lands with Task 9 (final commit) per plan
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 is being actively resolved by this task chain; final removal note lands in Task 9
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, decision was already captured in the AgentEvent validator plan

## Commit message

- [x] Conventional Commits format: `refactor(viewer): drop AgentEvent catch-all, add tot_branch api_error arm`
- [x] Body explains *why* — catch-all silently hid the api_error branch shape that nova-agent's tot.py:166 has been publishing; removing it forces discriminated narrowing at every consumer
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
