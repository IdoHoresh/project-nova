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
- [x] `git diff --cached --stat` reviewed — third-pass CI fix; mostly mechanical pre-existing-file fixes (eof newlines on 5 SVGs + 1 plan + pyproject.toml; trailing whitespace on 2 docs/learn pages) plus the ruff-pre-commit hook version bump from 0.8.6 → 0.15.12
- [x] Atomic commit — single logical change: align repo state with what the pre-commit hooks would auto-fix on a `--all-files` run

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens (pure whitespace + eof + version-pin changes)
- [x] `nova-agent/`: only `pyproject.toml` eof newline; full `uv run pytest && uv run mypy && uv run ruff check && uv run ruff format --check` clean
- [x] `nova-viewer/` source not touched — only static asset SVGs in `public/` got eof newlines
- [x] Docs / config — `.pre-commit-config.yaml` ruff hook bumped to v0.15.12 to match local ruff 0.15.x; without this, the pre-commit-managed ruff (0.8.6) makes different formatting decisions than nova-agent's own ruff and CI re-flagged formatting that local check had cleared

## Review

- [x] `code-reviewer` subagent — N/A, mechanical whitespace + version-pin change with zero behavior risk
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, third-round CI plumbing fix
- [x] CLAUDE.md "Common gotchas" — N/A, the ruff-version-mismatch lesson is captured implicitly by the inline comment in `.pre-commit-config.yaml`
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision

## Commit message

- [x] Conventional Commits format: `ci: fix repo whitespace/eof + bump ruff-pre-commit to match local`
- [x] Body explains *why* — pre-commit `--all-files` on CI surfaced 8 pre-existing files with missing eof newlines or trailing whitespace; ruff-pre-commit at v0.8.6 disagreed with the project's pinned ruff 0.15.x on formatting; both were artifacts of CI never having exercised `--all-files` on this repo before
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
