---
description: Run a focused security-review pass on the current branch. Checks for leaked secrets, unsafe code patterns, dependency vulnerabilities, and unsafe data handling.
allowed-tools: Bash, Read, WebFetch, Agent
---

Invoke the `superpowers:security-review` skill to do a focused pass over the current branch's recent commits.

**Scope:**

1. **Secret leakage check.** Run gitleaks against the branch (it's installed as a pre-commit hook; this re-runs it explicitly):
   ```bash
   ROOT=$(git rev-parse --show-toplevel)
   cd "$ROOT"
   gitleaks detect --source . --verbose 2>&1 | tail -30
   ```
   Plus a manual grep for common patterns that gitleaks might miss:
   ```bash
   grep -rn "sk-ant-\|AIzaSy\|sk_live_\|sk_test_" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.md" --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git . 2>&1 | head
   ```

2. **Dependency vulnerability scan:**
   ```bash
   ROOT=$(git rev-parse --show-toplevel)
   cd "$ROOT/nova-viewer" && pnpm audit --prod --audit-level=moderate 2>&1 | tail -20
   ```
   For Python: pip-audit isn't currently configured; flag this as a follow-up if not present.

3. **Unsafe code patterns.** grep for:
   - `eval(` / `exec(` in Python or JavaScript
   - `dangerouslySetInnerHTML` in React
   - `subprocess.shell=True` in Python
   - `os.system(` in Python
   - Hardcoded credentials anywhere
   - Direct `os.environ[X]` reads bypassing Settings

4. **Data handling check.** Verify:
   - `.env` and `.env.local` not committed (`git ls-files | grep -E "^\.env"` should return only `.env.example`)
   - No `.db` / `.sqlite` files committed (game memory should be local-only)
   - No screenshots / personal data committed under `data/local/` or `screenshots/`

5. **Network surface check.** For nova-agent's bus.websocket.py: confirm it binds to 127.0.0.1 by default (not 0.0.0.0). For nova-viewer's WebSocket client: confirm it reads from configured host, doesn't accept arbitrary URLs.

**Output format:**

```
SECURITY PASS — <current branch>
═══════════════════════════════════════════════
gitleaks: clean / N findings
deps (pnpm audit): N moderate, N high, N critical
unsafe patterns: clean / N findings
data handling: clean / N issues
network surface: clean / N issues

ACTION ITEMS (in priority order):
  1. ...
  2. ...
```

If clean across the board, report `ALL GREEN` and the date stamp. If issues found, prioritize by severity: critical/high → fix before next commit; moderate → file for next session; low → note in `LESSONS.md`.

This should be run before any v1.0.0 tag, before any external code share, and quarterly otherwise.
