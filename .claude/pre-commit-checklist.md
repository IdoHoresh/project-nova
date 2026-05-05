# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — feature branch claude/practical-swanson-4b6468, atomic single coherent unit (cost-optimization rules: redteam.md Step 0 lighter triage + 5-line checklist template), 2 files / ~75 lines net
- [x] **Verification** — git diff --cached scanned for secrets clean; N/A: doc-only / Claude-tooling-only commit, no code paths to gate
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: Claude-tooling-only` (slash command + checklist file; no production code)
- [x] **Documentation** — N/A: memory files updated (feedback_subagent_dispatch_selectivity, feedback_session_hygiene, MEMORY.md index) — those live in ~/.claude/projects/, not git-tracked
- [x] **Commit message** — `chore(workflow): cost-opt rules — redteam triage + 5-line checklist`, body explains why (red-team-modulated cost optimizations from 2026-05-05 /usage audit), co-author tag present
