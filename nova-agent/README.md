# nova-agent

Python implementation of Project Nova's cognitive architecture.

## Setup

```bash
cd nova-agent
uv venv
uv sync --extra dev
cp ../.env.example ../.env  # then fill in ANTHROPIC_API_KEY
uv run pytest
```

## Run

```bash
uv run nova
```

See [`../docs/specs/2026-04-30-project-nova-design.md`](../docs/specs/2026-04-30-project-nova-design.md).
