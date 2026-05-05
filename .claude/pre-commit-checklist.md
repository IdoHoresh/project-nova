# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: ADR-0006 Amendment 1 documenting production.tot Gemini-Pro → Claude-Sonnet-4.6 swap, motivated by 2026-05-06 pilot's Pro RPD-quota + rate-limit-clustering findings (1 file, +50 lines, doc-only).
- [x] **Verification** — `git diff --cached` scanned, no secrets (amendment cites commit hashes + spec section numbers + cost figures, no API keys); pre-commit lint trio runs on file edit; implementation commit ships next, separate atomic.
- [x] **Review** — N/A: REVIEW.md taxonomy match `docs/**` → "No — skip with reason 'doc-only'". Documentation-only ADR amendment, no production code changes in this commit.
- [x] **Documentation** — amendment follows the Amendment-N pattern from ADR-0007 (Why → What changes → Cost/perf → What does NOT change → Reversibility → References). Cross-references the 2026-05-06 LESSONS entries + the pilot CSVs that inform the decision.
- [x] **Commit message** — `docs(adr): ADR-0006 Amendment 1 — production.tot Pro→Sonnet for cliff-test`, body summarizes RPD-quota + rate-limit-clustering rationale, co-author tag present.
