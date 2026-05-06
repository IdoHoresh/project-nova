# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/methodology-trauma-rewrite`. Atomic unit: Task 1a of workflow-simplification batch — remove claude-checklist-check + claude-checklist-reset local hooks from .pre-commit-config.yaml.
- [x] **Verification** — diff scanned, no secrets. `/check-agent` N/A: config-only. `/check-viewer` N/A: config-only.
- [x] **Review** — N/A: Claude-tooling-only per REVIEW.md taxonomy (`.pre-commit-config.yaml` is workflow infrastructure).
- [x] **Documentation** — `.pre-commit-config.yaml` IS the documentation artifact (workflow config).
- [x] **Commit message** — `chore(workflow): remove claude-checklist hooks from pre-commit config` (≤72 chars); co-author tag present.
