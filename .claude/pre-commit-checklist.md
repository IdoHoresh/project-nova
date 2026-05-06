# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/adr-0007-power-analysis`. Carrying forward `.gitattributes merge=ours` fix for pre-commit-checklist.md — same commit as on adr-0009 branch, ensures PR #14 also has the fix before merging.
- [x] **Verification** — `git diff --cached`: only `.gitattributes` (7 lines added). No secrets. No code touched.
- [x] **Review** — N/A: `.gitattributes` is CI-config/tooling-only per REVIEW.md taxonomy.
- [x] **Documentation** — comment in `.gitattributes` explains the invariant.
- [x] **Commit message** — `chore(git): merge=ours for pre-commit-checklist — eliminate parallel-branch conflicts` (≤72 chars); co-author tag present.
