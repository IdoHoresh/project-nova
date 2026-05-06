# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: CLAUDE.md first-time-setup — add `git config merge.ours.driver true` so the `.gitattributes merge=ours` attribute activates on fresh clones. 1 line added.
- [x] **Verification** — `git diff --cached` scanned (no secrets; CLAUDE.md one-liner only). `/check-agent` N/A. `/check-viewer` N/A.
- [x] **Review** — N/A: doc-only, tooling setup only per REVIEW.md taxonomy.
- [x] **Documentation** — CLAUDE.md first-time-setup IS the documentation artifact.
- [x] **Commit message** — `docs(setup): add merge.ours.driver config to first-time-setup` (≤72 chars); co-author tag present.
