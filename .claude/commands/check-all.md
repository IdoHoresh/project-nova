---
description: Run both nova-agent and nova-viewer check trios. Use before any commit that touches both subprojects.
allowed-tools: Bash, TodoWrite
---

Run the full check trios for BOTH nova-agent AND nova-viewer in sequence. Use before any commit that touches both subprojects, or as a sanity check before pushing.

**Sequence:**

1. Run the agent check trio per `/check-agent`:
   - pytest (with `UV_PROJECT_ENVIRONMENT` set)
   - mypy
   - ruff

2. Run the viewer check trio per `/check-viewer`:
   - vitest
   - tsc --noEmit
   - eslint

**Output format:**

```
nova-agent:
  ✓ pytest: 140/140 passed
  ✓ mypy: clean
  ✓ ruff: clean

nova-viewer:
  ✓ vitest: 47/47 passed
  ✓ tsc: clean
  ✓ eslint: clean

ALL GREEN — safe to commit/push.
```

If anything fails, stop and surface the failing stage's full output. Do not give a summary that hides failures.
