# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — feature branch claude/practical-swanson-4b6468, atomic single coherent unit (LESSONS.md entry: red-team numerical-claim verification rule), 1 file / +10 lines net
- [x] **Verification** — git diff scanned for secrets, none found; N/A: doc-only commit, no code paths to gate
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: doc-only` (LESSONS.md narrative entry; no code, no config, no production paths)
- [x] **Documentation** — LESSONS.md is itself the documentation; no other docs require update
- [x] **Commit message** — `docs(lessons): capture red-team numerical-claim verification rule`, body explains why (Test Runner brainstorm Q2 surfaced the pattern), co-author tag present
