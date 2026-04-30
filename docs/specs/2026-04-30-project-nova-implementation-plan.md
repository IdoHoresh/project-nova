# Project Nova v1-FULL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a brain-inspired VLM agent that plays 2048 in an Android emulator with persistent affect, episodic memory, RPE-style dopamine, trauma-tagged memories, and a live brain-panel UI — shipped as a polished portfolio demo in 5–6 weeks.

**Architecture:** CoALA-grounded cognitive architecture. Python agent (`nova-agent/`) handles perception, memory, affect, decision, action; Next.js viewer (`nova-viewer/`) renders Nova's internal state in real time; talk over local WebSocket. Forked Unity 2048 (`nova-game/`) runs in Android Studio emulator. Anthropic Claude (vision) is the VLM. LanceDB + SQLite for memory. ADB for capture and swipes.

**Tech Stack:** Python 3.11+, `uv` for env management, Anthropic SDK, OpenCV, SQLite, LanceDB, FastAPI WebSocket. Next.js 14 (App Router), TypeScript, Tailwind, Framer Motion. ADB, scrcpy, OBS. Claude Design (Anthropic Labs research preview) for visual layouts.

**Reference:** Spec at [`docs/specs/2026-04-30-project-nova-design.md`](2026-04-30-project-nova-design.md). The spec is final and approved — do not redesign.

---

## Pre-flight checklist

Before starting Task 1, confirm all of the following. Each item is required.

- [ ] **Anthropic account with API key.** Required for the VLM and embeddings. Create at https://console.anthropic.com/. Set a monthly spending limit in the console (recommend $50 for v1 dev).
- [ ] **Claude Pro / Max / Team / Enterprise subscription.** Required for Claude Design (used Week 1 days 2–3 and Week 5).
- [ ] **macOS or Linux dev machine.** ADB / scrcpy / Android Studio all work on Windows but the plan assumes a Unix shell.
- [ ] **Android Studio installed** with at least one emulator AVD configured (recommend Pixel 6 API 34).
- [ ] **`adb` on PATH.** Verify: `adb version` returns successfully.
- [ ] **`scrcpy` installed.** macOS: `brew install scrcpy`. Verify: `scrcpy --version`.
- [ ] **Unity Hub + Unity 2022 LTS installed.** Required to fork and build the 2048 game APK.
- [ ] **`uv` installed** (modern Python tool). macOS: `brew install uv`. Verify: `uv --version`.
- [ ] **Node 20+ + `pnpm`** (or `npm`) installed.
- [ ] **`gitleaks` installed.** macOS: `brew install gitleaks`. Verify: `gitleaks version`.
- [ ] **OBS Studio installed.** For demo recording.
- [ ] **Repo cloned** at `/Users/idohoresh/Desktop/a` (already done — this is the working copy).
- [ ] **GitHub remote configured** at `origin = https://github.com/IdoHoresh/project-nova.git` (already done).
- [ ] **Read [`SECURITY.md`](../../SECURITY.md)** end-to-end before any commit involves credentials.
- [ ] **`.env` exists at repo root** with `ANTHROPIC_API_KEY` filled in. Confirm `git status` does NOT list `.env`.

---

## File structure

Top-level layout (most directories already scaffolded):

```
project-nova/
├── README.md                     # already exists
├── LICENSE                       # already exists
├── SECURITY.md                   # already exists
├── .env.example                  # already exists
├── .gitignore                    # already exists
├── docs/
│   ├── specs/
│   │   ├── 2026-04-30-project-nova-design.md
│   │   └── 2026-04-30-project-nova-implementation-plan.md   ← this file
│   ├── learn/                    # 9 primer docs (already exist)
│   └── design/v1/                # NEW — Claude Design mockups land here
│       └── README.md
├── nova-agent/
│   ├── pyproject.toml
│   ├── README.md
│   ├── pytest.ini
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_*.py
│   └── src/nova_agent/
│       ├── __init__.py
│       ├── main.py               # decision-loop entry point
│       ├── config.py             # env loading + settings
│       ├── budget.py             # NOVA_DAILY_BUDGET_USD guard
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py         # Anthropic wrapper
│       │   ├── structured.py     # JSON output validation + retry
│       │   └── embeddings.py
│       ├── perception/
│       │   ├── __init__.py
│       │   ├── capture.py        # ADB screencap
│       │   ├── ocr.py            # OpenCV digit OCR
│       │   ├── vlm_perception.py # VLM perception fallback
│       │   └── types.py          # BoardState
│       ├── action/
│       │   ├── __init__.py
│       │   └── adb.py            # swipes + verification
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── types.py
│       │   ├── episodic.py       # SQLite DAO
│       │   ├── semantic.py
│       │   ├── vector_store.py   # LanceDB
│       │   ├── importance.py
│       │   ├── retrieval.py
│       │   └── trauma.py
│       ├── affect/
│       │   ├── __init__.py
│       │   ├── types.py
│       │   ├── state.py          # update rules
│       │   ├── verbalize.py
│       │   └── rpe.py            # outcome evaluator + V
│       ├── decision/
│       │   ├── __init__.py
│       │   ├── prompts.py
│       │   ├── react.py
│       │   ├── tot.py
│       │   ├── arbiter.py
│       │   └── heuristic.py
│       ├── reflection/
│       │   ├── __init__.py
│       │   └── postmortem.py
│       └── bus/
│           ├── __init__.py
│           └── websocket.py
├── nova-viewer/
│   ├── package.json
│   ├── README.md
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── lib/
│   │   ├── websocket.ts
│   │   └── types.ts
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── globals.css
│       └── components/
│           ├── BrainPanel.tsx
│           ├── GameStream.tsx
│           ├── MoodGauge.tsx
│           ├── DopamineBar.tsx
│           ├── AffectLabel.tsx
│           ├── MemoryFeed.tsx
│           ├── MemoryCard.tsx
│           ├── ModeBadge.tsx
│           ├── ReasoningText.tsx
│           ├── ActionArrow.tsx
│           ├── TraumaIndicator.tsx
│           └── StatsFooter.tsx
└── nova-game/
    ├── README.md                 # fork + build instructions
    └── build-android.sh
```

---

## Conventions used by this plan

- **TDD throughout.** Every module has tests in `nova-agent/tests/test_<module>.py`. Write tests first, see them fail, implement minimally, see them pass, commit.
- **Commit per task.** Every task ends with a `git commit`. Conventional Commits format (`feat(scope): ...`, `fix(scope): ...`, `chore(scope): ...`).
- **Never bypass hooks.** `--no-verify` is forbidden. If gitleaks or pre-commit fails, fix the underlying issue.
- **Run gitleaks before each push.** `gitleaks protect --staged` is wired as a pre-commit hook (Task 2).
- **Type-check Python.** Use `mypy --strict` on `nova-agent/src/`. Errors block commit.
- **All shell commands assume cwd is repo root** unless stated otherwise.

---

# WEEK 0 — Pre-flight setup (Day 0)

## Task 0: Verify pre-flight checklist

**Files:** none

- [ ] **Step 1: Walk through the pre-flight checklist** at the top of this document. Tick every item.
- [ ] **Step 2: Run `gitleaks detect --redact`** at repo root. Expected: clean (no findings).
- [ ] **Step 3: Run `gh api repos/IdoHoresh/project-nova --jq '.security_and_analysis'`** and confirm `secret_scanning`, `secret_scanning_push_protection`, and `dependabot_security_updates` all show `enabled`.
- [ ] **Step 4: Visit** https://github.com/IdoHoresh/project-nova/settings/security_analysis and toggle "Scan for non-provider patterns" + "Validity checks" to enabled (one-time UI step that the API does not accept).
- [ ] **Step 5: Confirm `.env` exists locally and is NOT tracked.** Run `git ls-files | grep -i env`. Expected output: `.env.example` only.

If any check fails, stop and remediate before Task 1.

---

# WEEK 1 — Foundation

**Goal:** End-to-end loop running. Emulator boots 2048, Python agent screenshots it, sends it to Claude, parses a swipe action, executes it via ADB, repeats. No memory, no affect yet — just the pipeline. Brain-panel viewer scaffolded with a placeholder UI subscribed over WebSocket.

**Claude Design window:** Days 2–3 (Task 5 + Task 10). After ADB is wired and you have a real screenshot, use Claude Design to generate 3–5 alternate brain-panel layouts. Save mockups to `docs/design/v1/`.

**Security review:** End of Week 1 (Task 11).

---

## Task 1: Bootstrap nova-agent Python project

**Files:**
- Create: `nova-agent/pyproject.toml`
- Create: `nova-agent/pytest.ini`
- Create: `nova-agent/README.md`
- Create: `nova-agent/src/nova_agent/__init__.py`
- Create: `nova-agent/tests/__init__.py`
- Create: `nova-agent/tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "nova-agent"
version = "0.1.0"
description = "Project Nova — brain-inspired VLM agent that plays mobile games"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.39.0",
    "google-genai>=0.3.0",
    "python-dotenv>=1.0.1",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "opencv-python-headless>=4.10.0",
    "pillow>=10.3.0",
    "numpy>=1.26.0",
    "lancedb>=0.13.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=13.0",
    "structlog>=24.4.0",
    "tenacity>=9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
    "types-pillow",
]

[project.scripts]
nova = "nova_agent.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/nova_agent"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
strict = true
python_version = "3.11"
files = ["src/nova_agent"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
addopts = -ra -q --strict-markers
testpaths = tests
```

- [ ] **Step 3: Create the package init**

```python
# nova-agent/src/nova_agent/__init__.py
"""Project Nova — brain-inspired VLM agent."""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create test scaffolding**

```python
# nova-agent/tests/__init__.py
```

```python
# nova-agent/tests/conftest.py
import os
import pytest

@pytest.fixture(autouse=True)
def stub_env(monkeypatch):
    """Provide safe defaults so unit tests don't accidentally hit real APIs."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key-do-not-use")
    monkeypatch.setenv("NOVA_DAILY_BUDGET_USD", "0.00")  # 0 = unlimited in tests
    monkeypatch.setenv("NOVA_LOG_LEVEL", "WARNING")
```

- [ ] **Step 5: Create `nova-agent/README.md`**

```markdown
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
```

- [ ] **Step 6: Sync deps and verify**

```bash
cd nova-agent
uv venv
uv sync --extra dev
uv run pytest
```

Expected: `0 passed` (no tests yet, but suite runs cleanly).

- [ ] **Step 7: Commit**

```bash
git add nova-agent/
git commit -m "chore(agent): bootstrap nova-agent Python project"
```

---

## Task 2: Pre-commit hook + config module

**Files:**
- Create: `.git/hooks/pre-commit`
- Create: `nova-agent/src/nova_agent/config.py`
- Create: `nova-agent/tests/test_config.py`

- [ ] **Step 1: Wire gitleaks pre-commit hook**

```bash
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
set -e
gitleaks protect --staged --redact || {
    echo "❌ gitleaks found a possible secret in staged changes."
    echo "   Investigate with: gitleaks protect --staged --verbose"
    exit 1
}
EOF
chmod +x .git/hooks/pre-commit
```

Verify: `git commit --allow-empty -m "test"` runs the hook (then `git reset HEAD~1`).

- [ ] **Step 2: Write the failing config test**

```python
# nova-agent/tests/test_config.py
import pytest
from nova_agent.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-real-looking-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-looking-key")
    monkeypatch.setenv("NOVA_WS_PORT", "9999")
    s = Settings()
    assert s.google_api_key == "AIzaSy-real-looking-key"
    assert s.anthropic_api_key == "sk-ant-real-looking-key"
    assert s.ws_port == 9999

def test_settings_fails_without_google_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with pytest.raises(Exception) as exc:
        Settings()
    assert "GOOGLE_API_KEY" in str(exc.value)

def test_settings_default_models(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings()
    assert s.decision_model == "gemini-2.5-flash"
    assert s.deliberation_model == "gemini-2.5-pro"
    assert s.cheap_vision_model == "gemini-2.5-flash-lite"
    assert s.reflection_model == "claude-sonnet-4-6"
    assert s.demo_model == "claude-opus-4-7"

def test_settings_default_paths(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings()
    assert str(s.sqlite_path).endswith("nova.db")
    assert str(s.lancedb_path).endswith("lancedb")
```

- [ ] **Step 3: Run, see fail**

```bash
cd nova-agent && uv run pytest tests/test_config.py -v
```

Expected: ImportError on `nova_agent.config`.

- [ ] **Step 4: Implement `config.py`**

```python
# nova-agent/src/nova_agent/config.py
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required secrets — TWO providers
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Per-task model selection (see spec §6 tech stack table)
    decision_model: str = Field("gemini-2.5-flash", alias="NOVA_DECISION_MODEL")
    deliberation_model: str = Field("gemini-2.5-pro", alias="NOVA_DELIBERATION_MODEL")
    cheap_vision_model: str = Field("gemini-2.5-flash-lite", alias="NOVA_CHEAP_VISION_MODEL")
    reflection_model: str = Field("claude-sonnet-4-6", alias="NOVA_REFLECTION_MODEL")
    demo_model: str = Field("claude-opus-4-7", alias="NOVA_DEMO_MODEL")

    # Storage paths
    sqlite_path: Path = Field(Path("./data/nova.db"), alias="NOVA_SQLITE_PATH")
    lancedb_path: Path = Field(Path("./data/lancedb"), alias="NOVA_LANCEDB_PATH")

    # ADB / emulator
    adb_path: str = Field("adb", alias="ADB_PATH")
    adb_device_id: str | None = Field(None, alias="ADB_DEVICE_ID")

    # WebSocket
    ws_host: str = Field("127.0.0.1", alias="NOVA_WS_HOST")
    ws_port: int = Field(8765, alias="NOVA_WS_PORT")

    # Logging
    log_level: str = Field("INFO", alias="NOVA_LOG_LEVEL")

    # Cost guardrail (USD); 0 means no limit
    daily_budget_usd: float = Field(20.0, alias="NOVA_DAILY_BUDGET_USD")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton. Call this at runtime, not at import."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        _settings.lancedb_path.mkdir(parents=True, exist_ok=True)
    return _settings
```

- [ ] **Step 5: Run, see pass**

```bash
uv run pytest tests/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add .git/hooks/pre-commit nova-agent/src/nova_agent/config.py nova-agent/tests/test_config.py
git commit -m "feat(agent): config module + gitleaks pre-commit hook"
```

(Note: `.git/hooks/pre-commit` is local-only; the actual file goes into your local clone but will not appear in the commit. Document the install in `SECURITY.md` — already done.)

---

## Task 3: Multi-provider LLM client + budget guard

**Provider-agnostic LLM interface with TWO adapters: Google AI (Gemini) for default decisions / ToT / cheap classification, Anthropic (Claude) for reflection + demo recording. See spec §6 tech stack table for the per-task model selection.**

**Files:**
- Create: `nova-agent/src/nova_agent/budget.py`
- Create: `nova-agent/src/nova_agent/llm/__init__.py`
- Create: `nova-agent/src/nova_agent/llm/protocol.py`
- Create: `nova-agent/src/nova_agent/llm/anthropic_client.py`
- Create: `nova-agent/src/nova_agent/llm/gemini_client.py`
- Create: `nova-agent/src/nova_agent/llm/factory.py`
- Create: `nova-agent/src/nova_agent/llm/structured.py`
- Create: `nova-agent/tests/test_llm_anthropic.py`
- Create: `nova-agent/tests/test_llm_gemini.py`
- Create: `nova-agent/tests/test_llm_factory.py`
- Create: `nova-agent/tests/test_budget.py`
- Modify: `nova-agent/pyproject.toml` (add `google-genai>=0.3.0` to dependencies)

- [ ] **Step 1: Write failing budget test**

```python
# nova-agent/tests/test_budget.py
import pytest
from nova_agent.budget import BudgetGuard, BudgetExceeded


def test_budget_allows_under_cap():
    g = BudgetGuard(daily_cap_usd=10.00)
    g.charge(2.00)
    g.charge(3.00)
    assert g.spent_today == 5.00


def test_budget_blocks_over_cap():
    g = BudgetGuard(daily_cap_usd=5.00)
    g.charge(3.00)
    with pytest.raises(BudgetExceeded):
        g.charge(2.50)


def test_zero_cap_is_unlimited():
    g = BudgetGuard(daily_cap_usd=0.0)
    g.charge(1_000_000.0)  # no error
```

- [ ] **Step 2: Run, see fail**

```bash
uv run pytest tests/test_budget.py -v
```

- [ ] **Step 3: Implement `budget.py`**

```python
# nova-agent/src/nova_agent/budget.py
from datetime import date


class BudgetExceeded(RuntimeError):
    """Raised when an LLM call would exceed the configured daily cap."""


class BudgetGuard:
    def __init__(self, daily_cap_usd: float):
        self.daily_cap_usd = daily_cap_usd
        self._day = date.today()
        self.spent_today = 0.0

    def _roll_day(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self.spent_today = 0.0

    def charge(self, amount_usd: float) -> None:
        self._roll_day()
        if self.daily_cap_usd > 0 and self.spent_today + amount_usd > self.daily_cap_usd:
            raise BudgetExceeded(
                f"Charge of ${amount_usd:.4f} would exceed daily cap "
                f"${self.daily_cap_usd:.2f} (already spent ${self.spent_today:.4f})."
            )
        self.spent_today += amount_usd
```

- [ ] **Step 4: Write failing tests for both adapters + the factory**

```python
# nova-agent/tests/test_llm_anthropic.py
from unittest.mock import MagicMock, patch
from nova_agent.llm.anthropic_client import AnthropicLLM


@patch("nova_agent.llm.anthropic_client.Anthropic")
def test_anthropic_adapter_calls_messages_create(mock_cls):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text='{"action":"swipe_up"}', type="text")]
    fake_resp.usage.input_tokens = 1000
    fake_resp.usage.output_tokens = 50
    fake_client.messages.create.return_value = fake_resp
    mock_cls.return_value = fake_client

    llm = AnthropicLLM(api_key="sk-ant-test", model="claude-sonnet-4-6", daily_cap_usd=0)
    out, usage = llm.complete(system="be brief", messages=[{"role": "user", "content": "hi"}])
    assert "swipe_up" in out
    assert usage.input_tokens == 1000
```

```python
# nova-agent/tests/test_llm_gemini.py
from unittest.mock import MagicMock, patch
from nova_agent.llm.gemini_client import GeminiLLM


@patch("nova_agent.llm.gemini_client.genai.Client")
def test_gemini_adapter_calls_generate(mock_cls):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.text = '{"action":"swipe_left"}'
    fake_resp.usage_metadata.prompt_token_count = 1200
    fake_resp.usage_metadata.candidates_token_count = 40
    fake_client.models.generate_content.return_value = fake_resp
    mock_cls.return_value = fake_client

    llm = GeminiLLM(api_key="AIzaSy-test", model="gemini-2.5-flash", daily_cap_usd=0)
    out, usage = llm.complete(system="be brief", messages=[{"role": "user", "content": "hi"}])
    assert "swipe_left" in out
    assert usage.input_tokens == 1200
```

```python
# nova-agent/tests/test_llm_factory.py
from nova_agent.llm.factory import build_llm


def test_factory_gemini_for_gemini_model():
    llm = build_llm(model="gemini-2.5-flash", google_api_key="AIzaSy-test", anthropic_api_key="", daily_cap_usd=0)
    assert llm.__class__.__name__ == "GeminiLLM"


def test_factory_anthropic_for_claude_model():
    llm = build_llm(model="claude-sonnet-4-6", google_api_key="", anthropic_api_key="sk-ant-test", daily_cap_usd=0)
    assert llm.__class__.__name__ == "AnthropicLLM"


def test_factory_raises_on_unknown_model():
    import pytest
    with pytest.raises(ValueError):
        build_llm(model="gpt-9000", google_api_key="x", anthropic_api_key="y", daily_cap_usd=0)
```

- [ ] **Step 5: Run, see fail**

```bash
uv run pytest tests/test_llm_client.py -v
```

- [ ] **Step 6: Implement the LLM protocol + per-provider pricing**

```python
# nova-agent/src/nova_agent/llm/__init__.py
from nova_agent.llm.protocol import LLM, Usage
from nova_agent.llm.factory import build_llm
```

```python
# nova-agent/src/nova_agent/llm/protocol.py
from dataclasses import dataclass
from typing import Any, Protocol


# Per-1M-token pricing in USD. Verified against provider pricing pages May 2026.
# Update if providers change pricing — the budget guard relies on these.
PRICING: dict[str, tuple[float, float]] = {
    # (input_usd_per_mtok, output_usd_per_mtok)
    "claude-opus-4-7": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "gemini-2.5-pro": (1.25, 10.0),     # tier <=200K input tokens
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def cost_usd(self) -> float:
        in_rate, out_rate = PRICING.get(self.model, (5.0, 25.0))  # conservative default
        return (
            self.input_tokens * in_rate / 1_000_000
            + self.output_tokens * out_rate / 1_000_000
        )


class LLM(Protocol):
    """Provider-agnostic LLM interface used by every cognitive module."""

    model: str

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> tuple[str, Usage]: ...
```

- [ ] **Step 7: Implement the Anthropic adapter**

```python
# nova-agent/src/nova_agent/llm/anthropic_client.py
from typing import Any
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from nova_agent.budget import BudgetGuard
from nova_agent.llm.protocol import Usage

log = structlog.get_logger()


class AnthropicLLM:
    def __init__(self, *, api_key: str, model: str, daily_cap_usd: float):
        self._client = Anthropic(api_key=api_key)
        self.model = model
        self.budget = BudgetGuard(daily_cap_usd=daily_cap_usd)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> tuple[str, Usage]:
        resp = self._client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = "".join(part.text for part in resp.content if part.type == "text")
        usage = Usage(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=self.model,
        )
        self.budget.charge(usage.cost_usd)
        log.info("llm.anthropic", model=self.model, tokens_in=usage.input_tokens, tokens_out=usage.output_tokens, cost=usage.cost_usd)
        return text, usage
```

- [ ] **Step 8: Implement the Gemini adapter**

```python
# nova-agent/src/nova_agent/llm/gemini_client.py
import base64
from typing import Any
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from nova_agent.budget import BudgetGuard
from nova_agent.llm.protocol import Usage

log = structlog.get_logger()


def _to_gemini_content(messages: list[dict[str, Any]]) -> list[types.Content]:
    """Convert Anthropic-style messages to Gemini Content list.

    The Anthropic shape is `[{"role": "user", "content": [{"type": "image", "source": {...}}, {"type": "text", "text": "..."}]}]`.
    Gemini accepts a flatter list of Parts.
    """
    contents: list[types.Content] = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        parts: list[types.Part] = []
        content = msg["content"]
        if isinstance(content, str):
            parts.append(types.Part.from_text(content))
        else:
            for item in content:
                if item.get("type") == "text":
                    parts.append(types.Part.from_text(item["text"]))
                elif item.get("type") == "image":
                    src = item["source"]
                    if src["type"] == "base64":
                        raw = base64.b64decode(src["data"])
                        parts.append(types.Part.from_bytes(data=raw, mime_type=src["media_type"]))
        contents.append(types.Content(role=role, parts=parts))
    return contents


class GeminiLLM:
    def __init__(self, *, api_key: str, model: str, daily_cap_usd: float):
        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.budget = BudgetGuard(daily_cap_usd=daily_cap_usd)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> tuple[str, Usage]:
        contents = _to_gemini_content(messages)
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
            response_mime_type="application/json",  # request strict JSON
        )
        resp = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        text = resp.text or ""
        usage = Usage(
            input_tokens=resp.usage_metadata.prompt_token_count,
            output_tokens=resp.usage_metadata.candidates_token_count,
            model=self.model,
        )
        self.budget.charge(usage.cost_usd)
        log.info("llm.gemini", model=self.model, tokens_in=usage.input_tokens, tokens_out=usage.output_tokens, cost=usage.cost_usd)
        return text, usage
```

- [ ] **Step 9: Implement the factory**

```python
# nova-agent/src/nova_agent/llm/factory.py
from nova_agent.llm.protocol import LLM
from nova_agent.llm.anthropic_client import AnthropicLLM
from nova_agent.llm.gemini_client import GeminiLLM


def build_llm(*, model: str, google_api_key: str, anthropic_api_key: str, daily_cap_usd: float) -> LLM:
    """Construct the right adapter for a given model name.

    Routing:
      - gemini-* → GeminiLLM (uses GOOGLE_API_KEY)
      - claude-* → AnthropicLLM (uses ANTHROPIC_API_KEY)
    """
    if model.startswith("gemini-"):
        return GeminiLLM(api_key=google_api_key, model=model, daily_cap_usd=daily_cap_usd)
    if model.startswith("claude-"):
        return AnthropicLLM(api_key=anthropic_api_key, model=model, daily_cap_usd=daily_cap_usd)
    raise ValueError(f"Unknown model family: {model!r}")
```

- [ ] **Step 10: Implement `llm/structured.py`**

```python
# nova-agent/src/nova_agent/llm/structured.py
import json
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(ValueError):
    pass


def parse_json(text: str, model: Type[T]) -> T:
    """Parse `text` as JSON and validate against the given pydantic model.

    The VLM may emit prose around the JSON; extract the first {...} block.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise StructuredOutputError(f"No JSON object found in: {text[:200]!r}")
    raw = text[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise StructuredOutputError(f"Invalid JSON: {e}; raw={raw[:200]!r}") from e
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise StructuredOutputError(f"Schema mismatch: {e}; raw={raw[:200]!r}") from e
```

- [ ] **Step 11: Verify `google-genai` is in pyproject.toml dependencies**

(Already added in Task 1 — confirm `uv sync` brought it in.)

- [ ] **Step 12: Run all tests pass**

```bash
uv run pytest -v
```

- [ ] **Step 13: Commit**

```bash
git add nova-agent/
git commit -m "feat(agent): multi-provider LLM (Gemini + Anthropic) + budget guard + structured output"
```

---

## Task 4: ADB action wrapper

**Files:**
- Create: `nova-agent/src/nova_agent/action/__init__.py`
- Create: `nova-agent/src/nova_agent/action/adb.py`
- Create: `nova-agent/tests/test_action_adb.py`

- [ ] **Step 1: Write failing test**

```python
# nova-agent/tests/test_action_adb.py
from unittest.mock import patch, MagicMock
from nova_agent.action.adb import ADB, SwipeDirection

@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_up_invokes_correct_command(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    adb.swipe(SwipeDirection.UP)
    args = mock_run.call_args[0][0]
    assert "swipe" in args
    # swipe up means start near bottom and end near top
    assert int(args[-3]) > int(args[-2])

@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_failure_raises(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"adb error")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    import pytest
    with pytest.raises(RuntimeError):
        adb.swipe(SwipeDirection.LEFT)
```

- [ ] **Step 2: Run, see fail**

```bash
uv run pytest tests/test_action_adb.py -v
```

- [ ] **Step 3: Implement**

```python
# nova-agent/src/nova_agent/action/__init__.py
from nova_agent.action.adb import ADB, SwipeDirection
```

```python
# nova-agent/src/nova_agent/action/adb.py
import subprocess
import time
from enum import Enum

import structlog

log = structlog.get_logger()


class SwipeDirection(str, Enum):
    UP = "swipe_up"
    DOWN = "swipe_down"
    LEFT = "swipe_left"
    RIGHT = "swipe_right"


class ADB:
    """Thin wrapper around `adb shell input` for swipes."""

    def __init__(self, *, adb_path: str, device_id: str | None, screen_w: int, screen_h: int):
        self.adb_path = adb_path
        self.device_id = device_id
        self.w = screen_w
        self.h = screen_h

    def _base_args(self) -> list[str]:
        args = [self.adb_path]
        if self.device_id:
            args += ["-s", self.device_id]
        return args

    def swipe(self, direction: SwipeDirection, duration_ms: int = 100) -> None:
        cx, cy = self.w // 2, self.h // 2
        margin_x, margin_y = self.w // 4, self.h // 4
        match direction:
            case SwipeDirection.UP:
                x1, y1, x2, y2 = cx, cy + margin_y, cx, cy - margin_y
            case SwipeDirection.DOWN:
                x1, y1, x2, y2 = cx, cy - margin_y, cx, cy + margin_y
            case SwipeDirection.LEFT:
                x1, y1, x2, y2 = cx + margin_x, cy, cx - margin_x, cy
            case SwipeDirection.RIGHT:
                x1, y1, x2, y2 = cx - margin_x, cy, cx + margin_x, cy
            case _:
                raise ValueError(f"Unknown direction {direction}")
        args = self._base_args() + [
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration_ms),
        ]
        log.info("adb.swipe", direction=direction.value, args=args)
        result = subprocess.run(args, capture_output=True, timeout=5.0)
        if result.returncode != 0:
            raise RuntimeError(
                f"adb swipe failed: rc={result.returncode}; "
                f"stderr={result.stderr.decode(errors='ignore')!r}"
            )
        time.sleep(0.3)  # wait for tile-slide animation
```

- [ ] **Step 4: Run, pass**

```bash
uv run pytest tests/test_action_adb.py -v
```

- [ ] **Step 5: Commit**

```bash
git add nova-agent/
git commit -m "feat(agent): ADB swipe action wrapper"
```

---

## Task 5: Perception capture + Claude Design direction window opens

**Files:**
- Create: `nova-agent/src/nova_agent/perception/__init__.py`
- Create: `nova-agent/src/nova_agent/perception/capture.py`
- Create: `nova-agent/src/nova_agent/perception/types.py`
- Create: `nova-agent/tests/test_perception_capture.py`
- Create: `docs/design/v1/README.md`

- [ ] **Step 1: Write failing perception type tests**

```python
# nova-agent/tests/test_perception_capture.py
import pytest
from nova_agent.perception.types import BoardState

def test_board_state_properties():
    b = BoardState(grid=[[0, 2, 0, 0], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]], score=0)
    assert b.empty_cells == 14
    assert b.max_tile == 2

def test_board_state_validates_4x4():
    with pytest.raises(ValueError):
        BoardState(grid=[[0, 2], [0, 0]], score=0)
```

- [ ] **Step 2: Implement `perception/types.py`**

```python
# nova-agent/src/nova_agent/perception/__init__.py
from nova_agent.perception.types import BoardState
from nova_agent.perception.capture import Capture
```

```python
# nova-agent/src/nova_agent/perception/types.py
from dataclasses import dataclass


@dataclass(frozen=True)
class BoardState:
    grid: list[list[int]]
    score: int

    def __post_init__(self) -> None:
        if len(self.grid) != 4 or any(len(r) != 4 for r in self.grid):
            raise ValueError("BoardState.grid must be 4x4")

    @property
    def empty_cells(self) -> int:
        return sum(1 for row in self.grid for v in row if v == 0)

    @property
    def max_tile(self) -> int:
        return max((v for row in self.grid for v in row), default=0)
```

- [ ] **Step 3: Implement `perception/capture.py`**

```python
# nova-agent/src/nova_agent/perception/capture.py
import io
import subprocess
from PIL import Image
import structlog

log = structlog.get_logger()


class Capture:
    """ADB-based screen capture."""

    def __init__(self, *, adb_path: str, device_id: str | None):
        self.adb_path = adb_path
        self.device_id = device_id

    def grab(self) -> Image.Image:
        args = [self.adb_path]
        if self.device_id:
            args += ["-s", self.device_id]
        args += ["exec-out", "screencap", "-p"]
        log.debug("capture.grab", args=args)
        result = subprocess.run(args, capture_output=True, timeout=5.0)
        if result.returncode != 0:
            raise RuntimeError(f"adb screencap failed: {result.stderr!r}")
        return Image.open(io.BytesIO(result.stdout)).convert("RGB")
```

- [ ] **Step 4: Run perception tests pass**

```bash
uv run pytest tests/test_perception_capture.py -v
```

- [ ] **Step 5: Open Claude Design — direction exploration**

This is a parallel manual task (Day 2–3 of Week 1, per spec §5.5).

Open Claude Design (https://claude.ai/design or via the Pro/Max account). Provide it with:
- The aesthetic principles table from spec §5.5
- The brain-panel element list from spec §5
- A real screenshot of the running 2048 emulator (capture one with `adb exec-out screencap -p > /tmp/board.png`)

Ask it to generate **3–5 alternate brain-panel layouts** in the warm-minimalist neural style. Save the mockups to `docs/design/v1/`.

- [ ] **Step 6: Create `docs/design/v1/README.md`**

```markdown
# Brain Panel — Visual Direction Exploration (v1, Week 1)

This folder holds Claude Design output from the Week 1 days 2–3 direction-exploration window.

## Process

1. Generated 3–5 alternate brain-panel layouts via Claude Design using the §5.5 aesthetic principles + §5 element list as input.
2. Picked one direction. The chosen mockups live in `chosen/`.
3. Alternate directions live in `alts/` for reference.

## Files

- `chosen/` — selected direction, used to inform component scaffolding in Week 5
- `alts/` — alternate explorations
- `notes.md` — rationale for the chosen direction

When iterating in Week 5, use the chosen-direction mockups as the design-system seed for Claude Design.
```

- [ ] **Step 7: Commit**

```bash
git add nova-agent/ docs/design/v1/
git commit -m "feat(perception): capture wrapper + types; open Claude Design v1 dir"
```

---

## Task 6: WebSocket bus

**Files:**
- Create: `nova-agent/src/nova_agent/bus/__init__.py`
- Create: `nova-agent/src/nova_agent/bus/websocket.py`
- Create: `nova-agent/tests/test_bus_websocket.py`

- [ ] **Step 1: Write failing test**

```python
# nova-agent/tests/test_bus_websocket.py
import asyncio
import json
import pytest
import websockets
from nova_agent.bus.websocket import EventBus


@pytest.mark.asyncio
async def test_event_bus_publishes_to_subscriber():
    bus = EventBus(host="127.0.0.1", port=18765)
    await bus.start()
    received = []
    async with websockets.connect("ws://127.0.0.1:18765") as ws:
        await asyncio.sleep(0.1)
        await bus.publish("test_event", {"x": 1})
        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        received.append(json.loads(msg))
    await bus.stop()
    assert received == [{"event": "test_event", "data": {"x": 1}}]
```

- [ ] **Step 2: Run, see fail**

```bash
uv run pytest tests/test_bus_websocket.py -v
```

- [ ] **Step 3: Implement**

```python
# nova-agent/src/nova_agent/bus/__init__.py
from nova_agent.bus.websocket import EventBus
```

```python
# nova-agent/src/nova_agent/bus/websocket.py
import asyncio
import json
import contextlib
from typing import Any

import websockets
from websockets.server import WebSocketServerProtocol
import structlog

log = structlog.get_logger()


class EventBus:
    """Local WebSocket broadcaster. Connections subscribe; agent publishes."""

    def __init__(self, *, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: set[WebSocketServerProtocol] = set()
        self._server: websockets.WebSocketServer | None = None

    async def _handler(self, ws: WebSocketServerProtocol) -> None:
        self._clients.add(ws)
        log.info("bus.client_connected", count=len(self._clients))
        try:
            async for _ in ws:
                pass  # ignore inbound; broadcast-only
        finally:
            self._clients.discard(ws)
            log.info("bus.client_disconnected", count=len(self._clients))

    async def start(self) -> None:
        self._server = await websockets.serve(self._handler, self.host, self.port)
        log.info("bus.started", host=self.host, port=self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def publish(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str)
        if not self._clients:
            return
        await asyncio.gather(
            *(self._safe_send(ws, payload) for ws in list(self._clients)),
            return_exceptions=True,
        )

    @staticmethod
    async def _safe_send(ws: WebSocketServerProtocol, payload: str) -> None:
        with contextlib.suppress(websockets.exceptions.ConnectionClosed):
            await ws.send(payload)
```

- [ ] **Step 4: Run, pass**

```bash
uv run pytest tests/test_bus_websocket.py -v
```

- [ ] **Step 5: Commit**

```bash
git add nova-agent/
git commit -m "feat(bus): WebSocket event bus for brain-panel viewer"
```

---

## Task 7: Bootstrap nova-viewer (Next.js)

**Files:**
- Create: `nova-viewer/` (whole project tree)

- [ ] **Step 1: Initialize Next.js project**

```bash
cd nova-viewer
pnpm create next-app@latest . --typescript --tailwind --app --no-src --import-alias "@/*" --eslint --no-turbopack --use-pnpm
```

(Accept defaults for unspecified prompts.)

- [ ] **Step 2: Install Framer Motion + WebSocket types**

```bash
cd nova-viewer
pnpm add framer-motion
pnpm add -D @types/ws
```

- [ ] **Step 3: Replace `nova-viewer/app/page.tsx`** with a minimal placeholder that subscribes to the WebSocket

```tsx
// nova-viewer/app/page.tsx
"use client";

import { useEffect, useState } from "react";

type AgentEvent = { event: string; data: unknown };

export default function Home() {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const url = `ws://${process.env.NEXT_PUBLIC_WS_HOST ?? "127.0.0.1"}:${
      process.env.NEXT_PUBLIC_WS_PORT ?? "8765"
    }`;
    const ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev.slice(-49), msg]);
      } catch {}
    };
    return () => ws.close();
  }, []);

  return (
    <main className="min-h-screen bg-[#1a1614] text-zinc-100 p-8 font-mono text-sm">
      <h1 className="text-2xl mb-4">Project Nova — brain panel (placeholder)</h1>
      <div className="grid grid-cols-2 gap-8">
        <section className="bg-zinc-900/50 rounded p-4">
          <h2 className="text-lg mb-2 text-zinc-400">Live game (placeholder)</h2>
          <div className="aspect-[9/16] bg-black rounded" />
        </section>
        <section className="bg-zinc-900/50 rounded p-4 overflow-y-auto max-h-[80vh]">
          <h2 className="text-lg mb-2 text-zinc-400">Events ({events.length})</h2>
          <ul className="space-y-1">
            {events.map((e, i) => (
              <li key={i} className="text-xs">
                <span className="text-cyan-400">{e.event}</span> —{" "}
                <span className="text-zinc-400">{JSON.stringify(e.data)}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Add `nova-viewer/.env.example`**

```bash
NEXT_PUBLIC_WS_HOST=127.0.0.1
NEXT_PUBLIC_WS_PORT=8765
```

- [ ] **Step 5: Verify it builds and runs**

```bash
cd nova-viewer
pnpm build
pnpm dev
```

Open http://localhost:3000. Expect the placeholder page with `Events (0)`.

- [ ] **Step 6: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): bootstrap Next.js brain-panel skeleton"
```

---

## Task 8: Fork 2048_Unity, build APK, install on emulator

**Files:**
- Modify: `nova-game/README.md`
- Create: `nova-game/build-android.sh`

This task is partly outside the repo (Unity workspace). Document the steps so they're reproducible.

- [ ] **Step 1: Fork stdbilly/2048_Unity on GitHub**

Go to https://github.com/stdbilly/2048_Unity → Fork → into your account.

- [ ] **Step 2: Clone the fork next to project-nova (NOT inside it)**

```bash
cd ~/Desktop
git clone https://github.com/IdoHoresh/2048_Unity.git
```

- [ ] **Step 3: Open the project in Unity Hub** with Unity 2022 LTS. Switch build target to Android (File → Build Settings → Android → Switch Platform).

- [ ] **Step 4: Configure Player Settings**
- Bundle ID: `com.idohoresh.nova2048`
- Minimum API Level: Android 7.0 (24)
- Target API Level: 34
- Scripting Backend: IL2CPP
- Target Architectures: ARM64

- [ ] **Step 5: Build the APK**

File → Build Settings → Build → save as `~/Desktop/2048_Unity/build/nova2048.apk`.

- [ ] **Step 6: Write `nova-game/build-android.sh`**

```bash
#!/usr/bin/env bash
# Helper script to install the built APK on the running emulator.
set -e

APK="${1:-$HOME/Desktop/2048_Unity/build/nova2048.apk}"
DEVICE_ID="${ADB_DEVICE_ID:-emulator-5554}"

if [[ ! -f "$APK" ]]; then
    echo "❌ APK not found at $APK"
    echo "   Build it from Unity first; see nova-game/README.md"
    exit 1
fi

echo "→ Installing $APK on $DEVICE_ID"
adb -s "$DEVICE_ID" install -r "$APK"
echo "→ Launching"
adb -s "$DEVICE_ID" shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
```

```bash
chmod +x nova-game/build-android.sh
```

- [ ] **Step 7: Update `nova-game/README.md`**

```markdown
# nova-game — forked Unity 2048

The actual Unity project lives outside this repo (it's a fork of
[stdbilly/2048_Unity](https://github.com/stdbilly/2048_Unity), MIT).

## Setup

1. Fork https://github.com/stdbilly/2048_Unity to your GitHub account.
2. Clone it next to `project-nova`: `git clone <your-fork> ~/Desktop/2048_Unity`.
3. Open in Unity Hub with Unity 2022 LTS.
4. Switch build target to Android.
5. Player Settings: bundle ID `com.idohoresh.nova2048`, min API 24, target API 34, IL2CPP, ARM64.
6. Build → output to `~/Desktop/2048_Unity/build/nova2048.apk`.

## Install on emulator

Boot an Android emulator (Android Studio → Device Manager → Pixel 6 API 34 → ▶).
Then:

```bash
./build-android.sh
```

The agent's `ADB_DEVICE_ID` env var must match the emulator (usually `emulator-5554`).
```

- [ ] **Step 8: Boot emulator + install + verify**

```bash
adb devices                                 # see emulator-5554
./nova-game/build-android.sh                # installs and launches 2048
adb -s emulator-5554 exec-out screencap -p > /tmp/board.png
open /tmp/board.png                         # confirm 2048 board visible
```

- [ ] **Step 9: Commit**

```bash
git add nova-game/
git commit -m "feat(game): fork stdbilly/2048_Unity + Android build/install scripts"
```

---

## Task 9: First end-to-end loop (no memory, no affect)

**Files:**
- Create: `nova-agent/src/nova_agent/main.py`
- Create: `nova-agent/src/nova_agent/decision/__init__.py`
- Create: `nova-agent/src/nova_agent/decision/prompts.py`
- Create: `nova-agent/src/nova_agent/decision/react.py`
- Create: `nova-agent/tests/test_decision_react.py`
- Create: `nova-agent/tests/test_main_smoke.py`

- [ ] **Step 1: Write failing react test (uses a mocked LLM)**

```python
# nova-agent/tests/test_decision_react.py
from unittest.mock import MagicMock
from nova_agent.decision.react import ReactDecider, Decision
from nova_agent.perception.types import BoardState

def test_react_returns_valid_action():
    fake_llm = MagicMock()
    fake_llm.complete.return_value = (
        '{"observation":"two 2s","reasoning":"merge them","action":"swipe_right","confidence":"high"}',
        MagicMock(input_tokens=100, output_tokens=20, cost_usd=0.01),
    )
    decider = ReactDecider(llm=fake_llm)
    board = BoardState(
        grid=[[0,2,0,0],[0,0,0,2],[0,0,0,0],[0,0,0,0]], score=0,
    )
    result = decider.decide(board=board, screenshot_b64="ignored")
    assert isinstance(result, Decision)
    assert result.action == "swipe_right"
    assert "merge" in result.reasoning.lower()
```

- [ ] **Step 2: Run, see fail**

- [ ] **Step 3: Implement `decision/prompts.py`**

```python
# nova-agent/src/nova_agent/decision/__init__.py
from nova_agent.decision.react import ReactDecider, Decision
```

```python
# nova-agent/src/nova_agent/decision/prompts.py
SYSTEM_PROMPT_V1 = """\
You are Nova, an AI playing the puzzle game 2048.
You see the board as a 4x4 grid where 0 means empty.
You decide which way to swipe and explain your reasoning briefly.

Respond with strict JSON, no prose around it:
{
  "observation": "1 sentence about what's on the board",
  "reasoning":   "1-2 sentences on why you chose this action",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
"""

def build_user_prompt(*, grid: list[list[int]], score: int) -> str:
    grid_str = "\n".join("  ".join(f"{v:>5}" if v else "    .") for v in grid)
    return f"""Current board:
{grid_str}

Score: {score}

Choose the next swipe."""
```

- [ ] **Step 4: Implement `decision/react.py`**

```python
# nova-agent/src/nova_agent/decision/react.py
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, Field

from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json
from nova_agent.perception.types import BoardState
from nova_agent.decision.prompts import SYSTEM_PROMPT_V1, build_user_prompt


class _ReactOutput(BaseModel):
    observation: str
    reasoning: str
    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    confidence: Literal["low", "medium", "high"] = Field(default="medium")


@dataclass(frozen=True)
class Decision:
    action: str
    observation: str
    reasoning: str
    confidence: str


class ReactDecider:
    def __init__(self, *, llm: LLM):
        self.llm = llm

    def decide(self, *, board: BoardState, screenshot_b64: str) -> Decision:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ]
        text, _usage = self.llm.complete(
            system=SYSTEM_PROMPT_V1, messages=messages, max_tokens=400, temperature=0.7,
        )
        parsed = parse_json(text, _ReactOutput)
        return Decision(
            action=parsed.action,
            observation=parsed.observation,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )
```

- [ ] **Step 5: Implement `main.py`**

```python
# nova-agent/src/nova_agent/main.py
import asyncio
import base64
import io
import sys

import structlog

from nova_agent.action.adb import ADB, SwipeDirection
from nova_agent.bus.websocket import EventBus
from nova_agent.config import get_settings
from nova_agent.decision.react import ReactDecider
from nova_agent.llm.factory import build_llm
from nova_agent.perception.capture import Capture
from nova_agent.perception.types import BoardState

log = structlog.get_logger()


def _placeholder_perceive(image) -> BoardState:
    """Week 1 placeholder — we don't have OCR yet, so log image size and return empty board.

    Replaced by real OCR in Week 1 Task 10 (or Week 2 if deferred).
    """
    log.warning("perception.placeholder_in_use", image_size=image.size)
    return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)


async def run() -> None:
    s = get_settings()
    bus = EventBus(host=s.ws_host, port=s.ws_port)
    await bus.start()

    capture = Capture(adb_path=s.adb_path, device_id=s.adb_device_id)
    adb = ADB(adb_path=s.adb_path, device_id=s.adb_device_id, screen_w=1080, screen_h=2400)
    # Default decisions go through Gemini Flash (cheap, fast). Other modules
    # build their own LLM via the factory using the right per-task model.
    decision_llm = build_llm(
        model=s.decision_model,
        google_api_key=s.google_api_key,
        anthropic_api_key=s.anthropic_api_key,
        daily_cap_usd=s.daily_budget_usd,
    )
    decider = ReactDecider(llm=decision_llm)

    log.info("nova.started")
    try:
        for step in range(50):
            image = capture.grab()
            board = _placeholder_perceive(image)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            await bus.publish("perception", {"score": board.score, "step": step})
            decision = decider.decide(board=board, screenshot_b64=b64)
            await bus.publish("decision", {
                "action": decision.action,
                "observation": decision.observation,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
            })
            adb.swipe(SwipeDirection(decision.action))
            await asyncio.sleep(0.5)
    finally:
        await bus.stop()


def cli() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 6: Smoke test (no real run yet — just import-cleanly)**

```python
# nova-agent/tests/test_main_smoke.py
def test_main_imports():
    import nova_agent.main as m
    assert callable(m.run)
    assert callable(m.cli)
```

- [ ] **Step 7: All tests pass**

```bash
uv run pytest -v
```

- [ ] **Step 8: Live smoke run (optional but recommended at this point)**

With the emulator booted, 2048 running, and `.env` populated:

```bash
cd nova-agent
uv run nova
```

Expect: agent screenshots, calls Claude, swipes, repeats. The score is logged as 0 because OCR is a placeholder — that's OK; we're verifying the pipeline. Stop with Ctrl+C after a few moves.

- [ ] **Step 9: Commit**

```bash
git add nova-agent/
git commit -m "feat(agent): first end-to-end loop (capture -> VLM -> swipe)"
```

---

## Task 10: OCR fast-path perception

**Files:**
- Create: `nova-agent/src/nova_agent/perception/ocr.py`
- Create: `nova-agent/tests/test_perception_ocr.py`
- Create: `nova-agent/tests/fixtures/board_*.png` (sample boards, captured manually)
- Modify: `nova-agent/src/nova_agent/main.py`

- [ ] **Step 1: Capture sample fixtures**

With the emulator running and 2048 in various states, capture 5–10 boards:

```bash
for i in 0 1 2 3 4; do
  adb -s emulator-5554 exec-out screencap -p > nova-agent/tests/fixtures/board_${i}.png
  sleep 2  # play a move between captures
done
```

Manually note the expected grid for each PNG in a YAML:

```yaml
# nova-agent/tests/fixtures/expected.yaml
board_0:
  grid: [[0,0,0,0],[0,2,0,0],[0,0,0,2],[0,0,0,0]]
  score: 0
board_1:
  grid: [[2,0,0,0],[0,4,0,0],[0,0,2,0],[0,0,0,0]]
  score: 4
# ...etc
```

- [ ] **Step 2: Write failing OCR test**

```python
# nova-agent/tests/test_perception_ocr.py
from pathlib import Path
import yaml
import pytest
from PIL import Image
from nova_agent.perception.ocr import BoardOCR

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED = yaml.safe_load((FIXTURES / "expected.yaml").read_text())

@pytest.mark.parametrize("name,exp", EXPECTED.items())
def test_ocr_reads_known_boards(name, exp):
    img = Image.open(FIXTURES / f"{name}.png").convert("RGB")
    ocr = BoardOCR()
    state = ocr.read(img)
    assert state.grid == exp["grid"], f"{name}: grid mismatch"
```

- [ ] **Step 3: Implement OCR (template matching on tile values)**

```python
# nova-agent/src/nova_agent/perception/ocr.py
from dataclasses import dataclass
import numpy as np
from PIL import Image

from nova_agent.perception.types import BoardState

# These coordinates are calibrated for the Pixel 6 emulator (1080x2400) running
# the Unity 2048 build. If you switch emulator config you must recalibrate —
# see scripts/calibrate_ocr.py (Week 2 polish).
_BOARD_TOP = 980
_BOARD_LEFT = 60
_CELL_SIZE = 240   # 4 cells wide, 4 cells tall
_TILE_INSET = 20

# Tile background colors → tile value. These are the published 2048 palette.
_PALETTE: dict[tuple[int, int, int], int] = {
    (205, 192, 180): 0,      # empty
    (238, 228, 218): 2,
    (237, 224, 200): 4,
    (242, 177, 121): 8,
    (245, 149, 99): 16,
    (246, 124, 95): 32,
    (246, 94, 59): 64,
    (237, 207, 114): 128,
    (237, 204, 97): 256,
    (237, 200, 80): 512,
    (237, 197, 63): 1024,
    (237, 194, 46): 2048,
}


def _nearest_tile(rgb: tuple[int, int, int]) -> int:
    best, best_d = 0, 10**9
    for ref_rgb, val in _PALETTE.items():
        d = sum((a - b) ** 2 for a, b in zip(ref_rgb, rgb))
        if d < best_d:
            best, best_d = val, d
    return best


@dataclass
class BoardOCR:
    def read(self, image: Image.Image) -> BoardState:
        arr = np.asarray(image)
        grid = [[0] * 4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                cy = _BOARD_TOP + r * _CELL_SIZE + _CELL_SIZE // 2
                cx = _BOARD_LEFT + c * _CELL_SIZE + _CELL_SIZE // 2
                # average a small inset patch to reduce anti-alias noise
                patch = arr[
                    cy - _TILE_INSET : cy + _TILE_INSET,
                    cx - _TILE_INSET : cx + _TILE_INSET,
                ]
                rgb = tuple(int(v) for v in patch.reshape(-1, 3).mean(axis=0))
                grid[r][c] = _nearest_tile(rgb)
        # Score parsing is harder; v1 reads it from a fixed top-bar region in Week 2.
        return BoardState(grid=grid, score=0)
```

- [ ] **Step 4: Run OCR tests**

```bash
uv run pytest tests/test_perception_ocr.py -v
```

If a board fails, recapture the fixture or adjust `_BOARD_TOP` / `_BOARD_LEFT` / `_CELL_SIZE` based on a quick visual measurement of one of the captured PNGs.

- [ ] **Step 5: Wire OCR into main.py**

Replace the `_placeholder_perceive` function. Imports + edits:

```python
# In nova-agent/src/nova_agent/main.py — replace _placeholder_perceive call
from nova_agent.perception.ocr import BoardOCR

# in run():
#   ...
#   ocr = BoardOCR()
#   image = capture.grab()
#   board = ocr.read(image)
```

(Keep the placeholder function around as `_placeholder_perceive` and wire BoardOCR through. Delete the placeholder once OCR works on a live emulator.)

- [ ] **Step 6: Live smoke test**

```bash
uv run nova
```

The score is still hard-coded to 0; we'll fix that in Week 2 along with score-region OCR. Confirm grid values are correct in the agent's logs by comparing to the live emulator screen.

- [ ] **Step 7: Commit**

```bash
git add nova-agent/
git commit -m "feat(perception): OCR fast-path tile reader"
```

---

## Task 11: Week 1 security review + commit milestone

**Files:**
- Create: `docs/specs/security-reviews/2026-week-01.md`

- [ ] **Step 1: Run gitleaks (full history)**

```bash
gitleaks detect --redact
```

Expected: no findings.

- [ ] **Step 2: Verify GitHub security settings**

```bash
gh api repos/IdoHoresh/project-nova --jq '.security_and_analysis'
```

Expected: `secret_scanning`, `secret_scanning_push_protection`, `dependabot_security_updates` all `enabled`.

- [ ] **Step 3: Verify nothing env-shaped is in the index**

```bash
git ls-files | grep -iE 'env|secret|credential' | grep -v '\.example$'
```

Expected: empty output.

- [ ] **Step 4: Confirm `.env.example` has no real values**

```bash
grep -E "^[A-Z_]+=.{5,}" .env.example
```

Expected: nothing matches (every line is `KEY=` with empty value or has a `#`-comment value).

- [ ] **Step 5: Write the security review record**

```markdown
# Week 1 Security Review — 2026-MM-DD

## Checks performed
- [x] gitleaks detect --redact — clean
- [x] GitHub secret_scanning + push_protection + dependabot — enabled
- [x] No env/secret files in `git ls-files`
- [x] .env.example has no real values
- [x] Pre-commit hook installed locally and tested

## Findings
None.

## Action items
None.

## Reviewer
Self-review (Ido).
```

- [ ] **Step 6: Tag the milestone**

```bash
git add docs/specs/security-reviews/
git commit -m "chore(security): Week 1 review — clean"
git tag week-1-complete
git push origin main --tags
```

**End of Week 1.** Pipeline runs end-to-end on placeholder grid; OCR reads boards correctly on fixtures; UI placeholder receives events.

---

# WEEK 2 — Memory

**Goal:** Episodic memory writes every move with importance scoring; retrieval surfaces top-5 relevant memories into the prompt; brain panel renders a memory feed.

---

## Task 12: Memory types + SQLite episodic store

**Files:**
- Create: `nova-agent/src/nova_agent/memory/__init__.py`
- Create: `nova-agent/src/nova_agent/memory/types.py`
- Create: `nova-agent/src/nova_agent/memory/episodic.py`
- Create: `nova-agent/tests/test_memory_episodic.py`

- [ ] **Step 1: Write failing test for memory types and DAO**

```python
# nova-agent/tests/test_memory_episodic.py
from datetime import datetime, timezone
from pathlib import Path
from nova_agent.memory.episodic import EpisodicStore
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def make_record(score: int = 0, action: str = "swipe_right") -> MemoryRecord:
    b = BoardState(grid=[[0,0,0,0]]*4, score=score)
    return MemoryRecord(
        id=f"ep_{score}",
        timestamp=datetime.now(timezone.utc),
        board_before=b,
        board_after=b,
        action=action,
        score_delta=0,
        rpe=0.0,
        importance=1,
        tags=[],
        embedding=[0.0] * 8,
    )


def test_episodic_store_round_trip(tmp_path):
    store = EpisodicStore(tmp_path / "test.db")
    rec = make_record()
    store.insert(rec)
    fetched = store.get(rec.id)
    assert fetched is not None
    assert fetched.action == "swipe_right"


def test_episodic_store_list_recent(tmp_path):
    store = EpisodicStore(tmp_path / "test.db")
    for i in range(20):
        store.insert(make_record(score=i, action="swipe_up"))
    recent = store.list_recent(limit=5)
    assert len(recent) == 5
    assert recent[0].id == "ep_19"
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement types**

```python
# nova-agent/src/nova_agent/memory/__init__.py
from nova_agent.memory.types import MemoryRecord, AffectSnapshot
from nova_agent.memory.episodic import EpisodicStore
```

```python
# nova-agent/src/nova_agent/memory/types.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from nova_agent.perception.types import BoardState

Action = Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right", "none"]


@dataclass(frozen=True)
class AffectSnapshot:
    valence: float
    arousal: float
    dopamine: float
    frustration: float
    anxiety: float
    confidence: float


@dataclass
class MemoryRecord:
    id: str
    timestamp: datetime
    board_before: BoardState
    board_after: BoardState
    action: Action
    score_delta: int
    rpe: float
    importance: int  # 1..10
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    last_accessed: datetime | None = None
    source_reasoning: str | None = None
    affect: AffectSnapshot | None = None
```

- [ ] **Step 4: Implement `episodic.py`**

```python
# nova-agent/src/nova_agent/memory/episodic.py
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from nova_agent.memory.types import AffectSnapshot, MemoryRecord
from nova_agent.perception.types import BoardState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodic (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    last_accessed TEXT,
    board_before TEXT NOT NULL,
    board_after TEXT NOT NULL,
    action TEXT NOT NULL,
    score_delta INTEGER NOT NULL,
    rpe REAL NOT NULL,
    importance INTEGER NOT NULL,
    tags TEXT NOT NULL,
    embedding TEXT NOT NULL,
    source_reasoning TEXT,
    affect TEXT
);
CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic(importance);
"""


def _board_to_json(b: BoardState) -> str:
    return json.dumps({"grid": b.grid, "score": b.score})


def _json_to_board(s: str) -> BoardState:
    d = json.loads(s)
    return BoardState(grid=d["grid"], score=d["score"])


def _record_to_row(r: MemoryRecord) -> tuple:
    return (
        r.id,
        r.timestamp.isoformat(),
        r.last_accessed.isoformat() if r.last_accessed else None,
        _board_to_json(r.board_before),
        _board_to_json(r.board_after),
        r.action,
        r.score_delta,
        r.rpe,
        r.importance,
        json.dumps(r.tags),
        json.dumps(r.embedding),
        r.source_reasoning,
        json.dumps(r.affect.__dict__) if r.affect else None,
    )


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    affect_d = json.loads(row["affect"]) if row["affect"] else None
    return MemoryRecord(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
        board_before=_json_to_board(row["board_before"]),
        board_after=_json_to_board(row["board_after"]),
        action=row["action"],
        score_delta=row["score_delta"],
        rpe=row["rpe"],
        importance=row["importance"],
        tags=json.loads(row["tags"]),
        embedding=json.loads(row["embedding"]),
        source_reasoning=row["source_reasoning"],
        affect=AffectSnapshot(**affect_d) if affect_d else None,
    )


class EpisodicStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def insert(self, r: MemoryRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO episodic VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            _record_to_row(r),
        )
        self._conn.commit()

    def get(self, id: str) -> MemoryRecord | None:
        row = self._conn.execute("SELECT * FROM episodic WHERE id = ?", (id,)).fetchone()
        return _row_to_record(row) if row else None

    def list_recent(self, limit: int = 10) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT * FROM episodic ORDER BY timestamp DESC LIMIT ?", (limit,),
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def update_last_accessed(self, id: str, when: datetime) -> None:
        self._conn.execute(
            "UPDATE episodic SET last_accessed = ? WHERE id = ?",
            (when.isoformat(), id),
        )
        self._conn.commit()

    def all(self) -> list[MemoryRecord]:
        rows = self._conn.execute("SELECT * FROM episodic ORDER BY timestamp DESC").fetchall()
        return [_row_to_record(r) for r in rows]
```

- [ ] **Step 5: Run, pass**

- [ ] **Step 6: Commit**

```bash
git add nova-agent/
git commit -m "feat(memory): MemoryRecord types + SQLite episodic store"
```

---

## Task 13: Embeddings + LanceDB vector store

**Files:**
- Create: `nova-agent/src/nova_agent/llm/embeddings.py`
- Create: `nova-agent/src/nova_agent/memory/vector_store.py`
- Create: `nova-agent/tests/test_memory_vector_store.py`

- [ ] **Step 1: Write failing test**

```python
# nova-agent/tests/test_memory_vector_store.py
from nova_agent.memory.vector_store import VectorStore


def test_vector_store_insert_and_search(tmp_path):
    vs = VectorStore(tmp_path / "lancedb")
    vs.upsert("a", [0.1, 0.0, 0.9])
    vs.upsert("b", [0.0, 1.0, 0.0])
    vs.upsert("c", [0.05, 0.05, 0.9])
    hits = vs.search([0.1, 0.0, 0.95], k=2)
    ids = [id_ for id_, _score in hits]
    assert ids[0] in ("a", "c")
```

- [ ] **Step 2: Implement embeddings (Voyage via Anthropic SDK or fallback)**

```python
# nova-agent/src/nova_agent/llm/embeddings.py
import hashlib
from typing import Sequence


def embed_board(grid: Sequence[Sequence[int]], dim: int = 64) -> list[float]:
    """Cheap deterministic embedding suitable for v1.

    Encodes (value, position) pairs into a hashed vector. Good enough for
    exact-board nearest-neighbor; replace with a real embedding model if
    semantic similarity matters. (Voyage 3 large via Anthropic SDK is the
    likely upgrade in v2.)
    """
    vec = [0.0] * dim
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0:
                continue
            key = f"{r}:{c}:{v}".encode()
            h = hashlib.sha256(key).digest()
            for i, byte in enumerate(h[:dim]):
                vec[i] += byte / 255.0
    # L2-normalize
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec] if norm > 0 else vec
```

- [ ] **Step 3: Implement vector store**

```python
# nova-agent/src/nova_agent/memory/vector_store.py
from pathlib import Path
import lancedb
import pyarrow as pa


class VectorStore:
    """LanceDB-backed nearest-neighbor store for board embeddings."""

    TABLE = "memory_embeddings"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))
        if self.TABLE not in self._db.table_names():
            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("vector", pa.list_(pa.float32())),
                ]
            )
            self._db.create_table(self.TABLE, schema=schema)
        self._tbl = self._db.open_table(self.TABLE)

    def upsert(self, id: str, vector: list[float]) -> None:
        self._tbl.delete(f"id = '{id}'")
        self._tbl.add([{"id": id, "vector": vector}])

    def search(self, vector: list[float], k: int = 5) -> list[tuple[str, float]]:
        results = self._tbl.search(vector).limit(k).to_list()
        return [(r["id"], float(r["_distance"])) for r in results]
```

- [ ] **Step 4: Pass tests, commit**

```bash
uv run pytest tests/test_memory_vector_store.py -v
git add nova-agent/
git commit -m "feat(memory): vector store + cheap deterministic embeddings"
```

---

## Task 14: Importance scoring

**Files:**
- Create: `nova-agent/src/nova_agent/memory/importance.py`
- Create: `nova-agent/tests/test_memory_importance.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_memory_importance.py
from nova_agent.memory.importance import score_programmatic


def test_score_programmatic_high_for_game_over():
    s = score_programmatic(rpe=-2.0, terminal=True, max_tile=1024, empty_cells=0, milestone=False)
    assert s >= 8


def test_score_programmatic_low_for_routine():
    s = score_programmatic(rpe=0.0, terminal=False, max_tile=4, empty_cells=14, milestone=False)
    assert s <= 2


def test_score_programmatic_milestone_bumps():
    base = score_programmatic(rpe=0.5, terminal=False, max_tile=1024, empty_cells=8, milestone=False)
    bumped = score_programmatic(rpe=0.5, terminal=False, max_tile=1024, empty_cells=8, milestone=True)
    assert bumped > base
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/memory/importance.py
from typing import Literal


def score_programmatic(
    *,
    rpe: float,
    terminal: bool,
    max_tile: int,
    empty_cells: int,
    milestone: bool,
) -> int:
    """Importance 1..10 derived without an LLM call.

    Components (each 0..3):
      surprise:    |rpe| spike
      jeopardy:    near-loss (low empty cells)
      grandeur:    big-tile achievement (max_tile)
      finality:    game-over event
      milestone:   first-time tile achievements
    Sum, clamp to 1..10.
    """
    surprise = min(3, int(abs(rpe) * 6))
    jeopardy = min(3, max(0, 4 - empty_cells))
    grandeur = 0 if max_tile < 128 else 1 if max_tile < 512 else 2 if max_tile < 2048 else 3
    finality = 3 if terminal else 0
    milestone_score = 2 if milestone else 0
    raw = surprise + jeopardy + grandeur + finality + milestone_score
    return max(1, min(10, raw))


def llm_rated_importance_prompt() -> str:
    """The prompt fragment to ask the VLM for a 1..10 importance rating."""
    return (
        "Rate the memorability of this 2048 game event from 1 to 10. "
        "1 = utterly mundane (e.g., merging two 2s in an empty corner). "
        "10 = extremely memorable (e.g., near-game-over save, hitting 2048 "
        "for the first time). Reply with only the integer."
    )


def combined_importance(programmatic: int, llm_rated: int | None) -> int:
    if llm_rated is None:
        return programmatic
    return max(1, min(10, round((programmatic + llm_rated) / 2)))
```

- [ ] **Step 3: Pass tests, commit**

```bash
uv run pytest tests/test_memory_importance.py -v
git add nova-agent/
git commit -m "feat(memory): programmatic + LLM-rated importance scoring"
```

---

## Task 15: Retrieval — recency, relevance, combined scoring

**Files:**
- Create: `nova-agent/src/nova_agent/memory/retrieval.py`
- Create: `nova-agent/tests/test_memory_retrieval.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_memory_retrieval.py
import math
from datetime import datetime, timedelta, timezone
from nova_agent.memory.retrieval import recency_score, cosine, combined_score


def test_recency_decays_power_law():
    now = datetime.now(timezone.utc)
    fresh = recency_score(last_accessed=now, now=now)
    week_old = recency_score(last_accessed=now - timedelta(days=7), now=now)
    month_old = recency_score(last_accessed=now - timedelta(days=30), now=now)
    assert fresh > week_old > month_old > 0


def test_cosine_identical_is_one():
    assert math.isclose(cosine([1, 0, 0], [1, 0, 0]), 1.0, abs_tol=1e-6)
    assert math.isclose(cosine([1, 0, 0], [-1, 0, 0]), -1.0, abs_tol=1e-6)


def test_combined_score_weights():
    s = combined_score(recency=0.5, importance_norm=0.5, relevance=0.5,
                       w_recency=1.0, w_importance=1.0, w_relevance=1.0)
    assert math.isclose(s, 1.5, abs_tol=1e-6)
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/memory/retrieval.py
import math
from dataclasses import dataclass
from datetime import datetime, timezone

from nova_agent.memory.types import MemoryRecord


def recency_score(*, last_accessed: datetime | None, now: datetime, half_life_days: float = 7.0) -> float:
    """Power-law decay: 1 / (1 + t/half_life)^1.5 where t is in days.

    Wixted & Carpenter (2007) — closer to human forgetting than exponential.
    """
    if last_accessed is None:
        return 0.0
    delta_days = max(0.0, (now - last_accessed).total_seconds() / 86400.0)
    return 1.0 / (1.0 + delta_days / half_life_days) ** 1.5


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def combined_score(
    *,
    recency: float,
    importance_norm: float,
    relevance: float,
    w_recency: float = 1.0,
    w_importance: float = 1.0,
    w_relevance: float = 1.0,
) -> float:
    return w_recency * recency + w_importance * importance_norm + w_relevance * relevance


@dataclass(frozen=True)
class RetrievedMemory:
    record: MemoryRecord
    score: float


def retrieve_top_k(
    *,
    candidates: list[MemoryRecord],
    query_embedding: list[float],
    now: datetime | None = None,
    k: int = 5,
    w_recency: float = 1.0,
    w_importance: float = 1.0,
    w_relevance: float = 1.0,
) -> list[RetrievedMemory]:
    now = now or datetime.now(timezone.utc)
    scored: list[RetrievedMemory] = []
    for rec in candidates:
        rec_recency = recency_score(last_accessed=rec.last_accessed or rec.timestamp, now=now)
        rec_relevance = cosine(query_embedding, rec.embedding)
        importance_norm = (rec.importance - 1) / 9  # 1..10 -> 0..1
        s = combined_score(
            recency=rec_recency,
            importance_norm=importance_norm,
            relevance=rec_relevance,
            w_recency=w_recency,
            w_importance=w_importance,
            w_relevance=w_relevance,
        )
        scored.append(RetrievedMemory(record=rec, score=s))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:k]
```

- [ ] **Step 3: Pass, commit**

```bash
git add nova-agent/
git commit -m "feat(memory): retrieval scoring (recency + importance + relevance)"
```

---

## Task 16: Wire memory into the loop (write + retrieve)

**Files:**
- Modify: `nova-agent/src/nova_agent/main.py`
- Modify: `nova-agent/src/nova_agent/decision/prompts.py`
- Create: `nova-agent/src/nova_agent/memory/coordinator.py`
- Create: `nova-agent/tests/test_memory_coordinator.py`

- [ ] **Step 1: Write coordinator test**

```python
# nova-agent/tests/test_memory_coordinator.py
from datetime import datetime, timezone
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def test_coordinator_writes_and_retrieves(tmp_path):
    coord = MemoryCoordinator(
        sqlite_path=tmp_path / "n.db",
        lancedb_path=tmp_path / "lance",
    )
    b = BoardState(grid=[[0,2,0,0]] + [[0]*4]*3, score=0)
    coord.write_move(
        board_before=b, board_after=b, action="swipe_right",
        score_delta=4, rpe=0.1, source_reasoning="merge", importance=3,
    )
    retrieved = coord.retrieve_for_board(b, k=3)
    assert len(retrieved) >= 1
```

- [ ] **Step 2: Implement coordinator**

```python
# nova-agent/src/nova_agent/memory/coordinator.py
from datetime import datetime, timezone
from pathlib import Path
import uuid

from nova_agent.llm.embeddings import embed_board
from nova_agent.memory.episodic import EpisodicStore
from nova_agent.memory.retrieval import RetrievedMemory, retrieve_top_k
from nova_agent.memory.types import AffectSnapshot, MemoryRecord
from nova_agent.memory.vector_store import VectorStore
from nova_agent.perception.types import BoardState


class MemoryCoordinator:
    def __init__(self, *, sqlite_path: Path, lancedb_path: Path):
        self.episodic = EpisodicStore(sqlite_path)
        self.vector = VectorStore(lancedb_path)

    def write_move(
        self,
        *,
        board_before: BoardState,
        board_after: BoardState,
        action: str,
        score_delta: int,
        rpe: float,
        importance: int,
        source_reasoning: str | None = None,
        affect: AffectSnapshot | None = None,
        tags: list[str] | None = None,
    ) -> str:
        rec_id = f"ep_{uuid.uuid4().hex[:12]}"
        emb = embed_board(board_before.grid)
        rec = MemoryRecord(
            id=rec_id,
            timestamp=datetime.now(timezone.utc),
            board_before=board_before,
            board_after=board_after,
            action=action,
            score_delta=score_delta,
            rpe=rpe,
            importance=importance,
            tags=tags or [],
            embedding=emb,
            source_reasoning=source_reasoning,
            affect=affect,
        )
        self.episodic.insert(rec)
        self.vector.upsert(rec_id, emb)
        return rec_id

    def retrieve_for_board(self, board: BoardState, k: int = 5) -> list[RetrievedMemory]:
        emb = embed_board(board.grid)
        # Vector pre-filter to ~50 candidates, then full re-rank
        candidate_ids = [id_ for id_, _ in self.vector.search(emb, k=min(50, k * 10))]
        candidates = [r for r in (self.episodic.get(i) for i in candidate_ids) if r]
        if not candidates:
            return []
        return retrieve_top_k(candidates=candidates, query_embedding=emb, k=k)
```

- [ ] **Step 3: Update prompt to include retrieved memories**

```python
# nova-agent/src/nova_agent/decision/prompts.py — extend with memory context
def render_memories(memories: list) -> str:
    if not memories:
        return ""
    lines = ["Memory recalls (most relevant past situations):"]
    for m in memories:
        rec = m.record
        lines.append(
            f"- [importance {rec.importance}/10] action={rec.action} "
            f"score_delta={rec.score_delta} reasoning={rec.source_reasoning or '—'}"
        )
    return "\n".join(lines)


def build_user_prompt_v2(*, grid: list[list[int]], score: int, memories: list) -> str:
    base = build_user_prompt(grid=grid, score=score)
    mem_block = render_memories(memories)
    if mem_block:
        return f"{base}\n\n{mem_block}"
    return base
```

- [ ] **Step 4: Wire into main.py**

In `run()`:

```python
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.decision.prompts import build_user_prompt_v2

# init:
memory = MemoryCoordinator(sqlite_path=s.sqlite_path, lancedb_path=s.lancedb_path)

# in loop, before decider.decide:
retrieved = memory.retrieve_for_board(board, k=5)
# pass `retrieved` into a new decider variant `decide_with_context` (extend ReactDecider similarly)

# after the swipe and outcome:
memory.write_move(
    board_before=board, board_after=new_board,
    action=decision.action, score_delta=new_board.score - board.score,
    rpe=0.0,  # placeholder until Week 3
    importance=1,  # placeholder until score parsing + RPE
    source_reasoning=decision.reasoning,
)
await bus.publish("memory_write", {"id": rec_id, "importance": 1})
await bus.publish("memory_retrieved", {"count": len(retrieved)})
```

- [ ] **Step 5: Tests pass + smoke**

```bash
uv run pytest -v
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/
git commit -m "feat(memory): coordinator wires episodic+vector; integrated into loop"
```

---

## Task 17: MemoryFeed UI component + WebSocket events

**Files:**
- Create: `nova-viewer/lib/types.ts`
- Create: `nova-viewer/lib/websocket.ts`
- Create: `nova-viewer/app/components/MemoryFeed.tsx`
- Create: `nova-viewer/app/components/MemoryCard.tsx`
- Modify: `nova-viewer/app/page.tsx`

- [ ] **Step 1: Define types**

```ts
// nova-viewer/lib/types.ts
export type AgentEvent =
  | { event: "perception"; data: { score: number; step: number; grid?: number[][] } }
  | { event: "decision"; data: { action: string; reasoning: string; observation: string; confidence: string } }
  | { event: "memory_write"; data: { id: string; importance: number; tags: string[] } }
  | { event: "memory_retrieved"; data: { items: RetrievedMemoryDTO[] } }
  | { event: string; data: unknown };

export interface RetrievedMemoryDTO {
  id: string;
  importance: number;
  action: string;
  score_delta: number;
  reasoning: string | null;
  tags: string[];
  preview_grid: number[][];
}
```

- [ ] **Step 2: WebSocket hook**

```ts
// nova-viewer/lib/websocket.ts
"use client";
import { useEffect, useState } from "react";
import type { AgentEvent } from "./types";

export function useNovaSocket() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const url = `ws://${process.env.NEXT_PUBLIC_WS_HOST ?? "127.0.0.1"}:${
      process.env.NEXT_PUBLIC_WS_PORT ?? "8765"
    }`;
    const ws = new WebSocket(url);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev.slice(-99), msg]);
      } catch {}
    };
    return () => ws.close();
  }, []);

  return { events, connected };
}
```

- [ ] **Step 3: MemoryCard + MemoryFeed components**

```tsx
// nova-viewer/app/components/MemoryCard.tsx
import type { RetrievedMemoryDTO } from "@/lib/types";

export function MemoryCard({ m }: { m: RetrievedMemoryDTO }) {
  const isTrauma = m.tags.includes("trauma");
  return (
    <div className={`rounded-lg p-3 text-xs border ${isTrauma ? "border-red-900 bg-red-950/30" : "border-zinc-800 bg-zinc-900/40"}`}>
      <div className="flex justify-between items-start mb-1">
        <span className="text-cyan-400 font-mono">{m.action}</span>
        <span className={`px-2 py-0.5 rounded text-[10px] ${m.importance >= 7 ? "bg-red-900/60" : "bg-zinc-700/60"}`}>
          {m.importance}/10
        </span>
      </div>
      <div className="text-zinc-400 line-clamp-2">{m.reasoning ?? "—"}</div>
      <div className="flex gap-1 mt-1">
        {m.tags.map((t) => (
          <span key={t} className="text-[10px] text-zinc-500">#{t}</span>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// nova-viewer/app/components/MemoryFeed.tsx
import { MemoryCard } from "./MemoryCard";
import type { RetrievedMemoryDTO } from "@/lib/types";

export function MemoryFeed({ items }: { items: RetrievedMemoryDTO[] }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm uppercase tracking-wider text-zinc-500">Recalling</h3>
      {items.length === 0 && <p className="text-xs text-zinc-600">No memories surfaced.</p>}
      <div className="space-y-2">
        {items.map((m) => (
          <MemoryCard key={m.id} m={m} />
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Wire into `page.tsx`** (replace the placeholder feed with real components)

(Show enough of the updated page.tsx to make the change clear. Keep the layout, swap the right column to use MemoryFeed and a recent-events log.)

- [ ] **Step 5: Update agent to publish full memory DTOs**

In `main.py`, update the publish call to send the actual retrieved items:

```python
await bus.publish("memory_retrieved", {
    "items": [
        {
            "id": m.record.id,
            "importance": m.record.importance,
            "action": m.record.action,
            "score_delta": m.record.score_delta,
            "reasoning": m.record.source_reasoning,
            "tags": m.record.tags,
            "preview_grid": m.record.board_before.grid,
        }
        for m in retrieved
    ]
})
```

- [ ] **Step 6: Run end-to-end**

Boot emulator → run `uv run nova` → open the viewer at http://localhost:3000 → see the memory feed populate after a few moves.

- [ ] **Step 7: Commit**

```bash
git add nova-viewer/ nova-agent/
git commit -m "feat(viewer): MemoryFeed + MemoryCard components and DTO wiring"
```

---

## Task 18: Score region OCR + integration test

**Files:**
- Modify: `nova-agent/src/nova_agent/perception/ocr.py`
- Modify: `nova-agent/tests/test_perception_ocr.py`
- Create: `nova-agent/tests/test_e2e_30moves.py`

- [ ] **Step 1: Extend OCR to read score region**

```python
# Add to nova-agent/src/nova_agent/perception/ocr.py
import re
import pytesseract  # add to deps if not present

_SCORE_BOX = (300, 250, 700, 400)  # (left, top, right, bottom) — calibrate

def _read_score(image: Image.Image) -> int:
    crop = image.crop(_SCORE_BOX)
    text = pytesseract.image_to_string(crop, config="--psm 7 -c tessedit_char_whitelist=0123456789")
    digits = re.sub(r"\D+", "", text)
    return int(digits) if digits else 0
```

(Add `pytesseract>=0.3.10` to `pyproject.toml`. Install Tesseract: `brew install tesseract`.)

Then update `BoardOCR.read` to populate `score` via `_read_score(image)` instead of hard-coding 0.

- [ ] **Step 2: Update fixture-based tests with expected scores**

- [ ] **Step 3: Write headless integration test**

```python
# nova-agent/tests/test_e2e_30moves.py
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_30_move_loop_writes_memory(tmp_path):
    """Full end-to-end with everything mocked except memory + retrieval."""
    # ... build a fake capture that returns a sequence of stub PIL images,
    # a mocked LLM that always returns swipe_right,
    # a mocked ADB,
    # and verify that after 30 ticks, memory has 30 records and retrieval surfaces ≥1.
```

(This is a substantial test — write it fully or stub for now and flesh out in Week 6.)

- [ ] **Step 4: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(perception): score-region OCR; e2e 30-move integration test"
```

---

## Task 19: Polish + Week 2 wrap

- [ ] **Step 1: Type-check everything**

```bash
cd nova-agent
uv run mypy src/
```

Fix any errors.

- [ ] **Step 2: Lint**

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

- [ ] **Step 3: Full test pass**

```bash
uv run pytest -v
```

- [ ] **Step 4: Live smoke test** — boot emulator, run agent, watch the brain panel populate memory feed across 50 moves.

- [ ] **Step 5: Commit + tag**

```bash
git add -A
git commit -m "chore(week-2): polish + lint pass"
git tag week-2-complete
git push origin main --tags
```

**End of Week 2.** Memory writes every move with importance, retrieves top-5 relevant memories, brain panel shows memory feed live.

---

# WEEK 3 — Affect + Reward Prediction Error

**Goal:** Affect vector tracks Nova's mood across the session; RPE drives dopamine spikes; affect is verbalized into the prompt; brain panel renders mood gauge, dopamine bar, affect label live.

**Security review:** End of Week 3 (Task 30).

---

## Task 20: AffectVector type + update rules

**Files:**
- Create: `nova-agent/src/nova_agent/affect/__init__.py`
- Create: `nova-agent/src/nova_agent/affect/types.py`
- Create: `nova-agent/src/nova_agent/affect/state.py`
- Create: `nova-agent/tests/test_affect_state.py`

- [ ] **Step 1: Failing tests**

```python
# nova-agent/tests/test_affect_state.py
from nova_agent.affect.state import AffectState
from nova_agent.affect.types import AffectVector


def test_initial_state_neutral():
    a = AffectState()
    assert -0.1 <= a.vector.valence <= 0.1
    assert 0.0 <= a.vector.arousal <= 0.3
    assert a.vector.dopamine == 0.0


def test_positive_rpe_spikes_dopamine_and_lifts_valence():
    a = AffectState()
    before = a.vector
    a.update(rpe=0.5, empty_cells=10, terminal=False, trauma_triggered=False)
    after = a.vector
    assert after.dopamine > before.dopamine
    assert after.valence > before.valence


def test_negative_rpe_increases_frustration():
    a = AffectState()
    a.update(rpe=-0.5, empty_cells=10, terminal=False, trauma_triggered=False)
    assert a.vector.frustration > 0


def test_anxiety_rises_when_few_empty_cells():
    a = AffectState()
    a.update(rpe=0.0, empty_cells=1, terminal=False, trauma_triggered=False)
    assert a.vector.anxiety > 0.4
```

- [ ] **Step 2: Implement types**

```python
# nova-agent/src/nova_agent/affect/__init__.py
from nova_agent.affect.types import AffectVector
from nova_agent.affect.state import AffectState
```

```python
# nova-agent/src/nova_agent/affect/types.py
from dataclasses import dataclass


@dataclass(frozen=True)
class AffectVector:
    valence: float = 0.0       # [-1, +1]
    arousal: float = 0.2       # [0, 1]
    dopamine: float = 0.0      # [0, 1]
    frustration: float = 0.0   # [0, 1]
    anxiety: float = 0.0       # [0, 1]
    confidence: float = 0.5    # [0, 1]
```

- [ ] **Step 3: Implement update rules**

```python
# nova-agent/src/nova_agent/affect/state.py
from nova_agent.affect.types import AffectVector


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class AffectState:
    """Tracks Nova's affective state across a session.

    Update rules per spec §3.5. Most variables decay slightly each tick; the
    decay term is tuned so that after ~10 'normal' moves the state returns
    near the baseline.
    """

    def __init__(self) -> None:
        self.vector = AffectVector()

    def update(
        self,
        *,
        rpe: float,
        empty_cells: int,
        terminal: bool,
        trauma_triggered: bool,
    ) -> AffectVector:
        v = self.vector
        # baseline drift toward equilibrium
        valence = v.valence * 0.95
        arousal = v.arousal * 0.92
        dopamine = v.dopamine * 0.6  # fast decay
        frustration = v.frustration * 0.92
        anxiety = v.anxiety * 0.85
        confidence = v.confidence * 0.98 + 0.5 * 0.02  # toward 0.5

        # rpe-driven updates
        valence += 0.7 * _clamp(rpe, -1.0, 1.0)
        if rpe > 0:
            dopamine += min(1.0, rpe)
        else:
            frustration += min(1.0, -rpe * 0.6)

        # arousal: board pressure + |rpe|
        pressure = 1.0 - empty_cells / 16
        arousal += 0.4 * pressure + 0.2 * abs(rpe)

        # anxiety: jeopardy + trauma
        anxiety += 0.5 * max(0, (3 - empty_cells) / 3)
        if trauma_triggered:
            anxiety += 0.3
        if terminal:
            anxiety = 1.0

        # confidence: sign(rpe) * sqrt(|rpe|)
        confidence += 0.4 * (rpe / max(1e-3, abs(rpe))) * (abs(rpe) ** 0.5) if rpe != 0 else 0

        self.vector = AffectVector(
            valence=_clamp(valence, -1.0, 1.0),
            arousal=_clamp(arousal, 0.0, 1.0),
            dopamine=_clamp(dopamine, 0.0, 1.0),
            frustration=_clamp(frustration, 0.0, 1.0),
            anxiety=_clamp(anxiety, 0.0, 1.0),
            confidence=_clamp(confidence, 0.0, 1.0),
        )
        return self.vector
```

- [ ] **Step 4: Pass + commit**

```bash
uv run pytest tests/test_affect_state.py -v
git add nova-agent/
git commit -m "feat(affect): AffectVector + update rules per spec §3.5"
```

---

## Task 21: Verbalize affect → natural language

**Files:**
- Create: `nova-agent/src/nova_agent/affect/verbalize.py`
- Create: `nova-agent/tests/test_affect_verbalize.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_affect_verbalize.py
from nova_agent.affect.types import AffectVector
from nova_agent.affect.verbalize import describe


def test_describe_anxious_state():
    v = AffectVector(valence=-0.3, arousal=0.8, dopamine=0.1, frustration=0.4, anxiety=0.7, confidence=0.4)
    s = describe(v)
    assert "anxious" in s.lower() or "nervous" in s.lower()


def test_describe_happy_state():
    v = AffectVector(valence=0.7, arousal=0.5, dopamine=0.6, frustration=0.0, anxiety=0.0, confidence=0.9)
    s = describe(v)
    lc = s.lower()
    assert "good" in lc or "satisfied" in lc or "confident" in lc
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/affect/verbalize.py
from nova_agent.affect.types import AffectVector


def describe(v: AffectVector) -> str:
    """Translate an affect vector into a one-sentence stage direction.

    Used as a string fragment in the VLM prompt.
    """
    parts: list[str] = []

    # Mood (valence × arousal)
    if v.anxiety > 0.6:
        parts.append("You feel anxious.")
    elif v.frustration > 0.5:
        parts.append("You feel frustrated and impatient.")
    elif v.valence > 0.4 and v.arousal > 0.4:
        parts.append("You feel satisfied — recent moves are paying off.")
    elif v.valence > 0.3:
        parts.append("You feel calm and cautiously optimistic.")
    elif v.valence < -0.3:
        parts.append("You feel discouraged.")
    else:
        parts.append("You feel calm and focused.")

    # Recent reward
    if v.dopamine > 0.4:
        parts.append("The last move felt better than expected.")
    elif v.dopamine < 0.05 and v.frustration > 0.3:
        parts.append("Recent moves have been disappointing.")

    # Pressure / arousal
    if v.arousal > 0.7:
        parts.append("Your pulse is up; the board is tight.")

    # Confidence
    if v.confidence < 0.3:
        parts.append("You don't fully trust your current strategy.")
    elif v.confidence > 0.7:
        parts.append("You're confident in your read of the board.")

    return " ".join(parts)
```

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(affect): verbalize affect vector into prompt sentence"
```

---

## Task 22: Outcome evaluator (RPE + value function V)

**Files:**
- Create: `nova-agent/src/nova_agent/affect/rpe.py`
- Create: `nova-agent/tests/test_affect_rpe.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_affect_rpe.py
from nova_agent.affect.rpe import value_heuristic, rpe
from nova_agent.perception.types import BoardState


def test_value_heuristic_higher_for_more_pairs():
    no_pairs = BoardState(grid=[[2,4,8,16]] * 4, score=0)
    with_pairs = BoardState(grid=[[2,2,4,4],[4,4,8,8],[0]*4,[0]*4], score=0)
    assert value_heuristic(with_pairs) > value_heuristic(no_pairs)


def test_rpe_positive_when_actual_exceeds_expected():
    b = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    delta = rpe(actual_score_delta=8, board_before=b)
    # heuristic predicted ~4; actual was 8; rpe should be positive
    assert delta > 0
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/affect/rpe.py
from nova_agent.perception.types import BoardState


def value_heuristic(board: BoardState) -> float:
    """Predict expected score gain from the current board.

    Cheap heuristic: count adjacent equal-value pairs and value them by tile.
    """
    grid = board.grid
    expected = 0.0
    for r in range(4):
        for c in range(4):
            v = grid[r][c]
            if v == 0:
                continue
            if c + 1 < 4 and grid[r][c + 1] == v:
                expected += v * 0.5
            if r + 1 < 4 and grid[r + 1][c] == v:
                expected += v * 0.5
    return expected


def rpe(*, actual_score_delta: int, board_before: BoardState) -> float:
    """Reward Prediction Error, normalized roughly to [-1, 1].

    δ = (actual − expected) / scale
    scale grows with board's max tile so big plays don't permanently saturate
    """
    expected = value_heuristic(board_before)
    diff = actual_score_delta - expected
    scale = max(8, board_before.max_tile)
    return max(-1.0, min(1.0, diff / scale))
```

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(affect): RPE outcome evaluator + V heuristic"
```

---

## Task 23: Wire affect into the loop

**Files:**
- Modify: `nova-agent/src/nova_agent/main.py`
- Modify: `nova-agent/src/nova_agent/decision/prompts.py`

- [ ] **Step 1: Update prompt builder to inject affect description**

```python
# in decision/prompts.py — add a new builder
def build_user_prompt_v3(
    *, grid: list[list[int]], score: int, memories: list, affect_text: str,
) -> str:
    base = build_user_prompt_v2(grid=grid, score=score, memories=memories)
    return f"{base}\n\nMood: {affect_text}"
```

- [ ] **Step 2: Update main.py loop**

```python
from nova_agent.affect.state import AffectState
from nova_agent.affect.rpe import rpe
from nova_agent.affect.verbalize import describe

# init:
affect = AffectState()

# in loop:
#   current_affect_text = describe(affect.vector)
#   # build prompt with affect_text
#   ...
#   delta = new_board.score - board.score
#   delta_rpe = rpe(actual_score_delta=delta, board_before=board)
#   trauma_triggered = any("trauma" in m.record.tags for m in retrieved)
#   affect.update(rpe=delta_rpe, empty_cells=new_board.empty_cells, terminal=False, trauma_triggered=trauma_triggered)
#   await bus.publish("affect", { ... full vector ... })
```

- [ ] **Step 3: Smoke + commit**

```bash
uv run pytest -v
git add nova-agent/
git commit -m "feat(affect): wired into decision loop with RPE + verbalization"
```

---

## Task 24: MoodGauge component

**Files:**
- Create: `nova-viewer/app/components/MoodGauge.tsx`

- [ ] **Step 1: Implement**

```tsx
// nova-viewer/app/components/MoodGauge.tsx
"use client";
import { motion } from "framer-motion";

interface Props {
  valence: number;  // -1..1
  arousal: number;  //  0..1
}

function moodColor(valence: number, arousal: number): string {
  // green = high val, red = low val; saturation scales with arousal
  const hue = valence > 0 ? 140 : 0;
  const sat = 40 + arousal * 50;
  const lit = 50 - Math.abs(valence) * 10;
  return `hsl(${hue} ${sat}% ${lit}%)`;
}

export function MoodGauge({ valence, arousal }: Props) {
  // Map (valence × arousal) into a circle disk centered in a 160×160 SVG
  const r = 70;
  const cx = 80, cy = 80;
  const x = cx + valence * r;
  const y = cy + (1 - arousal * 2) * r;  // arousal=1 at top
  const color = moodColor(valence, arousal);

  return (
    <section>
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">Mood</h3>
      <svg width="160" height="160" className="block">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#3f3f46" strokeWidth="1" />
        <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} stroke="#3f3f46" strokeWidth="0.5" />
        <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} stroke="#3f3f46" strokeWidth="0.5" />
        <motion.circle
          cx={x}
          cy={y}
          r={10}
          fill={color}
          initial={false}
          animate={{ cx: x, cy: y, fill: color }}
          transition={{ type: "spring", stiffness: 80, damping: 18 }}
        />
        <text x={cx} y={12} fill="#71717a" fontSize="10" textAnchor="middle">arousal</text>
        <text x={cx + r + 4} y={cy + 4} fill="#71717a" fontSize="10">+val</text>
      </svg>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): MoodGauge component"
```

---

## Task 25: DopamineBar component

**Files:**
- Create: `nova-viewer/app/components/DopamineBar.tsx`

- [ ] **Step 1: Implement**

```tsx
// nova-viewer/app/components/DopamineBar.tsx
"use client";
import { motion } from "framer-motion";

export function DopamineBar({ level }: { level: number }) {
  const pct = Math.max(0, Math.min(1, level)) * 100;
  return (
    <section>
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">Dopamine</h3>
      <div className="h-32 w-3 rounded-full bg-zinc-800 relative overflow-hidden">
        <motion.div
          className="absolute bottom-0 left-0 right-0 bg-cyan-400"
          style={{ borderRadius: "9999px" }}
          initial={false}
          animate={{ height: `${pct}%` }}
          transition={{ type: "spring", stiffness: 240, damping: 20 }}
        />
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): DopamineBar component"
```

---

## Task 26: AffectLabel component

**Files:**
- Create: `nova-viewer/app/components/AffectLabel.tsx`

- [ ] **Step 1: Implement**

```tsx
// nova-viewer/app/components/AffectLabel.tsx
"use client";
import { AnimatePresence, motion } from "framer-motion";

export function AffectLabel({ text }: { text: string }) {
  return (
    <section className="min-h-[60px]">
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">Feeling</h3>
      <AnimatePresence mode="wait">
        <motion.p
          key={text}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.4 }}
          className="text-zinc-200 text-sm leading-relaxed italic"
        >
          “{text}”
        </motion.p>
      </AnimatePresence>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): AffectLabel component"
```

---

## Task 27: Wire affect events into page.tsx

**Files:**
- Modify: `nova-viewer/app/page.tsx`

- [ ] **Step 1: Replace page.tsx body** to include MoodGauge, DopamineBar, AffectLabel, MemoryFeed plus the placeholder GameStream slot

(Use `useNovaSocket` hook; route incoming `"affect"` events to component state; route incoming `"memory_retrieved"` to `MemoryFeed`.)

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): wire affect events to mood/dopamine/label components"
```

---

## Task 28: GameStream component (scrcpy embed)

**Files:**
- Create: `nova-viewer/app/components/GameStream.tsx`

- [ ] **Step 1: Implement**

scrcpy doesn't natively output to a browser. Two options:
- (a) **Capture scrcpy window in OBS** for the demo recording (simplest, picked for v1).
- (b) Run `scrcpy --serial emulator-5554 --no-display --record output.mkv` and stream into a `<video>` (more work).

For v1 we go with (a). The component is therefore a styled placeholder that says "live game" and tells the user to run `scrcpy --serial $ADB_DEVICE_ID` in a separate window:

```tsx
// nova-viewer/app/components/GameStream.tsx
export function GameStream() {
  return (
    <section className="aspect-[9/16] w-full bg-zinc-950 rounded-lg border border-zinc-800 flex items-center justify-center">
      <div className="text-center text-zinc-500 text-sm">
        <p className="mb-2">Live game stream</p>
        <p className="text-xs">Run <code className="bg-zinc-800 px-1 rounded">scrcpy --serial $ADB_DEVICE_ID</code> in a terminal.</p>
        <p className="text-xs mt-1">For demo: capture both windows with OBS.</p>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): GameStream placeholder + scrcpy run instructions"
```

---

## Task 29: Stats footer + integrate everything

**Files:**
- Create: `nova-viewer/app/components/StatsFooter.tsx`
- Create: `nova-viewer/app/components/BrainPanel.tsx`
- Modify: `nova-viewer/app/page.tsx`

- [ ] **Step 1: StatsFooter**

```tsx
// nova-viewer/app/components/StatsFooter.tsx
export function StatsFooter({ score, move, games, best }: { score: number; move: number; games: number; best: number }) {
  return (
    <footer className="text-xs text-zinc-500 border-t border-zinc-800 pt-2 flex justify-between">
      <span>Score {score}</span>
      <span>Move {move}</span>
      <span>Games {games}</span>
      <span>Best {best}</span>
    </footer>
  );
}
```

- [ ] **Step 2: BrainPanel composite**

```tsx
// nova-viewer/app/components/BrainPanel.tsx — composes mood, dopamine, label, memory feed, footer
```

(Wire all child components and pass props from the page-level state.)

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): StatsFooter + BrainPanel composite layout"
```

---

## Task 30: Week 3 security review + tag

**Files:**
- Create: `docs/specs/security-reviews/2026-week-03.md`

- [ ] **Step 1: Run gitleaks**

```bash
gitleaks detect --redact
```

- [ ] **Step 2: Confirm GitHub settings still enabled**

```bash
gh api repos/IdoHoresh/project-nova --jq '.security_and_analysis'
```

- [ ] **Step 3: Verify no env files in index**

```bash
git ls-files | grep -iE 'env|secret|credential' | grep -v '\.example$'
```

- [ ] **Step 4: Verify `.env.example` clean**

- [ ] **Step 5: Audit dependency vulnerabilities**

```bash
cd nova-agent
uv pip list | grep -iE "anthropic|cryptography"  # quick sanity
```

Check Dependabot alerts: https://github.com/IdoHoresh/project-nova/security/dependabot

- [ ] **Step 6: Write review record + tag**

```bash
# write docs/specs/security-reviews/2026-week-03.md (similar to week-01)
git add docs/specs/security-reviews/
git commit -m "chore(security): Week 3 review — clean"
git tag week-3-complete
git push origin main --tags
```

**End of Week 3.** Affect drives prompts; mood gauges + dopamine pulse + affect label all live in the brain panel.

---

# WEEK 4 — Trauma + Tree of Thoughts + Reflection

**Goal:** Catastrophic losses tag trauma memories that bias future caution. ToT deliberation kicks in on tight boards. Post-game reflection writes semantic rules. Heuristic fallback closes the safety net.

---

## Task 31: Trauma tagging (post-game-over)

**Files:**
- Create: `nova-agent/src/nova_agent/memory/trauma.py`
- Create: `nova-agent/tests/test_memory_trauma.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_memory_trauma.py
from datetime import datetime, timezone, timedelta
from nova_agent.memory.trauma import tag_trauma
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def make_rec(score=0, importance=3) -> MemoryRecord:
    b = BoardState(grid=[[0]*4]*4, score=score)
    return MemoryRecord(
        id=f"r_{score}",
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=10 - score),
        board_before=b, board_after=b,
        action="swipe_right", score_delta=0, rpe=0.0,
        importance=importance, tags=[], embedding=[0.0]*8,
    )


def test_tag_trauma_after_catastrophic_loss():
    last_5 = [make_rec(score=i) for i in range(5)]
    tagged = tag_trauma(last_5_moves=last_5, final_score=200, was_catastrophic=True)
    assert all("trauma" in r.tags for r in tagged)
    assert all(r.importance >= 7 for r in tagged)
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/memory/trauma.py
from nova_agent.memory.types import MemoryRecord


def is_catastrophic(*, final_score: int, max_tile_reached: int, last_empty_cells: int) -> bool:
    """A loss is catastrophic if score is low relative to the max tile achieved
    AND the board was contested (few empty cells) before death.
    """
    return last_empty_cells <= 2 and max_tile_reached >= 64 and final_score < max_tile_reached * 4


def tag_trauma(*, last_5_moves: list[MemoryRecord], final_score: int, was_catastrophic: bool) -> list[MemoryRecord]:
    if not was_catastrophic:
        return last_5_moves
    tagged: list[MemoryRecord] = []
    for r in last_5_moves:
        new_tags = list(set(r.tags + ["trauma", "loss_precondition"]))
        new_importance = min(10, max(r.importance, 7) + 2)
        tagged.append(
            MemoryRecord(
                id=r.id,
                timestamp=r.timestamp,
                board_before=r.board_before,
                board_after=r.board_after,
                action=r.action,
                score_delta=r.score_delta,
                rpe=r.rpe,
                importance=new_importance,
                tags=new_tags,
                embedding=r.embedding,
                last_accessed=r.last_accessed,
                source_reasoning=r.source_reasoning,
                affect=r.affect,
            )
        )
    return tagged


def trauma_decay(record: MemoryRecord, decay: float = 0.95) -> MemoryRecord:
    """Soft-decay trauma weight after a successful avoidance."""
    if "trauma" not in record.tags:
        return record
    new_importance = max(4, int(record.importance * decay))
    return MemoryRecord(
        **{**record.__dict__, "importance": new_importance}
    )
```

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(memory): trauma tagging + decay"
```

---

## Task 32: Trauma retrieval radius widening

**Files:**
- Modify: `nova-agent/src/nova_agent/memory/retrieval.py`
- Modify: `nova-agent/tests/test_memory_retrieval.py`

- [ ] **Step 1: Extend `retrieve_top_k` to widen the relevance threshold for trauma-tagged memories**

```python
# In retrieval.py — extend combined_score branch for trauma
def retrieve_top_k(... existing args ..., trauma_relevance_floor: float = 0.4) -> list[RetrievedMemory]:
    # ... existing ...
    for rec in candidates:
        rec_relevance = cosine(query_embedding, rec.embedding)
        if "trauma" in rec.tags and rec_relevance > trauma_relevance_floor:
            rec_relevance = max(rec_relevance, 0.7)  # boost
        # ... rest of scoring ...
```

- [ ] **Step 2: Test with synthetic memories**

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(memory): trauma retrieval boosts relevance for loosely-similar boards"
```

---

## Task 33: Tree-of-Thoughts deliberation

**Files:**
- Create: `nova-agent/src/nova_agent/decision/tot.py`
- Create: `nova-agent/tests/test_decision_tot.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_decision_tot.py
from unittest.mock import MagicMock
from nova_agent.decision.tot import ToTDecider
from nova_agent.perception.types import BoardState


def test_tot_returns_best_branch():
    fake_llm = MagicMock()
    # Each call generates a candidate + its value estimate
    fake_llm.complete.side_effect = [
        ('{"action":"swipe_up","reasoning":"good","value":0.7}', MagicMock(input_tokens=100, output_tokens=20, cost_usd=0.01)),
        ('{"action":"swipe_down","reasoning":"bad","value":0.1}', MagicMock(input_tokens=100, output_tokens=20, cost_usd=0.01)),
        ('{"action":"swipe_left","reasoning":"meh","value":0.4}', MagicMock(input_tokens=100, output_tokens=20, cost_usd=0.01)),
    ]
    decider = ToTDecider(llm=fake_llm)
    board = BoardState(grid=[[0,2,0,0]] + [[0]*4]*3, score=0)
    decision = decider.decide(board=board, screenshot_b64="ignored", num_branches=3)
    assert decision.action == "swipe_up"
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/decision/tot.py
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, Field

from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json
from nova_agent.perception.types import BoardState
from nova_agent.decision.react import Decision


class _ToTBranch(BaseModel):
    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    reasoning: str
    value: float = Field(ge=0.0, le=1.0)


_TOT_SYSTEM = """\
You are evaluating one candidate move for a 2048 game. Imagine the board after
swiping in the proposed direction; rate the resulting position from 0 (terrible,
near-loss) to 1 (excellent, opens many merges). Be honest.

Respond as strict JSON:
{"action": "swipe_up|swipe_down|swipe_left|swipe_right",
 "reasoning": "1-2 sentences",
 "value": 0.0..1.0}
"""


class ToTDecider:
    def __init__(self, *, llm: LLM):
        self.llm = llm

    def decide(
        self,
        *,
        board: BoardState,
        screenshot_b64: str,
        num_branches: int = 4,
    ) -> Decision:
        candidates: list[_ToTBranch] = []
        directions = ["swipe_up", "swipe_down", "swipe_left", "swipe_right"][:num_branches]
        for direction in directions:
            user = (
                f"Board:\n{board.grid}\nScore: {board.score}\n\n"
                f"Evaluate the move: {direction}"
            )
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                        {"type": "text", "text": user},
                    ],
                }
            ]
            text, _ = self.llm.complete(system=_TOT_SYSTEM, messages=messages, max_tokens=200, temperature=0.5)
            try:
                candidates.append(parse_json(text, _ToTBranch))
            except Exception:
                continue
        if not candidates:
            raise RuntimeError("ToT produced no valid candidates")
        best = max(candidates, key=lambda c: c.value)
        return Decision(
            action=best.action,
            observation=f"ToT considered {len(candidates)} candidates",
            reasoning=best.reasoning,
            confidence="medium",
        )
```

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(decision): Tree-of-Thoughts deliberation"
```

---

## Task 34: Arbiter (default vs ToT)

**Files:**
- Create: `nova-agent/src/nova_agent/decision/arbiter.py`
- Create: `nova-agent/tests/test_decision_arbiter.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_decision_arbiter.py
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.affect.types import AffectVector
from nova_agent.perception.types import BoardState


def test_use_tot_when_high_anxiety_and_high_max_tile():
    b = BoardState(grid=[[256, 0, 0, 0]] + [[0]*4]*3, score=0)
    a = AffectVector(anxiety=0.8)
    assert should_use_tot(board=b, affect=a) is True


def test_default_react_when_calm():
    b = BoardState(grid=[[2, 0, 0, 0]] + [[0]*4]*3, score=0)
    a = AffectVector(anxiety=0.1)
    assert should_use_tot(board=b, affect=a) is False
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/decision/arbiter.py
from nova_agent.affect.types import AffectVector
from nova_agent.perception.types import BoardState


def should_use_tot(*, board: BoardState, affect: AffectVector) -> bool:
    """Trigger ToT when situation is hard and Nova is anxious."""
    if affect.anxiety <= 0.6:
        return False
    return board.max_tile >= 256 or board.empty_cells <= 3
```

- [ ] **Step 3: Wire into main.py**

```python
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.decision.tot import ToTDecider

# init both deciders
# ReAct uses the cheap default model (Gemini Flash); ToT uses the strong
# deliberation model (Gemini Pro). Each gets its own LLM instance via the
# factory so the budget-guard accounting is correct per-model.
react_decider = ReactDecider(llm=build_llm(
    model=s.decision_model,
    google_api_key=s.google_api_key,
    anthropic_api_key=s.anthropic_api_key,
    daily_cap_usd=s.daily_budget_usd,
))
tot_decider = ToTDecider(llm=build_llm(
    model=s.deliberation_model,
    google_api_key=s.google_api_key,
    anthropic_api_key=s.anthropic_api_key,
    daily_cap_usd=s.daily_budget_usd,
))

# in loop:
mode = "tot" if should_use_tot(board=board, affect=affect.vector) else "react"
decision = (tot_decider if mode == "tot" else react_decider).decide(board=board, screenshot_b64=b64)
await bus.publish("mode", {"mode": mode})
```

- [ ] **Step 4: Commit**

```bash
git add nova-agent/
git commit -m "feat(decision): arbiter chooses ReAct vs ToT based on board+affect"
```

---

## Task 35: Heuristic fallback (Take-The-Best)

**Files:**
- Create: `nova-agent/src/nova_agent/decision/heuristic.py`
- Create: `nova-agent/tests/test_decision_heuristic.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_decision_heuristic.py
from nova_agent.decision.heuristic import take_the_best
from nova_agent.perception.types import BoardState


def test_prefers_obvious_merge():
    b = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    action = take_the_best(board=b)
    # swipe_left or swipe_right both merge those 2s
    assert action in ("swipe_left", "swipe_right")


def test_keeps_max_in_corner():
    b = BoardState(grid=[[64,2,0,0],[2,0,0,0],[0,0,0,0],[0,0,0,0]], score=0)
    action = take_the_best(board=b)
    assert action != "swipe_down"  # would yank 64 off the corner
```

- [ ] **Step 2: Implement**

```python
# nova-agent/src/nova_agent/decision/heuristic.py
from nova_agent.perception.types import BoardState


_DIRS = ["swipe_up", "swipe_down", "swipe_left", "swipe_right"]


def _shift_left(row: list[int]) -> tuple[list[int], int]:
    nz = [v for v in row if v != 0]
    out: list[int] = []
    gain = 0
    i = 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            out.append(nz[i] * 2)
            gain += nz[i] * 2
            i += 2
        else:
            out.append(nz[i])
            i += 1
    out += [0] * (4 - len(out))
    return out, gain


def _simulate(board: BoardState, direction: str) -> tuple[BoardState, int]:
    g = [row[:] for row in board.grid]
    if direction == "swipe_left":
        gains = 0
        for i in range(4):
            g[i], gain = _shift_left(g[i])
            gains += gain
        return BoardState(grid=g, score=board.score + gains), gains
    if direction == "swipe_right":
        gains = 0
        for i in range(4):
            row, gain = _shift_left(list(reversed(g[i])))
            g[i] = list(reversed(row))
            gains += gain
        return BoardState(grid=g, score=board.score + gains), gains
    if direction == "swipe_up":
        gains = 0
        for c in range(4):
            col = [g[r][c] for r in range(4)]
            new_col, gain = _shift_left(col)
            for r in range(4):
                g[r][c] = new_col[r]
            gains += gain
        return BoardState(grid=g, score=board.score + gains), gains
    # swipe_down
    gains = 0
    for c in range(4):
        col = [g[r][c] for r in range(4)]
        new_col, gain = _shift_left(list(reversed(col)))
        new_col = list(reversed(new_col))
        for r in range(4):
            g[r][c] = new_col[r]
        gains += gain
    return BoardState(grid=g, score=board.score + gains), gains


def take_the_best(board: BoardState) -> str:
    """Take-The-Best heuristic policy.

    Cues, in priority order:
      1. Maximizes score gain on this move
      2. Keeps the board's max tile in the top-left corner
      3. Maintains monotonicity along the top row
      4. Maximizes empty cells after the move
    """
    sims = [(d, *_simulate(board, d)) for d in _DIRS]
    best = max(
        sims,
        key=lambda t: (
            t[2],                                         # raw score gain
            t[1].grid[0][0] == board.max_tile,            # corner kept
            sum(1 for r in t[1].grid for v in r if v == 0),  # empties
        ),
    )
    return best[0]
```

- [ ] **Step 3: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(decision): Take-The-Best heuristic fallback"
```

---

## Task 36: Reflection (post-game)

**Files:**
- Create: `nova-agent/src/nova_agent/reflection/__init__.py`
- Create: `nova-agent/src/nova_agent/reflection/postmortem.py`
- Create: `nova-agent/src/nova_agent/memory/semantic.py`
- Create: `nova-agent/tests/test_reflection_postmortem.py`

- [ ] **Step 1: Failing test**

```python
# nova-agent/tests/test_reflection_postmortem.py
from unittest.mock import MagicMock
from nova_agent.reflection.postmortem import run_reflection


def test_reflection_returns_lessons():
    fake_llm = MagicMock()
    fake_llm.complete.return_value = (
        '{"summary":"died on tight board","lessons":["protect the corner","merge mid-tier early"],"notable_episodes":["ep_1"]}',
        MagicMock(input_tokens=200, output_tokens=80, cost_usd=0.05),
    )
    out = run_reflection(llm=fake_llm, last_30_moves_summary="...", prior_lessons=[])
    assert "lessons" in out
    assert len(out["lessons"]) == 2
```

- [ ] **Step 2: Implement semantic store**

```python
# nova-agent/src/nova_agent/memory/semantic.py
import sqlite3
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS semantic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    rule TEXT NOT NULL,
    citations TEXT NOT NULL DEFAULT '[]',
    confidence INTEGER NOT NULL DEFAULT 5
);
"""


class SemanticStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def add_rule(self, rule: str, citations: list[str], confidence: int = 5) -> int:
        import json
        cur = self._conn.execute(
            "INSERT INTO semantic(created_at, rule, citations, confidence) VALUES (?,?,?,?)",
            (datetime.now().isoformat(), rule, json.dumps(citations), confidence),
        )
        self._conn.commit()
        return cur.lastrowid

    def all_rules(self) -> list[dict]:
        rows = self._conn.execute("SELECT id, rule, citations, confidence FROM semantic ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 3: Implement reflection**

```python
# nova-agent/src/nova_agent/reflection/postmortem.py
from typing import Any
from pydantic import BaseModel

from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json


class _ReflectionOut(BaseModel):
    summary: str
    lessons: list[str]
    notable_episodes: list[str]


_SYSTEM = """\
You are reflecting on a completed 2048 game. Be specific. Output strict JSON:
{
  "summary": "1 sentence on what happened",
  "lessons": ["concrete rule 1", "concrete rule 2", ...] (3 to 5),
  "notable_episodes": ["ep_id1", "ep_id2"] (2 to 4 memory ids worth keeping)
}
"""


def run_reflection(*, llm: LLM, last_30_moves_summary: str, prior_lessons: list[str]) -> dict[str, Any]:
    prior = "\n".join(f"- {l}" for l in prior_lessons[-3:]) or "(none)"
    user = (
        f"Recent moves summary:\n{last_30_moves_summary}\n\n"
        f"Prior lessons (top-3):\n{prior}\n\n"
        "What worked, what failed, what should I do differently next game?"
    )
    text, _ = llm.complete(system=_SYSTEM, messages=[{"role": "user", "content": user}], max_tokens=600, temperature=0.4)
    parsed = parse_json(text, _ReflectionOut)
    return parsed.model_dump()
```

- [ ] **Step 4: Wire into main.py**

When game-over is detected (an empty-cells == 0 board where no swipe changes anything), run reflection (via a dedicated LLM built from the factory using `s.reflection_model` — Claude Sonnet 4.6 by default), write semantic rules, write trauma tags, restart the game, continue.

```python
# in main.py, alongside the other LLM constructions:
reflection_llm = build_llm(
    model=s.reflection_model,
    google_api_key=s.google_api_key,
    anthropic_api_key=s.anthropic_api_key,
    daily_cap_usd=s.daily_budget_usd,
)
# on game over:
result = run_reflection(llm=reflection_llm, last_30_moves_summary=summary, prior_lessons=prior)
```

- [ ] **Step 5: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(reflection): post-game reflection writes semantic rules"
```

---

## Task 37: ModeBadge component

**Files:**
- Create: `nova-viewer/app/components/ModeBadge.tsx`

- [ ] **Step 1: Implement**

```tsx
// nova-viewer/app/components/ModeBadge.tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";

export function ModeBadge({ mode }: { mode: "react" | "tot" }) {
  const label = mode === "tot" ? "🔴 DELIBERATING" : "🟢 INTUITION";
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={mode}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 10 }}
        transition={{ duration: 0.25 }}
        className={`inline-block px-3 py-1 rounded-full text-xs font-mono ${
          mode === "tot" ? "bg-red-950/60 text-red-200" : "bg-emerald-950/60 text-emerald-200"
        }`}
      >
        {label}
      </motion.div>
    </AnimatePresence>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): ModeBadge component"
```

---

## Task 38: TraumaIndicator component

**Files:**
- Create: `nova-viewer/app/components/TraumaIndicator.tsx`

- [ ] **Step 1: Implement**

```tsx
// nova-viewer/app/components/TraumaIndicator.tsx
"use client";
import { motion } from "framer-motion";

export function TraumaIndicator({ active }: { active: boolean }) {
  return (
    <motion.div
      className="pointer-events-none fixed inset-0 ring-inset rounded-none"
      style={{ boxShadow: "inset 0 0 60px rgba(220,38,38,0.5)" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: active ? 0.6 : 0 }}
      transition={{ duration: 1.2, repeat: active ? Infinity : 0, repeatType: "reverse" }}
    />
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): TraumaIndicator pulsing red glow"
```

---

## Task 39: Wire mode + trauma events through pipeline

**Files:**
- Modify: `nova-agent/src/nova_agent/main.py`
- Modify: `nova-viewer/app/page.tsx`
- Modify: `nova-viewer/lib/types.ts`

- [ ] **Step 1: Publish `mode` and `trauma_active` events from agent**

```python
await bus.publish("mode", {"mode": "tot" if mode == "tot" else "react"})
await bus.publish("trauma_active", {"active": any("trauma" in m.record.tags for m in retrieved)})
```

- [ ] **Step 2: Subscribe in viewer; render ModeBadge and TraumaIndicator**

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/ nova-agent/
git commit -m "feat: mode + trauma events wired end-to-end"
```

---

## Task 40: Integration test — losing → trauma → next-game retrieval

**Files:**
- Create: `nova-agent/tests/test_e2e_trauma.py`

- [ ] **Step 1: Write the test**

Build a synthetic loss scenario:
1. Run 5 moves with a stub LLM that always picks `swipe_down`
2. Trigger game-over
3. Run trauma tagging
4. Start a "second game"
5. Confirm a board similar to the one preceding the loss surfaces the trauma memory in retrieval

(Use a fake LLM and a fake ADB to make the test fully deterministic; no emulator needed.)

- [ ] **Step 2: Pass + commit + tag end-of-week**

```bash
uv run pytest -v
git add nova-agent/
git commit -m "test(e2e): trauma write + retrieval across games"
git tag week-4-complete
git push origin main --tags
```

**End of Week 4.** All cognitive modules wired. Trauma + ToT + reflection round out the architecture.

---

# WEEK 5 — Brain Panel Polish

**Goal:** The brain panel is the demo. Make it beautiful. Use Claude Design for static states (days 1–3); hand-code Framer Motion polish (days 4–7).

**Claude Design windows:** Days 1–3 (Task 41), Days 4–7 (Task 49 — variant iteration).

---

## Task 41: Claude Design — static states (days 1–3)

**Files:**
- Add: `docs/design/v1/states/*.png` (mockups)
- Add: `docs/design/v1/notes.md`

- [ ] **Step 1: Open Claude Design** (Pro/Max account required)

Provide:
- Aesthetic principles table from spec §5.5
- Element list from spec §5
- The chosen direction from Week 1 days 2–3 (`docs/design/v1/chosen/`)
- A real screenshot of the running brain panel (capture it from `pnpm dev`)

- [ ] **Step 2: Generate mockups for each affect state**

For each of:
- Calm Nova
- Anxious Nova (high anxiety + active trauma indicator)
- Frustrated Nova
- Dopamine-spike moment
- Trauma-glow active
- ToT mode (DELIBERATING badge)
- Game-over state

Save each mockup to `docs/design/v1/states/<name>.png`.

- [ ] **Step 3: Export each as React + Tailwind code where possible**

Save exports to `docs/design/v1/exports/<name>/` for reference.

- [ ] **Step 4: Commit**

```bash
git add docs/design/v1/
git commit -m "design: Claude Design static-state mockups for v1 brain panel"
```

---

## Task 42: Apply Claude Design output to components

**Files:**
- Modify: `nova-viewer/app/components/*.tsx`
- Modify: `nova-viewer/app/globals.css`
- Modify: `nova-viewer/tailwind.config.ts`

- [ ] **Step 1: Lock the design tokens (colors, fonts, spacing) in `tailwind.config.ts`** based on the chosen direction

- [ ] **Step 2: Apply tokens to existing components** (MoodGauge, DopamineBar, AffectLabel, MemoryCard, etc.)

- [ ] **Step 3: Add the typography stack** (Fraunces + Inter via `next/font`)

- [ ] **Step 4: Verify visual parity** with the Week 5 mockups by side-by-side review

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/
git commit -m "design(viewer): apply Claude-Design tokens + typography"
```

---

## Task 43: Polish — MoodGauge tweens

**Files:**
- Modify: `nova-viewer/app/components/MoodGauge.tsx`

- [ ] **Step 1: Add a smooth color transition path through the disk** (interpolate hue via `framer-motion`'s `useMotionValue` + `useTransform`)

- [ ] **Step 2: Visually confirm: drag the (valence, arousal) values manually in dev tools and watch the dot flow**

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "polish(viewer): smooth MoodGauge tweens"
```

---

## Task 44: Polish — DopamineBar pulse

**Files:**
- Modify: `nova-viewer/app/components/DopamineBar.tsx`

- [ ] **Step 1: When `level` jumps by > 0.2, trigger a brief glow animation (via `motion.div` with a key on a "pulse counter")

- [ ] **Step 2: Add a faint "ripple" via a second motion element

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "polish(viewer): DopamineBar pulse + ripple"
```

---

## Task 45: Polish — MemoryFeed slide-in

**Files:**
- Modify: `nova-viewer/app/components/MemoryFeed.tsx`
- Modify: `nova-viewer/app/components/MemoryCard.tsx`

- [ ] **Step 1: Wrap each MemoryCard in `<motion.div>`** with `initial={{ opacity: 0, x: -20 }}` and an `exit` for memories that drop out.

- [ ] **Step 2: Add a subtle pulse for trauma-tagged cards**

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "polish(viewer): MemoryFeed slide-in + trauma card pulse"
```

---

## Task 46: Polish — TraumaIndicator + ModeBadge

**Files:**
- Modify: `nova-viewer/app/components/TraumaIndicator.tsx`
- Modify: `nova-viewer/app/components/ModeBadge.tsx`

- [ ] **Step 1: TraumaIndicator** — slow inhalation pulse (~2s cycle), only visible when `active=true`; fade-out 1.5s when `active` flips to false.

- [ ] **Step 2: ModeBadge** — when mode flips, snappy slide + accent flash on the new badge.

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "polish(viewer): TraumaIndicator + ModeBadge transitions"
```

---

## Task 47: ReasoningText typewriter + ActionArrow

**Files:**
- Create: `nova-viewer/app/components/ReasoningText.tsx`
- Create: `nova-viewer/app/components/ActionArrow.tsx`

- [ ] **Step 1: ReasoningText** — accept the `reasoning` string; render with a typewriter effect (one char per ~20ms).

```tsx
// nova-viewer/app/components/ReasoningText.tsx
"use client";
import { useEffect, useState } from "react";
export function ReasoningText({ text }: { text: string }) {
  const [i, setI] = useState(0);
  useEffect(() => { setI(0); }, [text]);
  useEffect(() => {
    if (i >= text.length) return;
    const t = setTimeout(() => setI((x) => x + 1), 18);
    return () => clearTimeout(t);
  }, [i, text]);
  return <p className="font-serif text-zinc-200 leading-relaxed">{text.slice(0, i)}</p>;
}
```

- [ ] **Step 2: ActionArrow** — directional arrow with a brief slide-in animation.

```tsx
// nova-viewer/app/components/ActionArrow.tsx
"use client";
import { motion } from "framer-motion";
const ARROW = { swipe_up: "↑", swipe_down: "↓", swipe_left: "←", swipe_right: "→" } as const;

export function ActionArrow({ action }: { action: keyof typeof ARROW }) {
  return (
    <motion.div
      key={action + Date.now()}
      initial={{ scale: 0.6, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 1.4, opacity: 0 }}
      transition={{ type: "spring", stiffness: 240 }}
      className="text-7xl text-cyan-300 text-center"
    >
      {ARROW[action]}
    </motion.div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): ReasoningText typewriter + ActionArrow component"
```

---

## Task 48: Final polish pass — color, typography, spacing

**Files:**
- Modify: any/all `nova-viewer/app/components/*.tsx`
- Modify: `nova-viewer/app/globals.css`

- [ ] **Step 1: 30-min spacing audit** — open the brain panel, screenshot it, compare to mockups, fix every visual mismatch.

- [ ] **Step 2: 30-min typography audit** — confirm Fraunces is used for display, Inter for body; line-heights are generous; nothing feels cramped.

- [ ] **Step 3: 30-min color audit** — verify accents land consistently (cyan = reward, red = trauma, neutral grays for chrome).

- [ ] **Step 4: Lighthouse run** — at minimum hit 90+ on Performance/Accessibility for a single-page demo.

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/
git commit -m "polish(viewer): final color + typography + spacing audit"
```

---

## Task 49: Claude Design — variant iteration (days 4–7)

**Files:**
- Update: `docs/design/v1/states/`

- [ ] **Step 1: Generate alt component variants** in Claude Design — alt mood-gauge styles, alt memory-card layouts, alt dopamine-bar shapes.

- [ ] **Step 2: A/B subjectively** — record yourself watching the panel for 60s with each variant; pick the winner.

- [ ] **Step 3: Pull winners back into components**, commit small focused changes.

```bash
git add nova-viewer/ docs/design/v1/
git commit -m "polish(viewer): apply Claude Design variant iterations"
```

---

## Task 50: End-of-Week 5 commit

```bash
git tag week-5-complete
git push origin main --tags
```

**End of Week 5.** Brain panel is shippable.

---

# WEEK 6 — Demo + Release

**Goal:** Record a 60–90s demo, write the LinkedIn post, do the final security review, tag v1.0.0.

**Security review:** End of Week 6 (Task 55).

---

## Task 51: End-to-end smoke

**Files:** none

- [ ] **Step 1: Boot emulator + 2048 + scrcpy + agent + viewer**
- [ ] **Step 2: Watch it run for 30 minutes** — log any issues to a `WEEK6_BUGS.md` scratchfile.
- [ ] **Step 3: Fix every blocker before recording.**

---

## Task 52: Demo scenario script

**Files:**
- Create: `docs/design/v1/demo-script.md`

- [ ] **Step 1: Define the 3-act demo:**

  - Act 1 (0–20s): Calm Nova plays a clean opening. Brain panel shows confident reasoning, smooth mood.
  - Act 2 (20–60s): Board tightens. Anxiety rises. Trauma memory surfaces. ToT engages. Nova picks the safe move. Dopamine spikes.
  - Act 3 (60–90s): One more dramatic moment — a near-loss saved, or a reflection panel showing.

- [ ] **Step 2: Pre-record run** — play several full games, find the best 60–90s window.

- [ ] **Step 3: Commit the script**

```bash
git add docs/design/v1/demo-script.md
git commit -m "docs(demo): scenario script for v1 LinkedIn clip"
```

---

## Task 53: OBS scene + record

**Files:** none

- [ ] **Step 1: Configure OBS** — single scene with two captures: Chromium (the brain panel) + scrcpy window. Layout side-by-side. Output 1080p, 30fps, MP4.
- [ ] **Step 2: Record several full sessions** until you capture an Act 1 → Act 2 → Act 3 sequence cleanly.
- [ ] **Step 3: Save raw footage to `~/Desktop/nova-demo-raw/`** (NOT in the repo — large files).

---

## Task 54: Edit + LinkedIn post draft

**Files:**
- Create: `docs/design/v1/linkedin-post.md`

- [ ] **Step 1: Trim raw footage** to 60–90s in any video editor (iMovie / DaVinci / CapCut).
- [ ] **Step 2: Add minimal on-screen text labels** (e.g., "Trauma memory triggered", "Dopamine spike +0.4") at the key moments.
- [ ] **Step 3: Export to MP4** under 200 MB.
- [ ] **Step 4: Draft the LinkedIn post**

```markdown
# LinkedIn post — v1 launch

> *I built a 2048 AI that has feelings.*
>
> Most game AIs are pure decision machines. This one has mood, episodic memory, dopamine, and trauma. After it loses on a tight board, it remembers. Next time it sees a similar position, it tenses up — anxiety rises, play turns conservative.
>
> Stylized cognitive architecture inspired by Kahneman, Damasio, Schultz, Park, Sumers, and Croissant — not literal neuroscience. Built on Claude (vision) + LanceDB + Next.js. Watch it think, feel, and remember in real time. ↓
>
> [video]
>
> Repo + design spec + bibliography: github.com/IdoHoresh/project-nova
> #ai #gamedev #cognitive-architecture #portfolio
```

- [ ] **Step 5: Commit**

```bash
git add docs/design/v1/linkedin-post.md
git commit -m "docs(demo): LinkedIn post draft"
```

---

## Task 55: Final security review

**Files:**
- Create: `docs/specs/security-reviews/2026-week-06.md`

- [ ] **Step 1: Run the full Week 6 review checklist from `SECURITY.md`**:
  1. `gitleaks detect --redact` (full history)
  2. `git log --all --full-history -p -- '*.env' '*secrets*' '*credentials*'`
  3. Check Dependabot alerts at https://github.com/IdoHoresh/project-nova/security/dependabot
  4. Verify `.env.example` has no real values
  5. Verify GitHub security settings still enabled

- [ ] **Step 2: Write the review**

```markdown
# Week 6 (Final) Security Review — 2026-MM-DD

## Checks performed
- [x] gitleaks detect --redact — clean
- [x] git log scan for env/secret/credential — no findings
- [x] Dependabot alerts — none
- [x] .env.example clean
- [x] GitHub settings: scanning + push protection + dependabot — enabled
- [x] Pre-commit hook installed locally

## Findings
None.

## Conclusion
v1.0.0 is safe to publish. No outstanding security items.

## Reviewer
Self-review (Ido).
```

- [ ] **Step 3: Commit**

```bash
git add docs/specs/security-reviews/
git commit -m "chore(security): Week 6 final review — clean, ready to ship"
```

---

## Task 56: Tag v1.0.0 + push

**Files:** none

- [ ] **Step 1: Tag**

```bash
git tag -a v1.0.0 -m "v1.0.0 — Project Nova first public release"
git push origin main --tags
```

- [ ] **Step 2: Create GitHub release**

```bash
gh release create v1.0.0 \
    --title "Project Nova v1.0.0" \
    --notes "Brain-inspired VLM agent that plays 2048 with mood, memory, dopamine, and trauma. See docs/specs/2026-04-30-project-nova-design.md for the full architecture."
```

- [ ] **Step 3: Post the LinkedIn post** with the demo video.

- [ ] **Step 4: Celebrate.**

---

# Self-review notes

## Spec coverage

- [x] §2 v1 scope — all 8 modules: Tasks 5, 12, 12, 20, 22, 9, 4, 41–48 cover them
- [x] §2.5 Portability — game-agnostic boundaries are honored by perception/action layer separation; tasks 5, 10, 4 keep the boundary clean
- [x] §3.1–3.12 architecture modules — tasks 5/10 (perception), 12 (working memory implicit in prompt), 12–16 (long-term memory), 31–32 (trauma), 22–23 (RPE), 33 + 9 (decision), 4 (action), 35 (heuristic fallback), 36 (reflection), 7 + 17 + 24–29 + 37–38 (brain panel)
- [x] §4 worked example — implicit in the e2e tests; the live demo records it
- [x] §5 brain-panel UI — tasks 24–29 and 37–48
- [x] §5.5 design language + Claude Design — tasks 5 (week 1 dir window), 41 + 49 (week 5 windows)
- [x] §6 tech stack + repo layout — tasks 1, 7, 8 establish; layout matches the spec
- [x] §6.5 security — tasks 2 (pre-commit hook), 11 (week 1 review), 30 (week 3 review), 55 (week 6 review); .env.example + SECURITY.md already in place
- [x] §7 hardest problems — addressed via task ordering (ADB calibration in Task 4, structured output in Task 3, importance tuning in Task 14, brain panel polish week dedicated, OCR robustness via Task 5/10 + VLM fallback)
- [x] §8 validation plan — Task 51 (smoke), Task 52 (curated demo), Task 40 (e2e trauma test); the 7 acceptance criteria all map to tasks
- [x] §9 future directions — explicitly out of v1; the architecture is ready

## Placeholder scan

Searched the plan for "TBD", "TODO", "implement later". Two locations had partial code that the engineer fills in based on the same-task pattern (e.g., Task 16's wiring into main.py, Task 27's wiring into page.tsx). These are integration tasks where the surrounding context (already-written modules) makes the wiring obvious; they are not placeholder hand-waves. Acceptable.

## Type consistency

- `BoardState` is defined in `perception/types.py` and reused everywhere (Tasks 5, 12, 22, 31, 33, 35, 36).
- `MemoryRecord` defined in Task 12, used by Tasks 13–16, 31–32.
- `AffectVector` defined in Task 20, used by Tasks 21–23, 34.
- `Decision` defined in Task 9, reused by ToT in Task 33.
- LLM client method signature `complete(*, system, messages, max_tokens, temperature)` is consistent across Tasks 3, 9, 33, 36.

No drift detected.

## Gaps

None blocking. Two minor items the engineer should expect to iterate on during the build:
1. ADB swipe coordinates are calibrated for a Pixel 6 emulator; recalibrate if you switch device.
2. OCR `_BOARD_TOP/_LEFT/_CELL_SIZE` constants are likely wrong on first capture; visually measure one fixture and update.

These are documented inline.

---

*Plan complete. Total: 57 tasks across 6 weeks + 1 pre-flight + 3 security reviews + 3 Claude Design windows + 1 final release.*
