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

### PR cadence — when to actually open a PR

The feature branch (`claude/practical-swanson-4b6468`) is long-lived
and survives every merge to `main`. Commits accumulate on it
between PRs. The rule for **when to open a PR** is one of the
load-bearing workflow rules — get this wrong and you either drown
in ceremony (one PR per commit) or land in a 125-commit catch-up
trap (see PR #2 history).

**The rule: one PR per coherent unit of work.**

A unit is:

- one logical story — one or more atomic commits that together
  accomplish a single goal
- gate trio green at HEAD (`uv run pytest && uv run mypy && uv run
  ruff check` for the agent; `pnpm test && npx tsc --noEmit && pnpm
  run lint` for the viewer)
- something you'd be comfortable handing a reviewer and saying
  "this is done"
- at a natural stopping point — the next task is independent, not
  a continuation of this one

**When to open a PR (yes):**

- finished a chapter of work — e.g. "review-system port" was one
  unit (5 commits, one PR); "model-tuning of Layer 1.5 + Layer 2"
  was another unit (2 commits, one PR)
- 1+ commits that tell a single story
- you're moving to a different concern next session

**When NOT to open a PR (defer):**

- mid-feature, unfinished work — e.g. `Game2048Sim` half-built;
  keep committing on the branch, PR when the unit is shippable
- gate trio red — fix first, then PR
- exploratory commits that might get squashed or reordered later;
  PR when settled
- micro-fixes (typo in a comment, lint nit) that belong batched
  with the next coherent unit

**Backstops:**

- A `PreToolUse` command hook in `.claude/settings.json` fires on
  every `git push:*` and emits a `systemMessage` warning when the
  branch is >30 commits ahead of `origin/main` AND no PR is open.
  This catches the "I forgot to PR" trap before it becomes a
  100-commit catch-up. Doesn't block; just surfaces.
- Branch protection on `main` — direct pushes / direct commits to
  `main` are forbidden, period.

**Why one-PR-per-unit instead of every-commit-PR or one-big-PR:**

- *every-commit-PR* — ceremony overload. Layer 2 (`claude-code-action`,
  Opus) re-runs on every PR open. Cost spikes, value barely spikes.
- *one-big-PR* — drift trap. PR #2 was 125 commits because the rule
  was implicit, not codified. Review fatigue, hard to bisect,
  Layer 2 has to reason over a huge surface.
- *one-PR-per-unit* — Layer 2 reviews coherent diffs (where it
  earns its keep), reviewer sees one story per PR, branch stays
  close to `main`.

**Discipline rule:** if you're unsure whether the current branch
state is a "coherent unit," ask yourself — *what's the PR title?*
If you can write a single ≤70-char title that describes everything
on the branch since the last merge, it's a unit. If the title
needs an "and" or "plus" or "also," split into separate PRs (or
keep working on one half until the other half is shippable).

### Session hygiene — when to `/clear` and `/compact`

Long-running conversations are the dominant cost driver in
Claude Code sessions, more than model selection. Today's `/usage`
showed 89% of usage at >150k context — driven entirely by one
all-day conversation that crossed ~5 natural break points
without ever resetting. Session hygiene is a discipline, not a
nice-to-have.

**`/clear` triggers** (reset context with a curated handoff
prompt):

- After every PR merges to `main` — branch is synced, work chapter
  complete, natural break. A `PreToolUse` command hook in
  `.claude/settings.json` fires on the next `git push:*` after a
  merge and emits a `systemMessage` reminder; you can also `/clear`
  proactively the moment the merge lands.
- When switching to a different concern (e.g., from review-system
  tooling to `Game2048Sim` build).
- When the context window exceeds ~150k tokens (visible via
  `/usage`).
- After ~2 hours of continuous work in one session.

**Curated handoff prompt template** (paste into the new session
after `/clear`):

```
Last shipped: <PR # + 1-line summary>
Next task: <from CLAUDE.md "Active phase + next task">
Read: CLAUDE.md, project_nova_resume_point memory, recent git log
```

The auto-loaded `CLAUDE.md` + the resume-point memory file +
`git log --oneline -10` together reconstruct ~95% of what the
prior session knew. The remaining 5% (mid-feature flow context)
is what `/compact` is for.

**`/compact` triggers** (middle ground — keep continuity but
free context):

- Mid-feature when you want flow but context is heavy (>200k).
- Long debugging session that's still ongoing.

**Manual subagent dispatch policy** — when NOT to dispatch
`code-reviewer` / `security-reviewer` manually:

The three layers cover the surface automatically:

- Layer 1.5 — auto pre-push hook (fast command: secret grep + stat, no LLM) on every `git push:*`
- Layer 2 — auto PR workflow (Opus) on every PR open / sync
- Layer 1 — manual dispatch for operator judgment

Manual Layer 1 dispatches are reserved for **four cases**, NOT
for "every commit on a sensitive path":

1. About to open a PR with a non-trivial diff and want a final
   pre-PR sanity pass.
2. Mid-feature uncertainty about an architectural choice (e.g.,
   does this design fit ADR-0001's invariant?).
3. Explicit user request.
4. ADR-worthy decisions where Sonnet review at L1.5 isn't
   enough — invoke `security-reviewer` manually for Opus-tier
   security analysis on sensitive diffs.

`REVIEW.md`'s path-matched trigger taxonomy is for the `/review`
**orchestrator's** dispatch decision when the orchestrator is
invoked. It is NOT a blanket every-commit-on-a-sensitive-path
rule. Over-dispatching for "every commit" is the failure mode
that drove a 100% subagent-heavy session reading on 2026-05-04.
Trust the auto layers; reserve manual dispatch for high-leverage
moments.

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
