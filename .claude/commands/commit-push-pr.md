---
description: Stage, commit, and push the current change in one shot. Generates a Conventional Commits message from the staged diff. Optionally opens a PR if the branch has commits ahead of origin/main and no open PR exists.
allowed-tools: Bash, Read, Edit
---

Run the full ship sequence in one shot. Each step gates on the prior step's output.

**Steps:**

1. Show repo state in parallel:
   ```bash
   git status
   git diff --cached --stat
   git log --oneline -5
   ```
   If `git diff --cached` is empty, stop and tell the user "nothing staged — `git add <files>` first."

2. Scan the staged diff for secrets:
   ```bash
   git diff --cached | grep -E '^[+].*(ANTHROPIC_API_KEY|OPENAI_API_KEY|sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{35}|aws_(access|secret)_key|password\s*=\s*"[^"]')' | head -5
   ```
   Any match → STOP and surface to the user. Do not proceed without explicit "ignore, push anyway" instruction.

3. Read CLAUDE.md, REVIEW.md, and `.claude/rules/workflow.md` for current conventions.

4. Read the staged diff in full:
   ```bash
   git diff --cached
   ```

5. Apply REVIEW.md path-matched trigger taxonomy. If a "yes" row matches and the diff is non-trivial, recommend the user run `/review` before proceeding (skip if user has already done so this session).

6. Generate a Conventional Commits subject (≤72 chars) and a body that explains *why* not *what*. Format:
   ```
   type(scope): subject

   Body explaining motivation. Reference any ADR, spec, or methodology
   doc when applicable.

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```

   `type` ∈ {feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert}. If subject contains "and" or "plus", split into multiple commits.

7. Show the proposed commit message to the user. Wait for confirmation. If confirmed, commit:
   ```bash
   git commit -m "$(cat <<'EOF'
   <generated message here>
   EOF
   )"
   ```

8. Push immediately:
   ```bash
   git push
   ```

9. Check PR cadence:
   ```bash
   ahead=$(git rev-list --count origin/main..HEAD)
   branch=$(git branch --show-current)
   pr_open=$(gh pr list --head "$branch" --state open --json number --jq 'length')
   ```

   If `ahead > 0` AND `pr_open = 0` AND the branch is at a coherent unit per workflow.md "PR cadence" section, surface to the user: "Branch has $ahead commits ahead of origin/main with no open PR. Open one? (`gh pr create --base main`)"

10. After successful push, surface the `/clear` recommendation per CLAUDE.md "Context hygiene":
    > "/clear recommended — commit + push complete. Handoff: `Last shipped: <new sha + 1-line>. Next: <task from resume-point memory>. Read: CLAUDE.md, resume-point memory, git log --oneline -10`"

**When to invoke this command:**

- Any non-trivial change ready to ship (single coherent commit).
- Replaces the 14-step pre-commit ceremony.

**When NOT to invoke this command:**

- Mid-feature work that should be batched (commit incrementally with `git commit` directly; use `/commit-push-pr` only for the final shippable commit of the unit).
- WIP that may be reordered or squashed later.
