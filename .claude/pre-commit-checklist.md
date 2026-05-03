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
- [x] `git diff --cached --stat` reviewed — single file `LESSONS.md` (~25 lines added)
- [x] Atomic commit — single logical change: append a Workflow / process LESSONS.md entry covering the review-system port

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown narrative only
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` not touched — N/A, doc-only change
- [x] Docs / config — `LESSONS.md`: prepend a single entry to "Workflow / process learnings" section explaining the binary path-matched trigger pattern, the three-layer review model (Layer 1 in-session /review, Layer 1.5 pre-push hook, Layer 2 PR-time GH Action), and when to promote Layer 2 to a required check (future ADR, gated on ≥10 PRs of signal data)

## Review

- [x] `/review` dispatched on staged diff — N/A: doc-only change per REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by /review skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — this commit IS the LESSONS.md update; nothing further needed
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; the lesson is workflow-shaped not gotcha-shaped
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow lesson, not an architectural decision; the future "promote Layer 2 to required check" decision IS flagged in the lesson body as needing an ADR when it happens

## Commit message

- [x] Conventional Commits format: `docs(lessons): record the review-system port`
- [x] Body explains *why* — closes the 5-commit Gibor-pattern port for Week 0 Day 2 by capturing the underlying pattern (binary path-matched trigger > judgment-call review) so future contributors and Claude sessions don't have to re-derive it from the workflow.md / REVIEW.md / SKILL.md trio. Also documents the three-layer review model and the promotion-to-required-check ADR trigger.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
