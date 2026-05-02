---
description: Security rules for sensitive paths (secrets, LLM, bus, env)
paths:
  - '**/.env*'
  - 'nova-agent/src/nova_agent/config*.py'
  - 'nova-agent/src/nova_agent/llm/**/*.py'
  - 'nova-agent/src/nova_agent/bus/**/*.py'
  - 'nova-viewer/lib/websocket.ts'
---

# Security Rules

> Read this before editing any file matching the paths above.
> Path-scoped companion to `CLAUDE.md` and the `security-reviewer`
> subagent.

## Crown jewels

These are the things that must not leak:

1. **API keys** — Anthropic, Google (Gemini), future OpenAI / vLLM
   tokens. Loaded from `.env` via pydantic-settings. Never logged,
   never published on the bus, never echoed in error messages.
2. **LLM prompts** — may legitimately contain board state, persona
   context, retrieved memories. Must NOT contain user-identifying
   data, account info, internal trace IDs, or any environment
   secret.
3. **The WebSocket bus** — listens on localhost only with no auth.
   Anything published is visible to anything that connects to
   `ws://127.0.0.1:8765`. Treat it as untrusted output for secrets
   purposes.

## Hard rules

- **Never hardcode secrets** in any tracked file, including tests
  and example configs. If a fixture needs an API key, mark the
  fixture `@pytest.mark.skip` unless `CI_INTEGRATION` is set, and
  read the key from env.
- **No default values for secret env vars.** `os.getenv("KEY",
  "default")` is a leak risk; use pydantic-settings with no default
  so missing keys fail fast.
- **`pydantic-settings` must use `env_ignore_empty=True`.**
  Otherwise an empty shell export shadows the populated `.env` and
  produces confusing "no API key" errors. Gotcha #3 in CLAUDE.md.
- **Validate every external boundary with pydantic** — LLM
  responses, bus events accepted from outside, file inputs, env
  vars.
- **No secrets in error messages, logs, or exception chains.** When
  catching auth errors, scrub the credential field before logging.
- **`subprocess.run` only**, never `os.system`. Never `shell=True`
  with f-string interpolation of any data not under our control.
- **ADB calls** — currently no untrusted input flows in, but flag
  any new path that does.
- **LLM prompts** — scrub PII, scrub raw env values, scrub trace
  IDs that map back to internal infra.
- **Memory writes** — go through `MemoryCoordinator`'s typed API
  only. Never raw SQL string-format. Never raw LanceDB / SQLite
  calls outside the memory module.

## Viewer-specific

- `dangerouslySetInnerHTML` — forbidden unless the security-reviewer
  subagent explicitly approves.
- `localStorage` / `sessionStorage` — must not contain
  agent-internal metadata that could be read by another origin if a
  future deploy moves the viewer onto a shared host.
- Next.js server actions / API routes — currently none exist. Flag
  any appearance, and they must not call into the agent process
  directly.
- `eval` / `new Function(...)` / dynamic code execution — never.

## Repo hygiene

- `.env*` patterns in `.gitignore` — verify before commit.
- gitleaks pre-commit + CI hooks — never bypass with `--no-verify`.
- New dependencies — check for typosquats, unmaintained packages,
  known-CVE versions before adding.

## When to invoke the security-reviewer subagent

- New LLM adapter
- New bus event type
- New env var or `.env` field
- Anything touching `nova_agent/config*.py` or `nova_agent/llm/`
- Anything that runs subprocess / shell commands
- Any `eval`, `exec`, dynamic code path
- Before publishing any artifact (demo recording, blog post,
  external review brief) — verify no secret slipped in
