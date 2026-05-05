# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: anxiety threshold helpers + 7 tests (2 files: cliff_test.py +44 lines, test_cliff_test_helpers.py +40 lines)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (pure TDD per spec §2.7; no novel architecture, no security surface, no LLM/bus paths)
- [x] **Documentation** — spec §2.7 referenced inline in constants comment; no external docs need updating
- [x] **Commit message** — `feat(cliff-test): anxiety threshold helpers (>0.6 for >=2 moves)`, body explains why, co-author tag present
