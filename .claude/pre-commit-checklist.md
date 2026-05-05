# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: main() full wiring (scenario resolution + LLM construction + asyncio.run + exit code) + e2e CLI smoke test (2 files)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found; pytest 267 passed, mypy strict clean (55 files), ruff all checks passed; manual smoke exit 0 with real LLM calls
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical TDD task` — wiring argparse → existing run_cliff_test via tier-checked model_for + build_llm; no novel seams, no new LLM adapter/bus event/env var/subprocess; Layer 1.5 pre-push hook covers on push
- [x] **Documentation** — N/A: no doc changes; API shape (model_for, Settings, build_llm) verified from source before use; adaptations from plan draft documented inline
- [x] **Commit message** — `feat(cliff-test): main() wires argparse → run_cliff_test → exit code`, body explains why, co-author tag present
