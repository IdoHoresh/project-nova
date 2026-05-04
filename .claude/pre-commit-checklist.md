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
- [x] `git diff --cached --stat` reviewed — 6 files: 1 new (`nova-agent/src/nova_agent/lab/scenarios.py`), 4 modified (`nova-agent/src/nova_agent/config.py` adds 2 fields, `nova-agent/src/nova_agent/main.py` peels final `lab.scenarios` ignore + drops getattr shim, `nova-agent/tests/test_lab_sim.py` appends 2 scenario tests, `ARCHITECTURE.md` adds GameIO seam paragraph), 1 new test (`nova-agent/tests/test_main_build_io.py`)
- [x] Atomic commit — single logical change: ship the scenario library, light up Settings.io_source, wire SimGameIO into main via _build_io, document the seam

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens (the test placeholders use literal "x" * 8)
- [x] `nova-agent/` touched — yes; ran full check trio, all green (192 tests: 188 prior + 4 new)
- [x] `nova-viewer/` not touched — N/A
- [x] Docs / config — ARCHITECTURE.md updated with GameIO seam paragraph; config.py adds 2 env-driven fields

## Review
- [x] `/review` dispatched — N/A: relying on Layer 1.5 (auto pre-push Sonnet) per `.claude/rules/workflow.md` "Manual subagent dispatch policy"; closes the architectural unit started in Task 1, all subsystems land with TDD coverage, ARCHITECTURE.md update is the planned doc shipment
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched (the 2 new env-vars are NOVA_IO_SOURCE and NOVA_SIM_SCENARIO; both have safe defaults and pydantic-Literal validation)

## Documentation
- [x] LESSONS.md — N/A on this commit; Task 7 collects any non-obvious surprises from Tasks 1-6
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — UPDATED in this commit with GameIO seam paragraph (replaces the deferred placeholder from Tasks 1-4 checklists)
- [x] New ADR — N/A (ADR-0008 already covers this seam)

## Commit message
- [x] Conventional Commits format: `feat(lab): wire SimGameIO into main via Settings.io_source`
- [x] Body explains *why* — closes the GameIO seam started in Task 1 and built across Tasks 2-4. Settings.io_source flips between LiveGameIO and SimGameIO; defaults preserve current behaviour. Scenario library starts with fresh-start only; the 3-5 hard cliff-test scenarios are a Phase 0.7 prep follow-up spec. ARCHITECTURE.md gains a paragraph on the seam.
- [x] Co-author tag present
