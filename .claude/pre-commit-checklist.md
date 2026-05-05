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
- [x] `git diff --cached --stat` reviewed — 2 new files: baseline.py (~95 lines) + test_decision_baseline.py (~69 lines); well within 500-line limit
- [x] Atomic commit — single coherent unit: baseline module skeleton (types, constants, system prompt, stub decider)

## Verification
- [x] `git diff --cached` scanned for secrets — only Python source and test code; no API keys, no env values
- [x] `nova-agent/` — pytest 219 passing (was 213 + 6 new), mypy strict clean, ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: mechanical` — TDD skeleton task per approved plan (docs/superpowers/plans/2026-05-05-baseline-bot.md Task 2); no new architectural seams, no LLM/bus/secrets paths, purely structural types + stub
- [x] `code-reviewer` subagent — N/A: per manual-dispatch policy, Task 2 is isomorphic/mechanical; Layer 1.5 pre-push hook covers at push time
- [x] `security-reviewer` — N/A: no secrets / env / LLM call paths / bus paths touched in this commit (decide() raises NotImplementedError)

## Documentation
- [x] LESSONS.md — N/A: no new lesson from this task
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A: ADR-0007 already covers the Baseline Bot design

## Commit message
- [x] Conventional Commits format: `feat(baseline): add module skeleton — types, constants, system prompt`
- [x] Body explains why — skeleton ships BotDecision/TrialAborted/AbortReason types + constants + BASELINE_SYSTEM_PROMPT so subsequent Tasks 3-6 can build the decide() implementation incrementally without interface churn
- [x] Co-author tag present
