# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on claude/practical-swanson-4b6468; atomic unit: 2 new LESSONS entries (Carla fast-reaction-vs-prediction rigor rule + Gemini Pro 1000 RPD quota math) capturing 2026-05-06 session findings.
- [x] **Verification** — `git diff --cached` scanned, no secrets (lessons cite commit hashes + filenames + spec section numbers, no API keys); pre-commit lint trio runs on file edit.
- [x] **Review** — N/A: REVIEW.md taxonomy match `*.md` → "No — skip with reason 'doc-only'". Documentation-only addition, no production code changes.
- [x] **Documentation** — entries follow existing LESSONS.md format (date + cost + what happened + lesson + how to apply). Top-of-section placement preserves newest-first ordering. Both entries cross-reference the relevant commit hashes (ed90695, 60ac3bf, 9559367) and spec sections (§2.4, §7.4) for future-reader navigation.
- [x] **Commit message** — `docs(lessons): capture 2026-05-06 pilot findings — Pro RPD limit + Carla fast-reaction rigor rule`, body summarizes both entries, co-author tag present.
