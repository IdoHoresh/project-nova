# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: _CSV_COLUMNS + _append_csv_row + 4 tests (2 files, 123 lines)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (pure TDD per spec §2.7; no novel architecture, no security surface, no LLM/bus paths)
- [x] **Documentation** — spec §2.7 referenced in _CSV_COLUMNS comment; no external docs need updating
- [x] **Commit message** — `feat(cliff-test): _append_csv_row crash-resilient writer`, body explains why, co-author tag present
