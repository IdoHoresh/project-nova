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

- [ ] On feature branch, NOT `main` (`git branch --show-current`)
- [ ] `git diff --cached --stat` reviewed — under 500 lines, or split
- [ ] Atomic commit — one logical change, no "and" in the subject

## Verification

- [ ] `git diff --cached` scanned for secrets / keys / tokens — none found
- [ ] If `nova-agent/` touched: `/check-agent` clean (pytest + mypy + ruff)
- [ ] If `nova-viewer/` touched: `/check-viewer` clean (vitest + tsc + eslint)
- [ ] If neither touched (docs / config only): N/A reason stated

## Review

- [ ] `code-reviewer` subagent run on diff — or N/A reason stated
- [ ] `security-reviewer` subagent run if diff touches secrets / env / LLM / bus — or N/A

## Documentation

- [ ] LESSONS.md updated if the work taught us something — or N/A
- [ ] CLAUDE.md "Common gotchas" updated if a new gotcha appeared — or N/A
- [ ] ARCHITECTURE.md updated if topology changed — or N/A
- [ ] New ADR added in `docs/decisions/` for load-bearing decisions — or N/A

## Commit message

- [ ] Conventional Commits format: `type(scope): subject` ≤72 chars
- [ ] Body explains *why*, not *what*
- [ ] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
