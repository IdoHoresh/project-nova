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
- [x] `git diff --cached --stat` reviewed — 2 files: new Baseline Bot spec (+396 lines) + ADR-0007 Amendment 1 (+80 lines)
- [x] Atomic commit — single coherent unit: Bot spec + companion ADR amendment must ship together (spec §6.1 references the amendment; amendment cites the companion spec)

## Verification
- [x] `git diff --cached` scanned for secrets — only "token" references are LLM-token-counts in spec text, no API keys / env values
- [x] `nova-agent/` — N/A: doc-only commit, no Python touched
- [x] `nova-viewer/` — N/A: doc-only commit, no TS touched
- [x] Docs / config — both files are docs (spec + ADR amendment); no config changes

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: doc-only` (spec + ADR amendment, no code paths)
- [x] `code-reviewer` subagent — N/A: doc-only commit
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths touched

## Documentation
- [x] LESSONS.md — N/A this commit; brainstorm-process lessons may land in a follow-up commit after the implementation plan ships
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha surfaced in this work
- [x] ARCHITECTURE.md — N/A: spec is operational refinement of ADR-0007's existing two-arm design, not new architecture
- [x] New ADR — N/A: ratifies six operational decisions within ADR-0007's scope via Amendment 1; not a new architectural decision

## Commit message
- [x] Conventional Commits format: `docs(spec): baseline bot design + ADR-0007 amendment 1`
- [x] Body explains why — closes the second of two follow-up specs deferred from cliff-test scenarios spec; locks Bot architecture (LLM-based), schema/temperature configuration, failure-mode handling, and paired-discard threshold (≥ 18) through six rounds of red-team review
- [x] Co-author tag present
