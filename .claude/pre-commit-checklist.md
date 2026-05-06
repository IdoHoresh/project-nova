# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: Task 0 of workflow-simplification batch — insert model-escalation trigger table in CLAUDE.md.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A: doc-only. `/check-viewer` N/A: doc-only.
- [x] **Review** — N/A: doc-only change per REVIEW.md taxonomy ("doc-only" row).
- [x] **Documentation** — CLAUDE.md IS the documentation artifact.
- [x] **Commit message** — `docs(claude): add model-escalation trigger table` (≤72 chars); co-author tag present.
