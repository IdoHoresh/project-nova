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
- [x] `git diff --cached --stat` reviewed — two files: `docs/decisions/0005-defer-v1-demo-until-phase-0.7.md` (new ADR, ~85 lines) and `docs/product/product-roadmap.md` (Week 0 section rewritten + Phase 0 exit criteria revised + Phase 0.7 gets a demo-gate note, ~30 lines net change)
- [x] Atomic commit — single logical change: defer the v1.0.0 demo recording, gate it on Phase 0.7 passing instead

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; product-strategy docs only
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` not touched — N/A, doc-only change
- [x] Docs / config — ADR-0005 follows the `0000-template.md` shape (Context / Decision / Alternatives considered / Consequences / References) and explicitly references ADR-0001, ADR-0002, ADR-0004, methodology.md §3, the roadmap Week 0 + Phase 0.7 sections, and competitive-landscape.md. Roadmap update strikes the demo-recording task from Week 0 + Phase 0 exit criteria, marks completed items, redirects Days 3–7 to early `Game2048Sim` work, adds a synthetic dry-run walk-through as the UX-forcing-function replacement, and notes the demo-gate change in Phase 0.7's section header.

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/**` is the "skip with reason: doc-only" row of REVIEW.md path-matched trigger taxonomy. Strategic / methodology docs are reviewed by the user, not by the code-quality rubric.
- [x] `code-reviewer` subagent — N/A, covered by /review skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, this is a roadmap pivot not an engineering lesson; the reasoning is in the ADR
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — yes, `docs/decisions/0005-defer-v1-demo-until-phase-0.7.md` is THIS commit; it captures the decision, alternatives considered, consequences, and reversibility per the `0000-template.md` shape

## Commit message

- [x] Conventional Commits format: `docs(roadmap): defer v1.0.0 demo until Phase 0.7 passes (ADR-0005)`
- [x] Body explains *why* — methodology rule "Don't sell before Phase 0.7 passes" combined with the pivot lock-in (Cognitive Audit & Prediction Platform vs nunu.ai) means recording a 2048-only demo now records the wrong artifact; deferral with a hard new gate (Phase 0.7 passing) avoids the "everything working" trap and produces a stronger demo when it does record. Days 3–7 of Week 0 reallocate to direct Phase 0.7 work — `Game2048Sim` build pulls forward, compressing the 30-day timeline by up to 4 days.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
