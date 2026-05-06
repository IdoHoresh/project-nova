# Workflow Rules — Project Nova

> Single-developer workflow. Tier-1 invariants are load-bearing — never
> skip. Tier-2 advisories are codified in `REVIEW.md`, the slash
> commands (`.claude/commands/`), and the pre-commit hook config. Do
> NOT duplicate them here. Two-strikes rule for new additions: only
> add a rule the second time the same mistake is corrected.

## Five-stage loop

```
Brainstorm → Plan → Implement (TDD) → Review → Ship
```

Per-stage skill mapping lives in `CLAUDE.md` "When to use which skill"
table. Per-stage model mapping lives in `CLAUDE.md` "Model
escalation — when Sonnet must offer swap to Opus" table.

## Tier-1 invariants (NEVER skip)

1. **Branch.** Confirm `git branch --show-current` is NOT `main`.
   Direct commits to `main` are forbidden by branch protection;
   confirm anyway.
2. **ADR for load-bearing decisions.** Architectural / product
   decisions get `docs/decisions/NNNN-<title>.md` BEFORE the
   implementation commit. Captures why, alternatives, consequences.
3. **TDD on cognitive layer.** Mandatory for `nova_agent/{llm,bus,
   memory,perception}/**`, decision logic, bus protocol changes.
   Failing test first, minimal implementation, refactor green.
4. **Atomic commits.** One logical change per commit. "and" in the
   subject means split.
5. **Conventional Commits.** `type(scope): subject ≤72 chars`. Body
   explains *why*, not *what*. Co-author tag on Claude commits:
   `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
6. **Push after every commit.** Established cadence — never batch.
7. **No `--no-verify`** without explicit user authorisation in the
   same session.
8. **`/clear` after every commit + push.** Claude MUST proactively
   surface the recommendation with a ready-to-paste handoff. Use
   `/handoff` to write the Context Checkpoint first at any artifact
   cliff (post-commit + push, post-PR-merge, post-spec, post-plan,
   ~2h continuous work).

## PR cadence — one PR per coherent unit

A unit is: one logical story, gate trio green at HEAD, natural
stopping point, a title that fits ≤70 chars without "and" / "plus".

Open a PR when the unit is shippable. Do NOT open a PR for mid-
feature work, gate-trio-red HEAD, or exploratory commits. Do NOT
let the branch drift >30 commits ahead of `origin/main` without an
open PR — the pre-push hook surfaces a warning at that threshold.

## Ship sequence

Replace the prior 14-step pre-commit ceremony with `/commit-push-pr`.
The slash command runs status + diff scan + secret grep + REVIEW
trigger check + generated commit message + push + PR-cadence check
+ `/clear` recommendation. Read its frontmatter at
`.claude/commands/commit-push-pr.md` for the full sequence.

Pre-commit hooks (gitleaks, ruff, mypy, eslint, tsc, conventional-
pre-commit) run automatically and own deterministic enforcement.
The pre-push hook (`.claude/settings.json`) runs deterministic
secret grep + diff stat + PR-cadence + post-merge `/clear` hint —
no LLM at push time. Layer 2 (`.github/workflows/claude-review.yml`)
is the judgment pass at PR open: routine-review (Sonnet) on most
PRs, deep-review (Opus) on cognitive-layer / `.env*` paths.

## Manual review dispatch

Default: trust the auto layers (pre-commit + pre-push + Layer 2 PR
action). Manual `/review` dispatch is reserved for:

1. About to open a PR with a non-trivial diff and want a final
   pre-PR sanity pass.
2. Mid-feature uncertainty about an architectural choice.
3. Explicit user request.
4. ADR-worthy decisions where Sonnet review at Layer 2 routine pass
   is not enough — invoke `security-reviewer` manually for Opus-tier
   security analysis on sensitive diffs.

`REVIEW.md`'s path-matched trigger taxonomy is for `/review`
orchestrator dispatch when `/review` is invoked. It is NOT a
blanket every-commit-on-a-sensitive-path rule.

## Periodic — every ~5 commits or weekly

Sweep `LESSONS.md` (`/lessons-add`) for any non-obvious thing that
cost time. Sweep `CLAUDE.md` "Common gotchas" same. Two-strikes
rule: only add a rule the second time the same mistake recurs.
