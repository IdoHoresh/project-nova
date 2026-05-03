# Workflow Rules (HIGHEST PRIORITY — ABSOLUTE)

> Repo-wide workflow contract. Single-developer + Claude pair, ADR-driven,
> polyglot Python+TS, push-after-every-commit cadence.

**NEVER skip, auto-check, or rubber-stamp ANY step. NOT ONE. EVER.**

If a step doesn't apply, say so explicitly with a one-sentence reason.
Silent skipping is the failure mode this rule exists to prevent.

The signal-to-skill mapping (which superpower skill to invoke when)
lives in [`CLAUDE.md`](../../CLAUDE.md) under "When to use which
workflow skill" — do NOT duplicate it here. Same for context-clear
signals; they live in CLAUDE.md "Context hygiene".

## The Complete Flow (every non-trivial change)

### Before code

1. **Branch check** — confirm `git branch --show-current` returns
   `claude/practical-swanson-4b6468`. Never commit directly to `main`.
2. **Pre-task checklist** — work through the checklist in
   [`CLAUDE.md`](../../CLAUDE.md) "Pre-task checklist" section.
3. **Invoke the appropriate workflow skill** per CLAUDE.md's
   signal-to-skill table. Common cases: `superpowers:brainstorming`
   for new surface area, `superpowers:writing-plans` for multi-step,
   `ultrathink` + ADR for load-bearing architectural decisions.
4. **ADR** — for any load-bearing architectural or product decision,
   write `docs/decisions/NNNN-<title>.md` BEFORE the implementation
   commit. Captures why, alternatives, consequences.

### During implementation

5. **TDD** — write the failing test first, run it to confirm failure,
   implement minimally, run it to confirm pass, refactor with tests
   green. Mandatory for cognitive-layer code, decision logic, bus
   protocol changes.
6. **Mid-task verification** — at "I think this is done" moments,
   invoke `superpowers:verification-before-completion` BEFORE the
   pre-commit gate. Don't wait for the gate to find it.

### Before commit

7. **`/review`** — dispatch the review orchestrator (or skip with a
   stated REVIEW.md taxonomy reason). `/review` reads `REVIEW.md`'s
   path-matched trigger taxonomy and decides BINARY whether
   `code-reviewer` and/or `security-reviewer` should run, then
   dispatches them. "Did I review?" is yes/no on file paths, not
   judgment. If skipping, name the row that matched (e.g. `N/A:
   doc-only`, `N/A: CI-config-only`, `N/A: Claude-tooling-only`,
   `N/A: mechanical`).
8. **`/check-agent` or `/check-viewer`** — run the appropriate gate
   trio (pytest+mypy+ruff or vitest+tsc+eslint). Both must be clean
   before commit.
9. **`git diff --cached`** — actually scan it for secrets/keys/tokens
   even though gitleaks runs on commit. State "no secrets found" or
   fix.
10. **`git diff --cached --stat`** — review line count. Warn if >500
    lines; consider splitting the commit.
11. **Pre-commit hooks** — let them run. NEVER `--no-verify` without
    explicit user authorisation in the same session.
12. **Conventional Commits subject** — `type(scope): subject`, ≤72
    chars. Body explains *why*, not *what*.
13. **Co-author tag** on Claude-generated commits:
    `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
14. **Atomic commit** — one logical change. If you find yourself
    writing "and" in the subject, split.

### After commit

15. **Push immediately.** Established cadence — never batch.
    A `PreToolUse` agent hook (`.claude/settings.json`) auto-runs
    Nova-tuned code-review + conditional security-review on the
    commits-since-last-push. Critical findings block the push;
    medium/high surface as warnings. The hook is a backstop AT
    PUSH TIME, NOT a license to skip step 7 (in-session `/review`)
    or step 9 (manual secret scan). Layer 1 (in-session) catches
    things while context is hot; the hook is Layer 1.5; PR-time
    `claude-code-action` is Layer 2.
16. **CI check** (when on a branch with PR) — wait for CI green
    before starting the next task.

### Periodic — every ~5 commits or weekly

17. **LESSONS.md sweep** — anything from recent work worth capturing?
    Use `/lessons-add`. Better to over-capture than under-capture.
    Also: did `/review` surface any new "always check" rule that
    should be promoted into `REVIEW.md`?
18. **CLAUDE.md gotchas** — any new gotcha that cost time? Add it to
    the "Common gotchas" section.

## Why this matters

Project Nova is the substrate for a planned product (synthetic
playtesting platform for game studios). Every shortcut compounds:
sloppy ADRs make Phase-N decisions un-reviewable, missing tests
make Phase-0.7 / 0.8 validation un-replicable, leaked secrets in
the repo end the project. The workflow exists because the cost of
each shortcut is more than it appears.

"Ido has asked MULTIPLE TIMES to never skip steps. This rule has
been violated before. It must NEVER be violated again."
