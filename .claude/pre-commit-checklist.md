# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: enforce /clear after every commit+push in workflow.md session hygiene section.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A (no Python). `/check-viewer` N/A (no TS).
- [x] **Review** — N/A: Claude-tooling-only change per REVIEW.md taxonomy.
- [x] **Documentation** — workflow.md IS the documentation artifact.
- [x] **Commit message** — `docs(rules): enforce /clear after every commit+push` (≤72 chars); co-author tag present.
