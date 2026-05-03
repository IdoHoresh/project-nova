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
- [x] `git diff --cached --stat` reviewed — single-file change to `.claude/settings.json` adding one PreToolUse hook entry (~19 lines added)
- [x] Atomic commit — single logical change: add pre-push agent hook for auto code-review/security-review

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; settings.json adds prompt text only
- [x] `nova-agent/` not touched — N/A, Claude-config-only change
- [x] `nova-viewer/` not touched — N/A, Claude-config-only change
- [x] Docs / config — `.claude/settings.json`: adds `PreToolUse` hook on `Bash` matching `git push:*`, type `agent`, default Haiku model, 120s timeout. Hook reads `.claude/agents/code-reviewer.md` rubric on every push, conditionally reads `security-reviewer.md` when diff touches LLM/env/secret paths. Blocks push only on critical findings; medium/high surface as warnings.

## Review

- [x] `code-reviewer` subagent — N/A, this commit IS the auto-review wiring; reviewing it via Sonnet subagent before adding the Haiku hook would be circular. Hand-reviewed inline.
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched in this commit. The hook itself is the security upgrade.

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha to capture yet; will revisit after 3-5 real pushes prove or disprove hook reliability
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; hook activation requires `/hooks` reload but that's a known settings-watcher behavior, not Nova-specific
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-tooling addition, not a load-bearing architectural decision; can be reverted by removing one settings entry

## Commit message

- [x] Conventional Commits format: `feat(claude): add pre-push agent hook for auto code-review`
- [x] Body explains *why* — closes the "I forgot to invoke reviewer" gap by automating the dispatch at push time; uses Haiku for cost (~$0.02-0.05/push, ~$5-15 over 6-week sprint); blocks only on critical findings so most pushes pass through; reads existing Nova-tuned rubrics so behavior matches manual subagent dispatch
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
