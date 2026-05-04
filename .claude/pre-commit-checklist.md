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
- [x] `git diff --cached --stat` reviewed — 2 files: `nova-agent/src/nova_agent/action/live_io.py` (add structlog warning), `nova-agent/tests/test_action_live_io.py` (+1 test pinning the warning)
- [x] Atomic commit — single fix: restore the perception.calibration_failed warning log lost in the LiveGameIO extraction

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` touched — yes; ran `uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`, all green (162 tests: 161 prior + 1 new IMP-1 regression test)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — none

## Review
- [x] `/review` dispatched — N/A: targeted single-file fix in response to code-quality review of cf105be (IMP-1). Layer 1.5 pre-push hook will re-pass on the new commit.
- [x] `code-reviewer` subagent — N/A, fix applied per existing reviewer's IMP-1 instructions
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; observation deferred to Task 7 sweep
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A

## Commit message
- [x] Conventional Commits format: `fix(action): restore perception.calibration_failed warning log in LiveGameIO`
- [x] Body explains *why* — see code-quality review of cf105be (IMP-1). The pre-refactor main.py logged a structured warning when CalibrationError fired; the LiveGameIO extraction silently dropped it. Restoring the warning preserves the operator-facing signal for silent OCR failures (gotcha #6).
- [x] Co-author tag present
