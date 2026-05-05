# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — feature branch claude/practical-swanson-4b6468, atomic single coherent unit (LESSONS.md entry: test-runner spec drift — collector vs analyzer SoC), 1 file / +9 lines net
- [x] **Verification** — git diff scanned for secrets, none found; N/A: doc-only commit, no code paths to gate
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: doc-only` (LESSONS.md narrative entry; no code, no config)
- [x] **Documentation** — LESSONS.md is itself the documentation; no other docs require update
- [x] **Commit message** — `docs(lessons): collector-vs-analyzer SoC for experiment-runner specs`, body explains why (Q6 of Test Runner brainstorm surfaced the drift), co-author tag present
