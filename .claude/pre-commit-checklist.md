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
- [x] `git diff --cached --stat` reviewed — 1 file: test_decision_baseline.py (+55 lines, integration test only)
- [x] Atomic commit — single coherent unit: Task 7 integration test (Bot + Game2048Sim full trial)

## Verification
- [x] `git diff --cached` scanned for secrets — test-only addition; no secrets, keys, tokens, or env values
- [x] `nova-agent/` — pytest 228 passing (15 baseline, +1 integration), mypy strict + ruff clean
- [x] `nova-viewer/` — N/A: no viewer files touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: test-only change, mechanical Task 7 spec implementation; Layer 1.5 hook covers at push
- [x] `code-reviewer` subagent — N/A: single test file addition, gate trio green
- [x] `security-reviewer` — N/A: test file only, no new secrets surface

## Documentation
- [x] LESSONS.md — N/A: no new lesson; Baseline Bot lessons already captured in prior commits
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha
- [x] ARCHITECTURE.md — N/A: test-only change
- [x] New ADR — N/A: no architectural decision; test validates existing contract

## Commit message
- [x] Conventional Commits format: `test(baseline): integration test — Bot + Game2048Sim full trial`
- [x] Body explains why — validates BaselineDecider/sim contract end-to-end without production-tier LLM cost; cycling mock covers all four directions; real cliff-test execution lives in Test Runner (gated by ADR-0006)
- [x] Co-author tag present
