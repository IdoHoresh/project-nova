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
- [x] `git diff --cached --stat` reviewed — 8 files: `protocol.py` (extend Protocol), `gemini_client.py` (forward schema), `anthropic_client.py` + `mock.py` (accept-and-ignore), `decision/react.py` + `decision/tot.py` + `reflection/postmortem.py` (pass schema at callsites), `tests/test_llm_gemini.py` + `tests/test_llm_anthropic.py` + `tests/test_llm_mock.py` (4 new tests)
- [x] Atomic commit — single logical change: thread optional `response_schema: type[BaseModel] | None` arg through the LLM protocol so Gemini callsites get generation-time JSON schema enforcement; Anthropic and Mock providers accept-and-ignore for cross-provider symmetry

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; protocol + provider-adapter changes only
- [x] `nova-agent/` — gate trio green: 154/154 tests pass (added 2 Gemini schema tests, 1 Anthropic accept-and-ignore test, 1 Mock accept-and-ignore test), mypy strict clean (46 source files), ruff clean
- [x] `nova-viewer/` not touched — N/A, agent-only protocol change
- [x] Docs / config — `LLM` Protocol gains `response_schema: type[BaseModel] | None = None` kwarg with docstring explaining the cross-provider asymmetry (Gemini honors, Anthropic accepts-and-ignores, Mock accepts-and-ignores). `GeminiLLM.complete()` forwards schema to `GenerateContentConfig.response_schema` for OpenAPI 3.0 generation-time enforcement. Three callsites (`react.decide_with_context`, `tot._evaluate_branch`, `reflection.run_reflection`) now pass their pydantic output model. `parse_json` post-validation kept at every callsite as defense-in-depth.

## Review

- [x] `/review` dispatched on staged diff — yes. Code-reviewer (Sonnet) + security-reviewer (Opus) dispatched in parallel per REVIEW.md path-matched trigger taxonomy (`nova-agent/**/llm/**` is the yes-yes row).
- [x] Code-reviewer verdict: **APPROVE** with 2 WARN + 2 NIT.
  - **WARN mock.py:166** signature symmetry → fixed: `response_schema: type[BaseModel] | None` matches the Protocol exactly
  - **WARN protocol.py:32** load-bearing change without ADR → deferred to the next commit which bundles ADR-0006 (cost-tier discipline + record-replay rationale + schema-enforcement contract); this commit ships the plumbing-only protocol extension because the ADR also documents the `plumbing` tier addition shipping in commit N+1
  - **NIT** accept-and-ignore tests on Anthropic + Mock → fixed: 2 new tests added
  - **NIT** verify Gemini SDK preserves `Field(ge=0.0, le=1.0)` constraint metadata → deferred (one-line manual check; not load-bearing for current dev tier; will land with the plumbing-tier audit)
- [x] Security-reviewer verdict: **APPROVE** with 1 NIT (PRICING dict colocation; defer, not a real concern).
- [x] All BLOCKs addressed — there were no BLOCK findings on either pass.

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the schema-enforcement pattern itself is the reusable insight, captured in the protocol docstring
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha
- [x] ARCHITECTURE.md — N/A, no topology change; protocol extension is backward-compatible
- [x] New ADR — deferred to next commit (ADR-0006 will cover cost tiers + dev-mode discipline + record-replay rationale + this protocol extension as a single coherent decision document)

## Commit message

- [x] Conventional Commits format: `feat(llm): add response_schema enforcement to LLM protocol`
- [x] Body explains *why* — principal engineer red-teamed the cost-saving plan and warned that flash-lite (the cheapest Gemini tier) will drift on JSON shape unless the API enforces structure at generation time. The fix is to pass the consuming pydantic model to Gemini's `response_schema` parameter on every JSON-required callsite. Anthropic Messages API has no native equivalent (Claude is reliable enough on JSON-mode prompts that asymmetry is acceptable for now); Mock has its own role-based deterministic generation. All three providers accept the kwarg for cross-provider symmetry.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
