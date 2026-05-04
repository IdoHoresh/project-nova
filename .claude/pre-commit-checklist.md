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
- [x] `git diff --cached --stat` reviewed — 2 files in repo: `.claude/rules/workflow.md` (new "Session hygiene" section between PR cadence and Periodic, ~80 lines), `.claude/settings.json` (new third command hook for /clear-reminder, ~5 lines). Plus 3 files in cross-session memory (not in repo): two new feedback files + MEMORY.md index update.
- [x] Atomic commit — single logical change: codify session-hygiene discipline (when to /clear, when to /compact, when NOT to manually dispatch subagents) + add structural /clear-reminder hook so the discipline survives without requiring user vigilance

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown rules-doc + settings.json shell-pipeline command (calls `gh pr list` already authenticated via the user's `gh` CLI session); no new credential surface
- [x] `nova-agent/` not touched — N/A, Claude-tooling-only change
- [x] `nova-viewer/` not touched — N/A, Claude-tooling-only change
- [x] Docs / config — workflow.md gains a "Session hygiene" section covering /clear triggers (PR merges, concern switches, >150k context, >2h continuous work) + the curated handoff prompt template + /compact triggers + the manual-subagent-dispatch policy (4 allowed cases, NOT every-commit-on-sensitive-paths). settings.json gains a third command hook on `Bash(git push:*)` that emits a `systemMessage` reminder when the branch is 0 commits ahead of origin/main AND a PR for the branch was merged in the last 30 minutes. Both hooks share the same outer `2>/dev/null` pattern for error tolerance. JQ schema validated: 3 hooks total (1 agent + 2 command), all with `if: "Bash(git push:*)"`. Pipe-tested under bash explicitly: with PR #3 merged ~10 hours ago the new hook stays correctly silent (outside the 30-min window); the comparison logic is verified working.

## Review

- [x] `/review` dispatched on staged diff — N/A: `.claude/rules/**` and `.claude/settings.json` are both "skip with reason: Claude-tooling-only" rows of the REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above. Also: this commit IS the codification of the "don't over-dispatch manual reviewers" policy; reviewing it via manual dispatch would directly contradict the policy it ships.
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, the session-hygiene rules are workflow-shaped (live in workflow.md) not lesson-shaped (LESSONS.md is for past-incident gotchas). The over-dispatch + 89%-context cost data point IS captured in the workflow.md "Session hygiene" section as the precedent that motivated the rule.
- [x] CLAUDE.md "Common gotchas" — N/A; the session-hygiene rules are workflow contract, not setup-time environment gotchas
- [x] ARCHITECTURE.md — N/A, system topology unchanged; this is a Claude-pair-discipline addition only
- [x] New ADR — N/A, this is a workflow-doc addition + a hook extension, not a new architectural decision. Well within ADR-0006's existing cost-tier discipline scope; ADR-0006 already framed the layered review system that this commit clarifies the discipline for.

## Commit message

- [x] Conventional Commits format: `feat(claude): add session-hygiene discipline + /clear reminder hook`
- [x] Body explains *why* — `/usage` showed 100% subagent-heavy + 89% at >150k context on 2026-05-04. Both drivers are session-shape problems, not model-choice problems. Codifying when to /clear, when to /compact, and when NOT to manually dispatch subagents in `.claude/rules/workflow.md` "Session hygiene" puts the discipline in the auto-loaded contract. Adding a third PreToolUse command hook on `git push:*` that emits a `systemMessage` reminder when a PR for the current branch merged within the last 30 minutes makes the /clear suggestion structural — fires automatically at the exact moment a /clear is most valuable. Two new feedback memories cross-session reinforce both rules for future Claude sessions.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
