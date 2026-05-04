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
- [x] `git diff --cached --stat` reviewed — 1 modified file: `docs/superpowers/specs/2026-05-04-game2048sim-design.md` (2 small line edits — header + acceptance criterion #5 — flipping ADR-0008 from "to be written" to "Accepted, ref b743eef")
- [x] Atomic commit — single logical change: spec catches up to the now-existing ADR-0008 so a reader doesn't see contradictory deferred-vs-accepted statuses

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; 2-line markdown text edit only
- [x] `nova-agent/` not touched — N/A, doc-only edit
- [x] `nova-viewer/` not touched — N/A, doc-only edit
- [x] Docs / config — minimal text edit to keep the spec internally consistent with the just-merged ADR-0008. No structural change to the spec.

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/**` is the "skip with reason: doc-only" row of the REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, trivial cross-reference update
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A, this commit is the spec catching up to the just-landed ADR-0008 (b743eef)

## Commit message

- [x] Conventional Commits format: `docs(specs): point Game2048Sim spec at the now-Accepted ADR-0008`
- [x] Body explains *why* — ADR-0008 (b743eef) flipped from "to be written" to "Accepted". The spec previously said the ADR was deferred to "before implementation merges"; that's now stale. Two-line update keeps the spec internally consistent so readers don't see contradictory status statements.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
