# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — feature branch claude/practical-swanson-4b6468, atomic single coherent unit (Test Runner spec for Phase 0.7 cliff-test orchestrator), 1 file / +589 lines net
- [x] **Verification** — git diff scanned for secrets, none found; N/A: doc-only commit, no code paths to gate
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: doc-only` (spec narrative document; no code, no config, no production paths)
- [x] **Documentation** — spec is itself the documentation; LESSONS already updated in prior commits (031d6c6, 1f3a291, 0e3bcc6); CLAUDE.md / ARCHITECTURE.md / methodology.md unchanged (spec consumes them, doesn't redefine)
- [x] **Commit message** — `docs(spec): Phase 0.7 Test Runner design spec`, body explains why (last Phase 0.7 prep blocker; six brainstorm rounds locked Q1-Q6), co-author tag present
