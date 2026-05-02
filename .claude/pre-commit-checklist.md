# Pre-Commit Checklist

> Before EVERY commit, work through this list and check each item.
> The pre-commit framework runs `scripts/check-claude-checklist.sh`
> which **blocks the commit** if any item is left unchecked.
>
> After a successful commit, `scripts/reset-checklist.sh` runs at the
> post-commit stage and resets every box back to `[ ]` so the next
> commit starts fresh.
>
> If a step doesn't apply, write a one-sentence reason after the
> bracket (e.g. mark `[x]` and add `/review — skipped, doc-only change`)
> and check the box. Silent skipping is forbidden.

## Branch + scope

- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — ~346 lines (10 add to competitive-landscape.md + 336-line new casterai-deep-dive.md), under the 500 threshold
- [x] Atomic commit — single logical change: Alignment Day dossier update (CasterAI red-team flag → nunu.ai realistic competitor)

## Verification

- [x] `git diff --cached` scanned for secrets — only false-positive matches on "task-execution" and PlaytestCloud "video tokens" pricing copy
- [x] `nova-agent/` not touched — N/A, docs-only
- [x] `nova-viewer/` not touched — N/A, docs-only
- [x] Docs / config only (`docs/product/`) — N/A on test runs

## Review

- [x] `code-reviewer` subagent — N/A, docs-only change with no code logic
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, this commit IS the dossier update; the catch-all-hides-variants lesson lands with the AgentEvent validator commits, not here
- [x] CLAUDE.md "Common gotchas" — N/A, no new engineering gotcha; the competitive shift is captured in the dossier itself
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no Nova architectural decision; competitive-landscape update is product-strategy, not architecture

## Commit message

- [x] Conventional Commits format: `docs(product): replace CasterAI red-team flag with nunu.ai`
- [x] Body explains *why* — original CasterAI flag did not resolve to a real entity; nunu.ai is the realistic Goliath in vision-based game-agent QA, with counter-positioning around Nova's Product/UA buyer vs nunu's QA buyer
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
