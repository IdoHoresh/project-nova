---
name: security-review
description: Security-focused review for Project Nova. Checks for leaked secrets, unsafe code patterns, prompt-injection surfaces, bus protocol leaks, and dependency vulnerabilities. Dispatches the Nova-tuned security-reviewer subagent.
user-invocable: true
agent: true
---

# Project Nova Security Review

You are reviewing code changes for Project Nova as a senior security engineer. The threat model is documented in `.claude/agents/security-reviewer.md`; the crown jewels are API keys (Anthropic, Google), LLM prompts (which may contain board state and persona context), and the WebSocket bus (localhost-only, no auth assumed — treat as untrusted output for secrets).

## Process

1. **Read `REVIEW.md`** at repo root, focusing on the **Security (block on violation)** section.
2. **Read `.claude/agents/security-reviewer.md`** for the deeper Nova-tuned threat model and rubric (hardcoded secrets, default values for secret env vars, secrets in logs / errors / URLs, prompt-injection surface, bus protocol violations).
3. **Read `LESSONS.md`** at repo root — security-relevant lessons are mixed in with engineering ones.
4. **Get the diff:**
   - If staged changes exist (`git diff --cached --stat` non-empty): review staged.
   - Otherwise: review commits-since-`@{u}` via `git diff @{u}..HEAD`.
5. **Dispatch the `security-reviewer` subagent** via the Agent tool with the diff. Pass enough context for the subagent to read the rubric files itself if needed.
6. **Optionally re-run gitleaks** explicitly on the diff if anything looks suspicious — the pre-commit hook already runs it, but a focused pass adds confidence:
   ```bash
   gitleaks detect --source . --verbose 2>&1 | tail -30
   ```
7. **Forward findings** in the format below.

## Output Format

For each finding:

```
[SEVERITY] file:line — description
  Suggestion: how to fix
  Confidence: X/100
```

Severities:

- **BLOCK** — must fix before merge (committed secret, eval/exec on untrusted input, subprocess `shell=True` with f-string, secret in log/URL/error, default value for secret env var, bus event publishing a token / API key / credential)
- **WARN** — should fix this PR or open a follow-up issue (defensive logging that could leak info, weak validation at a boundary that's not yet exploitable)
- **NIT** — minor improvement (defense-in-depth suggestion that's not a current vuln)

Only report findings with **confidence ≥ 80**. Below that, the noise outweighs the signal.

### Verdict

End with one line:

- **APPROVE** — no BLOCK findings
- **REQUEST CHANGES** — at least one BLOCK finding

If `REQUEST CHANGES`, list the BLOCK findings up top. WARN/NIT come after.

## Rules

- Do NOT auto-fix issues without showing them first.
- Be specific — cite exact `file:line` for every finding.
- For any suspected secret leak, propose the rotation step alongside the code fix (rotate the key, then patch the code path that exposed it).
- Cross-reference `LESSONS.md` — particularly any security-tagged lessons.
- If a new "always check" rule emerges, propose it as a `REVIEW.md` Security-section edit.

## When to use this vs `/review`

- `/review` (orchestrator) is the default entry point — it applies the path-matched trigger taxonomy and dispatches `/code-review` and/or `/security-review`.
- Use `/security-review` directly when reviewing a change that is **only** security-relevant — e.g. an env handling refactor where you want a focused security pass without the broader code-quality rubric.
