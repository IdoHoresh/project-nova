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
- [x] `git diff --cached --stat` reviewed — three Claude-config files: `.claude/rules/workflow.md` (insert /review step + renumber), `CLAUDE.md` (replace 2 review-table rows with 4 covering /review, /code-review, /security-review, plus dedup the receiving-code-review row), `.claude/pre-commit-checklist.md` (this file — add /review binary line in Review section)
- [x] Atomic commit — single logical change: wire /review into workflow.md + pre-commit-checklist + CLAUDE.md so the new orchestrator is discoverable from every entry point

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown docs only
- [x] `nova-agent/` not touched — N/A, Claude-tooling-only change
- [x] `nova-viewer/` not touched — N/A, Claude-tooling-only change
- [x] Docs / config — workflow.md gains a new step 7 (`/review` invocation with REVIEW.md taxonomy reasons named) and renumbers existing steps 7-17 to 8-18; the after-commit step now classifies the auto pre-push hook as Layer 1.5 (between Layer 1 in-session /review and Layer 2 PR-time claude-code-action); CLAUDE.md "When to use which workflow skill" table replaces the two leaf-level reviewer rows with four rows covering /review (default), /code-review, /security-review, and receiving-code-review (de-duplicated against the existing leftover row).

## Review

- [x] `/review` dispatched on staged diff — N/A: Claude-tooling-only per REVIEW.md path-matched trigger taxonomy. This commit only touches `.claude/**` and `CLAUDE.md` (a doc / config file at repo root used by the Claude harness). The `/review` orchestrator itself ships in commit 2 and would skip this commit anyway.
- [x] `code-reviewer` subagent — N/A, covered by /review skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; CLAUDE.md is updated in THIS commit to expose /review in the workflow-skill table — that's the change, not a gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition, not an architectural decision

## Commit message

- [x] Conventional Commits format: `feat(workflow): wire /review into workflow.md, checklist, and CLAUDE.md`
- [x] Body explains *why* — completes the substrate→orchestrator→workflow chain. REVIEW.md (commit 1) is the rubric; /review and friends (commit 2) operationalize it; this commit makes them discoverable from every entry point Claude or a human will look at: workflow.md (step 7), CLAUDE.md (signal table), pre-commit-checklist (binary check). Layer 1 (in-session /review) + Layer 1.5 (auto pre-push hook) + Layer 2 (PR-time GH Action coming in commit 4) are now explicit in the workflow doc. Commit 3 of 5 in the Gibor-pattern port (Week 0 Day 2).
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
