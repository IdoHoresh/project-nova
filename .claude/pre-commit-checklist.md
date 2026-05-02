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
> bracket (e.g. `- [x] /review — skipped, doc-only change`) and check
> the box. Silent skipping is forbidden.

## Branch + scope

- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — 147 lines, under the 500 threshold
- [x] Atomic commit — single logical change: workflow research findings encoded into project memory

## Verification

- [x] `git diff --cached` scanned for secrets — markdown only, none found
- [x] `nova-agent/` not touched — N/A
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config only (CLAUDE.md + .claude/rules/workflow.md) — N/A on test runs

## Review

- [x] `code-reviewer` subagent — N/A, docs-only change with no code logic
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the workflow-research lessons are encoded in CLAUDE.md instead
- [x] CLAUDE.md "Common gotchas" — N/A, this commit adds workflow guidance, not gotchas
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no Nova architectural decision; workflow guidance derived from external research

## Commit message

- [x] Conventional Commits format: `docs: encode workflow research findings into project memory`
- [x] Body explains *why* — research-driven gap closure (Plan Mode triggers, MCP inventory, phase signals, context hygiene)
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
