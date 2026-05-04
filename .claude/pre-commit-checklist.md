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
- [x] `git diff --cached --stat` reviewed — single file `.claude/rules/workflow.md` (~70 lines added: new "PR cadence" section between After-commit and Periodic)
- [x] Atomic commit — single logical change: codify the "one PR per coherent unit of work" rule in workflow.md so the cadence is part of the auto-loaded contract, not implicit conversation knowledge

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown rules-doc only
- [x] `nova-agent/` not touched — N/A, Claude-rules-only change
- [x] `nova-viewer/` not touched — N/A, Claude-rules-only change
- [x] Docs / config — `.claude/rules/workflow.md` gains a "PR cadence — when to actually open a PR" section that codifies the rule (one PR per coherent unit of work), defines a "unit" (single logical story + gate trio green + comfortable handoff + natural stopping point), gives explicit yes/no examples, names both backstops (PR-cadence guardrail hook at >30 commits + branch protection on main forbidding direct commits), explains why one-PR-per-unit beats every-commit-PR (ceremony / cost spike) and one-big-PR (drift trap, citing PR #2's 125-commit history), and ends with a discipline rule ("if you can't write a single ≤70-char PR title, it's not a unit — split")

## Review

- [x] `/review` dispatched on staged diff — N/A: `.claude/rules/**` is the "skip with reason: Claude-tooling-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the lesson "PR cadence must be explicit, not implicit" is captured in the workflow.md section itself + cross-references PR #2's 125-commit history as the precedent
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; the cadence rule is workflow-shaped, not gotcha-shaped, and lives in workflow.md
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-doc clarification of an already-implicit rule, not a new architectural decision. The PR-cadence guardrail HOOK shipped earlier (commit 7ce1039) was the structural change; this commit documents the discipline that the hook backstops

## Commit message

- [x] Conventional Commits format: `docs(workflow): codify PR cadence rule (one PR per coherent unit of work)`
- [x] Body explains *why* — the cadence had been implicit in conversation only. Next session wouldn't see it. PR #2 happened because the rule was never written down, and the branch drifted 125 commits ahead of main before anyone surfaced the problem. This commit puts the rule in `.claude/rules/workflow.md` (the auto-loaded workflow contract) so it survives session boundaries and applies to anyone working in this repo. The PR-cadence guardrail hook (`.claude/settings.json`, shipped earlier) is the technical backstop; this is the discipline it backstops.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
