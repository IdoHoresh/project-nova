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
- [x] `git diff --cached --stat` reviewed — single file `.github/workflows/claude-review.yml` (~10 lines: model swap from Sonnet to Opus inside `claude_args`, plus expanded inline comment block explaining the rationale)
- [x] Atomic commit — single logical change: bump Layer 2 PR review model from Sonnet 4.6 to Opus 4.7 to maximize recall on multi-file architectural checks per the user's stated "best results > cost optimization" preference

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; workflow YAML only (still references `${{ secrets.ANTHROPIC_API_KEY }}` indirection)
- [x] `nova-agent/` not touched — N/A, CI-config-only change
- [x] `nova-viewer/` not touched — N/A, CI-config-only change
- [x] Docs / config — `.github/workflows/claude-review.yml` `claude_args` value changes from `--model claude-sonnet-4-6` to `--model claude-opus-4-7`. Inline comment block now documents the model-choice rationale (Layer 2 is the last automated check before human merge review, Opus pulls ahead on multi-file synthesis exactly where Nova invariants live, ~$0.075/PR vs Sonnet's $0.045 is rounding error against the sprint budget). Allowed-tools list unchanged (`Read,Grep,Glob,Bash`). All other workflow plumbing (id-token write permission, OIDC fix, draft skip, concurrency cancel) preserved from the previous commit.

## Review

- [x] `/review` dispatched on staged diff — N/A: `.github/workflows/**` is the "skip with reason: CI-config-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. Note: the change does mean Layer 2 now runs Opus against PR diffs that may include sensitive paths — this is a model upgrade for security-relevant analysis, not a downgrade

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the inline comment block in the workflow itself documents the choice + rationale + when to revisit
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged; the three-layer review model remains intact (Haiku at L1.5 / Sonnet-or-Opus at L1 manual / Opus now at L2)
- [x] New ADR — N/A, this is a model-tuning change inside the existing Layer 2 workflow shipped under ADR-0006's cost-tier discipline. Could be considered a minor amendment to ADR-0006 but doesn't rise to a new ADR; the inline comment captures the trade-off

## Commit message

- [x] Conventional Commits format: `ci: bump Layer 2 PR review model to Opus 4.7`
- [x] Body explains *why* — user explicitly preferred "best results" over cost optimization for Layer 2. Layer 2 is the last automated check before human merge review; at the safety net, default to max recall. Opus pulls meaningfully ahead of Sonnet on multi-file synthesis (catches "looks fine in isolation but violates an invariant three files away" — exactly Nova's cognitive-layer game-agnosticism / bus contract / MemoryCoordinator gateway / ADR-discipline checks). Cost delta ~$0.03/PR (~$3 per 100 PRs) is rounding error against the sprint budget. Three-layer model preserved: Haiku at L1.5 (every push), Sonnet/Opus at L1 (manual per-diff), Opus at L2 (every PR).
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
