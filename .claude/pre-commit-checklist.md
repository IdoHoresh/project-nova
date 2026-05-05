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
- [x] `git diff --cached --stat` reviewed — 1 file: integration test polish (Should-fixes from code-quality review on cfde06f)
- [x] Atomic commit — single coherent unit: 3 Should-fixes on Task 7's integration test (import canonical MAX_MOVES, replace tautological assertion with progress assertions, use Scenario.seed(0) over .seed_base for runner-fidelity intent)

## Verification
- [x] `git diff --cached` scanned for secrets — no API keys / env values
- [x] `nova-agent/` — pytest 228 passing (15 baseline including integration), mypy strict + ruff clean
- [x] `nova-viewer/` — N/A: not touched
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: this IS the code-quality reviewer Should-fix follow-up (verbatim recommendations from upstream review per memory feedback_subagent_dispatch_selectivity "skip re-review on verbatim fixes")
- [x] `code-reviewer` subagent — N/A: this is the response to the prior code-quality review on cfde06f
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A this commit; brainstorm-process lessons may land in a follow-up sweep after the plan completes
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A

## Commit message
- [x] Conventional Commits format: `test(baseline): tighten integration assertions per code review`
- [x] Body explains why — code-quality reviewer Should-fixes on commit cfde06f; canonical MAX_MOVES import prevents drift, progress assertions catch silent-no-op regressions that the tautological loop-exit assertion missed, scenario.seed(0) matches runner intent
- [x] Co-author tag present
