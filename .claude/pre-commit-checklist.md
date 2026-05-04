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
- [x] `git diff --cached --stat` reviewed — single file `.claude/settings.json` (~6 lines added: a second `command`-type hook in the existing PreToolUse-on-Bash entry)
- [x] Atomic commit — single logical change: add a PR-cadence guardrail hook so the "branch silently drifted 125 commits ahead of main" failure mode that motivated PR #2 cannot recur

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; settings.json adds shell-pipeline command text only (counts commits ahead of origin/main, calls `gh pr list`, emits a `systemMessage` warning if >30 commits ahead AND no open PR)
- [x] `nova-agent/` not touched — N/A, Claude-config-only change
- [x] `nova-viewer/` not touched — N/A, Claude-config-only change
- [x] Docs / config — adds a second hook to the existing PreToolUse[matcher:Bash][if:Bash(git push:*)] block. Type `command`, 10s timeout. Pipeline: `git rev-list --count origin/main..HEAD` → if result >30 AND branch is not `main` AND `gh pr list --head <branch> --state open` returns nothing → emit `{"systemMessage": "PR overdue: <N> commits ahead..."}` to stdout. Otherwise silent. Errors swallowed via outer `2>/dev/null` so a missing `gh` or detached HEAD never breaks the push. JQ schema validated; pipe-tested with current state (returns silent because PR #2 is open).

## Review

- [x] `/review` dispatched on staged diff — N/A: `.claude/settings.json` is the "skip with reason: Claude-tooling-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. Note: the hook's shell pipeline runs on every `git push:*` and shells out to `gh pr list` — the only network call is `gh`'s standard GitHub API call (already authenticated via the user's `gh` CLI session). No new credential surface introduced.

## Documentation

- [x] LESSONS.md — N/A, the lesson "branch can drift many commits ahead of main without a PR — guard against it at push time" is implicit in the hook's existence and the PR #2 body that called out the failure mode. No separate LESSONS entry needed since the guardrail makes the lesson structural rather than retrospective
- [x] CLAUDE.md "Common gotchas" — N/A, the guardrail makes the gotcha self-correcting
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition (one shell pipeline in settings.json) that can be removed by deleting one entry. Not a load-bearing architectural decision

## Commit message

- [x] Conventional Commits format: `feat(claude): add PR-cadence guardrail hook to prevent branch drift`
- [x] Body explains *why* — branch drifted 125 commits ahead of main without a PR (see PR #2). Each commit silently increased the eventual merge cost; nothing surfaced the problem until manual inspection. The new hook fires on every `git push:*` and emits a `systemMessage` warning when the branch is >30 commits ahead of origin/main AND no PR is open. Doesn't block the push (drift may be intentional during a sprint), but makes the threshold visible at the moment the user is about to push the 31st commit. Threshold of 30 is a judgment call — high enough to not nag during normal small-PR work, low enough to catch the "I'll PR later" trap before it turns into a 100+ commit catch-up PR.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
