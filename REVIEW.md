# Project Nova Code Review Rules

> **Purpose:** binary-decision review checklist for Nova. The reviewer
> ticks each line against the staged diff and reports findings with a
> confidence score (0-100). Only findings with confidence ≥ 80 are
> reported.
>
> **Read alongside:** `.claude/agents/code-reviewer.md` (rubric for
> code-review pass), `.claude/agents/security-reviewer.md` (rubric for
> security-review pass), `LESSONS.md` (known patterns and gotchas the
> reviewer cross-references).
>
> **Block-on-violation** sections fail the review. **Code quality**
> and language-specific sections are advisory unless they intersect
> a block-on-violation rule.

---

## Security (block on violation)

- [ ] No hardcoded secrets, keys, tokens, or passwords in any tracked file (including tests, fixtures, examples)
- [ ] No default values for secret env vars — `os.getenv("KEY", "...")` with a non-empty default is a leak risk
- [ ] No secrets in error messages, log statements, exception chains, or URL query strings
- [ ] No secrets in commit messages or PR descriptions
- [ ] All env-var access goes through `pydantic-settings` `Settings` with `env_ignore_empty=True`
- [ ] All subprocess / shell calls pass arguments as a list — never `shell=True` with f-strings
- [ ] No `eval`, `exec`, or `Function()`-via-string anywhere
- [ ] LLM prompts scrub PII, environment values, and trace IDs before sending
- [ ] WebSocket bus is treated as untrusted output for secrets — nothing published can be a token / API key / credential
- [ ] gitleaks pre-commit hook not bypassed (`--no-verify` requires explicit user authorization in the same session)

## Cognitive architecture invariants (block on violation)

- [ ] Memory writes go through `MemoryCoordinator` — never directly into LanceDB or SQLite
- [ ] Cognitive layer (memory / affect / decision / reflection / arbiter) stays game-agnostic above the perception/action interface
- [ ] New `LLM` adapters implement the protocol in `nova_agent/llm/protocol.py` — no cloud-SDK leaks into call sites
- [ ] Decision modules cite the methodology when changing affect dynamics, RPE, or trauma weighting
- [ ] ToT branch evaluator never calls `memory.write_*` — branches are read-only over memory
- [ ] Trauma tagging weighting stays centralized — no per-call-site overrides
- [ ] Load-bearing architectural changes have a corresponding `docs/decisions/NNNN-*.md` ADR

## Bus contract (block on violation)

- [ ] Every new agent event has a matching TS type in `nova-viewer/lib/types.ts`
- [ ] Every new agent event has a matching predicate in `nova-viewer/lib/eventGuards.ts`
- [ ] No `{event: string; data: unknown}` catch-all returns in the AgentEvent union
- [ ] Bus event field renames update BOTH `nova_agent/bus/` (when it exists) AND `nova-viewer/lib/types.ts` in the same commit
- [ ] No raw-string event names — all events flow through the typed discriminated union

## Code quality

- [ ] No magic numbers — extract named constants, cite source where applicable (paper, methodology doc, empirical sample)
- [ ] No duplicated logic — extract to shared functions
- [ ] No dead code or commented-out blocks ("git has history")
- [ ] Functions stay small and single-purpose; if a function exceeds ~30 lines, look for an extraction
- [ ] Meaningful names — `data`, `result`, `thing`, `temp` without context are red flags
- [ ] No over-engineering — the simplest thing that satisfies the spec
- [ ] Path aliases used where configured (`@/lib/...` not `../../lib/...` in nova-viewer)
- [ ] No `TODO:` comments left in logic paths — TODOs in committed code are bugs waiting to happen

## Python (nova-agent)

- [ ] mypy strict clean — no `# type: ignore` without a comment explaining why
- [ ] ruff check + ruff format clean — zero warnings
- [ ] pydantic models for I/O at boundaries (LLM responses, bus events, env config)
- [ ] No bare `except Exception:` unless re-raising with context
- [ ] `structlog` for structured logging — never `print` in committed code
- [ ] pytest fixtures preferred over inline mocks where possible
- [ ] Algorithm entry points have validation guards — `RangeError` / pydantic at the boundary, not deep in the call

## TypeScript (nova-viewer)

- [ ] No `any` types — use `unknown` with narrowing or proper discriminated unions
- [ ] No `as` casts without a comment justifying why narrowing isn't possible
- [ ] Discriminated-union narrowing preferred over runtime `typeof` / `in` checks
- [ ] vitest tests, not jest — and they live next to the code that exercises them
- [ ] Functional components only — no class components in this codebase
- [ ] Tailwind 4 utility classes — avoid inline `style={{}}` unless animating
- [ ] `useEffect` cleanup functions on every subscription, timer, or async callback
- [ ] `pnpm`, never `npm` — the viewer crashes on npm-shaped node_modules

## Testing

- [ ] TDD discipline followed for cognitive-layer code, decision logic, and bus protocol changes
- [ ] Tests use descriptive names — `methodName_scenario_expectedResult` shape
- [ ] Tests cover behavior, not implementation details
- [ ] Edge cases covered (zero, negative, boundary, empty list, null)
- [ ] New bus event types have unit + integration coverage
- [ ] No skipped tests left in committed code without an issue link

---

## Output Format

For each finding:

```
[SEVERITY] file:line — description
  Suggestion: how to fix
  Confidence: X/100
```

Severities:

- **BLOCK** — must fix before merge (security violation, cognitive-architecture invariant violation, bus contract violation, data loss, correctness bug)
- **WARN** — should fix in this PR or open a follow-up issue (significant quality concern that doesn't block)
- **NIT** — minor improvement, optional (style, naming, docs)

Only report findings with confidence ≥ 80. Below that, the noise outweighs the signal.

### Verdict

End the review with one line:

- **APPROVE** — no blocking issues found
- **REQUEST CHANGES** — has at least one BLOCK finding that must be fixed

If `REQUEST CHANGES`, list the BLOCK findings up top. WARN/NIT come after.

---

## When `/review` is required (path-matched trigger)

The `/review` skill (and the pre-commit-checklist binary check) decides
whether review is required by matching the staged diff against this
table. **Yes/no, not judgment.**

| Path touched                                                                  | `/review` required?                                                |
|-------------------------------------------------------------------------------|--------------------------------------------------------------------|
| `nova-agent/src/**`                                                           | **Yes** — code-reviewer + (if config / llm / bus / .env) security-reviewer |
| `nova-viewer/{lib,app}/**`                                                    | **Yes** — code-reviewer                                            |
| `nova-agent/**/{config,llm,bus}/**`                                           | **Yes** — code-reviewer + security-reviewer                        |
| `.env*`                                                                       | **Yes** — security-reviewer                                        |
| Anything with `subprocess`, `shell=True`, `eval`, `exec`, dynamic-code        | **Yes** — security-reviewer                                        |
| `docs/**`, `*.md`                                                             | No — skip with reason "doc-only"                                   |
| `.github/workflows/**`                                                        | No — skip with reason "CI-config-only"                             |
| `.claude/**`                                                                  | No — skip with reason "Claude-tooling-only"                        |
| Test fixtures, lockfiles, version bumps, generated files                      | No — skip with reason "mechanical"                                 |

If a commit touches files in BOTH a "yes" and a "no" row, the "yes"
wins — review is required.

---

## After-review loop

If a review surfaces a previously-uncaptured pattern that other code
might also violate, append it to `LESSONS.md` (note the uppercase
filename — Nova's convention). Use `/lessons-add` if a slash command
exists; otherwise append directly. Better to over-capture than
under-capture.

If a review reveals a new "always check" rule that doesn't fit any
existing block-on-violation section, propose it as a REVIEW.md edit
in the same PR.
