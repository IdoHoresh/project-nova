---
description: Run the full nova-viewer check trio (vitest + tsc + eslint) and report pass/fail per stage.
allowed-tools: Bash, TodoWrite
---

Run the full check trio for `nova-viewer` and report results per stage.

**Steps (in order, stop on first failure):**

1. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-viewer && pnpm test 2>&1 | tail -10`
   Report: passed test count, failed test count. If any failed, show the failing test names.

2. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-viewer && npx tsc --noEmit 2>&1 | tail -10`
   Report: clean or list of type errors with file:line references.

3. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-viewer && pnpm run lint 2>&1 | tail -10`
   Report: clean or list of lint errors.

**Output format:**

```
✓ vitest: 47/47 passed
✓ tsc: clean
✓ eslint: clean
```

If any stage fails, stop and surface the actual error output. Don't silently continue past failures.

This is the gate that nova-viewer code must clear before commit. If you're running this after edits, fix any failure before continuing.
