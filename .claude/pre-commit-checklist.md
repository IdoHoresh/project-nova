# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: implementation plan artifact for the Phase 0.7 Test Runner (1 file, +2599 lines, doc-only)
- [x] **Verification** — N/A: doc-only change, no code paths to gate; git diff scanned, no secrets
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: doc-only` (plan narrative artifact for subagent-driven-development; no production paths)
- [x] **Documentation** — plan IS the documentation; sibling plans live in same dir (`docs/superpowers/plans/`)
- [x] **Commit message** — `docs(plan): Phase 0.7 Test Runner implementation plan`, body explains why (subagent-driven-development artifact behind 10 implementation commits), co-author tag present
