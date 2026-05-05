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
- [x] `git diff --cached --stat` reviewed — 2 modified files: baseline.py (+35 lines retry impl) + test_decision_baseline.py (+68 lines 2 new retry tests + helper mock); well within 500-line limit
- [x] Atomic commit — single coherent unit: API-error retry loop (3x exponential backoff + TrialAborted) + 2 TDD tests

## Verification
- [x] `git diff --cached` scanned for secrets — only Python source and test code; no API keys, no env values, no secrets
- [x] `nova-agent/` — pytest 222 passing (was 213 prior + 9 baseline), mypy strict clean, ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — TDD implementation of approved plan Task 4 (docs/superpowers/plans/2026-05-05-baseline-bot.md); retry loop wraps existing self.llm.complete() call; no new architectural seams, no new bus paths, no secrets paths
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, Task 4 is isomorphic/mechanical TDD; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: no new LLM adapter, no env/secrets paths, no bus events; broad Exception catch is explicitly documented as a follow-up audit item in commit message

## Documentation
- [x] LESSONS.md — N/A: no new lesson from this task; retry pattern is straightforward async exponential backoff
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: ADR-0007 already covers the Baseline Bot design; retry policy is captured in spec §3.3

## Commit message
- [x] Conventional Commits format: `feat(baseline): add API-error retry loop (3x exponential backoff, then abort)`
- [x] Body explains why — wraps LLM.complete in _call_with_api_retry; broad Exception tuple documented as follow-up audit; spec ref §3.3
- [x] Co-author tag present
