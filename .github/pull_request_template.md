## Summary

<!-- What does this PR do? 1-3 bullet points. Focus on the *why*, not the *what*. -->

-

## Type

<!-- Check one. Conventional Commit type — must match the commit subject prefix. -->

- [ ] feat: new feature (user-facing capability)
- [ ] fix: bug fix
- [ ] refactor: code change that is neither a feature nor a bug fix
- [ ] perf: performance improvement
- [ ] test: adding or updating tests
- [ ] chore: tooling, config, dependencies (no production code change)
- [ ] docs: documentation only
- [ ] ci: CI/CD pipeline changes

## Scope

<!-- Which subproject(s) does this touch? -->

- [ ] `nova-agent/` (Python cognitive architecture)
- [ ] `nova-viewer/` (Next.js brain panel)
- [ ] `docs/` (product, methodology, decisions, internal)
- [ ] root config (CLAUDE.md, LESSONS.md, ARCHITECTURE.md, .pre-commit-config.yaml, .github/workflows/)
- [ ] other:

## Changes

<!-- Key files changed and why. Use the table or a bulleted list — whichever reads cleaner. -->

| File | Change |
| ---- | ------ |
|      |        |

## Verification

<!-- Show evidence each gate passed. Don't check a box without proof. -->

### nova-agent (if touched)

- [ ] `uv run pytest` — passes (paste pass count)
- [ ] `uv run mypy` — strict, clean
- [ ] `uv run ruff check` — clean
- [ ] `UV_PROJECT_ENVIRONMENT` exported (see CLAUDE.md gotcha #1)

### nova-viewer (if touched)

- [ ] `pnpm test` — passes (paste pass count)
- [ ] `npx tsc --noEmit` — clean
- [ ] `pnpm run lint` — clean
- [ ] manual check on `localhost:3000` if UI changed

### Always

- [ ] gitleaks pre-commit hook passed (no secrets)
- [ ] `git diff --cached --stat` reviewed (warn if >500 lines)
- [ ] commit subject follows Conventional Commits (`type(scope): subject`)

## Documentation

<!-- Did this change call for any of these? Check + describe, or check N/A. -->

- [ ] CLAUDE.md updated (gotcha added or build command changed)
- [ ] LESSONS.md updated (new lesson learned)
- [ ] ARCHITECTURE.md updated (topology changed)
- [ ] new ADR added in `docs/decisions/` (architecture / product decision)
- [ ] methodology / roadmap / personas updated (`docs/product/`)
- [ ] N/A — no docs change called for

## Related

<!-- Link relevant ADRs, prior PRs, issues, roadmap items. -->

- ADR:
- Roadmap phase:
- Closes:

## Notes for reviewer

<!-- Anything that's not obvious from the diff. Tradeoffs accepted, alternatives considered, things you're not sure about. -->
