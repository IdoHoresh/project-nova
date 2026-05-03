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
- [x] `git diff --cached --stat` reviewed — single-file rewrite of `.claude/rules/workflow.md` (133 → 89 lines, ~33% smaller)
- [x] Atomic commit — single logical change: trim workflow rules to remove duplication with CLAUDE.md

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown rules-doc only
- [x] `nova-agent/` not touched — N/A, Claude-config-only change
- [x] `nova-viewer/` not touched — N/A, Claude-config-only change
- [x] Docs / config — `.claude/rules/workflow.md`: removed "Phase signals" table (was duplicate of CLAUDE.md "When to use which workflow skill"), removed "Context-clear signals" section (was duplicate of CLAUDE.md "Context hygiene"). Workflow.md now points at CLAUDE.md as single source of truth and lists 17 numbered steps (was 19, collapsed near-duplicates and added pointer to the new pre-push agent hook in step 14).

## Review

- [x] `code-reviewer` subagent — N/A, doc-only change with no executable logic; rubric checks (atomic commits, naming, dead code) don't apply to a markdown rules trim
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the duplication itself was the gotcha and this commit removes it
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a workflow-doc cleanup, not a load-bearing decision

## Commit message

- [x] Conventional Commits format: `chore(workflow): trim duplication, point at CLAUDE.md as single source`
- [x] Body explains *why* — three documents previously held the same signal-to-skill table and context-clear signals; drift between them is a real risk; trimming workflow.md to 89 lines and pointing at CLAUDE.md keeps one source of truth and adds a forward reference to the new pre-push hook in step 14
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
