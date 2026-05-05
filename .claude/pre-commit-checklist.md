# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: _apply_with_tiebreak + _try_apply + 3 tests (2 files)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (pure TDD per spec §2.3; no novel architecture, no security surface, no LLM/bus paths)
- [x] **Documentation** — spec §2.3 referenced in _TIEBREAK_ORDER comment; no external docs need updating
- [x] **Commit message** — `feat(cliff-test): _apply_with_tiebreak invalid-move fallback`, body explains why, co-author tag present
