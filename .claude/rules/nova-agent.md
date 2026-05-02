---
description: Rules for the Python cognitive architecture (nova-agent)
paths:
  - 'nova-agent/src/**/*.py'
  - 'nova-agent/tests/**/*.py'
---

# nova-agent Rules

> Read this before editing any file in `nova-agent/`. Path-scoped
> companion to `CLAUDE.md`. If a rule here contradicts CLAUDE.md, this
> file wins for nova-agent paths.

## Environment

- `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"`
  must be set before any `uv` command. The repo lives under
  `~/Desktop/`, where macOS auto-flags files with `UF_HIDDEN` and
  Python 3.14 then ignores them. Skipping this leads to
  `ModuleNotFoundError: nova_agent`. See gotcha #1 in CLAUDE.md.
- Python target: 3.11+ (current dev env runs 3.14)
- Package manager: `uv` exclusively. Never `pip install` directly.

## Code style

- mypy `strict = true` — no `# type: ignore` without an inline comment
  explaining the reason
- ruff check + ruff format — zero warnings, zero suppressions without
  justification
- Type hints on every public function signature, including return type
  (use `-> None` explicitly, don't omit)
- pydantic models for any data crossing a boundary: LLM responses,
  bus events, config, file inputs
- `pydantic-settings` with `env_ignore_empty=True` — otherwise empty
  shell exports shadow populated `.env` values (gotcha #3)
- `structlog` for logging, not `print` and not the stdlib `logging`
  module directly
- Async by default for I/O paths (LLM calls, WebSocket, ADB);
  synchronous only for pure compute

## Discipline

- TDD is mandatory for the cognitive layer (memory, affect, decision,
  reflection). Write the failing test first. Implement minimally.
  Refactor.
- Never catch bare `Exception` and continue silently. Either re-raise
  with context or log structured error fields. The ToT branch
  evaluator was burned by exactly this — see LESSONS.md.
- Keep functions short and single-purpose. If you're past ~30 lines,
  look for an extraction.
- pytest fixtures over inline mocks where possible. Fixtures
  document the shape of the world; inline mocks describe one test.

## Architecture

- The cognitive layer is **game-agnostic above the perception/action
  interface.** New game support means new perception/action code, not
  changes to memory / affect / decision modules.
- New `LLM` adapters implement the protocol in
  `nova_agent/llm/protocol.py`. No cloud-SDK leaks into call sites.
- Bus events: typed in `nova_agent/bus/protocol.py`, mirrored in
  `nova-viewer/lib/types.ts`. Never publish a raw string event name.
- Memory writes go through `MemoryCoordinator`, never raw LanceDB or
  SQLite calls.
- New ADR required when changing the cognitive architecture or
  inference stack — see `docs/decisions/`.

## Quality gate

Before commit (or use `/check-agent`):

```bash
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

All three must be clean. No `--no-verify` skipping.
