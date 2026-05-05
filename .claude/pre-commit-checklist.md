# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: _worker paired-trial coroutine + DEFAULT_CONCURRENCY + 3 worker integration tests (2 files)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found; pytest 261 passed, mypy strict clean (55 files), ruff all checks passed
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical TDD task` — composing existing _run_carla_trial + _run_bot_trial + _BudgetState + _append_csv_row + RecordingEventBus per spec §2.2/§4.3 pseudocode; no novel seams, no new LLM adapter/bus event/env var/subprocess; Layer 1.5 pre-push hook covers on push
- [x] **Documentation** — N/A: no doc changes; signatures verified from source (_BudgetState, _append_csv_row, RecordingEventBus) before use
- [x] **Commit message** — `feat(cliff-test): _worker paired-trial coroutine`, body explains why, co-author tag present
