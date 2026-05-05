# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: e2e smoke now opt-in via NOVA_E2E_SMOKE=1 (1 file, +9/-3 lines)
- [x] **Verification** — diff scanned, no secrets; local pytest confirms SKIP fires in normal env (1 skipped in 1.5s, no LLM calls). Prior fix attempt (truthy guard) failed in CI because the workflow now exposes real API keys (per resume-point one-time setup), making any presence-based guard wrong against `_run_cli`'s strip behavior.
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (test-only opt-in skip; no production paths; Layer 1.5 pre-push covers)
- [x] **Documentation** — inline rationale references the conflict between `_run_cli`'s strip-design and e2e's need-keys-design
- [x] **Commit message** — `fix(cliff-test): make e2e smoke opt-in via NOVA_E2E_SMOKE=1`, body explains the strip-vs-keys design conflict, co-author tag present
