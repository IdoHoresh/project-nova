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
- [x] `git diff --cached --stat` reviewed — two doc-only files (`LESSONS.md` + `.claude/pre-commit-checklist.md`); no source code touched
- [x] Atomic commit — single logical change: capture the AgentEvent catch-all anti-pattern lesson and refresh the per-commit checklist for this commit

## Verification

- [x] `git diff --cached` scanned for secrets — pure prose addition + checklist rewrite; no env / API keys / tokens / URLs touched
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` — full gate trio re-run before staging: `pnpm test` 98/98 across 5 files, `npx tsc --noEmit` exit 0, `pnpm run lint` zero warnings (no source files modified by this commit)
- [x] Docs / config — LESSONS.md gains one new "Engineering / debugging gotchas" entry above the existing UF_HIDDEN entry (newest-at-top); checklist file rewritten for this commit's scope

## Review

- [x] `code-reviewer` subagent — N/A, doc-only change with no behavior risk
- [x] `security-reviewer` — N/A by trigger; no secrets / env / LLM / bus code touched

## Documentation

- [x] LESSONS.md — new entry "Discriminated-union catch-alls hide missing variants" added at the top of "Engineering / debugging gotchas"; metadata format (Date / Cost / What happened / Lesson / How to apply) matches existing entries
- [x] CLAUDE.md "Common gotchas" — N/A, gotcha #9 (AgentEvent catch-all) was resolved by Tasks 1–8 of this branch; the LESSONS entry is the canonical postmortem
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, no architectural decision; this is the closing doc commit for the AgentEvent validator chain

## Commit message

- [x] Conventional Commits format: `docs(lessons): record AgentEvent catch-all anti-pattern`
- [x] Body explains *why* — captures the postmortem from Tasks 1–8 so future protocol-mirroring work doesn't reach for the same string-keyed catch-all "for safety"; points future contributors at `nova-viewer/lib/eventGuards.ts` as the template for new event types
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
