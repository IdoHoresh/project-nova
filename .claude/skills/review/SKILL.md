---
name: review
description: Review code changes against Project Nova quality standards. Run after completing any implementation task, before commit. Picks code-reviewer + security-reviewer based on REVIEW.md path-matched trigger taxonomy.
user-invocable: true
agent: true
---

# Project Nova Code Review (Orchestrator)

You are reviewing code changes for Project Nova. Act as a senior engineer doing a thorough PR review. This skill is an **orchestrator** — it inspects the staged (or recently-committed) diff, applies the path-matched trigger taxonomy in `REVIEW.md`, and dispatches `/code-review` and/or `/security-review` accordingly.

## Process

1. **Read `REVIEW.md`** at repo root for Nova-specific review rules and the path-matched trigger taxonomy.
2. **Read `LESSONS.md`** at repo root for known patterns and gotchas (note the uppercase filename).
3. **Get the diff:**
   - If staged changes exist (`git diff --cached --stat` is non-empty): review staged.
   - Otherwise: review commits-since-`@{u}` via `git diff @{u}..HEAD`.
   - If both are empty: report "nothing to review" and stop.
4. **Apply the path-matched trigger taxonomy** (`REVIEW.md` table) to the changed paths to decide which reviewers to dispatch:
   - `nova-agent/src/**` → code-reviewer (+ security-reviewer if config / llm / bus / .env paths involved)
   - `nova-viewer/{lib,app}/**` → code-reviewer
   - `nova-agent/**/{config,llm,bus}/**`, `.env*`, anything with `subprocess` / `shell=True` / `eval` / `exec` / dynamic-code → code-reviewer + security-reviewer
   - `docs/**`, `*.md`, `.github/workflows/**`, `.claude/**`, lockfiles, version bumps, generated files → **no review required**, report skip with stated reason
5. **Dispatch** the chosen reviewer(s):
   - For code-review: invoke `/code-review` (or dispatch the `code-reviewer` subagent directly via the Agent tool)
   - For security-review: invoke `/security-review` (or dispatch the `security-reviewer` subagent directly)
   - When both fire, run them **in parallel** via two Agent tool calls in the same message.
6. **Aggregate findings** from the dispatched reviewer(s) into a single output.
7. **Apply the after-review loop:** if a finding surfaces a previously-uncaptured pattern, propose adding it to `LESSONS.md` (offer the diff, don't write directly).

## Output Format

Always start with the trigger decision, so the user can audit the binary check:

```
Trigger:
  Files touched: <N files across these top-level paths>
  Decision: <code-review | security-review | both | skip>
  Reason: <which row of REVIEW.md table matched>
```

Then forward the dispatched reviewer(s) output. If both fired, group findings under `## Code Review` and `## Security Review` headers.

End with a single overall verdict line:

- **APPROVE** — no `BLOCK` findings from any dispatched reviewer
- **REQUEST CHANGES** — at least one `BLOCK` finding

## Skip-with-reason format

If the path-matched taxonomy says no review is required, output:

```
Trigger:
  Files touched: <N files>
  Decision: skip
  Reason: <doc-only | CI-config-only | Claude-tooling-only | mechanical>

Skipped review per REVIEW.md path-matched trigger taxonomy.
No findings.
```

Do NOT review when the taxonomy says skip — silent over-reviewing trains rubber-stamping. The taxonomy is binary by design.

## When BOTH "yes" and "no" rows match

If a single commit touches files in both a "yes" row and a "no" row, "yes" wins — review is required. Mention in the trigger decision which "yes" row applied.

## Rules

- Do NOT auto-fix issues without showing them first.
- Be specific — cite exact `file:line` for every finding.
- No false praise — skip "great job" language if there are real issues.
- Cross-reference `LESSONS.md` patterns — flag any that are violated.
- If review surfaces a new "always check" rule, propose it as a `REVIEW.md` edit in the same PR.
- Confidence threshold ≥ 80 — below that, the noise outweighs the signal.
