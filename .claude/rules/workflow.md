# Workflow Rules (HIGHEST PRIORITY — ABSOLUTE)

> Repo-wide workflow contract. Adapted from the Gibor app's
> `.claude/rules/workflow.md` and trimmed to Project Nova reality:
> single-developer + Claude pair, ADR-driven, polyglot Python+TS,
> push-after-every-commit cadence.

**NEVER skip, auto-check, or rubber-stamp ANY step. NOT ONE. EVER.**

If a step doesn't apply, say so explicitly with a one-sentence reason.
Silent skipping is the failure mode this rule exists to prevent.

## The Complete Flow (every non-trivial change)

### Before code

1. **Branch check** — confirm `git branch --show-current` returns the
   working branch (`claude/practical-swanson-4b6468`). Never commit
   directly to `main`.
2. **Pre-task checklist** — work through the list in `CLAUDE.md`
   "Pre-task checklist" section (read methodology / roadmap / ADRs as
   relevant; confirm tests will be written; confirm acceptance
   criterion is clear).
3. **Brainstorm** — for new surface area, use `superpowers:brainstorming`
   to lock the design before implementation. Save the spec to
   `docs/superpowers/specs/`.
4. **Plan** — for multi-step changes, use `superpowers:writing-plans`.
   Save the plan alongside the spec.
5. **ADR** — for any load-bearing architectural or product decision,
   write `docs/decisions/NNNN-<title>.md` BEFORE the implementation
   commit. The ADR captures the why, alternatives, consequences.

### During implementation

6. **TDD** — write the failing test first. Run it to confirm failure.
   Implement minimally. Run it to confirm pass. Refactor with
   tests still green. Mandatory for cognitive-layer code, decision
   logic, and bus protocol changes.
7. **Subagents for review** — for non-trivial changes, dispatch the
   `code-reviewer` subagent on the diff before commit. For anything
   touching secrets, env, LLM, or the bus, also dispatch
   `security-reviewer`.

### Before commit

8. **`/check-agent` or `/check-viewer`** — run the appropriate gate
   trio. Both clean before commit.
9. **`git diff --cached`** — actually scan it for secrets/keys/tokens.
   State "no secrets found" or fix.
10. **`git diff --cached --stat`** — review line count. Warn if >500
    lines; consider splitting the commit.
11. **Pre-commit hooks** — let them run. Never `--no-verify` without
    explicit user authorisation in the same session.
12. **Conventional Commits subject** — `type(scope): subject`, ≤72
    chars. Body explains *why*, not *what*.
13. **Co-author tag** on Claude-generated commits:
    `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
14. **Atomic commit** — one logical change. If you find yourself
    writing "and" in the subject, split.

### After commit

15. **Push immediately.** Established cadence — never batch.
16. **CI check** (when on a branch with PR) — wait for CI green
    before starting the next task.

### Periodic — every ~5 commits or weekly

17. **LESSONS.md sweep** — anything from the recent work worth
    capturing? Use `/lessons-add`. Better to over-capture than
    under-capture.
18. **REVIEW.md sweep** (when added) — any new "always check"
    patterns? Promote them.
19. **CLAUDE.md gotchas** — any new gotcha that cost time? Add it
    to the "Common gotchas" section.

## Phase signals — what to invoke when

The Claude pair MUST proactively flag these signals when they fire.
Do not silently default to "just start coding." Each signal maps to
a specific skill or artifact.

| The user's request implies... | Flag + invoke |
|-------------------------------|---------------|
| New feature or unclear surface area | `superpowers:brainstorming` (design before code) |
| 3+ files, multiple steps, needs handoff | `superpowers:writing-plans` |
| Plan exists, tasks are atomic + independent | `superpowers:subagent-driven-development` |
| Two or more independent investigations | `superpowers:dispatching-parallel-agents` |
| Code touches cognitive layer / decision logic / bus protocol | `superpowers:test-driven-development` |
| Mid-task "I think this is done" moment | `superpowers:verification-before-completion` |
| Non-obvious failure / debugging session | `superpowers:systematic-debugging` |
| Review pushback (human or `code-reviewer` subagent) | `superpowers:receiving-code-review` |
| Wrapping up branch / opening PR | `superpowers:finishing-a-development-branch` |
| Architectural choice with long-term consequences | `ultrathink` prefix + draft an ADR |

## Context-clear signals — when to suggest `/clear`

Long sessions degrade. The Claude pair MUST proactively suggest
`/clear` when any of these fires, with a curated next-session
hand-off prompt:

- A feature shipped (commit pushed that closes a roadmap item)
- A major refactor finished
- A phase milestone hit (Phase 0.7 cliff test passes, etc.)
- A long debugging session resolved
- ~2+ hours of continuous work in one session
- The user pivots to an unrelated task

**Hand-off prompt template:**

```
[What just shipped: commit/PR + 1-line summary]
[What's next per docs/product/product-roadmap.md]
[Which workflow skill to start with — brainstorming / writing-plans / direct]
[Anything left in working tree that needs attention]
```

`/compact` is also available but considered opaque — prefer explicit
`/clear` + curated prompt.

## Why this matters

Project Nova is the substrate for a planned product (synthetic
playtesting platform for game studios). Every shortcut compounds:
sloppy ADRs make Phase-N decisions un-reviewable, missing tests
make Phase-0.7 / 0.8 validation un-replicable, leaked secrets in
the repo end the project. The workflow exists because the cost of
each shortcut is more than it appears.

The Gibor app's principle applies here: "Ido has asked MULTIPLE
TIMES to never skip steps. This rule has been violated before. It
must NEVER be violated again."
