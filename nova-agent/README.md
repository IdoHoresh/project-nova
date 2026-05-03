# nova-agent

Python implementation of Project Nova's cognitive architecture.

## Setup

```bash
cd nova-agent
uv venv
uv sync --extra dev
cp ../.env.example ../.env  # then fill in GOOGLE_API_KEY (dev tier; ANTHROPIC_API_KEY needed only for production/demo)
uv run pytest
```

### macOS + repo on `~/Desktop`

Sequoia App Management auto-applies `UF_HIDDEN` to files under `~/Desktop`, and Python 3.14's site
loader skips hidden `.pth` files. The editable install (`_editable_impl_nova_agent.pth`) becomes
invisible to `uv run nova`, so the CLI fails with `ModuleNotFoundError: nova_agent` even though
`pytest` works (pytest uses `pythonpath = src` from `pytest.ini`).

Workaround — point uv at a venv outside `~/Desktop`:

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
uv sync --extra dev
uv run nova
```

Set the variable in your shell session (or per-command) only when working in this repo; setting it
globally would redirect every uv project at the same venv path.

## Run

```bash
uv run nova
```

See [`../docs/specs/2026-04-30-project-nova-design.md`](../docs/specs/2026-04-30-project-nova-design.md).
