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
- [x] `git diff --cached --stat` reviewed — 1 modified file: `.claude/settings.json` (4 deny rules: replaces invalid `:* | sh|bash` patterns with valid wildcard `* | sh|bash` form per /doctor diagnostic)
- [x] Atomic commit — single logical change: fix invalid permission rule format in deny list (curl/wget piped to sh/bash). All 4 rules silently disabled previously due to `:*`-not-at-end validation; now valid wildcard form so curl-bash + wget-bash blocking actually works.

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; pure permission-rule pattern fix
- [x] `nova-agent/` not touched — N/A, Claude-tooling-only change
- [x] `nova-viewer/` not touched — N/A, Claude-tooling-only change
- [x] Docs / config — `.claude/settings.json` deny array fix; restores defense-in-depth blocking against `curl ... | bash` and `wget ... | bash` pipe-to-shell patterns. JSON parses cleanly post-edit (verified via `jq -e '.permissions.deny[] | select(test("curl|wget"))'` returning all 4 rules).

## Review

- [x] `/review` dispatched on staged diff — N/A: `.claude/**` is the "skip with reason: Claude-tooling-only" row of the REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above. Trivial pattern fix per /doctor diagnostic guidance.
- [x] `security-reviewer` — N/A by REVIEW.md taxonomy, but worth noting: this commit RESTORES a security boundary (curl-bash/wget-bash blocking) that was silently disabled. Net positive for the security posture.

## Documentation

- [x] LESSONS.md — N/A on this commit; the underlying lesson ("invalid permission patterns silently skip — verify rules with /doctor") is too narrow to merit a top-level LESSONS entry. The /doctor diagnostic itself is the canonical surface for catching this.
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A

## Commit message

- [x] Conventional Commits format: `chore(claude): fix invalid Bash(wget:* | bash) deny rules`
- [x] Body explains *why* — /doctor flagged `Bash(wget:* | bash)` invalid (`:*` must be at end of pattern). All 4 sibling rules (curl|sh, curl|bash, wget|sh, wget|bash) had the same defect and were silently disabled. Replaced `:*` with `*` (wildcard form per diagnostic guidance). Restores defense-in-depth blocking against curl-bash and wget-bash pipe-to-shell attack patterns.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
