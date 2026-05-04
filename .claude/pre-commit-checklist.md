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
- [x] `git diff --cached --stat` reviewed — 4 files: `nova-agent/src/nova_agent/lab/__init__.py` (empty), `nova-agent/src/nova_agent/lab/sim.py` (Game2048Sim + Scenario), `nova-agent/tests/test_lab_sim.py` (17 tests), `nova-agent/src/nova_agent/main.py` (drop now-stale `# type: ignore[import-untyped]` on the lab.sim import — Task 1 added it as temporary, Task 2 makes it real)
- [x] Atomic commit — single logical change: add Game2048Sim engine with seeded RNG and the 4 canonical merge edge cases (the main.py 1-line change is a forced consequence of the new module resolving an import previously gated by `# type: ignore`)

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` touched — yes; ran `uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`, all green (179 tests: 162 prior + 17 new sim)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — none for this commit; ARCHITECTURE.md update bundled into Task 5

## Review
- [x] `/review` dispatched — N/A: relying on Layer 1.5 (auto pre-push Sonnet) per `.claude/rules/workflow.md` "Manual subagent dispatch policy"; pure-Python new module with TDD coverage of all 4 edge cases, no LLM/bus/secret/env paths touched
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; Task 7 collects any non-obvious surprises (one candidate: rotation-direction sign for swipe-LEFT-canonicalization is easy to flip, caught by the UP/DOWN merge tests)
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — DEFERRED to Task 5's commit
- [x] New ADR — N/A (ADR-0008 already covers this engine's existence + design choices)

## Commit message
- [x] Conventional Commits format: `feat(lab): add Game2048Sim engine with seeded RNG and the 4 canonical merges`
- [x] Body explains *why* — see ADR-0008 + spec §Game2048Sim. Engine + Scenario dataclass land before SimGameIO (Task 4) so the adapter has something to wrap.
- [x] Co-author tag present
