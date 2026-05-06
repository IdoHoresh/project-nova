# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/adr-0007-power-analysis` (sub-branch off `main`). Atomic unit: ADR-0007 §A2 power analysis amendment — method, formula, σ̂ placeholder table, and pre-committed adjustment rules. 1 file (`docs/decisions/0007-blind-control-group-for-cliff-test.md`), +101 insertions, 0 code touched. σ̂ values are [TBD]; placeholder fills when pilot CSV is generated.
- [x] **Verification** — `git diff --cached` scanned (no secrets, no API keys, no PII; ADR addition only). `/check-agent` N/A: doc-only, no Python touched. `/check-viewer` N/A: doc-only, no TS touched.
- [x] **Review** — N/A: doc-only per REVIEW.md taxonomy (`docs/**/*.md` row). Layer 1.5 pre-push hook + PR-time `claude-code-action` (Layer 2) provide backstop coverage.
- [x] **Documentation** — ADR-0007 Amendment 2 IS the documentation artifact. Adds §A2 with test structure, σ̂ source, placeholder table, and two-branch adjustment rules (σ̂ > 4 → raise N; σ̂ < 2 → raise Δ_min).
- [x] **Commit message** — `docs(adr): ADR-0007 §A2 — power analysis, σ̂ placeholder, adjustment rules` (≤72 chars); body explains why + deferred fill; co-author tag present.
