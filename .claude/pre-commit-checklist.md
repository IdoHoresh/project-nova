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
- [x] `git diff --cached --stat` reviewed — 3 files: `nova-agent/src/nova_agent/lab/io.py` (~25 lines: SimGameIO adapter), `nova-agent/tests/test_lab_io.py` (3 tests), `nova-agent/src/nova_agent/main.py` (peel 2 now-unused `# type: ignore` comments for `lab.io` since the module now exists)
- [x] Atomic commit — single logical change: add SimGameIO adapter (the main.py peel is the mechanical follow-on the new module unblocks)

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` touched — yes; ran full check trio, all green (188 tests: 185 prior + 3 new; mypy strict clean; ruff clean)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — none for this commit; ARCHITECTURE.md update bundled into Task 5

## Review
- [x] `/review` dispatched — N/A: relying on Layer 1.5 (auto pre-push Sonnet) per `.claude/rules/workflow.md` "Manual subagent dispatch policy"; tiny adapter with TDD coverage, no LLM/bus/secret/env paths touched
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A on this commit; Task 7 collects any non-obvious surprises
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — DEFERRED to Task 5's commit
- [x] New ADR — N/A (ADR-0008 already covers the adapter)

## Commit message
- [x] Conventional Commits format: `feat(lab): add SimGameIO adapter`
- [x] Body explains *why* — wraps Game2048Sim + brutalist renderer behind the GameIO protocol; the seam from ADR-0008 + Task 1 now has its sim implementation. Task 5 wires it via Settings. main.py peel is the mechanical unblocking the new module enables.
- [x] Co-author tag present
