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
- [x] `git diff --cached --stat` reviewed — single file `LESSONS.md` (~25 lines added: new "Engineering / debugging gotchas" entry at top)
- [x] Atomic commit — single logical change: capture the by-design constraint that `claude-code-action@v1` cannot self-review PRs that modify the workflow file, so it doesn't surprise the next contributor (or the next session) when it happens again

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; markdown narrative only
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` not touched — N/A, doc-only change
- [x] Docs / config — `LESSONS.md` gains an "Engineering / debugging gotchas" entry at the top of that section (newest-on-top per the file's convention) describing what failed (App Token Exchange 401 with "Workflow validation failed" message), why (anti-tampering: workflow on PR branch must be byte-identical to main's version so a PR can't modify the workflow during its own review), and the four how-to-apply rules (expect failure on workflow-modifying PRs, don't split, manually review, dispatch /security-review for sensitive changes).

## Review

- [x] `/review` dispatched on staged diff — N/A: `LESSONS.md` is a doc-only change at repo root; per REVIEW.md path-matched trigger taxonomy this falls under "doc-only" (the same row that exempts `docs/**` and `*.md`)
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. Note: the lesson IS about a security-relevant constraint (anti-tampering on workflow files), but the lesson text itself is documentation, not code that handles secrets

## Documentation

- [x] LESSONS.md — this commit IS the LESSONS.md update; nothing further needed
- [x] CLAUDE.md "Common gotchas" — N/A; LESSONS.md is the right home for engineering gotchas (CLAUDE.md "Common gotchas" is for setup-time issues like UF_HIDDEN, pnpm vs npm, gemini quota — environmental gotchas, not workflow-system constraints)
- [x] ARCHITECTURE.md — N/A, system topology unchanged
- [x] New ADR — N/A, this is a lesson capturing an external system's by-design behavior, not a Nova architectural decision

## Commit message

- [x] Conventional Commits format: `docs(lessons): record claude-code-action workflow self-review constraint`
- [x] Body explains *why* — PR #3's Layer 2 run failed with `401 Unauthorized — Workflow validation failed` because the action requires byte-identical workflow file between PR branch and main (anti-tampering). The error is structural, not fixable, and the action's own message says it's "normal" — but it cost ~10 minutes to read the error carefully and recognize the constraint. Capturing it in LESSONS.md so the next workflow-modifying PR doesn't surprise anyone.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
