# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: pass `thinking_budget` to Gemini-flash decision/bot LLMs (=0) and Gemini-pro tot LLM (=1024) in `cliff_test._build_llms` (3 files staged: src + test + LESSONS, +95/-0 lines)
- [x] **Verification** — `git diff --cached` scanned, no secrets (test uses literal "fake-google-key-for-test" / "fake-anthropic-key-for-test" strings; gitleaks regex requires real Google/Anthropic key prefixes); `/check-agent` trio clean (267 pytest passed, mypy strict clean, ruff clean); pilot calibration repro confirmed Gemini-flash thinking_budget=None emits `tokens_out=8` truncated JSON.
- [x] **Review** — `/code-review` dispatched; APPROVE with one WARN (pre-existing bare-except at cliff_test.py:471, captured as Task #10 follow-up) and one NIT (test side-effect on data dirs, accepted). REVIEW.md taxonomy match: `nova-agent/src/**` + `nova-agent/tests/**`; security-reviewer not required (no llm/config/bus modification, only kwarg routing).
- [x] **Documentation** — inline comment in `_build_llms` cross-references `main.py:165-193` and `gemini_client.py:53-58`; LESSONS.md entry captures the failure mode + fingerprint + how-to-apply for future call sites.
- [x] **Commit message** — `fix(cliff-test): pass thinking_budget to Gemini build_llm calls`, body explains why Flash without thinking_budget=0 truncates output, references `main.py` canonical pattern, co-author tag present.
