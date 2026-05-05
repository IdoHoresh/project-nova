# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: CarlaTrialResult + _run_carla_trial + _carla_call_cost_estimate + 2 Carla integration tests (2 files)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found; pytest 258 passed, mypy strict clean (55 files), ruff all checks passed
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical TDD task` — composing existing AffectState + MemoryCoordinator + ReactDecider + ToTDecider + SimGameIO per canonical main.py:240-319 pattern; no novel seams, no new LLM adapter/bus event/env var/subprocess; Layer 1.5 pre-push hook covers on push
- [x] **Documentation** — N/A: no doc changes; signatures verified from source before call sites written; run_reflection signature mismatch adapted at call site (not production code)
- [x] **Commit message** — `feat(cliff-test): _run_carla_trial single Carla trial coroutine`, body explains why, co-author tag present
