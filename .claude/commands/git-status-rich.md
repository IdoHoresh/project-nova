---
description: Comprehensive git state inspection — shows uncommitted changes, branch divergence from main, recent commits, and any anomalies. Use at the start of any session to orient.
allowed-tools: Bash
---

Run a thorough git state inspection and report concisely. Use at session start to orient on where the branch is.

**Sequence (run in parallel where possible):**

1. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git status --short`
2. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git log --oneline -10`
3. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git branch --show-current`
4. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git rev-parse HEAD`
5. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git status -sb` (branch ahead/behind tracking)
6. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 && git stash list`

**Output format:**

```
BRANCH: claude/practical-swanson-4b6468 @ abc1234
TRACKING: ahead N / behind M of origin

UNCOMMITTED:
  M path/to/file.py
  ?? new/file.md

RECENT COMMITS:
  abc1234 feat(scope): ...
  def5678 fix(scope): ...
  [...]

STASHES: 0  (or list if any)
```

If anything looks anomalous (unexpected branch, large uncommitted set, behind origin), flag it explicitly. Otherwise report the clean state and we proceed.
