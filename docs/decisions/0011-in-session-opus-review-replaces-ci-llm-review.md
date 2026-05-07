# ADR-0011: In-Session Opus Review Replaces CI LLM Review

**Status:** Accepted
**Date:** 2026-05-07
**Deciders:** Ido Horesh

---

## Context

Project Nova's Layer 2 review (`.github/workflows/claude-review.yml`) ran
`claude-code-action` on every PR open, using `secrets.ANTHROPIC_API_KEY` on
GitHub-hosted runners. This billed per-token against the API key regardless
of the developer's subscription plan.

Two jobs existed:
- `routine-review` — Sonnet 4.6, fired on every non-doc PR
- `deep-review` — Opus 4.7, fired on cognitive-layer / `.env*` paths

When the developer switched Claude Code CLI authentication from API key to a
Max subscription (OAuth), CI review continued billing the API key. The
combined spend was ~$38 Opus + ~$13 Sonnet over 5 days, with CI LLM review
accounting for a meaningful portion.

Additionally, CI review produced false positives on `.claude/commands/` and
`.claude/skills/` paths because the reviewer subagent lacked knowledge of
Claude Code internals, generating BLOCK findings on valid Agent tool dispatch
patterns.

## Decision

Remove CI LLM review entirely. Replace with in-session Opus review dispatched
automatically by `/commit-push-pr` before every non-doc commit:

- `/commit-push-pr` step 5 dispatches `code-reviewer` + `security-reviewer`
  subagents (both `model: opus`) via the Agent tool.
- Billed against Max subscription quota — zero API billing.
- BLOCK findings halt the commit; WARN/NIT surface and proceed.
- Doc-only diffs skip review (same taxonomy as before).

The `claude-review.yml` file is retained as a disabled comment-only file for
git history traceability.

## Alternatives considered

- **Keep CI Opus review, accept API billing:** Estimated ~$8/PR on cognitive
  paths. Acceptable if infrequent, but cumulative over a feature-velocity
  phase. Rejected — Max subscription covers the same quality at flat cost.

- **Keep CI review but downgrade to Sonnet:** Reduces API cost ~5×. Rejected —
  if we're running review, it should be Opus quality. Sonnet-in-CI is worse
  than Opus-in-session on the cognitive layer where it matters most.

- **Label-gated CI Opus job:** Add a `deep-review` label to trigger Opus only
  when explicitly requested. Partially considered — rejected because it
  requires developer discipline to label PRs, and in-session review is
  triggered automatically with no extra step.

- **Keep CI Sonnet + add in-session Opus:** Belt-and-suspenders. Rejected —
  CI Sonnet still bills API on every PR open. Redundant once in-session Opus
  covers the same surface.

## Consequences

**Positive:**
- Zero API billing from CI or review tooling. All review against Max quota.
- Review quality increases: Opus in-session > Sonnet in CI on cognitive paths.
- Review fires before commit (not after PR open) — catches issues earlier.
- No cold-start latency on GitHub runners; subagents dispatch inline.

**Negative:**
- Review only fires when developer uses `/commit-push-pr`. Manual `git commit`
  bypasses it. Mitigated by: (a) workflow rule enforcing `/commit-push-pr`,
  (b) memory entry flagging the bypass pattern, (c) pre-commit hooks still
  catch formatting/type/secret issues deterministically.
- No async safety net after push — if developer forgets `/commit-push-pr`,
  there is no CI fallback for logic/architecture review.

**Neutral:**
- CI still runs deterministic checks: pytest, mypy, ruff, eslint, tsc,
  gitleaks. These are unaffected.
- `.claude/**` paths were already excluded from review in REVIEW.md
  (`Claude-tooling-only` skip). The false-positive issue with CI reviewer is
  resolved by removal, not by taxonomy fix.

**Reversibility:** Easy. Re-add `on:` trigger to `claude-review.yml` from git
history. Consider restoring if: (a) Max subscription removed, (b) team grows
beyond solo developer and per-PR async review becomes valuable.

## References

- Supersedes Layer 2 workflow established in commit `9b36814`
- `REVIEW.md` — path-matched trigger taxonomy (unchanged)
- `.claude/commands/commit-push-pr.md` — implementation of in-session review
- `.github/workflows/claude-review.yml` — disabled workflow (retained for history)
- Commit `18edde8` — implementation commit
