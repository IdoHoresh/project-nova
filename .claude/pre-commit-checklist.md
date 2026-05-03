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
- [x] `git diff --cached --stat` reviewed — single new file `.github/workflows/claude-review.yml` (~85 lines, advisory PR-time review workflow)
- [x] Atomic commit — single logical change: add Layer 2 claude-code-action GitHub workflow for PR-time advisory review

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; workflow references `${{ secrets.ANTHROPIC_API_KEY }}` (an indirection, not a literal)
- [x] `nova-agent/` not touched — N/A, CI-config-only change
- [x] `nova-viewer/` not touched — N/A, CI-config-only change
- [x] Docs / config — `.github/workflows/claude-review.yml` triggers on `pull_request: [opened, synchronize, reopened]`, skips drafts, runs `anthropics/claude-code-action@v1` against the PR diff with a prompt that dispatches the same `/review` orchestrator logic. Advisory only — not a required check until ≥10 PRs of signal data exist. Uses Sonnet because Layer 1.5 (pre-push hook) already runs Haiku; Layer 2's job is the deeper pass.

## Review

- [x] `/review` dispatched on staged diff — N/A: `.github/workflows/**` is the "skip with reason: CI-config-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by /review skip reason above
- [x] `security-reviewer` — N/A, no executable code; the workflow references one secret (ANTHROPIC_API_KEY) by name only — the actual value lives in GitHub Actions secrets and is never in the tracked file

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; final commit (5/5) appends a single LESSONS.md entry covering the full review-system port
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; the three-layer review model is documented in workflow.md and the SKILL.md files
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition that can be removed by deleting one file; not a load-bearing architectural decision

## Commit message

- [x] Conventional Commits format: `ci: add claude-code-action for PR-time advisory review`
- [x] Body explains *why* — adds the third and final layer of the review system. Layer 1 = in-session /review (manual, hot context). Layer 1.5 = pre-push hook (Haiku, auto, fast). Layer 2 (this commit) = PR-time GitHub Action (Sonnet, advisory comments, deeper pass against full PR diff). Each layer catches a different failure mode; together they remove the "I forgot to dispatch the reviewer" trap that bit PR #1. Setup requires ANTHROPIC_API_KEY repo secret — documented inline. Commit 4 of 5 in the Gibor-pattern port (Week 0 Day 2). Commit 5 records the lesson.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
