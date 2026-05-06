# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: replace pre-push Sonnet agent hook with fast command-only gate (secret grep + stat). Files: `.claude/settings.json`, `.claude/rules/workflow.md`.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A (no Python changes). `/check-viewer` N/A (no TS changes).
- [x] **Review** — N/A: Claude-tooling-only change per REVIEW.md taxonomy.
- [x] **Documentation** — `_hooks_explanation` in settings.json + workflow.md Layer 1.5 description updated inline.
- [x] **Commit message** — `chore(config): replace pre-push Sonnet agent with fast command hook` (≤72 chars); co-author tag present.
