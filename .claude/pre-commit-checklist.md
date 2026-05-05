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
- [x] `git diff --cached --stat` reviewed — 2 files: react.py (+14/-8), test_decision_react.py (+53/-0); well under 500-line threshold
- [x] Atomic commit — single coherent unit: make screenshot_b64 optional in ReactDecider + 3 tests (1 regression + 2 new text-only)

## Verification
- [x] `git diff --cached` scanned for secrets — no API keys, tokens, or env values; only type annotations and test assertions
- [x] `nova-agent/` — pytest 213 passed, mypy clean (no issues in 53 source files), ruff clean (all checks passed)
- [x] `nova-viewer/` — N/A: no TS files touched
- [x] Docs / config — N/A: no doc or config changes

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — this is a straightforward type-signature relaxation (str → str | None) with TDD coverage; no new architecture, no security surface
- [x] `code-reviewer` subagent — N/A: mechanical refactor per spec §5.1; covered by gate trio
- [x] `security-reviewer` — N/A: no LLM adapter changes, no env/bus/secrets paths touched; screenshot_b64 content is never logged or published

## Documentation
- [x] LESSONS.md — N/A this commit; no new lesson; the optional-screenshot pattern is straightforward
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha
- [x] ARCHITECTURE.md — N/A: no architectural change; signature relaxation only
- [x] New ADR — N/A: no load-bearing architectural decision; spec already exists at docs/superpowers/specs/2026-05-05-baseline-bot-design.md §5.1

## Commit message
- [x] Conventional Commits format: `refactor(react): make screenshot_b64 optional for Phase 0.7 text-only mode`
- [x] Body explains why — Game2048Sim produces no pixels; both Carla and Baseline Bot need text-only mode; production emulator path unchanged
- [x] Co-author tag present
