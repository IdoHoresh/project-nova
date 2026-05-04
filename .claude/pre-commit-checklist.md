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
- [x] `git diff --cached --stat` reviewed — 2 new files: `nova-agent/src/nova_agent/lab/render.py` (~50 lines: PALETTE table + render_board function), `nova-agent/tests/test_lab_render.py` (6 tests including a meta-test for LoC bound)
- [x] Atomic commit — single logical change: add brutalist 2048 board renderer

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` touched — yes; ran `uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`, all green (185 tests: 179 prior + 6 new render)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — none for this commit; ARCHITECTURE.md update bundled into Task 5

## Review
- [x] `/review` dispatched — N/A: relying on Layer 1.5 (auto pre-push Sonnet) per `.claude/rules/workflow.md` "Manual subagent dispatch policy"; pure-Python new module with TDD coverage including a drift-guard meta-test, no LLM/bus/secret/env paths touched
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; Task 7 collects any non-obvious surprises
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — DEFERRED to Task 5's commit
- [x] New ADR — N/A (ADR-0008 already covers the brutalist constraint)

## Commit message
- [x] Conventional Commits format: `feat(lab): add brutalist 2048 board renderer`
- [x] Body explains *why* — see ADR-0008 §Decision §2. Renderer is the second half of the SimGameIO surface (Task 4 wraps both); structural-identity-with-emulator-pipeline contract; meta-test enforces brutalist budget against drift.
- [x] Co-author tag present
