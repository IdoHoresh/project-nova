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
- [x] `git diff --cached --stat` reviewed — single-byte fix to `nova-agent/pyproject.toml` + checklist
- [x] Atomic commit — single logical change: strip extra trailing newline from pyproject.toml that survived 907f189's eof-fixer pass

## Verification

- [x] `git diff --cached` scanned for secrets — no env / API keys / tokens
- [x] `nova-agent/`: only the trailing-newline byte; full check trio still clean (no logic touched)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — N/A; this is the byte that pre-commit's end-of-file-fixer hook objects to (file ended with TWO `\n`, the hook wants exactly one)

## Review

- [x] `code-reviewer` subagent — N/A, single trailing-byte fix
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, mechanical follow-up to 907f189
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A

## Commit message

- [x] Conventional Commits format: `ci: strip extra trailing newline from nova-agent/pyproject.toml`
- [x] Body explains *why* — 907f189's eof script appended a newline only when missing; pyproject.toml already had one but had a SECOND blank line after it, which end-of-file-fixer rejects. Truncate any trailing `\n+` and rewrite with a single `\n`
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
