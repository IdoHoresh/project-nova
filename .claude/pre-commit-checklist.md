# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: run_cliff_test orchestrator + cap halt + pilot routing + 5 new tests (2 files)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found; pytest 266 passed, mypy strict clean (55 files), ruff all checks passed
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical TDD task` — composing existing _worker + _BudgetState + asyncio.Semaphore per spec §6.3 pseudocode; no novel seams, no new LLM adapter/bus event/env var/subprocess; Layer 1.5 pre-push hook covers on push
- [x] **Documentation** — N/A: no doc changes; all signatures verified from source before use; _budget_for_test seam documented inline
- [x] **Commit message** — `feat(cliff-test): run_cliff_test orchestrator + cap halt + pilot routing`, body explains why, co-author tag present
