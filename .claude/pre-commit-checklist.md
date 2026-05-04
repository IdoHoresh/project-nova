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
- [x] `git diff --cached --stat` reviewed — 3 files: `docs/product/methodology.md` (§4.1 Cliff Test rewritten with two-arm design), `docs/product/product-roadmap.md` (Week 1 tasks + gate criteria updated for Blind Control Group), `docs/decisions/0007-blind-control-group-for-cliff-test.md` (new ADR)
- [x] Atomic commit — single logical change: introduce a Blind Control Group (Baseline Bot) into the Phase 0.7 Cliff Test so the falsification criterion is "affect predicts cliff earlier than a non-affective baseline" rather than "Carla's Anxiety peaked before her game-over"

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; methodology + roadmap + ADR docs only
- [x] `nova-agent/` not touched — N/A, methodology + ADR-only change
- [x] `nova-viewer/` not touched — N/A, methodology + ADR-only change
- [x] Docs / config — methodology.md §4.1 now defines two arms (Casual Carla N=20 + Baseline Bot N=20 per scenario, same seeded sequences), the comparison metric `Δ = t_baseline_fails - t_carla_predicts`, two pass criteria (prediction-validity + affect-earns-its-keep), and three failure modes (both pass / single-arm pass / both fail) with the demoted "architecture-as-narrator" reposition path. roadmap.md Week 1 task list mirrors the two-arm split with explicit `NOVA_TIER=production` discipline (cliff test is forbidden from plumbing tier per ADR-0006). ADR-0007 documents the falsification gap that motivated the change, the Baseline Bot prompt verbatim, the alternatives considered (single-armed N=100, random-move control, ground-truth comparison, deferral), and the reversibility path.

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/**` is the "skip with reason: doc-only" row of REVIEW.md path-matched trigger taxonomy. Strategic / methodology docs are reviewed by the user, not by the code-quality rubric.
- [x] `code-reviewer` subagent — N/A, doc-only addition with no executable logic
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the methodology rationale is captured in ADR-0007 and §4.1; the lesson "single-armed tests of cognitive prediction are not falsifiable" is implicit in the ADR's Context section
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; CLAUDE.md "Active phase + next task" gets a separate refresh in commit 3 of tonight's plan
- [x] ARCHITECTURE.md — N/A, system topology unchanged; this is methodology, not code
- [x] New ADR — yes, `docs/decisions/0007-blind-control-group-for-cliff-test.md` follows the `0000-template.md` shape (Context / Decision / Alternatives considered / Consequences / References) and explicitly references ADR-0001, ADR-0002, ADR-0005, ADR-0006, methodology.md §4.1, roadmap Week 1, and competitive-landscape.md (nunu.ai counter-positioning)

## Commit message

- [x] Conventional Commits format: `docs(methodology): add Blind Control Group to Phase 0.7 cliff test (ADR-0007)`
- [x] Body explains *why* — principal engineer red-teamed the cliff test on 2026-05-04 and found a falsifiability gap: a single-armed test cannot distinguish "the cognitive architecture predicts" from "any agent fails at this threshold because the game's mechanics get harder past it." A non-affective Baseline Bot run on the same seeded sequences turns the comparison into the right shape: `Δ = t_baseline_fails - t_carla_predicts`. Cost is +300-500 games (<$50 at production tier), gain is the entire scientific validity of the demo gate Phase 0.7 must pass per ADR-0005.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
