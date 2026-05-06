# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: Task 0 review-fix — collapse duplicate Model rule line, normalize memory pointer style in CLAUDE.md.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A: doc-only. `/check-viewer` N/A: doc-only.
- [x] **Review** — N/A: addressing prior review findings on the same task; no new code surface introduced.
- [x] **Documentation** — CLAUDE.md IS the documentation artifact.
- [x] **Commit message** — `docs(claude): collapse duplicate Model rule + normalize memory pointer` (≤72 chars); co-author tag present.
