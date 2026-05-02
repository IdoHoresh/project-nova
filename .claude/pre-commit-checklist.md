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
- [x] `git diff --cached --stat` reviewed — small CI-fix patch (~30 lines across `.github/workflows/ci.yml` + `nova-viewer/public/window.svg` + checklist), well under the 500 threshold
- [x] Atomic commit — single logical change: fix CI workflow failures surfaced by PR #1's first run

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` not touched in source — N/A, the `tesseract-ocr` apt step lands in `.github/workflows/ci.yml` only
- [x] `nova-viewer/` only the SVG trailing newline — eof-fixer auto-fixed; static asset only
- [x] Docs / config only (`.github/workflows/`) — N/A on test runs

## Review

- [x] `code-reviewer` subagent — N/A, CI-config + static-asset change with no executable logic
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the CI bumps are infra plumbing; no engineering insight worth capturing
- [x] CLAUDE.md "Common gotchas" — N/A, the pnpm-9-vs-10 quirk is captured implicitly by the workflow comment
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; standard infra fix

## Commit message

- [x] Conventional Commits format: `ci: fix workflow failures surfaced by PR #1 first run`
- [x] Body explains *why* — pnpm 9 vs 10 workspace-file parsing, missing tesseract on ubuntu-latest, broken cache step, SVG eof-newline; all four were pre-existing CI bugs that surfaced on the first nova-viewer-touching CI run since the workflow landed
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
