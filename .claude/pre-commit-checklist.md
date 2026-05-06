# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: trim CLAUDE.md from 434 to ~200 lines to reduce per-turn auto-loaded context.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A. `/check-viewer` N/A.
- [x] **Review** — N/A: doc-only change per REVIEW.md taxonomy.
- [x] **Documentation** — CLAUDE.md IS the documentation artifact.
- [x] **Commit message** — `docs(claude): trim CLAUDE.md ~60% to cut per-turn context load` (≤72 chars); co-author tag present.
