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
- [x] `git diff --cached --stat` reviewed — 2 files: SessionStart hook in .claude/settings.json + LESSONS.md entry capturing the incident
- [x] Atomic commit — single coherent unit: prevention work for the commits-stacked-on-open-PR drift trap (PR #7 incident on 2026-05-05). Hook + lesson + memory entry are one logical artifact triple — hook is enforcement, lesson is project-internal record, memory is cross-session backstop.

## Verification
- [x] `git diff --cached` scanned for secrets — no API keys / env values
- [x] `nova-agent/` — N/A: no Python touched
- [x] `nova-viewer/` — N/A: no TS touched
- [x] Docs / config — settings.json hook validated via `jq -e` + pipe-tested with current branch state (returned valid JSON systemMessage); LESSONS.md entry follows the existing section structure

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: Claude-tooling-only` (settings.json hook + LESSONS.md doc; no production code paths)
- [x] `code-reviewer` subagent — N/A: Claude-tooling change, no production code
- [x] `security-reviewer` — N/A: settings.json hook is read-only (gh pr list + jq); no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — IS the documentation update in this commit (Workflow / process learnings § new entry at top)
- [x] CLAUDE.md "Common gotchas" — N/A: this is a workflow-process gotcha, not an engineering gotcha; LESSONS.md is the right home
- [x] ARCHITECTURE.md — N/A: workflow tooling, not architecture
- [x] New ADR — N/A: no architectural decision; tooling improvement

## Commit message
- [x] Conventional Commits format: `chore(workflow): SessionStart hook + LESSONS entry for open-PR drift trap`
- [x] Body explains why — captures the 2026-05-05 PR #7 incident where Baseline Bot work stacked under a still-open cliff-test scenarios PR; SessionStart hook surfaces open PRs on the current branch at every session start as a systemMessage; companion LESSONS.md entry records the failure mode + recovery options. Memory entry saved separately to user-scope auto-memory (not part of this repo commit).
- [x] Co-author tag present
