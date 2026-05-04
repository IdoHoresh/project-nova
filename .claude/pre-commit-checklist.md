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
- [x] `git diff --cached --stat` reviewed — 1 new file: `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` (~165 lines, ADR documenting the GameIO protocol abstraction + brutalist renderer rationale that the Game2048Sim spec depends on)
- [x] Atomic commit — single logical change: ADR-0008 captures two coupled architectural commitments (GameIO seam + brutalist renderer policy) per the ADR template + red-team correction that ADRs must be written BEFORE implementation, not post-hoc

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; pure ADR markdown referencing existing ADR-0005/0006/0007 + spec at docs/superpowers/specs/2026-05-04-game2048sim-design.md
- [x] `nova-agent/` not touched — N/A, ADR is decision-record-only; implementation lands in a separate plan-driven commit chain
- [x] `nova-viewer/` not touched — N/A, cognitive layer + viewer don't change with this ADR
- [x] Docs / config — `docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md` follows the existing ADR template at `docs/decisions/0000-template.md` with the Status/Date/Deciders header, Context, Decision, Alternatives considered (6 options), Consequences (positive/negative/neutral/reversibility), and References sections. Mirrors the depth of ADR-0007 (the most recent multi-decision ADR).

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/decisions/**` (subset of `docs/**`) is the "skip with reason: doc-only" row of the REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above. The ADR documents future code; that code's review happens when it lands.
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. ADR mentions LLM payload structure (PNG-bytes-base64) at the architectural level only; no credentials or sensitive surfaces.

## Documentation

- [x] LESSONS.md — N/A on this commit; the ADR IS the architectural decision record. Lessons get added during/after implementation if non-obvious surprises surface.
- [x] CLAUDE.md "Common gotchas" — N/A, no setup-time environment gotcha; the ADR's own consequences section captures expected behavior.
- [x] ARCHITECTURE.md — N/A on this commit; the new GameIO protocol is documented in the ADR and the spec. ARCHITECTURE.md update lands with the implementation PR.
- [x] New ADR — THIS commit IS the new ADR. Companion to the spec at docs/superpowers/specs/2026-05-04-game2048sim-design.md committed in 1001be5.

## Commit message

- [x] Conventional Commits format: `docs(decisions): add ADR-0008 — GameIO abstraction + brutalist renderer`
- [x] Body explains *why* — Phase 0.7 cliff test (per ADR-0007) requires byte-identical seeded scenarios both arms can consume; live emulator pipeline can't deliver that. ADR-0008 documents the two coupled architectural commitments that make the sim land cleanly: GameIO protocol as the only acceptable seam (alternatives rejected: branched main, env-polymorphic Capture, image-drop, pixel-faithful render, finer-grained protocols, parallel bus path) + brutalist renderer to keep the prompt template a controlled variable across Week-0 calibration and Phase-0.7 cliff test. Written BEFORE the implementation plan per the discipline that ADRs lose value when written post-hoc.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
