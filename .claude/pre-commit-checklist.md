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
- [x] `git diff --cached --stat` reviewed — single file `CLAUDE.md` (Active phase + next task section rewritten, ~50 lines net)
- [x] Atomic commit — single logical change: refresh CLAUDE.md "Active phase + next task" so Claude's auto-load reflects post-Day-2 state (not the 2026-05-02 stale prompt about CasterAI research and v1.0.0 demo prep that's been overtaken by 10 commits and 3 ADRs)

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; CLAUDE.md doc only
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` not touched — N/A, doc-only change
- [x] Docs / config — CLAUDE.md "Active phase + next task" section now reflects: (a) Week 0 Day 2 done with 10 commits shipped today, (b) the ADR-0005 demo deferral and the Week 0 Days 3-7 reallocation to early `Game2048Sim` build, (c) the full list of today's deliverables (review-system port, pre-push hook, dependabot fixes, record-replay, schema enforcement, plumbing tier + ADR-0006, Blind Control Group + ADR-0007, Phase 1/5 roadmap additions), (d) the four next-session tasks (live 50-move + dry-run + /review + start Game2048Sim), (e) the two one-time setup items (`/hooks` reload + `ANTHROPIC_API_KEY` repo secret). The CasterAI prompt is gone (already shipped via PR #1's nunu.ai pivot); the v1.0.0 demo prep is gone (deferred per ADR-0005).

## Review

- [x] `/review` dispatched on staged diff — N/A: `CLAUDE.md` is at repo root but is a Claude-tooling configuration file; per REVIEW.md path-matched trigger taxonomy this falls under "Claude-tooling-only" (the same row that exempts `.claude/**`). Strategic / methodology / operator-facing prose docs are reviewed by the user, not by the code-quality rubric.
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; this commit IS a documentation-currency update, not a lesson
- [x] CLAUDE.md "Common gotchas" — N/A, untouched in this commit; the Active-phase rewrite is the change
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a documentation-currency update; the underlying decisions live in ADR-0005 / ADR-0006 / ADR-0007

## Commit message

- [x] Conventional Commits format: `docs(claude): refresh Active phase + next task to reflect post-Day-2 state`
- [x] Body explains *why* — Claude auto-loads CLAUDE.md on every session start. The previous "Active phase" section was timestamped 2026-05-02 and pointed at first-task work that has since shipped (CasterAI/nunu.ai research) or been deferred (v1.0.0 demo). Stale auto-loaded context is worse than none — it would point a future session at completed work and miss the current next-task list. This commit updates the section to reflect today's actual state and the four-item next-session task list per the revised Week 0 plan.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
