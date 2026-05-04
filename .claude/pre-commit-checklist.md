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
- [x] `git diff --cached --stat` reviewed — 5 files: `nova-agent/src/nova_agent/llm/tiers.py` (add `plumbing` tier), `nova-agent/src/nova_agent/config.py` (add `tier: TierName | None` field), `nova-agent/src/nova_agent/main.py` (tier-aware model routing), `nova-agent/tests/test_llm_tiers.py` (2 plumbing tests), `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` (new ADR consolidating cost-tier discipline + schema-enforcement contract + record-replay rationale)
- [x] Atomic commit — single logical change: add `plumbing` cost-discipline tier, wire `NOVA_TIER` into main.py, document the whole decision in ADR-0006

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; tier name strings only
- [x] `nova-agent/` — gate trio green: 156/156 tests pass (added 2 plumbing-tier tests, retained all 154 prior including bus recorder/replayer + LLM schema-enforcement tests), mypy strict clean (46 source files), ruff clean
- [x] `nova-viewer/` not touched — N/A, agent + docs change
- [x] Docs / config — `tiers.py` adds `plumbing` (flash-lite everywhere, tot_branches=2) with explicit "SAFE only because every JSON callsite passes response_schema; NEVER for cognitive-judgment work" docstring. `config.py` adds `tier: TierName | None` field validated against the Literal at the pydantic-settings chokepoint per `.claude/rules/security.md`. `main.py` consults `s.tier`: when set, sets `os.environ["NOVA_TIER"]` from validated value and routes the 3 cognitive roles through `tiers.model_for(role)`; otherwise falls back to per-task `s.X_model` fields (backward-compatible). ADR-0006 documents the four tiers, the schema-enforcement contract, the record-replay design, and the explicit rejections (vcrpy, Ollama, batch-API-now) per the principal engineer's red team.

## Review

- [x] `/review` dispatched on staged diff — yes. Code-reviewer (Sonnet) + security-reviewer (Opus) dispatched in parallel per REVIEW.md path-matched trigger taxonomy (`nova-agent/**/llm/**` + `main.py` is the yes-yes row).
- [x] Code-reviewer verdict: **APPROVE** with 3 NIT.
  - **NIT config.py:46** `tier: str | None` loses Literal validation → fixed: now `tier: TierName | None`, validated at the pydantic-settings chokepoint
  - **NIT main.py:131** env round-trip inverts source-of-truth → deferred (would refactor `model_for(role, tier=...)` signature; out of scope for this commit, captured as future cleanup in ADR-0006 §Reversibility)
  - **NIT main.py:143-145** three asserts smell → deferred (smell points at TypedDict union return type — `tot_branches: int` while `decision/tot/reflection: str` — splitting `model_for(role) -> str` and `branches_for_tot() -> int` is the right cleanup; deferred until plumbing-tier branch-count tuning surfaces a need)
- [x] Security-reviewer verdict: **APPROVE**. All concerns LOW / NEGLIGIBLE: env write is benign tier-name string; unvalidated-input concern resolved by NIT-1 fix; no prompt-injection surface today (board state + own-process memory + Unity-fork screenshot — no untrusted user prompts cross the boundary; flagged for re-review when persona-driven multi-game arrives at Week 4+); LLM-output-as-control-flow path is bounded enums + typed coordinator API.
- [x] All BLOCKs addressed — there were no BLOCK findings.

## Documentation

- [x] LESSONS.md — N/A, the lesson is captured in ADR-0006; LESSONS.md cross-references the ADR (no separate entry needed for the decision artifact itself)
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; tier semantics live in `tiers.py` docstring and ADR-0006
- [x] ARCHITECTURE.md — N/A, no topology change; tier system is a configuration overlay on the existing model-routing code path
- [x] New ADR — yes, `docs/decisions/0006-cost-tier-discipline-and-record-replay.md` consolidates: the four-tier system (plumbing/dev/production/demo), the `response_schema` enforcement contract that makes plumbing safe, the record-and-replay design, and the explicit "what we are NOT doing" list (no vcrpy, no Ollama Week 0, no batch API yet, no auto-detection)

## Commit message

- [x] Conventional Commits format: `feat(llm): add plumbing tier and ADR-0006 wiring NOVA_TIER`
- [x] Body explains *why* — closes the cost-discipline loop opened by the principal engineer's red team. The recorder/replayer (commit a296ff1) saves UI-iteration cost by recording sessions to disk; the schema-enforcement extension (commit 07e7b9d) makes the cheap tier safe to use; THIS commit adds the cheap tier (plumbing = flash-lite everywhere) and the wiring that activates it via NOVA_TIER. ADR-0006 ties the three commits together and documents the rejected alternatives (vcrpy maintenance treadmill, Ollama Week-0 scope creep, batch-API-now-vs-Week-2) so future contributors don't re-derive the trade-offs.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
