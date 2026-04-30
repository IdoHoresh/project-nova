# Security Policy — Project Nova

Security is a top-priority requirement for this project. The repository is public, so any leaked secret is publicly exposed within minutes of being pushed.

This document defines how secrets are handled, the layers of defense in place, and the procedure to follow if a secret is leaked.

---

## What counts as a secret

Anything that grants access to a paid service, a private resource, or your identity. For Project Nova specifically:

- **Google AI Studio API key** (`AIzaSy...`) — primary risk; grants access to your paid Gemini quota (used for default decisions, ToT deliberation, OCR fallback in v1)
- **Anthropic API key** (`sk-ant-...`) — secondary risk; grants access to your paid Claude account (used for reflection + demo recording in v1)
- **Other VLM provider keys** (OpenAI) if used
- **Personal access tokens** (GitHub, Vercel, etc.)
- **Service-account JSON files**
- **Database connection strings with embedded passwords**
- **Recordings or screenshots that capture personal information**

Anything in this list MUST never be committed to git.

---

## Five layers of defense

### Layer 1 — `.gitignore` patterns

The repository's `.gitignore` blocks all the standard secret filename patterns: `.env`, `.env.*`, `*.key`, `*.pem`, `secrets.json`, `credentials.json`, `service-account*.json`, `*api_key*`, `*apikey*`, `.anthropic`, `.openai`, etc.

**However** — `.gitignore` only protects files that *match* its patterns. A secret hardcoded into a `.py` or `.ts` source file is not caught by `.gitignore`. The other four layers exist to catch that case.

### Layer 2 — Environment-variable-only loading

All secrets in code MUST be loaded from environment variables. NEVER from a hardcoded string, NEVER from a checked-in JSON file, NEVER from a command-line flag with the value embedded.

The canonical pattern in `nova-agent/`:

```python
import os
from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. "
        "Copy .env.example to .env and fill it in. See SECURITY.md."
    )

client = Anthropic(api_key=api_key)
```

In `nova-viewer/` (Next.js), secrets must NEVER be exposed to the browser. Use server-only env vars (no `NEXT_PUBLIC_` prefix) and call them from server actions or API routes — never from client components.

The brain-panel viewer in v1 doesn't actually need any secrets — it talks to the local Nova agent over WebSocket, and the agent owns the VLM credentials. Keep it that way.

### Layer 3 — Local pre-commit hook (gitleaks)

Install [gitleaks](https://github.com/gitleaks/gitleaks) as a pre-commit hook to scan staged changes for secret-like patterns BEFORE the commit lands:

```bash
brew install gitleaks
cd /path/to/project-nova
gitleaks protect --staged --redact   # one-shot scan of staged changes
```

To wire it into pre-commit automatically (recommended):

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
gitleaks protect --staged --redact || {
    echo "❌ Possible secret detected in staged changes. Aborting commit."
    echo "   Review with: gitleaks protect --staged --verbose"
    exit 1
}
EOF
chmod +x .git/hooks/pre-commit
```

This catches accidental secret commits before they hit the local repo, let alone GitHub.

### Layer 4 — GitHub secret scanning (server-side)

Public GitHub repos have **secret scanning** enabled by default. Anthropic API keys are on the list of patterns GitHub scans for. If a key is pushed, GitHub will:

1. Detect it within minutes
2. Notify the repository owner via email
3. (For partnered providers like Anthropic) automatically notify the provider, who may auto-revoke the key

**Push protection** is the stronger version — it BLOCKS pushes containing detected secrets.

#### Currently enabled on this repo (verified via `gh api`)

- ✅ `secret_scanning` — scanning enabled
- ✅ `secret_scanning_push_protection` — pushes containing secrets are BLOCKED at the GitHub edge
- ✅ `dependabot_security_updates` — automated dependency vulnerability fixes
- ⚠ `secret_scanning_non_provider_patterns` — currently disabled; enable manually in repo Settings → Code security
- ⚠ `secret_scanning_validity_checks` — currently disabled; enable manually in repo Settings → Code security

To verify:

```bash
gh api repos/IdoHoresh/project-nova --jq '.security_and_analysis'
```

The two ⚠ items can be toggled via the GitHub UI:
1. Go to https://github.com/IdoHoresh/project-nova/settings/security_analysis
2. Enable "Scan for non-provider patterns" and "Validity checks"

Both are free for public repos. Worth doing once.

### Layer 5 — Spending guardrails

Even if a key is leaked and abused, a daily-spend cap on the Anthropic Console limits the blast radius. Set:

- **Anthropic Console:** monthly spending limit + per-key rate limit
- **In-code:** the `NOVA_DAILY_BUDGET_USD` env var (see `.env.example`); the agent counts cost per VLM call and refuses to continue past the cap

This is defense-in-depth — even if every other layer fails, the financial damage is bounded.

---

## What to do if a key is leaked

If a secret has been committed to git (whether or not it has been pushed yet):

### Step 1 — Rotate the key IMMEDIATELY

Do this BEFORE anything else. Do not wait, do not try to "fix it with git rebase first." A leaked key is compromised the moment it touches a public repo, even if you push-force-deleted it seconds later — automated scanners pick up keys in <60 seconds.

- **Google AI Studio key:** https://aistudio.google.com/apikey → revoke the leaked key, generate a new one
- **Anthropic key:** https://console.anthropic.com/ → revoke the leaked key, generate a new one
- **GitHub token:** https://github.com/settings/tokens → revoke
- **Other providers:** equivalent action in their console

### Step 2 — Update your `.env` with the new key

Confirm the new key works:

```bash
# Quick test
ANTHROPIC_API_KEY=$NEW_KEY python -c "
from anthropic import Anthropic
print(Anthropic().models.list().data[0].id)
"
```

### Step 3 — Remove the secret from git history (optional, secondary)

After the key is rotated, the leaked one is just a dead string. But for hygiene, you can scrub it from git history:

```bash
# Use BFG Repo-Cleaner or git-filter-repo for this
brew install git-filter-repo
git filter-repo --replace-text <(echo 'sk-ant-OLD_LEAKED_KEY==>REDACTED')
git push --force-with-lease origin main
```

This is OPTIONAL. The rotated key is already useless. Skipping this step is fine for a low-risk situation; it's only worth doing if the leak is genuinely embarrassing or if you fear future scanners.

### Step 4 — Audit what else might have been exposed

If one secret leaked, others might have too. Run:

```bash
gitleaks detect --redact   # scans full git history
```

Rotate anything else flagged.

---

## Pre-commit checklist

Before every commit, run:

```bash
git diff --cached         # review staged changes manually
gitleaks protect --staged # automated scan
```

Before every push, run:

```bash
gitleaks detect --redact  # scan full repo state
```

These are habits, not perfect defenses — Layer 4 (GitHub push protection) is the safety net.

---

## Reporting a security issue

If you discover a security issue in Project Nova (a leaked credential, a vulnerability, an auth bypass):

- **Do NOT open a public GitHub issue.**
- Email the maintainer at `ihoresh07@gmail.com` with subject `[SECURITY] Project Nova`.
- Expect a response within 7 days.

---

## Security review — required before each milestone

The design spec lists v1 milestones at end-of-week-1, end-of-week-3, and end-of-week-6. At each of these milestones, run a security review:

1. `gitleaks detect --redact` (full-history scan)
2. `git log --all --full-history -p -- '*.env' '*secrets*' '*credentials*'` (verify nothing snuck in)
3. Check the GitHub Security tab → secret scanning alerts
4. Confirm `.env.example` does not contain real values
5. Confirm `gh api repos/IdoHoresh/project-nova --jq '.security_and_analysis'` shows secret scanning + push protection both `enabled`

If any check fails, the milestone is not done.

---

## Threat model — what we're protecting against

- **Accidental key commits** (most common). Layers 1–4 catch these.
- **Compromised dev machine** — out of scope; the OS keychain owns these secrets.
- **Malicious dependency** that exfiltrates env vars — partial mitigation only; pin deps and review changes.
- **Production deployment with public WebSocket** — out of scope for v1 (local only). When v2/v3 add deployment, this section gets a follow-up.

The point of this doc is to make accidental leaks dramatically less likely and survivable when they happen.
