# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: CI fix — e2e smoke skip-guard handles empty-string env vars (1 file, 5 lines changed)
- [x] **Verification** — diff scanned, no secrets; logic verified against CI failure log (empty env → pydantic ValidationError on missing keys → exit 1 → assertion fail). Old guard `"X" not in os.environ` is False for empty-but-present; new guard `not os.environ.get("X")` is True for both absent and empty. CI run 25391469783 reproduces; fix targets root cause.
- [x] **Review** — N/A: REVIEW.md taxonomy `N/A: mechanical` (test-only skip-guard fix; no production code, no novel surface; Layer 1.5 pre-push hook covers on push)
- [x] **Documentation** — inline comment in test references gotcha #3 (CLAUDE.md "Empty shell env vars shadow .env"), explaining why CI exposes empty values
- [x] **Commit message** — `fix(cliff-test): e2e skip-guard handles empty-string env vars`, body explains why (CI failure root cause), co-author tag present
