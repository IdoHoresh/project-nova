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
- [x] `git diff --cached --stat` reviewed — single file `.github/workflows/claude-review.yml` (~6 line net change: add `id-token: write` to permissions block, replace invalid `model:` + `allowed_tools:` keys with single `claude_args:` string)
- [x] Atomic commit — single logical change: fix the two real failures the Layer 2 GH Action surfaced on PR #2's first run

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; workflow YAML only (still references `${{ secrets.ANTHROPIC_API_KEY }}` indirection, not a literal)
- [x] `nova-agent/` not touched — N/A, CI-config-only change
- [x] `nova-viewer/` not touched — N/A, CI-config-only change
- [x] Docs / config — `.github/workflows/claude-review.yml`: (1) `permissions:` gains `id-token: write` (the action authenticates via OIDC even when an API key is provided; without it the action exits at attempt 3 of 3 with "Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable"); (2) the standalone `model:` and `allowed_tools:` keys are not valid `anthropics/claude-code-action@v1` inputs per the workflow-parse warning, so model+tool restrictions are passed through the supported `claude_args:` string (`--model claude-sonnet-4-6 --allowed-tools Read,Grep,Glob,Bash`). Inline comment block explains the rationale for both changes so future contributors don't re-introduce either bug.

## Review

- [x] `/review` dispatched on staged diff — N/A: `.github/workflows/**` is the "skip with reason: CI-config-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A. The new `id-token: write` permission is exactly what the action needs to acquire an OIDC token; it is scoped to this single workflow and its only effect is enabling OIDC-based authentication. No new secret surface introduced.

## Documentation

- [x] LESSONS.md — N/A; the lesson "validate workflow YAML inputs against the action's published schema" is implicit in this fix and the inline comment block. No separate LESSONS entry warranted for a one-off CI fix
- [x] CLAUDE.md "Common gotchas" — N/A, no new Nova-specific gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a CI-config bugfix, not an architectural decision

## Commit message

- [x] Conventional Commits format: `ci: fix Layer 2 claude-code-action workflow inputs and OIDC permission`
- [x] Body explains *why* — PR #2's first Layer 2 run on `claude-code-action@v1` failed with two diagnostics. (1) Workflow-parse warning: `model:` and `allowed_tools:` are not valid action inputs in v1; the published schema only accepts `claude_args` for CLI-style customization. (2) Action runtime error: the OIDC token request fails ("Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable") because the workflow's `permissions:` block lacked `id-token: write`. Both are real, both fail-closed, both surfaced cleanly on first run rather than silently — the workflow did its job by failing visibly.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
