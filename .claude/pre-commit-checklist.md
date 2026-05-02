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
- [x] `git diff --cached --stat` reviewed — small CI-fix patch (~20 lines across `.github/workflows/ci.yml` + `nova-agent/src/nova_agent/decision/tot.py` + checklist), well under the 500 threshold
- [x] Atomic commit — single logical change: second-pass CI fixes after `d69e855` resolved 2 of 4 (viewer + security green now)

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/`: only a 4-line `ruff format` cosmetic break (line wrap on a `; ".join(...)` ternary in `tot.py`); no logic change. `uv run ruff format --check` is clean post-fix
- [x] `nova-viewer/` not touched — N/A, viewer + security jobs already green from `d69e855`
- [x] Docs / config — `.github/workflows/ci.yml` `pre-commit` job now sets `SKIP=eslint-viewer,tsc-viewer,prettier-viewer,claude-checklist-check` so the Python-only pre-commit runner doesn't try to invoke node-dependent hooks

## Review

- [x] `code-reviewer` subagent — N/A, CI-config + cosmetic ruff format change with no behavior risk
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, second-round CI plumbing fix
- [x] CLAUDE.md "Common gotchas" — N/A, the pre-commit-runner-has-no-node and dev-only-hook semantics are now self-explanatory in the workflow's `SKIP` env block
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision

## Commit message

- [x] Conventional Commits format: `ci: skip node-only pre-commit hooks + apply ruff format`
- [x] Body explains *why* — pre-commit runner is Python-only; eslint/tsc/prettier hooks need node_modules and would always fail there. Also commits the ruff format that the local hook would have applied if it had been run before pushing
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
