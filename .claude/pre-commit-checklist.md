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
- [x] `git diff --cached --stat` reviewed — 1 new file: `docs/superpowers/specs/2026-05-04-game2048sim-design.md` (~565 lines, brainstorm spec for `Game2048Sim` Phase 0.7 cliff-test infrastructure)
- [x] Atomic commit — single logical change: spec doc for `Game2048Sim` per superpowers brainstorming skill output. Successor artifacts (writing-plans implementation plan, ADR-0008, code) ship in separate commits.

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; pure brainstorm-design markdown referencing existing env var NAMES (`NOVA_IO_SOURCE`, `NOVA_SIM_SCENARIO`) and palette hex colors only
- [x] `nova-agent/` not touched — N/A, doc-only spec; implementation lands in a separate plan-driven commit chain
- [x] `nova-viewer/` not touched — N/A, doc-only spec; cognitive layer doesn't change with this design
- [x] Docs / config — `docs/superpowers/specs/2026-05-04-game2048sim-design.md` follows the same shape as the prior spec at `docs/superpowers/specs/2026-05-02-thinking-stream-design.md` (date prefix, status, owner, goals, non-goals, architecture, components, test plan, acceptance criteria, risk register). Self-reviewed for placeholders, internal consistency, scope, and ambiguity per brainstorming skill checklist.

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/**` is the "skip with reason: doc-only" row of the REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above. The spec describes future code; that code's review happens when it lands.
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched (paths are described in the spec but no implementation is committed here)

## Documentation

- [x] LESSONS.md — N/A on this commit; lessons get added during/after implementation if non-obvious surprises surface
- [x] CLAUDE.md "Common gotchas" — N/A, no setup-time environment gotcha; the spec's own risk register captures implementation-time risks
- [x] ARCHITECTURE.md — N/A on this commit; the new `GameIO` protocol abstraction is design-only here. ARCHITECTURE.md update lands with the implementation PR.
- [x] New ADR — DEFERRED: ADR-0008 (`GameIO` abstraction + brutalist renderer rationale) is explicitly required per the spec's acceptance criteria #5, to be authored before the implementation PR merges. Not on this commit because the spec is the WHAT-and-WHY artifact; the ADR is the formal architectural-decision record that the implementation chain will reference.

## Commit message

- [x] Conventional Commits format: `docs(specs): add Game2048Sim brainstorm design spec`
- [x] Body explains *why* — Phase 0.7 cliff test (per ADR-0007) needs deterministic, OCR-and-emulator-free game I/O so both Carla and Baseline Bot consume byte-identical seeded scenarios. ADR-0005 deferred the v1.0.0 demo and reallocated Week 0 Days 3-4 to early `Game2048Sim` build. Spec pins: `GameIO` protocol abstraction (the seam that lets sim land cleanly without branching `main.py`), `Game2048Sim` engine (4 canonical merge edge cases pinned in tests), brutalist renderer (400×400 PNG, ~30 LoC, structural-identity-not-pixel-perfect), `Scenario` dataclass + library, deterministic-seed contract with explicit "same seed ≠ identical games" caveat, ~31 new tests (TDD-first), acceptance criteria. ADR-0008 to be written before implementation merges.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
