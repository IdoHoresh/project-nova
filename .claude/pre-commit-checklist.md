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
- [x] `git diff --cached --stat` reviewed — single new file `REVIEW.md` at repo root (~150 lines, project-specific review checklist + path-matched trigger taxonomy)
- [x] Atomic commit — single logical change: add Nova-specific REVIEW.md as the binary-decision review checklist

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown rules-doc only
- [x] `nova-agent/` not touched — N/A, repo-root doc only
- [x] `nova-viewer/` not touched — N/A, repo-root doc only
- [x] Docs / config — `REVIEW.md` adopts the structure from Gibor's review pattern, adapted to Nova: 4 block-on-violation sections (security, cognitive architecture invariants, bus contract, code quality with explicit path-matched trigger taxonomy), Python + TypeScript language-specific sections, testing section, output format spec ([BLOCK|WARN|NIT] file:line — desc + Suggestion + Confidence ≥80), verdict (APPROVE / REQUEST CHANGES), and an after-review loop pointing at LESSONS.md (uppercase per Nova convention).

## Review

- [x] `code-reviewer` subagent — N/A, doc-only addition; no executable logic. /review skill doesn't exist yet (this PR establishes the substrate; the skill ships in commit 2).
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, this commit IS the rubric that future LESSONS.md entries cross-reference; nothing to add here
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; CLAUDE.md will be updated to reference REVIEW.md when commit 3 wires it into the workflow
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition, not an architectural decision

## Commit message

- [x] Conventional Commits format: `feat(review): add REVIEW.md project-specific checklist`
- [x] Body explains *why* — adopts Gibor's review-pattern checklist structure (proven to remove the "did I review?" judgment call) and adapts it to Nova's two-reviewer split (code-reviewer + security-reviewer) and polyglot Python/TS shape; the path-matched trigger taxonomy makes review a yes/no on file paths, not a vibes call; this is commit 1 of the 5-commit Gibor-port queued in the resume-point memory for Week 0 Day 2
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
