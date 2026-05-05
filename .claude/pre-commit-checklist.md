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
- [x] `git diff --cached --stat` reviewed — 3 files: baseline.py (excerpt narrowed) + types.ts + eventGuards.ts (mirror schema update)
- [x] Atomic commit — single coherent unit: security-reviewer MEDIUM #1 fix on commit 0bfcca3 (raw_response_excerpt narrowed 200→40 + excerpt_length added for diagnostics)

## Verification
- [x] `git diff --cached` scanned for secrets — fix REMOVES a potential leak surface; no new secrets / API keys / env values
- [x] `nova-agent/` — pytest 227 passing (14 baseline), mypy strict + ruff clean
- [x] `nova-viewer/` — vitest 98 passing, tsc clean, eslint clean
- [x] Docs / config — N/A: not touched

## Review
- [x] `/review` dispatched — N/A: this IS the security-reviewer MEDIUM #1 follow-up fix (verbatim recommendation from upstream review per memory feedback_subagent_dispatch_selectivity "skip re-review on verbatim fixes")
- [x] `code-reviewer` subagent — N/A: mechanical follow-up; gate trio green
- [x] `security-reviewer` — N/A: this IS the response to the prior security review (MEDIUM #1)

## Documentation
- [x] LESSONS.md — N/A this commit; security-reviewer process learnings may land in a follow-up sweep
- [x] CLAUDE.md "Common gotchas" — N/A: no new gotcha
- [x] ARCHITECTURE.md — N/A: implementation detail change, not architecture
- [x] New ADR — N/A: telemetry payload tightening within the existing telemetry contract (Bot spec §3.4 unchanged at the contract level, just one field narrower)

## Commit message
- [x] Conventional Commits format: `fix(baseline): narrow parse-failure excerpt to 40 chars + add length`
- [x] Body explains why — security-reviewer MEDIUM #1 on commit 0bfcca3; 200-char excerpt fits Anthropic (~108) and Google (~39) API keys, with persistence via RecordingEventBus → JSONL on disk; 40 chars preserves debug shape and forces any current-format key into a truncated state; excerpt_length surfaces full size for diagnostics
- [x] Co-author tag present
