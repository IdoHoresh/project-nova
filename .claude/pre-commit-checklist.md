# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — feature branch claude/practical-swanson-4b6468, atomic single coherent unit (LESSONS.md addendum extending the just-committed numerical-claim rule to cover code-state claims), 1 file / +2 lines net
- [x] **Verification** — git diff scanned for secrets, none found; N/A: doc-only commit, no code paths to gate
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: doc-only` (LESSONS.md narrative addendum; no code, no config)
- [x] **Documentation** — LESSONS.md is itself the documentation; no other docs require update
- [x] **Commit message** — `docs(lessons): extend redteam-verification rule to code-state claims`, body explains why (Q3 of Test Runner brainstorm reinforced the pattern in same session), co-author tag present
