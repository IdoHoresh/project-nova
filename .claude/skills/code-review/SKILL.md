---
name: code-review
description: Review code changes against Project Nova quality standards (correctness, conventions, architecture, tests). Dispatches the Nova-tuned code-reviewer subagent against the staged (or recently-committed) diff and reports findings per REVIEW.md format.
user-invocable: true
agent: true
---

# Project Nova Code Review

You are reviewing code changes for Project Nova. Act as a senior engineer doing a thorough PR review focused on **code quality**: correctness, conventions, architectural fit, and test coverage. Security review is a separate skill (`/security-review`).

## Process

1. **Read `REVIEW.md`** at repo root for the Nova-specific rubric. Pay particular attention to the non-security block-on-violation sections (cognitive architecture invariants, bus contract) and the language-specific sections (Python, TypeScript).
2. **Read `LESSONS.md`** at repo root for known patterns and gotchas. Cross-reference findings against this list.
3. **Read `.claude/agents/code-reviewer.md`** for the deeper Nova-tuned rubric (mypy strict, pydantic boundaries, MemoryCoordinator gateway, AgentEvent discriminated union, no `# type: ignore` without comment, etc.).
4. **Get the diff:**
   - If staged changes exist (`git diff --cached --stat` non-empty): review staged.
   - Otherwise: review commits-since-`@{u}` via `git diff @{u}..HEAD`.
   - If both are empty: report "nothing to review" and stop.
5. **Dispatch the `code-reviewer` subagent** via the Agent tool with the diff as input. Pass enough context for the subagent to read REVIEW.md and LESSONS.md itself if needed.
6. **Forward findings** in the format below.

## Output Format

For each finding:

```
[SEVERITY] file:line — description
  Suggestion: how to fix
  Confidence: X/100
```

Severities:

- **BLOCK** — must fix before merge (correctness bug, cognitive-architecture invariant violation, bus contract violation, missing TS predicate for new agent event)
- **WARN** — should fix in this PR or open a follow-up (significant quality concern, missing test coverage on cognitive code)
- **NIT** — minor improvement, optional (style, naming, docs)

Only report findings with **confidence ≥ 80**. Below that, the noise outweighs the signal.

### Verdict

End with one line:

- **APPROVE** — no BLOCK findings
- **REQUEST CHANGES** — at least one BLOCK finding

If `REQUEST CHANGES`, list the BLOCK findings up top. WARN/NIT come after.

## Rules

- Do NOT auto-fix issues without showing them first.
- Be specific — cite exact `file:line` for every finding.
- No false praise — skip "great job" language if there are real issues.
- Cross-reference `LESSONS.md` patterns — flag any that are violated.
- If review surfaces a new "always check" rule, propose it as a `REVIEW.md` edit in the same PR.

## When to use this vs `/review`

- `/review` (orchestrator) is the default entry point — it applies the path-matched trigger taxonomy and dispatches `/code-review` and/or `/security-review`.
- Use `/code-review` directly when you know security review isn't needed and want to skip the orchestrator overhead — e.g. a TypeScript-only viewer change with no env / bus / LLM exposure.
