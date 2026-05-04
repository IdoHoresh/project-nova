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
- [x] `git diff --cached --stat` reviewed — 4 files: 2 new (`nova-agent/src/nova_agent/action/{game_io,live_io}.py`), 1 modified (`nova-agent/src/nova_agent/main.py` — extracts inline I/O block + loop calls into the LiveGameIO adapter), 1 new test (`nova-agent/tests/test_action_live_io.py` — 5 tests)
- [x] Atomic commit — single logical change: introduce GameIO protocol + LiveGameIO refactor; no behavioural change to the live path

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` touched — yes; ran `uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`, all green (161 tests total: 156 existing + 5 new LiveGameIO)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — none for this commit; ARCHITECTURE.md update bundled into Task 5's commit

## Review
- [x] `/review` dispatched — N/A: relying on Layer 1.5 (auto pre-push Sonnet) per `.claude/rules/workflow.md` "Manual subagent dispatch policy"; this is a behavioural-equivalent refactor with full test coverage, not an ADR-worthy or architecturally novel diff
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; Task 7 collects any non-obvious surprises
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — DEFERRED to Task 5's commit (single update once the full GameIO + sim wiring lands)
- [x] New ADR — N/A (ADR-0008 already covers this seam)

## Commit message
- [x] Conventional Commits format: `feat(action): add GameIO protocol + LiveGameIO refactor`
- [x] Body explains *why* — see ADR-0008. The seam needs to land before SimGameIO can plug in (Task 4). Behavioural-equivalent extraction; same Capture+OCR+ADB calls in the same order, plus an explicit screenshot cache invalidated on apply_move so the loop never feeds a pre-move screenshot to the post-move VLM prompt.
- [x] Co-author tag present
