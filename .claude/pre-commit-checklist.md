# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: add Haiku architectural gate to pre-push hooks for diffs ≥80 lines or cognitive paths.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A. `/check-viewer` N/A.
- [x] **Review** — N/A: Claude-tooling-only change per REVIEW.md taxonomy.
- [x] **Documentation** — `_hooks_explanation` in settings.json updated inline.
- [x] **Commit message** — `chore(config): add Haiku architectural gate for large/cognitive diffs` (≤72 chars); co-author tag present.
