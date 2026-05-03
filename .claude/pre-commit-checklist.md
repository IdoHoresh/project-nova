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
- [x] `git diff --cached --stat` reviewed — three new files: `.claude/skills/review/SKILL.md`, `.claude/skills/code-review/SKILL.md`, `.claude/skills/security-review/SKILL.md` (~200 lines total)
- [x] Atomic commit — single logical change: add /review orchestrator + /code-review and /security-review wrapper skills

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown skill-frontmatter only
- [x] `nova-agent/` not touched — N/A, Claude-tooling-only change
- [x] `nova-viewer/` not touched — N/A, Claude-tooling-only change
- [x] Docs / config — `.claude/skills/review/SKILL.md` orchestrator applies REVIEW.md path-matched trigger taxonomy and dispatches `/code-review` + `/security-review` in parallel when both fire; `/code-review` and `/security-review` are thin wrappers that read REVIEW.md + the matching `.claude/agents/*-reviewer.md` agent definition + LESSONS.md, then dispatch the subagent. Output format mirrors REVIEW.md: [BLOCK|WARN|NIT] file:line — desc + Suggestion + Confidence ≥80, plus APPROVE / REQUEST CHANGES verdict.

## Review

- [x] `code-reviewer` subagent — N/A per `/review` path-matched trigger taxonomy: this commit is Claude-tooling-only (`.claude/skills/**`), which is the "skip with reason: Claude-tooling-only" row of REVIEW.md. The skills themselves ARE the review machinery; reviewing them with themselves is circular.
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched in this commit

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the skills implement the rubric, no new lesson to record yet
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; CLAUDE.md will gain a `/review` reference in commit 3 (the workflow-wiring commit)
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition, not an architectural decision

## Commit message

- [x] Conventional Commits format: `feat(review): add /review, /code-review, /security-review slash skills`
- [x] Body explains *why* — operationalizes the REVIEW.md checklist shipped in commit 1; orchestrator skill removes the "did I review?" judgment by applying the REVIEW.md path-matched trigger taxonomy as a binary check; thin wrapper skills let the user invoke a focused pass directly when the orchestrator overhead isn't needed; commit 2 of 5 in the Gibor-pattern port queued in the resume-point memory for Week 0 Day 2
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
