# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: Task -1 of workflow-simplification batch — commit the design spec, implementation plan, and the LESSONS.md meta-lesson before starting the 10-task implementation.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A: doc-only. `/check-viewer` N/A: doc-only.
- [x] **Review** — N/A: doc-only change per REVIEW.md taxonomy ("doc-only" row).
- [x] **Documentation** — the spec + plan + LESSONS entry ARE the documentation artifacts; this is the contract for the upcoming batch.
- [x] **Commit message** — `docs(workflow): spec + plan + lesson for workflow-simplification batch` (≤72 chars); co-author tag present.
