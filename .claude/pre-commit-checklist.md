# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: cliff-test CLI skeleton + tier guard (3 files: pyproject.toml +1 line, cliff_test.py +84 lines, test_cliff_test_runner.py +46 lines)
- [x] **Verification** — git diff --cached scanned; no secrets, keys, or tokens found
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (TDD skeleton per spec; no novel architecture, no security surface, no LLM/bus paths)
- [x] **Documentation** — spec §6.1 + ADR-0006 referenced inline in module docstring and error message; no external docs need updating
- [x] **Commit message** — `feat(cliff-test): CLI skeleton + tier guard`, body explains why (first Task 1 of 11 cliff-test runner slices; tier guard enforces ADR-0006 for cognitive-judgment model integrity), co-author tag present
