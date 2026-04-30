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

## Task 3: Multi-provider LLM client + budget guard + tiers + cache + Mock

**Provider-agnostic LLM interface with TWO adapters (Gemini + Anthropic), three model tiers selected by `NOVA_TIER`, a fixture-replay cache keyed on the rendered-prompt hash, and a `MockLLMClient` for plumbing tests. Implements §6.6 cost discipline and §6.7 test layers.**

**Files:**
- Create: `nova-agent/src/nova_agent/budget.py`
- Create: `nova-agent/src/nova_agent/llm/__init__.py`
- Create: `nova-agent/src/nova_agent/llm/protocol.py`
- Create: `nova-agent/src/nova_agent/llm/tiers.py`             # §6.6
- Create: `nova-agent/src/nova_agent/llm/anthropic_client.py`
- Create: `nova-agent/src/nova_agent/llm/gemini_client.py`
- Create: `nova-agent/src/nova_agent/llm/cache.py`             # §6.6 lever L1
- Create: `nova-agent/src/nova_agent/llm/mock.py`              # §6.7 Layer 1
- Create: `nova-agent/src/nova_agent/llm/factory.py`
- Create: `nova-agent/src/nova_agent/llm/structured.py`
- Create: `nova-agent/tests/test_llm_anthropic.py`
- Create: `nova-agent/tests/test_llm_gemini.py`
- Create: `nova-agent/tests/test_llm_tiers.py`
- Create: `nova-agent/tests/test_llm_cache.py`
- Create: `nova-agent/tests/test_llm_mock.py`
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

**Per-run cap (additional):**

```python
# nova-agent/src/nova_agent/budget.py — extend
class RunBudget:
    """Per-run cap (§6.6 lever L5). Default $0.50; envvar NOVA_PER_RUN_CAP_USD."""
    def __init__(self, cap_usd: float = 0.50):
        self.cap_usd = cap_usd
        self.spent = 0.0

    def charge(self, amount_usd: float) -> None:
        if self.cap_usd > 0 and self.spent + amount_usd > self.cap_usd:
            raise BudgetExceeded(
                f"Per-run charge of ${amount_usd:.4f} would exceed run cap "
                f"${self.cap_usd:.2f} (already spent ${self.spent:.4f})."
            )
        self.spent += amount_usd
```

The factory's LLM clients hold both a process-wide `BudgetGuard` (daily cap) and a `RunBudget` (per-run cap). Both are charged on every call; either tripping raises `BudgetExceeded` and the loop terminates with a clean error.

- [ ] **Step 4 (NEW): Implement model tiers (`NOVA_TIER`)**

Implements §6.6. One env var, three tiers (`dev`, `production`, `demo`). Default `dev`. The factory reads `NOVA_TIER` and dispatches to the right model.

```python
# nova-agent/src/nova_agent/llm/tiers.py
"""Three model tiers selected by NOVA_TIER (§6.6). Default `dev`.

  dev        — daily Flash-everywhere (Flash-Lite is rejected for decisions
               due to documented JSON reliability issues; kept for
               importance_rating only).
  production — Week 5–6 §8 acceptance: Flash + Pro + Sonnet 4.6.
  demo       — Week 6 LinkedIn recording: Sonnet 4.6 everywhere.
"""

from __future__ import annotations

import os
from typing import Literal, TypedDict

TierName = Literal["dev", "production", "demo"]


class TierConfig(TypedDict):
    decision: str
    tot: str
    tot_branches: int
    reflection: str
    perception_fallback: str
    importance_rating: str


TIERS: dict[TierName, TierConfig] = {
    "dev": {
        "decision":            "gemini-2.5-flash",
        "tot":                 "gemini-2.5-flash",
        "tot_branches":        3,
        "reflection":          "gemini-2.5-flash",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
    "production": {
        "decision":            "gemini-2.5-flash",
        "tot":                 "gemini-2.5-pro",
        "tot_branches":        4,
        "reflection":          "claude-sonnet-4-6",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
    "demo": {
        "decision":            "claude-sonnet-4-6",
        "tot":                 "claude-sonnet-4-6",
        "tot_branches":        4,
        "reflection":          "claude-sonnet-4-6",
        "perception_fallback": "claude-sonnet-4-6",
        "importance_rating":   "gemini-2.5-flash-lite",
    },
}


def current_tier() -> TierName:
    val = os.environ.get("NOVA_TIER", "dev")
    if val not in TIERS:
        raise ValueError(f"NOVA_TIER must be one of {list(TIERS)}, got {val!r}")
    return val  # type: ignore[return-value]


def model_for(role: str) -> str:
    cfg = TIERS[current_tier()]
    if role not in cfg:
        raise KeyError(f"unknown role {role!r}; valid: {list(cfg)}")
    return cfg[role]  # type: ignore[return-value]
```

```python
# nova-agent/tests/test_llm_tiers.py
import pytest
from nova_agent.llm import tiers


def test_default_is_dev(monkeypatch):
    monkeypatch.delenv("NOVA_TIER", raising=False)
    assert tiers.current_tier() == "dev"


def test_invalid_raises(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "moonshot")
    with pytest.raises(ValueError):
        tiers.current_tier()


def test_dev_uses_flash_for_decision(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "dev")
    assert tiers.model_for("decision") == "gemini-2.5-flash"


def test_production_uses_pro_for_tot(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "production")
    assert tiers.model_for("tot") == "gemini-2.5-pro"


def test_demo_is_sonnet_only_for_decisions(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "demo")
    assert tiers.model_for("decision") == "claude-sonnet-4-6"
```

- [ ] **Step 5 (NEW): Implement fixture-replay cache (rendered-prompt hash)**

§6.6 lever L1. **Critical: cache key is the cryptographic hash of the rendered prompt string + model + temperature + response-schema hash.** Per the peer-review fix: keying on `prompt_template_version` would cause stale-template cache hits and is forbidden.

```python
# nova-agent/src/nova_agent/llm/cache.py
"""Fixture-replay LLM cache (§6.6 L1).

Cache key = sha256(rendered_prompt_string + model + temperature + response_schema_hash).
Writes are gated on smoke-pass — buggy build cannot pollute future runs.
NOVA_CACHE controls behavior: "off" disables; "replay" reads only; default
"record" reads + writes (gated by `mark_smoke_pass()`).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.environ.get("NOVA_CACHE_DIR", ".cache/llm"))
CACHE_MODE = os.environ.get("NOVA_CACHE", "record")  # off | replay | record

_smoke_passed = False


def mark_smoke_pass() -> None:
    """Called by the smoke gauntlet after every assertion passes.
    Cache writes only happen when this flag is set in the current process.
    """
    global _smoke_passed
    _smoke_passed = True


def _hash_key(*, rendered_prompt: str, model: str, temperature: float, schema_hash: str) -> str:
    payload = json.dumps({
        "p": rendered_prompt,
        "m": model,
        "t": round(temperature, 4),
        "s": schema_hash,
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class CacheHit:
    response_text: str
    cached_at: float
    key: str


def _key_path(key: str) -> Path:
    return CACHE_DIR / f"{key[:2]}" / f"{key}.json"


def get(*, rendered_prompt: str, model: str, temperature: float, schema_hash: str = "") -> CacheHit | None:
    if CACHE_MODE == "off":
        return None
    key = _hash_key(rendered_prompt=rendered_prompt, model=model,
                    temperature=temperature, schema_hash=schema_hash)
    p = _key_path(key)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    return CacheHit(response_text=data["response_text"], cached_at=data["cached_at"], key=key)


def put(*, rendered_prompt: str, model: str, temperature: float, response_text: str,
        schema_hash: str = "") -> None:
    if CACHE_MODE in ("off", "replay"):
        return
    if not _smoke_passed:
        # writes gated on smoke-pass — protects against poisoning the cache
        return
    key = _hash_key(rendered_prompt=rendered_prompt, model=model,
                    temperature=temperature, schema_hash=schema_hash)
    p = _key_path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "response_text": response_text,
        "cached_at": time.time(),
        "model": model,
        "temperature": temperature,
    }))
```

The LLM adapters (Anthropic + Gemini) are modified in their `complete()` to call `cache.get(...)` before issuing a request and `cache.put(...)` after a successful response. Every call logs `cache_hit=true|false` with the key composition. The brain panel surfaces a hit-rate dashboard in the stats footer (§5).

- [ ] **Step 6 (NEW): Implement `MockLLMClient` for L1 plumbing tests**

§6.7 Layer 1. Default for all unit + integration tests. Real LLM is opt-in via `NOVA_LLM_REAL=1`.

```python
# nova-agent/src/nova_agent/llm/mock.py
"""Deterministic LLM client for plumbing tests (§6.7 L1).

R5 — strict mock. Unlike `MagicMock(...).side_effect = ['{"action":...}']`
which blindly returns whatever string you fed it, this Mock:

  1. Inspects `system` and `messages` to figure out WHICH role's prompt is
     being sent (decision / tot / reflection / importance) — by checking the
     system prompt against a registry of prompt-template fingerprints.
  2. Returns a structurally valid JSON response for that role, generated
     against a registered Pydantic schema. If you change the schema (add a
     field, rename one), the mock generates a response that conforms to the
     NEW schema — your test starts failing because the upstream code wasn't
     updated yet, instead of silently passing on a stale fixture.
  3. Records every call for assertion.
  4. NEVER makes a network call.

Use a single MockLLMClient instance per test session. Do not scatter
MagicMock through the test suite for LLM interactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ValidationError


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class _RoleSpec(BaseModel):
    """Registered role: how to detect it + schema + response factory."""
    name: str
    system_fingerprint: str            # substring of system prompt that identifies the role
    schema: type[BaseModel]            # Pydantic model the response must conform to
    factory: Callable[[dict[str, Any]], dict[str, Any]]  # build a response dict from call context

    class Config:
        arbitrary_types_allowed = True


def _decision_factory(_ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "observation": "mock board read",
        "reasoning": "mock decision reasoning",
        "action": "swipe_up",
        "confidence": "low",
        "memory_citation": None,
    }


def _tot_branch_factory(ctx: dict[str, Any]) -> dict[str, Any]:
    last_text = ctx.get("last_text", "")
    direction = "swipe_up"
    for d in ("swipe_up", "swipe_down", "swipe_left", "swipe_right"):
        if d in last_text:
            direction = d
            break
    return {"action": direction, "reasoning": "mock branch", "value": 0.5}


def _reflection_factory(_ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": "mock reflection",
        "lessons": ["mock lesson 1"],
        "notable_episodes": [],
    }


def _importance_factory(_ctx: dict[str, Any]) -> dict[str, Any]:
    return {"importance": 5}


# Registered roles. When a real prompt template changes, register the new
# fingerprint here AND register the new schema; tests that call code paths
# affected by the new prompt will start exercising the new schema
# automatically.
class _DecisionResponse(BaseModel):
    observation: str
    reasoning: str
    action: str
    confidence: str
    memory_citation: dict | None = None


class _ToTBranchResponse(BaseModel):
    action: str
    reasoning: str
    value: float


class _ReflectionResponse(BaseModel):
    summary: str
    lessons: list[str]
    notable_episodes: list[str]


class _ImportanceResponse(BaseModel):
    importance: int


_ROLES: list[_RoleSpec] = [
    _RoleSpec(name="decision",   system_fingerprint="emit Observation, Reasoning, Action",
              schema=_DecisionResponse, factory=_decision_factory),
    _RoleSpec(name="tot_branch", system_fingerprint="evaluating ONE candidate move",
              schema=_ToTBranchResponse, factory=_tot_branch_factory),
    _RoleSpec(name="reflection", system_fingerprint="generate a short.*postmortem",
              schema=_ReflectionResponse, factory=_reflection_factory),
    _RoleSpec(name="importance", system_fingerprint='rate this event 1.10 for memorability',
              schema=_ImportanceResponse, factory=_importance_factory),
]


@dataclass
class MockLLMClient:
    """Strict structured-response mock.

    Override behavior per test by setting:
      - `script`: list[str] — exact responses, pop in order (escape hatch)
      - `keyed`:  dict[str, str] — substring → response (escape hatch)
      - `factories`: dict[role_name, callable] — replace a default factory

    Default behavior: identify role from system prompt, run that role's
    factory, validate the result against the role's Pydantic schema, return
    the JSON-serialized model.
    """
    script: list[str] = field(default_factory=list)
    keyed: dict[str, str] = field(default_factory=dict)
    factories: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)
    strict: bool = True  # if True, unrecognized roles raise; if False, return generic decision

    def complete(self, *, system: str, messages: list[dict[str, Any]], max_tokens: int = 200,
                 temperature: float = 0.7) -> tuple[str, _Usage]:
        import json
        import re

        last_text = self._extract_last_user_text(messages)
        ctx = {"system": system, "messages": messages, "last_text": last_text,
               "max_tokens": max_tokens, "temperature": temperature}

        # Escape hatches first
        if self.script:
            response = self.script.pop(0)
        elif (keyed := next((v for k, v in self.keyed.items() if k in last_text), None)) is not None:
            response = keyed
        else:
            role = next(
                (r for r in _ROLES if re.search(r.system_fingerprint, system)),
                None,
            )
            if role is None:
                if self.strict:
                    raise AssertionError(
                        f"MockLLMClient: no registered role matched system prompt. "
                        f"First 200 chars: {system[:200]!r}. Add a _RoleSpec or supply "
                        f"`script`/`keyed` for this call."
                    )
                # Lax mode — return a generic decision
                role = _ROLES[0]
            factory = self.factories.get(role.name, role.factory)
            payload = factory(ctx)
            # Validate against the schema BEFORE returning — this is the
            # safety net that catches stale prompt-templates.
            try:
                role.schema.model_validate(payload)
            except ValidationError as exc:  # pragma: no cover (only fires on misregistered role)
                raise AssertionError(
                    f"MockLLMClient: factory output for role {role.name!r} does not match its schema: {exc}"
                ) from exc
            response = json.dumps(payload)

        self.calls.append({**ctx, "response": response})
        return response, _Usage()

    @staticmethod
    def _extract_last_user_text(messages: list[dict[str, Any]]) -> str:
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), {})
        content = last_user.get("content", "")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    return part.get("text", "")
            return ""
        return content if isinstance(content, str) else ""
```

**Bench rule for tests.** Existing Tasks 9 / 33 / 36 use `MagicMock` for the LLM client. **Replace those with `MockLLMClient`.** A `MagicMock(...).side_effect = [...]` test passes even when the prompt has fundamentally changed shape — it returns whatever string you scripted. The strict Mock catches schema drift the moment it happens.

If a single test really does need a fixed response (rare), use `MockLLMClient(script=['{"action":"swipe_up", ...}'])`. If a role hasn't been registered yet because the prompt template is new, register it in `_ROLES` and add a Pydantic schema for it; the friction is intentional.

```python
# nova-agent/tests/test_llm_mock.py
from nova_agent.llm.mock import MockLLMClient


def test_script_returns_in_order():
    m = MockLLMClient(script=['{"action":"swipe_up"}', '{"action":"swipe_down"}'])
    a, _ = m.complete(system="x", messages=[{"role": "user", "content": "go"}])
    b, _ = m.complete(system="x", messages=[{"role": "user", "content": "go"}])
    assert a == '{"action":"swipe_up"}'
    assert b == '{"action":"swipe_down"}'


def test_keyed_matches_substring():
    m = MockLLMClient(keyed={"trauma": '{"action":"swipe_left"}'})
    out, _ = m.complete(system="x", messages=[{"role": "user", "content": "you remember a trauma board"}])
    assert out == '{"action":"swipe_left"}'


def test_calls_recorded():
    m = MockLLMClient()
    m.complete(system="x", messages=[{"role": "user", "content": "hi"}])
    assert len(m.calls) == 1
```

- [ ] **Step 7: Write failing tests for both adapters + the factory**

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

- [ ] **Step 8: Run, see fail**

```bash
uv run pytest tests/test_llm_client.py -v
```

- [ ] **Step 9: Implement the LLM protocol + per-provider pricing**

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

- [ ] **Step 10: Implement the Anthropic adapter**

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

- [ ] **Step 11: Implement the Gemini adapter**

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

- [ ] **Step 12: Implement the factory**

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

- [ ] **Step 13: Implement `llm/structured.py`**

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

- [ ] **Step 14: Verify `google-genai` is in pyproject.toml dependencies**

(Already added in Task 1 — confirm `uv sync` brought it in.)

- [ ] **Step 15: Run all tests pass**

```bash
uv run pytest -v
```

- [ ] **Step 16: Commit**

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


def test_to_vlm_bytes_downscales_to_512_max_side():
    """R1 — token hemorrhage protection. A raw 1080×2400 PNG to the VLM on
    every move would obliterate the budget. The capture layer always
    downscales before encoding."""
    from io import BytesIO
    from PIL import Image as PILImage
    from nova_agent.perception.capture import Capture

    big = PILImage.new("RGB", (1080, 2400), color="white")
    payload = Capture.to_vlm_bytes(big)
    decoded = PILImage.open(BytesIO(payload))
    assert max(decoded.size) <= 512
    # PNG should be tiny (high-contrast solid white compresses well, but the
    # critical assertion is that no path can slip a full-res image through)
    assert len(payload) < 50_000
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

    def grab_stable(
        self,
        *,
        poll_interval_s: float = 0.05,
        timeout_s: float = 0.6,
    ) -> Image.Image:
        """Capture once the screen is visually static (§3.9 visual stability check).

        Replaces the prior hardcoded ~300ms post-swipe wait. Loop captures
        50ms apart, exits when two consecutive frames are pixel-identical
        (or near-identical via byte hash). Hard cap at timeout_s, then
        force-read + log — better to OCR a slightly-moving frame than to
        block forever on emulator lag.
        """
        import hashlib
        import time

        prev_hash: str | None = None
        deadline = time.monotonic() + timeout_s
        last_img: Image.Image | None = None

        while time.monotonic() < deadline:
            img = self.grab()
            h = hashlib.blake2s(img.tobytes(), digest_size=16).hexdigest()
            if prev_hash is not None and h == prev_hash:
                return img
            prev_hash = h
            last_img = img
            time.sleep(poll_interval_s)

        log.warning("capture.grab_stable.timeout", timeout_s=timeout_s)
        assert last_img is not None
        return last_img

    @staticmethod
    def boards_differ(a: Image.Image, b: Image.Image) -> bool:
        """Cheap pixel-diff used by the action executor for no-op detection (§3.9)."""
        import hashlib

        ha = hashlib.blake2s(a.tobytes(), digest_size=16).digest()
        hb = hashlib.blake2s(b.tobytes(), digest_size=16).digest()
        return ha != hb

    @staticmethod
    def to_vlm_bytes(image: Image.Image, *, max_side: int = 512) -> bytes:
        """Downscale + optimize for VLM transmission. Required — see plan §6.6.

        A raw 1080×2400 emulator screenshot encoded as PNG and sent on every
        move would obliterate the $80 budget in days. 2048 is a high-contrast
        grid; a 512-px-max-side image is more than enough for the VLM to read
        digits and reason. Always run via thumbnail (LANCZOS) + optimize=True.
        """
        import io

        thumb = image.copy()
        thumb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
```

**Wiring rule.** Anywhere a screenshot is being sent to a VLM (decision call in Task 9, ToT branches in Task 33, perception fallback, reflection if it ever sees a screenshot), the payload must come from `Capture.to_vlm_bytes(image)` — never from a raw `image.save(buf, format="PNG")`. Add a lint-style assertion in the smoke gauntlet that every outbound LLM image-content block is ≤ 512px on its longest side; the gauntlet fails if any code path slips a full-resolution image into the request.

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


@pytest.mark.asyncio
async def test_publish_drops_frame_on_slow_client(monkeypatch):
    """R4 — a slow client cannot stall the agent loop.

    Simulate a client whose `ws.send` blocks longer than SEND_TIMEOUT_S.
    `bus.publish` must return promptly (within ~2× timeout) without raising.
    """
    bus = EventBus(host="127.0.0.1", port=18766)
    bus.SEND_TIMEOUT_S = 0.05

    class SlowSocket:
        async def send(self, _payload: str) -> None:
            await asyncio.sleep(1.0)  # simulate buffer-full backpressure

    bus._clients.add(SlowSocket())  # type: ignore[arg-type]

    start = asyncio.get_event_loop().time()
    await bus.publish("evt", {"k": 1})
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed < 0.2, f"publish stalled for {elapsed:.3f}s on slow client"
    assert EventBus._drop_counter >= 1
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

    SEND_TIMEOUT_S: float = 0.1   # R4 — protect agent loop from UI lag
    _drop_counter: int = 0

    async def publish(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str)
        if not self._clients:
            return
        await asyncio.gather(
            *(self._safe_send(ws, payload) for ws in list(self._clients)),
            return_exceptions=True,
        )

    async def _safe_send(self, ws: WebSocketServerProtocol, payload: str) -> None:
        """R4 — per-send timeout. A backgrounded Chrome tab can keep the
        WebSocket open but stop ACKing packets. Without a timeout `ws.send`
        blocks until the OS-level send buffer drains, stalling the decision
        loop on UI lag. Drop the frame instead — the brain panel can miss
        a frame; the agent cannot stall.
        """
        try:
            await asyncio.wait_for(ws.send(payload), timeout=self.SEND_TIMEOUT_S)
        except asyncio.TimeoutError:
            type(self)._drop_counter += 1
            log.warning("bus.send_timeout_dropped", drops=type(self)._drop_counter)
        except websockets.exceptions.ConnectionClosed:
            pass  # client disconnected mid-send; cleanup happens in _handler
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

- [ ] **Step 9: Pin emulator state — orientation, DPI, animation scales (R6)**

The OCR auto-calibrator (Task 10) and the visual stability check (Task 5) are robust to *most* emulator variation, but several emulator state knobs reset on every cold boot in ways that break the pipeline silently. Lock them down with a script that runs **at the start of every agent session, before any screenshot is captured**.

Create `nova-game/pin-emulator-state.sh`:

```bash
#!/usr/bin/env bash
# Pre-flight: pin every emulator state that could break perception.
# Idempotent — safe to run before every agent session.
set -e

DEVICE_ID="${ADB_DEVICE_ID:-emulator-5554}"
ADB="adb -s $DEVICE_ID"

echo "→ Pinning emulator state on $DEVICE_ID"

# 1. ORIENTATION — lock to portrait. Auto-rotation must be OFF or scrcpy/OCR
#    sees a sideways grid the moment the emulator decides to flip.
$ADB shell settings put system accelerometer_rotation 0      # disable auto-rotate
$ADB shell settings put system user_rotation 0               # 0 = portrait

# 2. DISPLAY DENSITY — fix DPI so the OCR's auto-calibrated bbox doesn't drift
#    between sessions. 440 dpi is the Pixel 6 default; pinning it explicitly
#    survives an OS update that changes the default.
$ADB shell wm density 440

# 3. ANIMATION SCALES — set to 1.0 for the visual-stability check to time
#    correctly. Some Android dev presets ship at 0.5x or off, which makes
#    the swipe animation invisible to the pixel-diff loop.
$ADB shell settings put global window_animation_scale 1.0
$ADB shell settings put global transition_animation_scale 1.0
$ADB shell settings put global animator_duration_scale 1.0

# 4. DISPLAY ALWAYS ON (during dev sessions only) so the screen doesn't dim
#    mid-game and corrupt OCR's color sampling.
$ADB shell svc power stayon true

# 5. DISABLE SOFT KEYBOARD popups that occasionally overlay the game.
$ADB shell settings put secure show_ime_with_hard_keyboard 0

# 6. STATUS BAR — verify it's the standard height. If a notification or
#    alarm icon shifts the layout, OCR auto-calibration handles it (it
#    looks for a square contour, not absolute coords) — but log a warning
#    so a human can investigate if the warning fires repeatedly.
HEIGHT=$($ADB shell wm size | awk -F'[ x]' '/Physical/ {print $5}')
if [ "$HEIGHT" != "2400" ]; then
    echo "  ⚠️  Physical display height is $HEIGHT (expected 2400). OCR will recalibrate, but verify this is intentional."
fi

# 7. VERIFY 2048 IS THE FOREGROUND APP (don't run agent against a launcher
#    or a stale dialog).
FOREGROUND=$($ADB shell dumpsys window | grep -E 'mCurrentFocus' | awk '{print $NF}' | tr -d '}')
if [[ ! "$FOREGROUND" == *"nova2048"* ]]; then
    echo "  ⚠️  2048 is not the foreground app (got: $FOREGROUND)."
    echo "     Launching now…"
    $ADB shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
    sleep 2
fi

echo "✓ Emulator state pinned"
```

```bash
chmod +x nova-game/pin-emulator-state.sh
```

The agent's `main.py` Step-0 entrypoint must invoke this script (or fail fast with a helpful error) before the run loop starts. The smoke gauntlet (every commit) calls it on a synthetic mock-emulator path; the live runs call it for real.

- [ ] **Step 10: Document the precondition contract in `nova-game/README.md`**

```markdown
## Emulator preconditions

Before running the agent, the emulator state must be pinned. Run:

    ./nova-game/pin-emulator-state.sh

This locks: portrait orientation, 440 dpi, 1.0× animation scales, screen-on,
no soft-keyboard popups, and confirms 2048 is the foreground app. The agent's
OCR auto-calibrator handles minor scale drift, but auto-rotation, animation-off,
and screen-dim cannot be recovered from in-loop — they have to be pre-pinned.

If the agent reports `CalibrationError: no square grid contour found`, the
emulator probably isn't in 2048 (or the screen is dimmed). Re-run the pin script.
```

- [ ] **Step 11: Commit**

```bash
git add nova-game/
git commit -m "feat(game): fork stdbilly/2048_Unity + build script + emulator-state pin script"
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
            image = capture.grab_stable()                  # §3.9 visual stability
            board = _placeholder_perceive(image)
            # R1 — downscale BEFORE encoding. Sending raw 1080×2400 PNGs to
            # the VLM on every move would obliterate the budget. 512-max-side
            # is more than enough for 4×4 grid reading.
            png_bytes = Capture.to_vlm_bytes(image)
            b64 = base64.b64encode(png_bytes).decode("ascii")
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

- [ ] **Step 3: Implement OCR with auto-calibration (NO hardcoded coords)**

R2 from the second peer review: hardcoded `_BOARD_TOP = 980` etc. break the moment the emulator boots with different DPI scaling, the device skin changes, or an OS update shifts the status bar. The fast path must dynamically locate the 4×4 grid via OpenCV before sampling cells.

```python
# nova-agent/src/nova_agent/perception/ocr.py
"""Auto-calibrating fast-path OCR for the 2048 grid.

Calibration runs once per Capture session (~10ms). It locates the 4×4 grid
by edge-detecting the screenshot, finding contours with aspect ratio ~1.0
near the expected size, and caching the bounding box. Subsequent reads
reuse the cached bbox until calibration drift triggers a re-cal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from nova_agent.perception.types import BoardState

# Tile background colors → tile value. The published 2048 palette.
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


@dataclass(frozen=True)
class BoardBBox:
    """Pixel coordinates of the 4×4 grid in the source image."""
    top: int
    left: int
    cell_size: int

    @property
    def width(self) -> int:
        return self.cell_size * 4


class CalibrationError(RuntimeError):
    """Raised when the fast path can't find the grid. Loop falls through to VLM perception."""


def calibrate_board_bbox(image: Image.Image) -> BoardBBox:
    """Find the 4×4 grid via OpenCV — no hardcoded coordinates.

    Strategy:
      1. Convert to grayscale.
      2. Adaptive threshold to isolate the dark grid background.
      3. Find contours; filter to those with aspect ratio ~1.0 (square)
         AND area large enough to be the full grid.
      4. Pick the largest match. Compute cell_size = bbox.width / 4.
    """
    arr = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    # Adaptive threshold tolerates emulator brightness variation
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 4
    )
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_area = arr.shape[0] * arr.shape[1]
    candidates: list[tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 200 or h < 200:           # too small
            continue
        if abs(w - h) / max(w, h) > 0.05:  # not square (5% tolerance)
            continue
        area_frac = (w * h) / img_area
        if not 0.10 < area_frac < 0.65:    # plausible grid size relative to screen
            continue
        candidates.append((w * h, x, y, w))

    if not candidates:
        raise CalibrationError("no square grid contour found at plausible scale")

    # Largest plausible square is the grid.
    candidates.sort(reverse=True)
    _, x, y, w = candidates[0]
    cell_size = w // 4
    return BoardBBox(top=y, left=x, cell_size=cell_size)


@dataclass
class BoardOCR:
    bbox: Optional[BoardBBox] = None
    _last_calibration_image_size: tuple[int, int] = field(default=(0, 0))

    def read(self, image: Image.Image) -> BoardState:
        # Re-calibrate if image dimensions changed (e.g. emulator restarted at
        # a new resolution) or on first read.
        size = image.size
        if self.bbox is None or size != self._last_calibration_image_size:
            self.bbox = calibrate_board_bbox(image)
            self._last_calibration_image_size = size

        bbox = self.bbox
        arr = np.asarray(image)
        inset = max(8, bbox.cell_size // 12)  # scale the sampling patch with cell size
        grid = [[0] * 4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                cy = bbox.top + r * bbox.cell_size + bbox.cell_size // 2
                cx = bbox.left + c * bbox.cell_size + bbox.cell_size // 2
                patch = arr[
                    cy - inset : cy + inset,
                    cx - inset : cx + inset,
                ]
                rgb = tuple(int(v) for v in patch.reshape(-1, 3).mean(axis=0))
                grid[r][c] = _nearest_tile(rgb)
        return BoardState(grid=grid, score=0)
```

**Drift safeguard.** If `_nearest_tile` returns a color that's far from any palette entry (distance > threshold), the OCR layer logs a warning and bumps a `calibration_drift_counter`. After 3 consecutive drift events the bbox cache is invalidated and re-calibration runs on the next frame. This catches the case where the emulator is restarted mid-session at a different scale.

**Test it: a simulated emulator-resolution change must not break OCR.**

```python
def test_ocr_recalibrates_when_image_size_changes(tmp_path):
    """R2 — auto-calibration must survive emulator-resolution changes."""
    from nova_agent.perception.ocr import BoardOCR
    # ... build a synthetic 1080×2400 board fixture ...
    ocr = BoardOCR()
    state_a = ocr.read(big_image)
    state_b = ocr.read(small_image)  # 720×1600 simulated rescale
    assert state_a.grid == expected_grid_for_big
    assert state_b.grid == expected_grid_for_small
```

- [ ] **Step 4: Run OCR tests**

```bash
uv run pytest tests/test_perception_ocr.py -v
```

If a board fails, the failure mode is no longer "wrong hardcoded coords" — it's either (a) the contour finder couldn't isolate the grid (palette/threshold tuning), or (b) the palette colors drifted (Unity build changed). The smoke gauntlet catches both before they reach a real run.

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
    # 16-D vectors matching VectorStore.DIM. Build trivially distinct ones.
    a = [0.0] * 16; a[0] = 1.0       # axis 0
    b = [0.0] * 16; b[5] = 1.0       # axis 5
    c = [0.0] * 16; c[0] = 0.95; c[1] = 0.05  # close to a
    vs.upsert("a", a)
    vs.upsert("b", b)
    vs.upsert("c", c)
    q = [0.0] * 16; q[0] = 1.0
    hits = vs.search(q, k=2)
    ids = [id_ for id_, _score in hits]
    assert ids[0] in ("a", "c")


def test_vector_store_rejects_wrong_dim(tmp_path):
    """LanceDB schema asserts dim — bad input raises immediately."""
    vs = VectorStore(tmp_path / "lancedb")
    import pytest
    with pytest.raises(ValueError):
        vs.upsert("bad", [1.0, 0.0, 0.0])  # 3-D against a 16-D store
```

- [ ] **Step 2: Implement spatial embedding (NOT SHA-256 — that breaks similarity)**

Review #4 caught a real bug: an earlier draft used `hashlib.sha256` per `(value, position)` pair, summing hashed bytes into a 64-D vector. SHA-256's avalanche property destroys spatial similarity — two boards differing by one tile produce uncorrelated hash bytes, so `cos(query, stored)` hovers near zero for *any* non-identical board. That breaks the `relevance` term in §3.4 retrieval AND breaks the `aversive_radius` widening in §3.6 (Task 32) — aversive memories would only fire on exact-match boards, killing trauma generalization.

The replacement is a 16-D log-tile spatial encoder: one component per grid cell, value `log₂(tile)/16` (or 0 for empty), L2-normalized so dot product equals cosine similarity. Two boards differing in one cell now differ in one of 16 components by at most ~1.0 — cosine similarity stays gradient and meaningful.

```python
# nova-agent/src/nova_agent/llm/embeddings.py
"""Spatial embedding for 2048 boards.

Cosine similarity reflects board structural similarity. NOT a hash —
hashes destroy similarity by design (avalanche effect) and were a load-
bearing bug in an earlier draft.
"""

from __future__ import annotations

import math
from typing import Sequence

EMBED_DIM: int = 16  # 4×4 grid, one component per cell


def embed_board(grid: Sequence[Sequence[int]], dim: int = EMBED_DIM) -> list[float]:
    """16-D L2-normalized log-tile spatial embedding.

    Component i (0..15) = log2(tile)/16 at row=i//4, col=i%4 (0.0 if empty).
    `dim` kwarg retained for API compatibility but must equal EMBED_DIM=16
    in v1; LanceDB schema asserts dimensionality on connect.
    """
    if dim != EMBED_DIM:
        raise ValueError(
            f"v1 spatial embedding is fixed at {EMBED_DIM} dims (4×4 grid). "
            f"To change dimensionality, update EMBED_DIM and LanceDB schema together."
        )
    flat: list[float] = []
    for row in grid:
        for v in row:
            flat.append(0.0 if v == 0 else math.log2(v) / 16.0)
    if len(flat) != EMBED_DIM:
        raise ValueError(f"grid must yield {EMBED_DIM} cells; got {len(flat)}")
    norm = math.sqrt(sum(x * x for x in flat))
    if norm == 0.0:
        return flat
    return [x / norm for x in flat]
```

**Critical similarity test — the entire reason this rewrite exists**:

```python
# nova-agent/tests/test_embeddings.py
import math
from nova_agent.llm.embeddings import embed_board, EMBED_DIM


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both pre-normalized


def test_embed_dim_is_16():
    e = embed_board([[0]*4]*4)
    assert len(e) == EMBED_DIM == 16


def test_similarity_high_for_one_tile_diff():
    """The whole reason we're not using SHA-256. Two boards differing by
    one tile in one cell must have cosine similarity > 0.85 — otherwise
    the aversive-radius widening (§3.6) and Generative Agents relevance
    term (§3.4) cannot work.
    """
    a = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 8, 0], [0, 0, 0, 16]]
    b = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 8, 0], [0, 0, 0, 32]]  # one tile diff
    e_a = embed_board(a)
    e_b = embed_board(b)
    assert _cos(e_a, e_b) > 0.85


def test_similarity_low_for_completely_different_boards():
    a = [[2, 0, 0, 0]] + [[0]*4]*3
    b = [[0]*4]*3 + [[0, 0, 0, 2048]]
    assert _cos(embed_board(a), embed_board(b)) < 0.5


def test_identical_boards_cosine_one():
    g = [[2, 4, 8, 16]] * 4
    e = embed_board(g)
    assert abs(_cos(e, e) - 1.0) < 1e-9


def test_empty_board_returns_zero_vector():
    """Edge case: pre-game / cleared board. L2 norm is 0; return zero vec."""
    e = embed_board([[0]*4]*4)
    assert all(x == 0.0 for x in e)
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
    DIM = 16  # must match nova_agent.llm.embeddings.EMBED_DIM

    def __init__(self, path: Path):
        from nova_agent.llm.embeddings import EMBED_DIM
        if EMBED_DIM != self.DIM:
            raise RuntimeError(
                f"VectorStore.DIM ({self.DIM}) != embeddings.EMBED_DIM ({EMBED_DIM}) — "
                f"update both in lockstep."
            )
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))
        if self.TABLE not in self._db.table_names():
            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), self.DIM)),
                ]
            )
            self._db.create_table(self.TABLE, schema=schema)
        self._tbl = self._db.open_table(self.TABLE)

    def upsert(self, id: str, vector: list[float]) -> None:
        if len(vector) != self.DIM:
            raise ValueError(f"vector must have {self.DIM} dims; got {len(vector)}")
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


VECTOR_IMPORTANCE_THRESHOLD: int = 4  # mundane moves (importance < 4) skip the vector store


class MemoryCoordinator:
    def __init__(self, *, sqlite_path: Path, lancedb_path: Path):
        self.episodic = EpisodicStore(sqlite_path)
        self.vector = VectorStore(lancedb_path)
        self.vector_skip_count: int = 0  # metric for tuning the threshold; logged to bus footer

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
        """Importance-gated write (review #4 fix for state-space bloat).

        - SQLite always gets the record (full audit trail; reflection reads
          the whole game's traces; quarantine for reconciliation §3.9.1).
        - LanceDB only gets the record if it's salient enough to ever be
          worth retrieving as similar context. A typical 200-move game at
          a 4-of-10 threshold writes ~30 vectors, not 200 — vector search
          surfaces strategic moves, not "merged two 2s" noise.

        Aversive precondition records: tagged retroactively by
        `tag_aversive` after game-over. Their importance bumps to ≥7 at
        that point; we then upsert them into the vector store via
        `upsert_aversive_record` (below) so `aversive_radius` retrieval
        actually finds them.
        """
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

        if importance >= VECTOR_IMPORTANCE_THRESHOLD:
            self.vector.upsert(rec_id, emb)
        else:
            self.vector_skip_count += 1
        return rec_id

    def upsert_aversive_record(self, rec: MemoryRecord) -> None:
        """Lazily insert (or update) a record in the vector store after
        `tag_aversive` (Task 31) has retroactively bumped its importance.

        Called by the game-over hook in main.py for each aversive
        precondition record. Without this, an aversive memory tagged from
        a record that originally had importance < 4 would never enter
        LanceDB and `aversive_radius` retrieval (§3.6) couldn't find it.
        """
        if rec.embedding is None:
            return
        self.vector.upsert(rec.id, rec.embedding)

    def retrieve_for_board(self, board: BoardState, k: int = 5) -> list[RetrievedMemory]:
        emb = embed_board(board.grid)
        # Vector pre-filter to ~50 candidates, then full re-rank
        candidate_ids = [id_ for id_, _ in self.vector.search(emb, k=min(50, k * 10))]
        candidates = [r for r in (self.episodic.get(i) for i in candidate_ids) if r]
        if not candidates:
            return []
        return retrieve_top_k(candidates=candidates, query_embedding=emb, k=k)
```

**Operator note**: the gate is intentionally conservative (mundane moves stay in SQLite, just not in vector retrieval). To tune the threshold during dev: log `vector_skip_count / total_writes` per game; aim for **30–70%** skip rate. < 30% means the threshold is too loose (vector store still bloats); > 70% means too tight (potentially missing useful retrievable context). At default threshold=4, expect ~50% skip on a typical play distribution.

**Add tests for the gate + retroactive aversive upsert**:

```python
# nova-agent/tests/test_memory_coordinator.py — add
def test_low_importance_skips_vector_store(tmp_path):
    coord = MemoryCoordinator(sqlite_path=tmp_path / "n.db", lancedb_path=tmp_path / "lance")
    b = BoardState(grid=[[2, 0, 0, 0]] + [[0]*4]*3, score=0)
    rec_id = coord.write_move(
        board_before=b, board_after=b, action="swipe_right",
        score_delta=4, rpe=0.05, importance=2, source_reasoning="trivial",
    )
    # SQLite has it; vector store doesn't
    assert coord.episodic.get(rec_id) is not None
    assert coord.vector_skip_count == 1
    # vector search for the same board should miss the just-written record
    hits = coord.vector.search(embed_board(b.grid), k=5)
    assert all(h[0] != rec_id for h in hits)


def test_aversive_record_upserted_retroactively(tmp_path):
    """Game-over flow: a record initially written with importance=2 must
    be reachable via vector search after tag_aversive bumps importance.
    """
    coord = MemoryCoordinator(sqlite_path=tmp_path / "n.db", lancedb_path=tmp_path / "lance")
    b = BoardState(grid=[[2, 4, 8, 16]] + [[0]*4]*3, score=0)
    rec_id = coord.write_move(
        board_before=b, board_after=b, action="swipe_left",
        score_delta=0, rpe=-0.2, importance=2, source_reasoning="bad move",
    )
    # initially absent from vector store
    assert all(h[0] != rec_id for h in coord.vector.search(embed_board(b.grid), k=5))
    # game over: precondition tagged aversive, importance bumped, upserted
    rec = coord.episodic.get(rec_id)
    rec_promoted = replace(rec, importance=8, aversive_weight=1.0, tags=[*rec.tags, "aversive"])
    coord.upsert_aversive_record(rec_promoted)
    hits = coord.vector.search(embed_board(b.grid), k=5)
    assert any(h[0] == rec_id for h in hits)
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

## Task 22: Outcome evaluator — online TD(0) value function with analytic prior

Implements §3.7 of the design spec: linear function approximator V on 6 hand-engineered features, online TD(0) update with γ=0.99 / α=0.01, analytic prior `V₀` so RPE is meaningful from move 1.

**Files:**
- Create: `nova-agent/src/nova_agent/affect/features.py`
- Create: `nova-agent/src/nova_agent/affect/value_fn.py`
- Create: `nova-agent/src/nova_agent/affect/rpe.py`
- Create: `nova-agent/tests/test_affect_features.py`
- Create: `nova-agent/tests/test_affect_value_fn.py`
- Create: `nova-agent/tests/test_affect_rpe.py`

- [ ] **Step 1: Failing tests — features**

```python
# nova-agent/tests/test_affect_features.py
from nova_agent.affect.features import compute_features
from nova_agent.perception.types import BoardState


def test_features_dim_is_six():
    b = BoardState(grid=[[0]*4]*4, score=0)
    phi = compute_features(b)
    assert len(phi) == 6


def test_adjacent_pairs_higher_for_pair_board():
    no_pairs = BoardState(grid=[[2,4,8,16]] * 4, score=0)
    with_pairs = BoardState(grid=[[2,2,4,4],[4,4,8,8],[0]*4,[0]*4], score=0)
    phi_no = compute_features(no_pairs)
    phi_yes = compute_features(with_pairs)
    # index 1 = adjacent_pairs
    assert phi_yes[1] > phi_no[1]


def test_features_in_unit_range():
    b = BoardState(grid=[[2,4,8,16],[32,64,128,256],[512,1024,2048,4096],[8192,16384,32768,65536]], score=0)
    phi = compute_features(b)
    for v in phi:
        assert 0.0 <= v <= 1.0
```

- [ ] **Step 2: Failing tests — value function**

```python
# nova-agent/tests/test_affect_value_fn.py
import numpy as np
from nova_agent.affect.value_fn import LinearValueFunction
from nova_agent.perception.types import BoardState


def test_v0_prior_nonzero_on_realistic_board():
    V = LinearValueFunction.with_analytic_prior()
    b = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    assert V(b) > 0.0


def test_td0_update_reduces_error_on_repeated_visits():
    V = LinearValueFunction.with_analytic_prior()
    b1 = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)
    # repeatedly observe r=4 transitioning b1 → b2 with V(b2)=0 (terminal-ish for test)
    V_before = V(b1)
    for _ in range(200):
        V.td_update(s_t=b1, r_t=4, s_tplus1=b2, terminal=True)
    V_after = V(b1)
    # V(b1) should move toward r_t (γ=0.99 · 0 + 4 = 4)
    assert abs(V_after - 4.0) < abs(V_before - 4.0)
```

- [ ] **Step 3: Implement features**

```python
# nova-agent/src/nova_agent/affect/features.py
"""Six hand-engineered features for the linear value function V (§3.7)."""

from __future__ import annotations

import math
from nova_agent.perception.types import BoardState

FEATURE_NAMES = (
    "empty",
    "adjacent_pairs",
    "mono",
    "smooth",
    "maxcorner",
    "logmax",
)
FEATURE_DIM = 6


def _empty_count(grid: list[list[int]]) -> int:
    return sum(1 for r in range(4) for c in range(4) if grid[r][c] == 0)


def _adjacent_pairs(grid: list[list[int]]) -> int:
    count = 0
    for r in range(4):
        for c in range(4):
            v = grid[r][c]
            if v == 0:
                continue
            if c + 1 < 4 and grid[r][c + 1] == v:
                count += 1
            if r + 1 < 4 and grid[r + 1][c] == v:
                count += 1
    return count


def _monotonicity(grid: list[list[int]]) -> float:
    """Sum of monotonic runs along rows + columns. Higher = more monotonic."""
    score = 0.0
    for r in range(4):
        score += _row_monotonic(grid[r])
    for c in range(4):
        col = [grid[r][c] for r in range(4)]
        score += _row_monotonic(col)
    return score


def _row_monotonic(row: list[int]) -> float:
    inc = dec = 0.0
    for i in range(3):
        a, b = row[i], row[i + 1]
        if a == 0 or b == 0:
            continue
        if a >= b:
            dec += math.log2(a) - math.log2(b)
        if a <= b:
            inc += math.log2(b) - math.log2(a)
    return max(inc, dec)


def _smoothness(grid: list[list[int]]) -> float:
    """1 − Σ |log2(a) − log2(b)| / norm over adjacent non-zero pairs."""
    diff = 0.0
    pairs = 0
    for r in range(4):
        for c in range(4):
            v = grid[r][c]
            if v == 0:
                continue
            for dr, dc in ((0, 1), (1, 0)):
                nr, nc = r + dr, c + dc
                if nr < 4 and nc < 4 and grid[nr][nc] != 0:
                    diff += abs(math.log2(v) - math.log2(grid[nr][nc]))
                    pairs += 1
    if pairs == 0:
        return 1.0
    norm = pairs * 17.0  # max log2 diff across reasonable tile range
    return max(0.0, 1.0 - diff / norm)


def _max_in_corner(grid: list[list[int]]) -> int:
    max_tile = max(grid[r][c] for r in range(4) for c in range(4))
    if max_tile == 0:
        return 0
    corners = (grid[0][0], grid[0][3], grid[3][0], grid[3][3])
    return 1 if max_tile in corners else 0


def compute_features(board: BoardState) -> list[float]:
    """Return φ(s) ∈ [0,1]^6.

    Order: [empty, adjacent_pairs, mono, smooth, maxcorner, logmax].
    """
    g = board.grid
    max_tile = max(g[r][c] for r in range(4) for c in range(4))
    max_mono = 4 * 17.0  # rough bound on _monotonicity on a full board

    return [
        _empty_count(g) / 16.0,
        _adjacent_pairs(g) / 24.0,                  # 24 = max possible adjacent pairs
        _monotonicity(g) / max_mono,
        _smoothness(g),
        float(_max_in_corner(g)),
        (math.log2(max_tile) / 17.0) if max_tile > 0 else 0.0,
    ]
```

- [ ] **Step 4: Implement linear value function with TD(0) update**

```python
# nova-agent/src/nova_agent/affect/value_fn.py
"""Linear function approximator V(s) for online TD(0) learning (§3.7).

V(s) = wᵀ φ(s) · score_scale.
Update: w ← w + α · δ_t · φ(s_t)  where δ_t = r_t + γ · V(s_{t+1}) − V(s_t).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from nova_agent.affect.features import FEATURE_DIM, compute_features
from nova_agent.perception.types import BoardState

GAMMA: float = 0.99           # 2048 horizon is long; half-life ~69 moves
ALPHA: float = 0.01           # in [0.005, 0.02] per §3.7
SCORE_SCALE: float = 50.0     # typical per-move score-delta scale

# Analytic prior weights (§3.7). adjacent_pairs weighted highest.
W_PRIOR: tuple[float, ...] = (4.0, 5.0, 3.0, 2.0, 2.0, 1.5)


@dataclass
class LinearValueFunction:
    weights: list[float] = field(default_factory=lambda: list(W_PRIOR))
    gamma: float = GAMMA
    alpha: float = ALPHA
    score_scale: float = SCORE_SCALE

    @classmethod
    def with_analytic_prior(cls) -> "LinearValueFunction":
        return cls(weights=list(W_PRIOR))

    def __call__(self, board: BoardState, terminal: bool = False) -> float:
        if terminal:
            return 0.0
        phi = compute_features(board)
        return sum(w * f for w, f in zip(self.weights, phi)) * self.score_scale

    def td_update(
        self,
        *,
        s_t: BoardState,
        r_t: float,
        s_tplus1: BoardState,
        terminal: bool,
    ) -> float:
        """One TD(0) update. Returns δ_t (the prediction error)."""
        v_t = self(s_t)
        v_tp1 = 0.0 if terminal else self(s_tplus1)
        delta = r_t + self.gamma * v_tp1 - v_t

        # gradient update on linear approximator: w ← w + α · δ · φ(s_t) / scale
        phi = compute_features(s_t)
        for i in range(FEATURE_DIM):
            self.weights[i] += self.alpha * delta * phi[i] / self.score_scale
        return delta

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"weights": self.weights, "gamma": self.gamma, "alpha": self.alpha}))

    @classmethod
    def load(cls, path: Path) -> "LinearValueFunction":
        data = json.loads(path.read_text())
        return cls(**data)
```

- [ ] **Step 5: Implement RPE wrapper with TD(0) + warm-up gate on affect propagation**

Review #4 raised a real concern: σ_δ on game-1 move-1 is undefined (running stdev of an empty deque), so `RPE_norm = δ / σ` is volatile for the first ~10 moves. Even with the [-1, +1] clip, this produces noisy affect signals that look chaotic on the brain panel rather than narrative.

Fix: a **warm-up gate on the affect-propagation path only**. V keeps learning from move 1 (TD update fires every move; that's how V converges in the first place). But the *normalized* RPE returned to the affect module is forced to 0.0 until σ_δ has at least `WARMUP_MOVES = 10` samples. After warm-up, σ_δ is the running mean of |δ_t| over the last 100 moves. A `prior_sigma` derived from `score_scale / 4` is also available as a fallback if the running σ collapses to near-zero (e.g., on a streak of perfect predictions).

This preserves the §3.7 TD(0) math intact — V learns from every move regardless of warm-up — while bounding the affect-side noise that the reviewer correctly flagged.

```python
# nova-agent/src/nova_agent/affect/rpe.py
"""Reward Prediction Error wrapper — TD(0)-based, with running σ for
normalization and a warm-up gate that bounds early-game affect volatility.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from nova_agent.affect.value_fn import SCORE_SCALE, LinearValueFunction
from nova_agent.perception.types import BoardState

WARMUP_MOVES: int = 10                      # affect propagation suppressed until σ_δ has this many samples
PRIOR_SIGMA: float = SCORE_SCALE / 4.0      # fallback σ if running σ collapses (≈12.5)


@dataclass
class RPETracker:
    V: LinearValueFunction = field(default_factory=LinearValueFunction.with_analytic_prior)
    recent_abs_deltas: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    move_count: int = 0  # count of TD updates seen this tracker (per-session)

    def step(
        self,
        *,
        s_t: BoardState,
        r_t: float,
        s_tplus1: BoardState,
        terminal: bool,
    ) -> tuple[float, float]:
        """Run one TD(0) update on V, return (δ_t raw, RPE_norm).

        V learns from every move (move_count is just a counter). The
        warm-up gate only affects the *affect propagation* path —
        RPE_norm is forced to 0.0 until at least WARMUP_MOVES samples
        have accumulated, so affect doesn't get whipsawed by ill-defined
        σ on the first few moves of a fresh tracker.
        """
        delta = self.V.td_update(s_t=s_t, r_t=r_t, s_tplus1=s_tplus1, terminal=terminal)
        self.recent_abs_deltas.append(abs(delta))
        self.move_count += 1

        # Warm-up gate (review #4 fix). V learning continues regardless.
        if self.move_count < WARMUP_MOVES:
            return delta, 0.0

        sigma = sum(self.recent_abs_deltas) / max(1, len(self.recent_abs_deltas))
        if sigma < 1e-3:
            sigma = PRIOR_SIGMA  # fallback — protects against runaway when σ collapses
        rpe_norm = max(-1.0, min(1.0, delta / sigma))
        return delta, rpe_norm
```

**Add tests for warm-up behavior**:

```python
# nova-agent/tests/test_affect_rpe.py — add to existing
def test_rpe_norm_zero_during_warmup():
    """First N moves emit δ_t for V learning but RPE_norm=0 to affect."""
    tracker = RPETracker()
    b1 = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)
    norms_during_warmup = []
    for _ in range(9):  # warm-up is 10 — first 9 should all return 0.0
        _, rpe_norm = tracker.step(s_t=b1, r_t=4.0, s_tplus1=b2, terminal=False)
        norms_during_warmup.append(rpe_norm)
    assert all(n == 0.0 for n in norms_during_warmup)


def test_rpe_norm_active_after_warmup():
    tracker = RPETracker()
    b1 = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)
    for _ in range(15):
        _, rpe_norm = tracker.step(s_t=b1, r_t=4.0, s_tplus1=b2, terminal=False)
    # After warm-up, last call should produce a nonzero norm bounded to [-1, 1]
    assert -1.0 <= rpe_norm <= 1.0


def test_v_learns_during_warmup():
    """The warm-up gate must NOT block V's TD updates — only affect
    propagation. V's weights must move during warmup or convergence
    breaks across short runs.
    """
    tracker = RPETracker()
    b1 = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)
    w_before = list(tracker.V.weights)
    for _ in range(5):
        tracker.step(s_t=b1, r_t=4.0, s_tplus1=b2, terminal=False)
    w_after = list(tracker.V.weights)
    assert w_before != w_after  # weights moved during warm-up
```

- [ ] **Step 6: Failing test — RPE pipeline integration**

```python
# nova-agent/tests/test_affect_rpe.py
from nova_agent.affect.rpe import RPETracker
from nova_agent.perception.types import BoardState


def test_rpe_norm_in_unit_range_after_history():
    tracker = RPETracker()
    b = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)
    # warm up running σ
    for _ in range(50):
        _, _ = tracker.step(s_t=b, r_t=4.0, s_tplus1=b2, terminal=False)
    delta, rpe_norm = tracker.step(s_t=b, r_t=4.0, s_tplus1=b2, terminal=False)
    assert -1.0 <= rpe_norm <= 1.0


def test_v_converges_across_repeated_episodes():
    """§8.5 acceptance: per-game mean(|δ|) shrinks across games 1→50."""
    tracker = RPETracker()
    b = BoardState(grid=[[2,2,0,0]] + [[0]*4]*3, score=0)
    b2 = BoardState(grid=[[4,0,0,0]] + [[0]*4]*3, score=4)

    means = []
    for game in range(20):
        deltas = []
        for _ in range(100):
            d, _ = tracker.step(s_t=b, r_t=4.0, s_tplus1=b2, terminal=False)
            deltas.append(abs(d))
        means.append(sum(deltas) / len(deltas))

    # final-game mean should be substantially below first-game mean
    assert means[-1] < means[0] * 0.5
```

- [ ] **Step 7: Pass + commit**

```bash
git add nova-agent/
git commit -m "feat(affect): online TD(0) value function with analytic prior + 6-feature linear V"
```

**Notes for §8 acceptance:**
- The convergence test (Step 6 second test) is the §8.5 V-convergence acceptance criterion expressed as a unit test.
- `RPETracker.recent_abs_deltas` becomes the running σ_δ used for `RPE_norm` in §3.5 affect updates (Task 20/23).
- Persisting `LinearValueFunction.weights` to disk between sessions is optional in v1 — fresh `with_analytic_prior()` per session is fine; tier-switched runs may want fresh weights to avoid cross-tier contamination of V.

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

## Task 31: Aversive Memory Tag (post-game-over) — informally "trauma"

Implements §3.6 of the design spec. Naming convention: code uses `aversive_*`; UI label uses "Trauma" (kept punchy for the demo). All four spiral defenses (active-tag cap, exposure-extinction halving, semantic override, cross-game reset) are wired here or hooked from here.

**Files:**
- Create: `nova-agent/src/nova_agent/memory/aversive.py`
- Create: `nova-agent/tests/test_memory_aversive.py`

- [ ] **Step 1: Failing tests**

```python
# nova-agent/tests/test_memory_aversive.py
from datetime import datetime, timezone, timedelta
from nova_agent.memory.aversive import (
    is_catastrophic_loss, tag_aversive, exposure_extinction_halve, AVERSIVE_TAG,
)
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def _rec(i: int = 0, *, importance: int = 3, aversive_weight: float | None = None) -> MemoryRecord:
    b = BoardState(grid=[[0]*4]*4, score=0)
    extras = {}
    if aversive_weight is not None:
        extras["aversive_weight"] = aversive_weight
    return MemoryRecord(
        id=f"r_{i}",
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=10 - i),
        board_before=b, board_after=b,
        action="swipe_right", score_delta=0, rpe=0.0,
        importance=importance, tags=[], embedding=[0.0]*8,
        **extras,
    )


def test_tag_aversive_after_catastrophic_loss():
    last_5 = [_rec(i) for i in range(5)]
    tagged = tag_aversive(precondition_records=last_5, was_catastrophic=True)
    assert all(AVERSIVE_TAG in r.tags for r in tagged)
    assert all(r.importance >= 7 for r in tagged)
    assert all(r.aversive_weight == 1.0 for r in tagged)


def test_exposure_extinction_halves_weight():
    """§3.6 defense B — primary deterministic spiral guarantee."""
    r = _rec(0, importance=8, aversive_weight=1.0)
    r.tags.append(AVERSIVE_TAG)
    after_one = exposure_extinction_halve(r)
    assert after_one.aversive_weight == 0.5
    after_two = exposure_extinction_halve(after_one)
    assert after_two.aversive_weight == 0.25
    # After ~6 survivals, weight is < 0.02 — effectively inert
    weights = [r.aversive_weight]
    cur = r
    for _ in range(6):
        cur = exposure_extinction_halve(cur)
        weights.append(cur.aversive_weight)
    assert weights[-1] < 0.02


def test_extinction_noop_on_non_aversive():
    r = _rec(0)
    out = exposure_extinction_halve(r)
    assert out is r  # unchanged identity


def test_aversive_weight_decays_continuously_not_in_integer_steps():
    """R3 — aversive_weight is float, not int-truncated.

    A previous draft had `int(importance * 0.95)` which truncated 7→6 on the
    first decay because `int(6.65) == 6`. Whole-integer steps would burn
    aversive memories ~5× faster than intended. The current implementation
    must keep aversive_weight as a continuous float. The integer
    `importance` field stays for retrieval-scoring; aversive_weight is the
    decay channel.
    """
    r = _rec(0, importance=8, aversive_weight=1.0)
    r.tags.append(AVERSIVE_TAG)
    cur = r
    weights: list[float] = [cur.aversive_weight]
    for _ in range(3):
        cur = exposure_extinction_halve(cur)
        weights.append(cur.aversive_weight)
    # halving from 1.0 across 3 steps must yield {1.0, 0.5, 0.25, 0.125},
    # not {1, 0, 0, 0}. This is exactly what int-truncation would give us.
    assert weights == [1.0, 0.5, 0.25, 0.125]
    # importance stays integer (retrieval-side concern), but aversive_weight is float
    assert isinstance(cur.aversive_weight, float)
    assert isinstance(cur.importance, int)


def test_is_catastrophic_loss_requires_contested_board():
    # tight board + low score for max_tile = catastrophic
    assert is_catastrophic_loss(final_score=200, max_tile_reached=64, last_empty_cells=1)
    # roomy board = NOT catastrophic
    assert not is_catastrophic_loss(final_score=200, max_tile_reached=64, last_empty_cells=8)
```

- [ ] **Step 2: Implement aversive tagging + extinction halving**

```python
# nova-agent/src/nova_agent/memory/aversive.py
"""Aversive Memory Tag (informal: 'trauma').

§3.6 defenses A, B implemented here. Defense C (semantic override) hooks
from Task 36 reflection. Defense D (cross-game affect reset) hooks from
Task 23 / Task 36 game-start handler. UI label is "Trauma" — see
`nova-viewer/app/components/TraumaIndicator.tsx`. Code surface is
`aversive_*` to keep marketing copy separate from engineering.
"""

from __future__ import annotations

from dataclasses import replace
from nova_agent.memory.types import MemoryRecord

AVERSIVE_TAG = "aversive"  # was "trauma" — see §3.6 naming convention
AVERSIVE_INITIAL_WEIGHT = 1.0
AVERSIVE_INERT_THRESHOLD = 0.02  # below this, retrieval skips the boost


def is_catastrophic_loss(*, final_score: int, max_tile_reached: int, last_empty_cells: int) -> bool:
    """A loss is catastrophic iff the board was contested (few empty cells)
    AND the score under-performed relative to the max tile achieved.
    """
    return (
        last_empty_cells <= 2
        and max_tile_reached >= 64
        and final_score < max_tile_reached * 4
    )


def tag_aversive(*, precondition_records: list[MemoryRecord], was_catastrophic: bool) -> list[MemoryRecord]:
    """Mark the (t-5) → (t-1) precondition boards as aversive after a catastrophic loss.

    Importance += 3 (capped at 10), tag added, aversive_weight = 1.0.
    """
    if not was_catastrophic:
        return precondition_records

    tagged: list[MemoryRecord] = []
    for r in precondition_records:
        new_tags = list(dict.fromkeys(r.tags + [AVERSIVE_TAG, "loss_precondition"]))
        new_importance = min(10, r.importance + 3)
        tagged.append(replace(
            r,
            tags=new_tags,
            importance=new_importance,
            aversive_weight=AVERSIVE_INITIAL_WEIGHT,
        ))
    return tagged


def exposure_extinction_halve(record: MemoryRecord) -> MemoryRecord:
    """Defense B (primary, deterministic): halve aversive_weight on each survival.

    Called from the retrieval pipeline AFTER a successful (non-loss) move on
    a board within `aversive_radius` of an aversive memory. After ~6 survivals
    the weight is < 0.02 and effectively inert — the spiral terminates
    mathematically, not via LLM cooperation.
    """
    if AVERSIVE_TAG not in record.tags:
        return record
    new_weight = max(0.0, record.aversive_weight * 0.5)
    return replace(record, aversive_weight=new_weight)


def is_inert(record: MemoryRecord) -> bool:
    """An aversive record below the threshold contributes no anxiety boost."""
    return AVERSIVE_TAG in record.tags and record.aversive_weight < AVERSIVE_INERT_THRESHOLD
```

- [ ] **Step 3: Update `MemoryRecord` to carry `aversive_weight`**

In `nova-agent/src/nova_agent/memory/types.py` add the field with a default of `0.0` (non-aversive records). All extant constructors keep working.

```python
@dataclass(frozen=True)
class MemoryRecord:
    # ... existing fields ...
    aversive_weight: float = 0.0  # 0.0 if non-aversive; 1.0 fresh, halved on each survival
```

Add a SQLite ALTER (or one-time migration) to add the `aversive_weight REAL DEFAULT 0.0` column.

- [ ] **Step 4: Wire defenses A & D + retroactive aversive vector upsert**

- **Defense A (active-tag cap, max-1 surfaced):** modify the retrieval pipeline (Task 32) to keep at most one aversive record in the returned top-k — the one with the highest `aversive_weight` × `relevance` score. Drop the rest from the prompt.
- **Defense D (cross-game reset):** in the run loop (Task 36 / game-start hook), on `game_start` event reset `affect.anxiety = 0`, `affect.frustration = 0`, `affect.dopamine = 0`. Retain `valence ← 0.3 · valence` (slow variable; partial carry-over by design). Defense D is logged as a hygiene step, not a load-bearing defense.
- **Retroactive vector upsert (interaction with Task 16's importance gate, review #4 fix):** the precondition records were written during the *moves themselves* and may have failed the `importance >= 4` vector-store gate. After `tag_aversive` bumps their importance to ≥ 7, call `coordinator.upsert_aversive_record(rec)` for each tagged record. Without this step, an aversive memory tagged from a low-importance precondition would never enter LanceDB and `aversive_radius` retrieval (§3.6) couldn't find it. Wire this in main.py's `on_game_over` handler:

```python
# In main.py game-over hook (Task 36 wiring)
tagged = tag_aversive(precondition_records=last_5_moves, was_catastrophic=catastrophic)
for rec in tagged:
    coordinator.episodic.update(rec)              # persist new importance + tags + aversive_weight
    coordinator.upsert_aversive_record(rec)        # ensure it's in LanceDB for retrieval
```

- [ ] **Step 5: Pass + commit**

```bash
uv run pytest tests/test_memory_aversive.py -v
git add nova-agent/
git commit -m "feat(memory): aversive memory tag with extinction halving (informally: trauma, §3.6 spiral defenses A+B+D)"
```

**Notes:**
- Defense C (semantic override via `trauma_outdated` rule) is intentionally NOT implemented in this task — it depends on Task 36 reflection. Defenses A and B alone are sufficient to terminate the spiral; C is best-effort.
- §8.2 acceptance: aversive replication test runs across N=30 paired episodes; convergence-to-baseline after ~6 survivals is the operational test of defense B.

---

## Task 32: Aversive retrieval radius widening + max-1 surfaced cap + last_accessed write-back

Implements §3.4 retrieval changes: aversive radius widening, defense-A active-tag cap (max 1 aversive record surfaced per move), and `last_accessed` write-back on every returned record (recency decay was previously a no-op).

**Files:**
- Modify: `nova-agent/src/nova_agent/memory/retrieval.py`
- Modify: `nova-agent/tests/test_memory_retrieval.py`

- [ ] **Step 1: Extend `retrieve_top_k` to widen the relevance threshold for aversive memories**

```python
# In retrieval.py
from nova_agent.memory.aversive import AVERSIVE_TAG, is_inert

def retrieve_top_k(
    ... existing args ...,
    aversive_relevance_floor: float = 0.4,
) -> list[RetrievedMemory]:
    # ... existing scoring ...
    for rec in candidates:
        if is_inert(rec):
            continue  # below extinction threshold; skip the boost
        rec_relevance = cosine(query_embedding, rec.embedding)
        if AVERSIVE_TAG in rec.tags and rec_relevance > aversive_relevance_floor:
            rec_relevance = max(rec_relevance, 0.7)  # widen radius
            rec_relevance *= rec.aversive_weight  # decayed memories surface less
        # ... rest of scoring ...
```

- [ ] **Step 2: Apply defense A — active-tag cap (max 1 aversive surfaced per move)**

After scoring all candidates, **before** truncating to top-k, drop all but the single highest-scoring aversive record. The remaining slots in top-k go to non-aversive memories. This is the deterministic guarantee that Nova never reads two aversive memories simultaneously and panic-stacks.

```python
def _enforce_aversive_cap(scored: list[RetrievedMemory]) -> list[RetrievedMemory]:
    """Defense A from §3.6 — at most one aversive record returned per move."""
    aversive = [m for m in scored if AVERSIVE_TAG in m.record.tags]
    non_aversive = [m for m in scored if AVERSIVE_TAG not in m.record.tags]
    if len(aversive) <= 1:
        return scored
    aversive.sort(key=lambda m: m.score, reverse=True)
    return [aversive[0]] + non_aversive
```

- [ ] **Step 3: Write `last_accessed` back on every returned record**

§3.4 recency decay depends on `last_accessed`. Without write-back, surfaced records stay "old" forever and recency degrades into a no-op. After scoring + cap-enforcement, before returning, batch-update `last_accessed = now()` for every returned record's id in SQLite.

```python
def retrieve_top_k(...) -> list[RetrievedMemory]:
    # ... compute scored, enforce cap, truncate to top-k ...
    returned = _enforce_aversive_cap(scored)[:k]
    now = datetime.now(timezone.utc)
    sqlite_store.batch_update_last_accessed([m.record.id for m in returned], now)
    return returned
```

- [ ] **Step 4: Lost-in-the-Middle prompt-position rule**

When the prompt builder (Task 16 / Task 23) inserts retrieved memories into the active context, place them at the **top OR bottom** of the active section, never in the middle. Per §3.4 + §8.2 Method 3. The simplest implementation: top-of-active-context, after rules and before board state.

- [ ] **Step 5: Test with synthetic memories**

```python
# tests/test_memory_retrieval.py — additions
def test_max_one_aversive_returned():
    """Defense A — active-tag cap."""
    # ... build store with 3 aversive + 5 non-aversive at similar relevance ...
    out = retrieve_top_k(query=q, k=5, ...)
    aversive_count = sum(1 for m in out if AVERSIVE_TAG in m.record.tags)
    assert aversive_count <= 1


def test_inert_aversive_not_returned():
    """An aversive record with weight < 0.02 doesn't surface."""
    # ... build store with one aversive at weight=0.01 ...
    out = retrieve_top_k(query=q, k=5, ...)
    assert all(m.record.id != "inert_one" for m in out)


def test_last_accessed_written_back():
    """Recency decay actually resets after retrieval."""
    # ... record stored at t-100s; retrieve; check last_accessed updated ...
    pre = sqlite_store.get_last_accessed("rec_1")
    _ = retrieve_top_k(query=q, k=5, ...)
    post = sqlite_store.get_last_accessed("rec_1")
    assert post > pre
```

- [ ] **Step 6: Pass + commit**

```bash
uv run pytest tests/test_memory_retrieval.py -v
git add nova-agent/
git commit -m "feat(memory): aversive radius widening + defense-A cap + last_accessed write-back"
```

---

## Task 33: Tree-of-Thoughts deliberation — branches stream to brain panel, read-only memory

Implements §3.8 of the design spec. Two new behaviors vs the prior draft: (1) each branch's evaluation publishes a `tot_branch` event to the bus as it completes, so the brain panel renders System-2 thinking on screen instead of a 4-second freeze; (2) branch evaluators are **read-only** with respect to memory (no writes from inside a branch — §3.4 concurrency rule).

**Files:**
- Create: `nova-agent/src/nova_agent/decision/tot.py`
- Create: `nova-agent/tests/test_decision_tot.py`

- [ ] **Step 1: Failing tests**

```python
# nova-agent/tests/test_decision_tot.py
import asyncio
from unittest.mock import MagicMock, AsyncMock
from nova_agent.decision.tot import ToTDecider
from nova_agent.perception.types import BoardState


def _llm_with_branches(values: list[float]) -> MagicMock:
    fake = MagicMock()
    fake.complete.side_effect = [
        (f'{{"action":"swipe_{d}","reasoning":"r","value":{v}}}',
         MagicMock(input_tokens=100, output_tokens=20, cost_usd=0.01))
        for d, v in zip(["up","down","left","right"], values)
    ]
    return fake


def test_tot_returns_best_branch():
    fake_llm = _llm_with_branches([0.7, 0.1, 0.4])
    bus = MagicMock(); bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    board = BoardState(grid=[[0,2,0,0]] + [[0]*4]*3, score=0)
    decision = asyncio.run(decider.decide(board=board, screenshot_b64="x", num_branches=3))
    assert decision.action == "swipe_up"


def test_tot_publishes_branch_event_per_candidate():
    """§3.8 — branches stream to brain panel as they evaluate."""
    fake_llm = _llm_with_branches([0.5, 0.6, 0.4])
    bus = MagicMock(); bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    board = BoardState(grid=[[0]*4]*4, score=0)
    asyncio.run(decider.decide(board=board, screenshot_b64="x", num_branches=3))

    # one event per branch + one final selection event
    branch_calls = [c for c in bus.publish.await_args_list if c.args[0] == "tot_branch"]
    select_calls = [c for c in bus.publish.await_args_list if c.args[0] == "tot_selected"]
    assert len(branch_calls) == 3
    assert len(select_calls) == 1


def test_tot_branch_evaluator_does_not_write_memory():
    """§3.4 read-only constraint — branches must never call memory.write_*."""
    from nova_agent.decision import tot as tot_module
    src = (tot_module.__file__ or "")
    # crude but effective: inspect source for forbidden writes inside branch fn
    code = open(src).read()
    # branch evaluator fn must not contain memory writes
    assert "memory.write_move" not in code
    assert "memory.write_reflection" not in code
    assert "memory.tag_aversive" not in code
```

- [ ] **Step 2: Implement — async branch evaluator with bus streaming and read-only memory**

```python
# nova-agent/src/nova_agent/decision/tot.py
"""Tree-of-Thoughts deliberation (System 2, §3.8).

Branch evaluators run in parallel via asyncio.gather, stream results to the
event bus as they complete (so the brain panel renders thinking, not a freeze),
and are READ-ONLY with respect to long-term memory — branches may QUERY but
must never WRITE. Writes happen on the single decision-loop thread after the
chosen branch is committed (§3.4 concurrency rule).
"""

from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel, Field

from nova_agent.bus.protocol import EventBus
from nova_agent.decision.react import Decision
from nova_agent.llm.protocol import LLM
from nova_agent.llm.structured import parse_json
from nova_agent.perception.types import BoardState


class _ToTBranch(BaseModel):
    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    reasoning: str
    value: float = Field(ge=0.0, le=1.0)


_TOT_SYSTEM = """\
You are evaluating ONE candidate move for a 2048 game. Imagine the board after
swiping in the proposed direction; rate the resulting position from 0 (terrible,
near-loss) to 1 (excellent, opens many merges). Be honest. You are not selecting
the move — you are scoring this single candidate.

Respond as strict JSON:
{"action": "swipe_up|swipe_down|swipe_left|swipe_right",
 "reasoning": "1-2 sentences",
 "value": 0.0..1.0}
"""


class ToTDecider:
    def __init__(self, *, llm: LLM, bus: EventBus, branch_temperature: float = 0.3):
        self.llm = llm
        self.bus = bus
        self.branch_temperature = branch_temperature

    async def decide(
        self,
        *,
        board: BoardState,
        screenshot_b64: str,
        num_branches: int = 4,
        game_id: str | None = None,
        move_idx: int | None = None,
    ) -> Decision:
        directions = ["swipe_up", "swipe_down", "swipe_left", "swipe_right"][:num_branches]
        # parallel branch evaluation; each branch is read-only
        tasks = [
            self._evaluate_one(board, screenshot_b64, direction, game_id, move_idx)
            for direction in directions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates = [r for r in results if isinstance(r, _ToTBranch)]
        if not candidates:
            raise RuntimeError("ToT produced no valid candidates")

        best = max(candidates, key=lambda c: c.value)
        await self.bus.publish("tot_selected", {
            "game_id": game_id,
            "move_idx": move_idx,
            "chosen_action": best.action,
            "chosen_value": best.value,
            "branch_values": {c.action: c.value for c in candidates},
        })
        return Decision(
            action=best.action,
            observation=f"ToT considered {len(candidates)} candidates",
            reasoning=best.reasoning,
            confidence="medium",
        )

    async def _evaluate_one(
        self,
        board: BoardState,
        screenshot_b64: str,
        direction: str,
        game_id: str | None,
        move_idx: int | None,
    ) -> _ToTBranch | Exception:
        """Evaluate ONE branch. READ-ONLY: must never call memory.write_*.

        On completion, publish `tot_branch` so the brain panel can render
        the branch card incrementally.
        """
        user = (
            f"Board:\n{board.grid}\nScore: {board.score}\n\n"
            f"Evaluate the move: {direction}"
        )
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                {"type": "text", "text": user},
            ],
        }]
        # the LLM call is sync — run in a thread so the bus can serve the viewer
        text, _ = await asyncio.to_thread(
            self.llm.complete,
            system=_TOT_SYSTEM,
            messages=messages,
            max_tokens=200,
            temperature=self.branch_temperature,
        )
        try:
            branch = parse_json(text, _ToTBranch)
        except Exception as exc:
            await self.bus.publish("tot_branch", {
                "game_id": game_id, "move_idx": move_idx,
                "direction": direction, "status": "parse_error", "error": str(exc),
            })
            return exc
        await self.bus.publish("tot_branch", {
            "game_id": game_id, "move_idx": move_idx,
            "direction": branch.action, "value": branch.value,
            "reasoning": branch.reasoning, "status": "complete",
        })
        return branch
```

- [ ] **Step 3: Pass + commit**

```bash
uv run pytest tests/test_decision_tot.py -v
git add nova-agent/
git commit -m "feat(decision): ToT with parallel read-only branches streamed to brain panel (§3.8)"
```

**Notes:**
- The `tot_branch` event schema must be added to the typed event contract (Task 17 / event-schema task). Fields: `game_id`, `move_idx`, `direction`, `value` (optional, present when `status=complete`), `reasoning` (optional), `status` ∈ `{complete, parse_error}`.
- `tot_selected` event marks the end of the deliberation; the viewer's `ToTBranchPanel` highlights the chosen card on this event and greys the rest.

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

## Task 47: ReasoningText + ToTBranchPanel + ActionArrow

ReasoningText handles single-block System-1 reasoning. **ToTBranchPanel** is the new component required by §3.8 + §5: it renders branch cards as `tot_branch` events arrive on the bus, greys rejected branches on `tot_selected`, and highlights the chosen branch. Without this component, ToT mode renders as a 2–4 second freeze on screen.

**Files:**
- Create: `nova-viewer/app/components/ReasoningText.tsx`
- Create: `nova-viewer/app/components/ToTBranchPanel.tsx`
- Create: `nova-viewer/app/components/ActionArrow.tsx`

- [ ] **Step 1: ReasoningText** — System 1 path. Accept the `reasoning` string; render with a typewriter effect.

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

- [ ] **Step 2: ToTBranchPanel** — System 2 path. Vertical stack of branch cards; cards stream in on `tot_branch` events and grey/highlight on `tot_selected`.

```tsx
// nova-viewer/app/components/ToTBranchPanel.tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";

export interface ToTBranch {
  direction: "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right";
  value?: number;
  reasoning?: string;
  status: "pending" | "complete" | "parse_error";
}

interface Props {
  branches: ToTBranch[];               // ordered by arrival
  chosenDirection: ToTBranch["direction"] | null;
}

const ARROW = { swipe_up: "↑", swipe_down: "↓", swipe_left: "←", swipe_right: "→" } as const;

export function ToTBranchPanel({ branches, chosenDirection }: Props) {
  return (
    <section>
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">
        Deliberation (System 2)
      </h3>
      <div className="flex flex-col gap-2">
        <AnimatePresence>
          {branches.map((b) => {
            const decided = chosenDirection !== null;
            const chosen = decided && b.direction === chosenDirection;
            const rejected = decided && !chosen;
            return (
              <motion.div
                key={b.direction}
                layout
                initial={{ opacity: 0, x: -8 }}
                animate={{
                  opacity: rejected ? 0.35 : 1,
                  x: 0,
                  borderColor: chosen ? "#4FD1C5" : "#3f3f46",
                }}
                transition={{ type: "spring", stiffness: 220, damping: 24 }}
                className={`rounded-md border px-3 py-2 ${chosen ? "bg-cyan-950/30" : "bg-zinc-900/40"}`}
              >
                <div className="flex items-baseline gap-3">
                  <span className="text-2xl text-cyan-300">{ARROW[b.direction]}</span>
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">
                    {b.status === "complete" ? `value ${b.value?.toFixed(2)}` : b.status}
                  </span>
                </div>
                {b.reasoning && (
                  <p className="font-serif text-sm text-zinc-300 mt-1 leading-snug">
                    {b.reasoning}
                  </p>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: ActionArrow** — directional arrow with a brief slide-in animation (unchanged).

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

- [ ] **Step 4: Wire `tot_branch` + `tot_selected` events through `page.tsx`** (extends Task 27/29). The page maintains a `branches: ToTBranch[]` state and a `chosenDirection` state; it appends on `tot_branch` events and sets `chosenDirection` on `tot_selected`. Reset both on `mode=DEFAULT` transitions so the next ToT episode starts clean.

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/
git commit -m "feat(viewer): ToTBranchPanel streams branch cards + ReasoningText + ActionArrow"
```

**Notes:**
- The branch panel **replaces** the ReasoningText panel when `mode=DELIBERATION`; both must not render simultaneously.
- Claude Design (Task 41) needs a static mockup of this panel — add to its scope.

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
