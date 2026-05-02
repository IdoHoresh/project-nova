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
- [x] `git diff --cached --stat` reviewed — small docs patch (~50 lines), well under the 500 threshold
- [x] Atomic commit — single logical change: apply code-reviewer findings to the AgentEvent validator plan

## Verification

- [x] `git diff --cached` scanned for secrets — markdown only, no env values / API keys / tokens
- [x] `nova-agent/` not touched — N/A, plan-only patch
- [x] `nova-viewer/` not touched — N/A, plan-only patch (the implementation lands when execution starts)
- [x] Docs / config only (`docs/superpowers/plans/`) — N/A on test runs

## Review

- [x] `code-reviewer` subagent — THIS COMMIT applies its findings; running it again would be circular
- [x] `security-reviewer` — already ran on the original plan (commit cc26a31), 3 LOW items deliberately deferred to implementation PR

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson still lands with execution Task 9, not here
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 unchanged
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no decision change; this is artifact correction

## Commit message

- [x] Conventional Commits format: `docs(plan): apply code-reviewer findings to AgentEvent validator plan`
- [x] Body explains *why* — fixes 2 BLOCKING + 3 MEDIUM + 2 LOW issues a future worker would hit; avoids carrying a stack of override notes into the subagent-driven execution
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
