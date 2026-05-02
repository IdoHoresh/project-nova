---
description: Run the full nova-agent check trio (pytest + mypy strict + ruff) and report pass/fail per stage.
allowed-tools: Bash, TodoWrite
---

Run the full check trio for `nova-agent` and report results per stage.

**CRITICAL — set the env var first.** Without `UV_PROJECT_ENVIRONMENT`, `uv run` will fail on macOS due to the UF_HIDDEN venv issue (see CLAUDE.md "Common gotchas"). Every command below assumes:

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
```

**Steps (in order, stop on first failure):**

1. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent && UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run pytest --tb=short -p no:warnings 2>&1 | tail -5`
   Report: passed count / total. If any failed, show test names + first traceback.

2. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent && UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run mypy 2>&1 | tail -5`
   Report: clean or list of type errors with file:line.

3. `cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent && UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run ruff check 2>&1 | tail -5`
   Report: clean or list of lint errors.

**Output format:**

```
✓ pytest: 140/140 passed
✓ mypy: Success: no issues found in 44 source files
✓ ruff: All checks passed!
```

If any stage fails, stop and surface the actual error output. Don't silently continue past failures.

This is the gate that nova-agent code must clear before commit.
