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
- [x] `git diff --cached --stat` reviewed — 1 file: new Baseline Bot implementation plan (+1423 lines)
- [x] Atomic commit — single coherent unit: implementation plan for the Bot spec shipped in commit fea8ac0

## Verification
- [x] `git diff --cached` scanned for secrets — plan content references "tokens" only as LLM-token-counts, no API keys / env values
- [x] `nova-agent/` — N/A: doc-only commit, no Python touched
- [x] `nova-viewer/` — N/A: doc-only commit, no TS touched
- [x] Docs / config — plan file is docs; no config changes

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: doc-only` (implementation plan, no code paths)
- [x] `code-reviewer` subagent — N/A: doc-only commit
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths touched in the plan content; security-reviewer is invoked when Task 6 of the plan executes (per plan's Task 6 Step 5)

## Documentation
- [x] LESSONS.md — N/A this commit; brainstorm-process lessons may land in a follow-up commit after the plan executes
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha
- [x] ARCHITECTURE.md — N/A: plan implements an existing spec, no new architecture
- [x] New ADR — N/A: ADR-0007 Amendment 1 already shipped in commit fea8ac0

## Commit message
- [x] Conventional Commits format: `docs(plan): baseline bot implementation plan`
- [x] Body explains why — TDD-decomposed seven-task plan executes the Bot spec; companion to commit fea8ac0; ready for subagent-driven execution
- [x] Co-author tag present
