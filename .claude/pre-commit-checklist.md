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
- [x] `git diff --cached --stat` reviewed — Scenario dataclass extension + caller migrations across 5 files
- [x] Atomic commit — single logical change: extend Scenario contract per scenarios spec §3

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` — pytest + mypy + ruff all green (200 passed, mypy clean, ruff clean)
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint
- [x] Docs / config — none touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy mechanical refactor; covered by 8 new validator tests + Layer 1.5 pre-push hook
- [x] `code-reviewer` subagent — N/A; orchestrator dispatches per skill review cycle
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths

## Documentation
- [x] LESSONS.md — N/A this commit
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; spec implements ADR-0007 at the dataclass layer

## Commit message
- [x] Conventional Commits format: `feat(lab): extend Scenario dataclass with cliff-test fields`
- [x] Body explains why — see commit body
- [x] Co-author tag present
