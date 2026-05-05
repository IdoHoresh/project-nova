# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: lower `DEFAULT_CONCURRENCY` 8→4 in `cliff_test.py` to address Pro rate-limit clustering surfaced in 2026-05-06 pilot (1 file, +9/-2 lines).
- [x] **Verification** — `git diff --cached` scanned, no secrets; `/check-agent` trio clean (267 pytest passed, mypy strict clean, ruff clean); root cause confirmed in pilot data — 3/3 Carla aborts in 2026-05-06 pilot show all 4 ToT branches `RetryError[ClientError]` within <1s of each other (rate-limit cluster), not budget starvation.
- [x] **Review** — N/A: REVIEW.md taxonomy match `nova-agent/src/**` would normally require code-reviewer. Skipping in-session for this small atomic fix; auto Layer 1.5 pre-push hook will run code-review at push time. The change is a single constant + arg-default unification + comment; no new logic, no new types, no new boundaries. Per `feedback_subagent_dispatch_selectivity`: small fixes mirroring debugged data don't warrant per-commit Layer-1 manual dispatch.
- [x] **Documentation** — inline comment cross-references the 2026-05-06 pilot's empirical finding (per-branch failure rate, joint-failure clustering) and gives tune-up/tune-down guidance for future operators.
- [x] **Commit message** — `fix(cliff-test): lower default concurrency 8→4 to absorb Pro rate-limits`, body explains the per-branch vs trial-level failure-rate math, references the 2026-05-06 pilot evidence, co-author tag present.
