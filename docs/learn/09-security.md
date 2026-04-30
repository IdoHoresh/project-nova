# 09 — Security: Keys, Secrets, and Not Getting Burned

> Security is a top-priority requirement. This doc explains why, what can go wrong, and how Project Nova defends against it. Beginner-friendly.

## The core problem in one paragraph

The Anthropic API costs money per call. Your API key is what proves to Anthropic that the call is yours and authorizes them to bill you. If anyone else gets your key, they can run unlimited Claude calls on your account until you notice. The repository is public, so if your key ever lands in git, the moment you push it, automated scanners find it and (worst case) someone is racking up your bill within minutes.

This is not theoretical. It happens daily on GitHub. Project Nova takes it seriously.

## Why public repos are dangerous for keys

Within ~60 seconds of pushing a commit to a public GitHub repo:

- GitHub's own secret scanner sees it
- Third-party scanners (run by attackers) see it
- Search engines may begin to index it

Even if you delete the file 30 seconds later and force-push, the key is already harvested. Treat any key that has ever touched a public commit as **compromised** — rotate it.

This is why Project Nova has multiple defenses, not just one. No single defense is perfect.

## The five layers of defense

Think of it like an onion. To leak a secret, all five layers have to fail simultaneously.

### Layer 1 — `.gitignore` blocks secret filename patterns

The `.gitignore` file at the root of the repo lists every filename pattern that secrets typically live in: `.env`, `*.key`, `*.pem`, `secrets.json`, `credentials.json`, anything starting with `api_key`, etc. Git refuses to track any file matching these patterns.

This catches the most common mistake: putting your API key in a `.env` file (which is the right place) and accidentally trying to commit that `.env`. Git will silently skip it.

**Limitation:** `.gitignore` only protects FILES that match its patterns. If you hardcode a key inside a `.py` or `.ts` file, `.gitignore` doesn't help. That's what the next four layers are for.

### Layer 2 — Code loads secrets only from environment variables

The rule: **no secret ever appears literally in source code.** Every key is read from `os.environ` (Python) or `process.env` (Node) at runtime.

Right way:
```python
import os
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)
```

Wrong way:
```python
client = Anthropic(api_key="sk-ant-abc123...")  # NEVER DO THIS
```

The wrong way is what `.gitignore` cannot save you from.

To set environment variables locally, you copy `.env.example` to `.env`, fill in your real keys, and your code reads from `.env` at startup (using a library like `python-dotenv`). The `.env` file stays on your machine, never goes into git.

### Layer 3 — Pre-commit hook (gitleaks) catches accidents

Even with rules 1 and 2, humans slip. You're tired, you commit a hardcoded key, you push.

**gitleaks** is a tool that scans your staged git changes for patterns that look like secrets (Anthropic key prefix `sk-ant-`, OpenAI prefix `sk-`, common token shapes, etc.). When wired up as a pre-commit hook, gitleaks runs every time you try to commit. If it finds something suspicious, the commit is blocked until you fix it.

Setup:
```bash
brew install gitleaks
# Hook up the pre-commit script per SECURITY.md
```

This is the "trip wire" layer.

### Layer 4 — GitHub server-side scanning + push protection

Even if gitleaks fails (you didn't install it, you bypassed it, the pattern was novel), GitHub itself scans every push. For Project Nova:

- ✅ **Secret scanning** is enabled — GitHub examines every commit for known-secret patterns
- ✅ **Push protection** is enabled — GitHub will *refuse* the push if a known-secret pattern is found, before the commit ever reaches the server. This is the safety net.
- ✅ **Dependabot security updates** is enabled — automated PRs to fix vulnerable dependencies

If a key matches a known pattern (Anthropic, OpenAI, Stripe, etc.), Anthropic and other partners get notified by GitHub and may auto-revoke the key. Helpful in the worst case.

### Layer 5 — Spending guardrails

Even if all four layers above fail and your key leaks publicly, the financial damage is bounded:

- **Anthropic Console:** set a monthly spending limit. If reached, the key stops working until you raise it manually.
- **In-code guardrail:** Project Nova reads `NOVA_DAILY_BUDGET_USD` from env. The agent counts cost per VLM call and halts if it exceeds the cap. Useful for development too — prevents a buggy infinite loop from burning $500.

## Things that are NOT secrets and CAN be in git

To make this concrete, here's what you SHOULD commit:

- `.env.example` — a template showing what env vars your code expects, with no real values
- `README.md`, `LICENSE`, `SECURITY.md` — public docs
- All source code (provided no secrets are in it)
- All design specs and primers
- `.gitignore` itself — that's how you tell git what to skip

And here's what you should NEVER commit:

- `.env` — the real one with your keys
- Any file with "secret" or "credential" in its name
- API keys, tokens, passwords, certificates (`.pem`, `.key`, `.p12`)
- JSON service account files
- Hardcoded keys inside source files

## What to do if a key leaks

Step 1, before anything else: **rotate the key.** Go to https://console.anthropic.com/, revoke the leaked key, generate a new one. Do this within minutes, not hours.

After rotation, the leaked key is just a dead string. You can optionally scrub it from git history with `git filter-repo`, but that's secondary — the rotation is what stops the bleeding.

Full procedure in `SECURITY.md`.

## Pre-commit habits

Before every commit, two seconds:

```bash
git diff --cached       # eyeball your staged changes
gitleaks protect --staged  # automated scan
```

Before every push, two seconds:

```bash
gitleaks detect --redact  # scan whole repo state
```

Boring. Effective.

## Threat model in plain terms

Project Nova's security is calibrated for the real risks:

- ✅ **Accidental key commits** — covered by all five layers
- ✅ **Public-repo exposure of leaked keys** — covered by GitHub server-side scanning
- ✅ **Cost-amplification attacks** — covered by the spending guardrail

Out of scope (these need separate solutions):

- ❌ A compromised laptop — OS keychain handles those secrets, not Project Nova
- ❌ Malicious npm/pip dependencies that exfiltrate env vars — partial mitigation through pinning + review
- ❌ Production deployment with a public WebSocket — v1 is local only; deployment hardening lands when v2/v3 deploy

## Summary

| Layer | What it does |
| --- | --- |
| `.gitignore` | Refuses to track secret files |
| Env-only loading | No secret ever in source code |
| `gitleaks` pre-commit | Local scan, blocks bad commits |
| GitHub scanning + push protection | Server-side safety net, blocks bad pushes |
| Spending cap | Bounds damage if all else fails |

If you're new to API security: read `SECURITY.md` once, set up gitleaks once, then check `git diff --cached` before each commit. That covers ~99% of real-world cases.
