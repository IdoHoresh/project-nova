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
- [x] `git diff --cached --stat` reviewed — 1301 lines, single new file (the implementation plan); over the 500 threshold but unsplittable as one logical artifact
- [x] Atomic commit — single logical change: AgentEvent runtime validator implementation plan

## Verification

- [x] `git diff --cached` scanned for secrets — markdown only, no env values / API keys / tokens
- [x] `nova-agent/` not touched — N/A, plan only describes future viewer-side changes
- [x] `nova-viewer/` not touched — N/A, plan only describes future viewer-side changes
- [x] Docs / config only (`docs/superpowers/plans/`) — N/A on test runs

## Review

- [x] `code-reviewer` subagent — N/A, no code in this commit; the plan itself self-reviewed against the spec inside the document
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the catch-all-hides-variants lesson is added by Task 9 of the plan itself when execution lands, not here
- [x] CLAUDE.md "Common gotchas" — N/A, the gotcha #9 entry already references this work as scheduled for Week 0 Day 1; updating it lands with execution, not the plan
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is an implementation plan, not an architectural decision; the underlying decision (typed bus contract) is implicit in nova-viewer/AGENTS.md "Bus contract" rule

## Commit message

- [x] Conventional Commits format: `docs(plan): add AgentEvent runtime validator plan`
- [x] Body explains *why* — locks the design before code; surfaces a real bug (tot_branch.api_error missing from union) discovered during planning
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
