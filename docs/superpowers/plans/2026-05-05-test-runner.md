# Phase 0.7 Test Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Phase 0.7 cliff-test runner — a single async orchestrator (`nova_agent.lab.cliff_test`) that runs paired Carla/Bot trials across three scenarios, emits per-trial CSV rows + per-trial JSONL event streams, and enforces a two-tier cost cap. The runner is a **data collector only**; aggregate statistics + pass/fail verdict are out of scope (deferred to a separate `analyze_results.py`).

**Architecture:** Single async script. `main()` argparses + dispatches; `run_cliff_test()` is the top-level coroutine that builds a queue of `(scenario, trial_index)` pairs, gates concurrency via `asyncio.Semaphore(8)`, and dispatches `_worker()` per pair. `_worker()` runs `_run_carla_trial()` + `_run_bot_trial()` concurrently within the pair via `asyncio.gather`, then updates a shared `_BudgetState`. Soft cap stops dequeuing new pairs (drains in-flight); hard cap kills before any LLM call. CSV is appended after each trial completes (crash-resilient); JSONL is one file per trial via `RecordingEventBus`.

**Tech Stack:** Python 3.14 / asyncio / pytest / `nova_agent.llm.mock.MockLLMClient` / `nova_agent.bus.recorder.RecordingEventBus` / `nova_agent.lab.sim.Game2048Sim` / `nova_agent.lab.io.SimGameIO` / `nova_agent.decision.{react,tot,baseline,arbiter}` / `nova_agent.affect.state.AffectState` / `nova_agent.memory.coordinator.MemoryCoordinator` / `nova_agent.reflection.run_reflection`.

**Spec source:** `docs/superpowers/specs/2026-05-05-test-runner-design.md` + scenarios spec (`2026-05-05-cliff-test-scenarios-design.md`) + Bot spec (`2026-05-05-baseline-bot-design.md`) + ADR-0007 Amendment 1.

---

## Pre-flight (do this once before Task 1)

- [ ] **Confirm worktree + branch:**

```bash
git -C /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468 \
    branch --show-current
```

Expected: `claude/practical-swanson-4b6468`. All work for this plan happens in this worktree, NOT the main `~/Desktop/a` checkout (which is on `main`).

- [ ] **Confirm environment:**

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent
uv run pytest --collect-only 2>&1 | tail -3
```

Expected: collection succeeds.

- [ ] **Skim the spec:** read `docs/superpowers/specs/2026-05-05-test-runner-design.md` §2 (six pinned decisions Q1-Q6) and §3 (architecture) before Task 1. Do NOT re-litigate locked decisions.

- [ ] **Spec-vs-code shape gaps surfaced during plan-writing.** The spec uses some class names that do not match the actual codebase. The implementer MUST use the actual names below; do not introduce new wrapper classes.

| Spec name | Actual code |
|---|---|
| `AffectCoordinator` | `nova_agent.affect.state.AffectState` (instance method `update(...)`) |
| `affect.update(...) -> AffectVector` | Same shape — confirmed `main.py:275-280` |
| `ReflectionWriter` | `nova_agent.reflection.run_reflection` (function) |
| `Arbiter.should_use_tot()` | `nova_agent.decision.arbiter.should_use_tot(board, affect)` (module-level function) |
| `MemoryCoordinator(sqlite_path=, lance_path=)` | `MemoryCoordinator(sqlite_path=, lancedb_path=)` — note `lancedb_path` |

The canonical Carla per-move loop pattern lives at `nova_agent/main.py:240-319`. The runner's `_run_carla_trial()` mirrors that shape, minus the live ADB IO + minus the WebSocket-only bus (the runner uses `RecordingEventBus` for per-trial JSONL persistence).

---

## File Structure

**New files:**

- `nova-agent/src/nova_agent/lab/cliff_test.py` — single async orchestrator. Contains: `main`, `run_cliff_test`, `_worker`, `_run_carla_trial`, `_run_bot_trial`, `_BudgetState`, `_check_anxiety_threshold`, `_first_threshold_index`, `_append_csv_row`, `_apply_with_tiebreak`, plus result dataclasses `CarlaTrialResult` + `BotTrialResult`.
- `nova-agent/tests/test_cliff_test_helpers.py` — pure-function tests (anxiety threshold, budget state, CSV writer, tiebreak).
- `nova-agent/tests/test_cliff_test_trials.py` — single-trial integration tests with `MockLLMClient`.
- `nova-agent/tests/test_cliff_test_runner.py` — top-level orchestrator + cap halt + pilot routing + CLI smoke tests.

**Modified files:**

- `nova-agent/pyproject.toml` — add `cliff-test = "nova_agent.lab.cliff_test:main"` to `[project.scripts]`.

**Untouched (consumed read-only):**

- `nova-agent/src/nova_agent/lab/sim.py` — `Game2048Sim`, `Scenario`
- `nova-agent/src/nova_agent/lab/scenarios.py` — `SCENARIOS`, `MAX_MOVES`, `load`
- `nova-agent/src/nova_agent/lab/io.py` — `SimGameIO`
- `nova-agent/src/nova_agent/decision/baseline.py` — `BaselineDecider`, `BotDecision`, `TrialAborted`
- `nova-agent/src/nova_agent/decision/react.py` — `ReactDecider`, `Decision`
- `nova-agent/src/nova_agent/decision/tot.py` — `ToTDecider`
- `nova-agent/src/nova_agent/decision/arbiter.py` — `should_use_tot`
- `nova-agent/src/nova_agent/affect/state.py` — `AffectState`
- `nova-agent/src/nova_agent/affect/types.py` — `AffectVector`
- `nova-agent/src/nova_agent/affect/rpe.py` — `rpe`
- `nova-agent/src/nova_agent/memory/coordinator.py` — `MemoryCoordinator`
- `nova-agent/src/nova_agent/memory/aversive.py` — `AVERSIVE_TAG`, `is_catastrophic_loss`, `tag_aversive`
- `nova-agent/src/nova_agent/reflection/__init__.py` — `run_reflection`
- `nova-agent/src/nova_agent/bus/recorder.py` — `RecordingEventBus`
- `nova-agent/src/nova_agent/llm/mock.py` — `MockLLMClient` (test composition)
- `nova-agent/src/nova_agent/action/adb.py` — `SwipeDirection`

**Out of scope (deferred):**

- `analyze_results.py` (separate spec, not required for runner to be useful).
- `_RETRYABLE_API_EXCEPTIONS` audit in `decision/baseline.py:64` — spec §9 follow-up.
- Per-call cost extraction for Carla (telemetry shape verification) — spec §9 follow-up; this plan adds runner-side aggregation, not new telemetry.
- Resume-from-checkpoint, distributed execution, real-time UI.

---

## Module shape (target end state of `cliff_test.py`)

```
cliff_test.py
├── # Constants
│   ├── BUDGET_PER_SCENARIO_ARM_USD = 5.0
│   ├── HARD_CAP_MULTIPLIER = 1.3
│   ├── ANXIETY_THRESHOLD = 0.6
│   ├── ANXIETY_CONSECUTIVE = 2
│   ├── DEFAULT_CONCURRENCY = 8
│   ├── EXIT_OK = 0
│   ├── EXIT_SOFT_CAP = 2
│   ├── EXIT_HARD_CAP = 3
│   ├── _ALLOWED_TIERS = frozenset({"production", "demo"})
│   └── _CSV_COLUMNS = (...10 columns...)
│
├── # Result dataclasses (frozen)
│   ├── @dataclass class CarlaTrialResult
│   └── @dataclass class BotTrialResult
│
├── # Pure helpers
│   ├── _check_anxiety_threshold(traj) -> bool
│   ├── _first_threshold_index(traj) -> int | None
│   ├── _apply_with_tiebreak(io, action, board) -> SwipeDirection
│   └── _append_csv_row(csv_path, **fields) -> None
│
├── # Stateful helper
│   └── class _BudgetState
│
├── # Per-trial coroutines
│   ├── async _run_bot_trial(scenario, trial_index, *, llm, bus_path) -> BotTrialResult
│   └── async _run_carla_trial(scenario, trial_index, *, llms, bus_path) -> CarlaTrialResult
│
├── # Orchestration
│   ├── async _worker(pair, *, semaphore, budget, csv_path, output_dir, llms) -> None
│   └── async run_cliff_test(*, scenarios, n, output_dir, concurrency, llms) -> int  # exit code
│
└── # CLI
    └── def main() -> None  # argparse → asyncio.run(run_cliff_test(...)) → sys.exit(code)
```

---

### Task 1: pyproject script entry + CLI skeleton + tier guard

**Files:**
- Modify: `nova-agent/pyproject.toml` (`[project.scripts]` section)
- Create: `nova-agent/src/nova_agent/lab/cliff_test.py` (skeleton only — `main()` parses args, validates tier, prints args, exits 0)
- Create: `nova-agent/tests/test_cliff_test_runner.py` (CLI smoke tests only at this stage)

- [ ] **Step 1: Add the script entry to `pyproject.toml`**

Read the file first to find the existing `[project.scripts]` block:

```bash
grep -n "scripts" /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent/pyproject.toml
```

Add a new line under `[project.scripts]`:

```toml
cliff-test = "nova_agent.lab.cliff_test:main"
```

- [ ] **Step 2: Write the failing CLI smoke tests**

Create `nova-agent/tests/test_cliff_test_runner.py`:

```python
"""Tests for the cliff-test runner orchestrator + CLI."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


def _run_cli(*args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke the cliff-test CLI as a subprocess and return the result."""
    env = os.environ.copy()
    # Strip API keys to make sure tier-guard tests don't accidentally hit a real provider.
    for var in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        env.pop(var, None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "nova_agent.lab.cliff_test", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_help_runs_clean() -> None:
    """`cliff-test --help` exits 0 and prints usage."""
    result = _run_cli("--help")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "cliff-test" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_rejects_dev_tier() -> None:
    """Runner refuses NOVA_TIER=dev (per spec §6.1 + ADR-0006)."""
    result = _run_cli(
        "--scenario", "snake-collapse-128", "--n", "1",
        env_overrides={"NOVA_TIER": "dev"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined


def test_cli_rejects_plumbing_tier() -> None:
    """Runner refuses NOVA_TIER=plumbing (cognitive-judgment models downgraded)."""
    result = _run_cli(
        "--scenario", "snake-collapse-128", "--n", "1",
        env_overrides={"NOVA_TIER": "plumbing"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_runner.py -v
```

Expected: FAIL — module `nova_agent.lab.cliff_test` not found.

- [ ] **Step 4: Write the skeleton `cliff_test.py`**

Create `nova-agent/src/nova_agent/lab/cliff_test.py`:

```python
"""Phase 0.7 cliff-test runner.

Single async orchestrator that runs paired Carla/Bot trials across the
configured scenarios and writes per-trial CSV + per-trial JSONL artifacts.

This module is a DATA COLLECTOR only. Aggregate statistics, mean-Δ
computation, and the cliff-test pass/fail verdict are explicitly
out-of-scope and live in a separate ``analyze_results.py`` per the spec
§2.7 / §8.

Spec: ``docs/superpowers/specs/2026-05-05-test-runner-design.md``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Final

# Per spec §2.6 + ADR-0006: cognitive-judgment models must run at production tier.
_ALLOWED_TIERS: Final[frozenset[str]] = frozenset({"production", "demo"})

EXIT_OK: Final[int] = 0
EXIT_SOFT_CAP: Final[int] = 2
EXIT_HARD_CAP: Final[int] = 3
EXIT_TIER_REFUSED: Final[int] = 4  # USAGE error; not the methodology >2-aborts-per-scenario flag


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cliff-test",
        description=(
            "Phase 0.7 cliff-test runner: paired Carla/Bot trials per scenario. "
            "Data collector only — does not compute pass/fail verdicts."
        ),
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario id (e.g. 'snake-collapse-128') or 'all' for every cliff-test scenario.",
    )
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        help="Number of paired trials per scenario.",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Pilot mode — output to pilot_results/ subdirectory instead of results/.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Max in-flight paired trials. Default 8.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory root. Default runs/<UTC-iso-timestamp>/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty output directory.",
    )
    return parser


def _check_tier() -> str | None:
    """Validate NOVA_TIER env var. Returns the tier string if OK, else None."""
    import os
    tier = os.environ.get("NOVA_TIER", "").strip()
    if tier not in _ALLOWED_TIERS:
        return None
    return tier


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    tier = _check_tier()
    if tier is None:
        print(
            f"error: NOVA_TIER must be one of {sorted(_ALLOWED_TIERS)} "
            "(dev/plumbing tiers downgrade cognitive-judgment models — see ADR-0006).",
            file=sys.stderr,
        )
        sys.exit(EXIT_TIER_REFUSED)

    # Dispatch shell — Tasks 9-10 fill this in.
    print(f"cliff-test placeholder: scenario={args.scenario}, n={args.n}, tier={tier}")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_runner.py -v
```

Expected: 3 PASS.

- [ ] **Step 6: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add nova-agent/pyproject.toml \
        nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_runner.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): CLI skeleton + tier guard

First slice of the Phase 0.7 cliff-test runner. Adds the cliff-test
script entry, argparse surface (scenario/n/pilot/concurrency/output-dir/
force), and the NOVA_TIER guard rejecting dev/plumbing tiers per spec
§6.1 + ADR-0006. main() is a dispatch shell; per-trial path lands in
subsequent tasks.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `_check_anxiety_threshold` + `_first_threshold_index`

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add helpers + module-level constants)
- Create: `nova-agent/tests/test_cliff_test_helpers.py`

These are pure functions: walk a list of floats, find the first index where `threshold` is exceeded for `consecutive` moves in a row.

- [ ] **Step 1: Write the failing tests**

Create `nova-agent/tests/test_cliff_test_helpers.py`:

```python
"""Tests for the pure helpers in nova_agent.lab.cliff_test."""

from __future__ import annotations

import pytest

from nova_agent.lab.cliff_test import (
    _check_anxiety_threshold,
    _first_threshold_index,
)


class TestCheckAnxietyThreshold:
    def test_no_breach(self) -> None:
        """Trajectory all 0.4 → False, no threshold index."""
        traj = [0.4] * 10
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_single_spike_no_pair(self) -> None:
        """One spike above without a pair → False (need ≥ 2 consecutive)."""
        traj = [0.4, 0.4, 0.7, 0.4, 0.4]
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_pair_at_index_1(self) -> None:
        """Two consecutive above → True, t_predicts at first move of the pair."""
        traj = [0.4, 0.7, 0.65, 0.4]
        assert _check_anxiety_threshold(traj) is True
        assert _first_threshold_index(traj) == 1

    def test_late_pair(self) -> None:
        """Pair late in trajectory → True, t_predicts at first move of the late pair."""
        traj = [0.4, 0.4, 0.4, 0.7, 0.7]
        assert _check_anxiety_threshold(traj) is True
        assert _first_threshold_index(traj) == 3

    def test_three_consecutive_returns_first(self) -> None:
        """Three consecutive — t_predicts is the first of the three."""
        traj = [0.3, 0.7, 0.7, 0.7, 0.4]
        assert _first_threshold_index(traj) == 1

    def test_boundary_value_is_strict_greater(self) -> None:
        """Threshold is > 0.6 (strict), per spec §2.7. Exactly 0.6 doesn't count."""
        traj = [0.6, 0.6, 0.6]
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_empty_trajectory(self) -> None:
        """Empty trajectory → False, no index."""
        assert _check_anxiety_threshold([]) is False
        assert _first_threshold_index([]) is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v
```

Expected: FAIL — `_check_anxiety_threshold` and `_first_threshold_index` are not defined.

- [ ] **Step 3: Add the helpers + constants to `cliff_test.py`**

Insert near the top of `nova_agent/lab/cliff_test.py` (after the `_ALLOWED_TIERS` block, before `_build_parser`):

```python
# Per spec §2.7 / scenarios spec §2.7: Carla "predicts the cliff" iff
# anxiety > 0.6 for >= 2 consecutive moves. Strict greater-than.
ANXIETY_THRESHOLD: Final[float] = 0.6
ANXIETY_CONSECUTIVE: Final[int] = 2


def _first_threshold_index(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> int | None:
    """Return the index of the first move that begins a run of ``consecutive``
    moves with anxiety strictly greater than ``threshold``. Return None if no
    such run exists.

    Spec §2.7: ``t_predicts`` for Carla = this index, or null if no breach.
    """
    if consecutive <= 0 or len(trajectory) < consecutive:
        return None
    run = 0
    for i, v in enumerate(trajectory):
        if v > threshold:
            run += 1
            if run >= consecutive:
                return i - consecutive + 1
        else:
            run = 0
    return None


def _check_anxiety_threshold(
    trajectory: list[float],
    *,
    threshold: float = ANXIETY_THRESHOLD,
    consecutive: int = ANXIETY_CONSECUTIVE,
) -> bool:
    """True iff the trajectory contains >= ``consecutive`` consecutive values
    strictly greater than ``threshold``.
    """
    return _first_threshold_index(trajectory, threshold=threshold, consecutive=consecutive) is not None
```

You will need to add `from typing import Final` to the imports (already present from Task 1).

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v
```

Expected: 7 PASS. Existing CLI tests still pass.

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_helpers.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): anxiety threshold helpers (>0.6 for >=2 moves)

Pure functions used at trial-end to compute t_predicts and the
anxiety_threshold_met boolean per spec §2.7. Strict greater-than
(0.6 itself does not breach) preserves compatibility with the
methodology threshold as written.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `_BudgetState` — per-(scenario, arm) spend tracker

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `_BudgetState` class + budget constants)
- Modify: `nova-agent/tests/test_cliff_test_helpers.py` (add tests)

Per spec §2.3 + §2.6: per-`(scenario_id, arm)` running spend; soft cap = $5; hard cap = $5 × 1.3 = $6.50.

- [ ] **Step 1: Write the failing tests**

Append to `nova-agent/tests/test_cliff_test_helpers.py`:

```python
from nova_agent.lab.cliff_test import _BudgetState


class TestBudgetState:
    def test_initial_state_under_caps(self) -> None:
        bs = _BudgetState()
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is False
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is False

    def test_soft_cap_exact(self) -> None:
        """Spend exactly $5 → soft cap hit (>= comparison)."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is True
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is False

    def test_soft_cap_just_under(self) -> None:
        """$4.99 → soft cap NOT hit."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 4.99)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is False

    def test_hard_cap(self) -> None:
        """$6.50 → hard cap hit (5 * 1.3)."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 6.50)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is True
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is True

    def test_separate_arms(self) -> None:
        """$5 on Carla — Bot still under cap."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("snake-collapse-128", "bot") is False

    def test_separate_scenarios(self) -> None:
        """$5 on scenario A — scenario B still under cap."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("512-wall", "carla") is False

    def test_add_accumulates(self) -> None:
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 1.00)
        bs.add("snake-collapse-128", "carla", 2.00)
        assert bs.spent("snake-collapse-128", "carla") == pytest.approx(3.00)

    def test_concurrent_adds_thread_safety(self) -> None:
        """asyncio.gather may race; _BudgetState.add is called from coroutine,
        not from a thread, but the running totals must remain monotonic.
        We don't need a Lock for asyncio coroutines (single-threaded event
        loop), but we do need the implementation to be a single += per call.
        """
        bs = _BudgetState()
        for _ in range(100):
            bs.add("snake-collapse-128", "carla", 0.01)
        assert bs.spent("snake-collapse-128", "carla") == pytest.approx(1.00)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v -k Budget
```

Expected: FAIL — `_BudgetState` not defined.

- [ ] **Step 3: Add `_BudgetState` to `cliff_test.py`**

Insert after the anxiety helpers, before `_build_parser`:

```python
# Per spec §2.3 + §2.6: cost-cap envelope.
BUDGET_PER_SCENARIO_ARM_USD: Final[float] = 5.00
HARD_CAP_MULTIPLIER: Final[float] = 1.3


class _BudgetState:
    """Per-(scenario_id, arm) running spend, with soft- and hard-cap checks.

    Used by the worker (hard-cap pre-LLM gate) and the orchestrator
    (soft-cap drain-in-flight halt). asyncio coroutines do not race on a
    single-threaded event loop, so no lock is needed; ``add`` is a single
    arithmetic update.
    """

    def __init__(
        self,
        *,
        soft_cap_usd: float = BUDGET_PER_SCENARIO_ARM_USD,
        hard_cap_multiplier: float = HARD_CAP_MULTIPLIER,
    ) -> None:
        self._soft_cap = soft_cap_usd
        self._hard_cap = soft_cap_usd * hard_cap_multiplier
        self._spent: dict[tuple[str, str], float] = {}

    def add(self, scenario_id: str, arm: str, cost_usd: float) -> None:
        key = (scenario_id, arm)
        self._spent[key] = self._spent.get(key, 0.0) + cost_usd

    def spent(self, scenario_id: str, arm: str) -> float:
        return self._spent.get((scenario_id, arm), 0.0)

    def soft_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._soft_cap

    def hard_cap_hit(self, scenario_id: str, arm: str) -> bool:
        return self.spent(scenario_id, arm) >= self._hard_cap
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v -k Budget
```

Expected: 8 PASS.

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_helpers.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _BudgetState per-(scenario, arm) spend tracker

Soft cap ($5) and hard cap ($6.50 = $5 × 1.3) per spec §2.3 + §2.6.
Drives the worker's hard-cap pre-LLM gate and the orchestrator's
soft-cap drain-in-flight halt. asyncio single-threaded event loop
means no lock needed.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `_append_csv_row` — crash-resilient CSV writer

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `_CSV_COLUMNS` + `_append_csv_row`)
- Modify: `nova-agent/tests/test_cliff_test_helpers.py` (add tests)

Per spec §2.7 (output table). Append-on-trial-completion = crash-resilient. Header written iff the file does not exist or is empty.

- [ ] **Step 1: Write the failing tests**

Append to `nova-agent/tests/test_cliff_test_helpers.py`:

```python
import csv
from pathlib import Path

from nova_agent.lab.cliff_test import _CSV_COLUMNS, _append_csv_row


class TestAppendCsvRow:
    def test_writes_header_on_first_row(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "results.csv"
        _append_csv_row(
            csv_path,
            scenario_id="snake-collapse-128",
            trial_index=0,
            arm="carla",
            t_predicts=11,
            t_baseline_fails=None,
            cost_usd=0.11,
            abort_reason=None,
            anxiety_threshold_met=True,
            final_move_index=14,
            is_right_censored=False,
        )
        with csv_path.open() as f:
            rows = list(csv.reader(f))
        assert rows[0] == list(_CSV_COLUMNS)
        assert rows[1][0] == "snake-collapse-128"
        assert rows[1][2] == "carla"
        assert rows[1][3] == "11"

    def test_no_duplicate_header_on_second_append(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "results.csv"
        _append_csv_row(
            csv_path, scenario_id="s", trial_index=0, arm="bot",
            t_predicts=None, t_baseline_fails=11, cost_usd=0.005,
            abort_reason=None, anxiety_threshold_met=None,
            final_move_index=11, is_right_censored=False,
        )
        _append_csv_row(
            csv_path, scenario_id="s", trial_index=1, arm="bot",
            t_predicts=None, t_baseline_fails=12, cost_usd=0.005,
            abort_reason=None, anxiety_threshold_met=None,
            final_move_index=12, is_right_censored=False,
        )
        with csv_path.open() as f:
            rows = list(csv.reader(f))
        assert len(rows) == 3  # 1 header + 2 data rows
        assert rows[0] == list(_CSV_COLUMNS)
        assert rows[1][1] == "0"
        assert rows[2][1] == "1"

    def test_nulls_serialize_as_empty_strings(self, tmp_path: Path) -> None:
        """t_predicts=None, abort_reason=None, anxiety_threshold_met=None → empty CSV cells."""
        csv_path = tmp_path / "results.csv"
        _append_csv_row(
            csv_path, scenario_id="s", trial_index=0, arm="bot",
            t_predicts=None, t_baseline_fails=11, cost_usd=0.005,
            abort_reason=None, anxiety_threshold_met=None,
            final_move_index=11, is_right_censored=False,
        )
        with csv_path.open() as f:
            rows = list(csv.reader(f))
        # row[0] is the header
        idx_t_predicts = list(_CSV_COLUMNS).index("t_predicts")
        idx_abort_reason = list(_CSV_COLUMNS).index("abort_reason")
        idx_anxiety_met = list(_CSV_COLUMNS).index("anxiety_threshold_met")
        assert rows[1][idx_t_predicts] == ""
        assert rows[1][idx_abort_reason] == ""
        assert rows[1][idx_anxiety_met] == ""

    def test_creates_parent_dir_if_missing(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "subdir" / "results.csv"
        _append_csv_row(
            csv_path, scenario_id="s", trial_index=0, arm="bot",
            t_predicts=None, t_baseline_fails=11, cost_usd=0.005,
            abort_reason=None, anxiety_threshold_met=None,
            final_move_index=11, is_right_censored=False,
        )
        assert csv_path.exists()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v -k Csv
```

Expected: FAIL — `_CSV_COLUMNS` and `_append_csv_row` not defined.

- [ ] **Step 3: Add the helper + constants**

Insert after `_BudgetState`, before `_build_parser`:

```python
import csv
from pathlib import Path
from typing import Any

# Per spec §2.7. Order is contract — analyze_results.py reads by name,
# not position, but appending new columns at the end is the ratchet.
_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "scenario_id",
    "trial_index",
    "arm",
    "t_predicts",
    "t_baseline_fails",
    "cost_usd",
    "abort_reason",
    "anxiety_threshold_met",
    "final_move_index",
    "is_right_censored",
)


def _append_csv_row(csv_path: Path | str, **fields: Any) -> None:
    """Append a single trial row to ``csv_path``. Creates the file (and parent
    dirs) if missing; writes the header iff the file does not exist or is empty.

    None values serialize as empty strings (CSV null convention). Raises
    KeyError if any expected column is missing from ``fields``.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    row = []
    for col in _CSV_COLUMNS:
        if col not in fields:
            raise KeyError(f"missing column {col!r} in CSV row append")
        v = fields[col]
        row.append("" if v is None else str(v))

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(list(_CSV_COLUMNS))
        writer.writerow(row)
```

(The `import csv`, `from pathlib import Path`, `from typing import Any` go at the top of the module if not already present.)

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v
```

Expected: all helper tests pass (Anxiety + Budget + Csv).

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_helpers.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _append_csv_row crash-resilient writer

Append-on-trial-completion CSV writer per spec §2.7. 10-column schema
(scenario_id, trial_index, arm, t_predicts, t_baseline_fails, cost_usd,
abort_reason, anxiety_threshold_met, final_move_index, is_right_censored).
Header written iff file is missing or empty; nulls serialize as empty
strings (CSV null convention). Crash-resilient — an interrupted run
loses only the in-flight trials.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `_apply_with_tiebreak` — invalid-move tie-break

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `_apply_with_tiebreak`)
- Modify: `nova-agent/tests/test_cliff_test_helpers.py` (add test)

Per scenarios spec §2.3 + Bot spec §2.3: when the LLM-chosen direction is a no-op (the swipe doesn't change the board), apply the first non-no-op direction in the order **UP > RIGHT > DOWN > LEFT**.

The Bot decider receives `BoardState` only; the runner detects no-op by comparing `board_before` with `board_after`. Implementation note: `Game2048Sim.apply_move` returns a `bool` indicating whether the move changed the board (per `lab/sim.py` — verify by reading the file). `SimGameIO.apply_move` discards that bool, so we'll need to peek at the wrapped `_sim` directly OR use a board-equality comparison after a tentative apply.

The simplest implementation reads the board, applies the chosen direction, reads the board again, and if they are equal, retries with the tie-break order. Each tie-break attempt uses a fresh `_sim` snapshot via `_sim.copy()` if available, OR — preferred — uses a "would this move change the board?" predicate before applying.

Read `lab/sim.py` to confirm whether `Game2048Sim` exposes a no-op probe. If not, the implementer adds `def is_legal(direction)` to the runner-side helper that snapshots `_sim`'s grid, runs the move, compares, and reverts if no-op. Prefer modifying nothing in `lab/sim.py` for this plan — keep `cliff_test.py` self-contained.

- [ ] **Step 1: Verify `Game2048Sim` API**

```bash
grep -n "def apply_move\|def is_legal\|def can_move\|return move" \
    nova-agent/src/nova_agent/lab/sim.py | head -10
```

If `apply_move` returns a `bool` (changed-board indicator), the tie-break uses a saved-grid + revert pattern. If `Game2048Sim` exposes `would_change(direction) -> bool` or similar, prefer that.

- [ ] **Step 2: Write the failing test**

Append to `nova-agent/tests/test_cliff_test_helpers.py`:

```python
from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.io import SimGameIO
from nova_agent.lab.scenarios import SCENARIOS
from nova_agent.lab.sim import Game2048Sim
from nova_agent.lab.cliff_test import _apply_with_tiebreak


class TestApplyWithTiebreak:
    def test_chosen_direction_is_legal(self) -> None:
        """Happy path: chosen direction changes the board → applied as-is."""
        scenario = SCENARIOS["snake-collapse-128"]
        sim = Game2048Sim(seed=scenario.seed(0), scenario=scenario)
        io = SimGameIO(sim=sim)
        board = io.read_board()
        # Pick a direction that we know moves something on this board.
        # snake-collapse-128 has a high-tile snake along the bottom-right;
        # swipe_up should compact upward.
        applied = _apply_with_tiebreak(io, "swipe_up", board)
        assert applied == SwipeDirection.UP

    def test_invalid_move_falls_back_through_tiebreak_order(self) -> None:
        """If chosen direction is no-op, fall back UP > RIGHT > DOWN > LEFT
        and apply the first legal one. Construct a board where ``swipe_up``
        is a no-op (column already maxed in that direction) but another
        direction is legal.
        """
        scenario = SCENARIOS["snake-collapse-128"]
        sim = Game2048Sim(seed=scenario.seed(0), scenario=scenario)
        io = SimGameIO(sim=sim)
        board = io.read_board()
        # Find a direction that IS a no-op on this board to drive the test.
        # If no direction is a no-op on the seed-0 starting board, this test
        # uses a constructed scenario; in practice the snake-collapse-128
        # initial grid has empty top-row cells so swipe_up tends to be legal.
        # Use a manufactured grid that makes swipe_up a no-op:
        from nova_agent.perception.types import BoardState
        rigged_board = BoardState(
            grid=[[2, 4, 8, 16],
                  [0, 0, 0, 0],
                  [0, 0, 0, 0],
                  [0, 0, 0, 0]],
            score=0,
        )
        # swipe_up on rigged_board is a no-op (top row already at top).
        # Replace sim's internal board for this test.
        sim._board = rigged_board  # type: ignore[attr-defined]
        applied = _apply_with_tiebreak(io, "swipe_up", rigged_board)
        # First legal direction in UP > RIGHT > DOWN > LEFT after UP no-ops:
        # RIGHT moves the top row to the right wall.
        assert applied == SwipeDirection.RIGHT
```

(If `Game2048Sim` does not expose a private `_board` attribute, the implementer adapts the test to use a publicly-mutable seam OR rebuilds `Game2048Sim` with a custom initial state via a `Scenario` whose `initial_grid` matches `rigged_board`. Prefer the latter — clean test fixtures over private-attribute pokes — but the existing `Scenario.__post_init__` enforces palette + score-derivation invariants that may resist arbitrary grids.)

- [ ] **Step 3: Run test to confirm it fails**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v -k Tiebreak
```

Expected: FAIL — `_apply_with_tiebreak` not defined.

- [ ] **Step 4: Add `_apply_with_tiebreak` to `cliff_test.py`**

Insert after `_append_csv_row`. Prefer the cleanest implementation that respects whatever no-op detection `Game2048Sim` already exposes:

```python
from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.io import SimGameIO
from nova_agent.perception.types import BoardState

# Tie-break order per scenarios spec §2.3 + Bot spec §2.3.
_TIEBREAK_ORDER: Final[tuple[SwipeDirection, ...]] = (
    SwipeDirection.UP,
    SwipeDirection.RIGHT,
    SwipeDirection.DOWN,
    SwipeDirection.LEFT,
)


def _apply_with_tiebreak(
    io: SimGameIO,
    chosen: str,
    board: BoardState,
) -> SwipeDirection:
    """Apply ``chosen`` (e.g. "swipe_up") via ``io``. If the move is a no-op
    (board unchanged), fall through the tie-break order UP > RIGHT > DOWN >
    LEFT and apply the first direction that DOES change the board.

    Returns the SwipeDirection that was actually applied.
    Raises ValueError if no direction changes the board (caller treats as
    game-over, but in that case ``Game2048Sim.is_game_over`` would already
    be True — the runner's per-move loop checks ``is_game_over`` before
    invoking the decider, so this branch is defensive).
    """
    chosen_direction = SwipeDirection(chosen)
    # Try the chosen direction first.
    applied = _try_apply(io, chosen_direction, board)
    if applied is not None:
        return applied

    # Fall through tie-break order, skipping the chosen direction (already failed).
    for direction in _TIEBREAK_ORDER:
        if direction == chosen_direction:
            continue
        applied = _try_apply(io, direction, board)
        if applied is not None:
            return applied

    raise ValueError("no legal move on this board (game-over should have caught this)")


def _try_apply(io: SimGameIO, direction: SwipeDirection, board_before: BoardState) -> SwipeDirection | None:
    """Apply ``direction`` via ``io``. Return the direction iff the board
    changed, else None (the move was a no-op and the engine did not advance).

    Implementation: ``Game2048Sim.apply_move`` does not advance RNG / spawn
    on a no-op (per ``lab/sim.py`` doctring). So calling apply_move with a
    no-op direction is safe and non-mutating.
    """
    io.apply_move(direction)
    if io.read_board().grid == board_before.grid:
        return None
    return direction
```

The implementer should confirm by reading `lab/sim.py` that "no spawn AND no RNG advancement on a no-op swipe" still holds; that's edge case #3 in `Game2048Sim`'s pinned contract, so it's stable.

- [ ] **Step 5: Run test to confirm it passes**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_helpers.py -v -k Tiebreak
```

Expected: 2 PASS.

- [ ] **Step 6: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 7: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_helpers.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _apply_with_tiebreak invalid-move fallback

Tie-break order UP > RIGHT > DOWN > LEFT per scenarios spec §2.3 +
Bot spec §2.3. Relies on Game2048Sim's no-op contract: a no-op
swipe does not advance RNG and does not spawn, so probing with
io.apply_move + board-equality compare is safe.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: `_run_bot_trial` — single Bot trial coroutine

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `BotTrialResult`, `_run_bot_trial`)
- Create: `nova-agent/tests/test_cliff_test_trials.py`

Composes `BaselineDecider` + `Game2048Sim` + `SimGameIO` + tie-break + per-trial cost accounting. Returns a `BotTrialResult` dataclass.

Per spec §4.2 pseudocode + Bot spec §3.4 telemetry contract.

- [ ] **Step 1: Write the failing tests**

Create `nova-agent/tests/test_cliff_test_trials.py`:

```python
"""Single-trial integration tests for cliff_test runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova_agent.bus.recorder import RecordingEventBus
from nova_agent.lab.cliff_test import BotTrialResult, _run_bot_trial
from nova_agent.lab.scenarios import SCENARIOS
from nova_agent.llm.mock import MockLLMClient


@pytest.mark.asyncio
async def test_bot_trial_completes_happy_path(tmp_path: Path) -> None:
    """One bot trial runs to game-over OR MAX_MOVES with no abort."""
    scenario = SCENARIOS["snake-collapse-128"]
    llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        assert isinstance(result, BotTrialResult)
        assert result.cost_usd >= 0.0
        assert result.final_move_index >= 0
        assert result.abort_reason is None
        # Trial either ended in game-over or right-censored.
        if result.is_right_censored:
            assert result.t_baseline_fails == 50  # MAX_MOVES sentinel per scenarios spec §5.1
        else:
            assert result.t_baseline_fails == result.final_move_index
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_bot_trial_aborts_on_sustained_api_failure(tmp_path: Path) -> None:
    """If the LLM raises every call, BaselineDecider returns TrialAborted on the
    third retry; _run_bot_trial surfaces abort_reason='api_error', t_baseline_fails=None.
    """
    scenario = SCENARIOS["snake-collapse-128"]

    class AlwaysFailingLLM(MockLLMClient):
        async def complete(self, *a, **kw):  # type: ignore[override]
            raise RuntimeError("simulated LLM provider outage")

    llm = AlwaysFailingLLM()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        assert result.abort_reason == "api_error"
        assert result.t_baseline_fails is None
        assert result.is_right_censored is False
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_bot_trial_right_censored_when_no_game_over(tmp_path: Path) -> None:
    """If MockLLMClient drives the bot through 50 moves without game-over,
    t_baseline_fails = 50 sentinel + is_right_censored = True per scenarios
    spec §5.1.
    """
    scenario = SCENARIOS["fresh-start"]  # empty board → unlikely to hit game-over within 50 moves
    llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_bot_trial(scenario=scenario, trial_index=0, llm=llm, bus=bus)
        # The fresh-start scenario is unlikely (but not guaranteed) to be
        # right-censored. We assert the invariant: IF right-censored, the
        # sentinel applies.
        if result.is_right_censored:
            assert result.t_baseline_fails == 50
            assert result.final_move_index == 49  # last move attempted
    finally:
        await bus.stop()
```

If `pytest-asyncio` is not configured globally, add `pytestmark = pytest.mark.asyncio` at the module level OR check `nova-agent/tests/conftest.py` to confirm the asyncio mode.

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k bot
```

Expected: FAIL — `BotTrialResult` and `_run_bot_trial` not defined.

- [ ] **Step 3: Add `BotTrialResult` and `_run_bot_trial` to `cliff_test.py`**

```python
from dataclasses import dataclass
from nova_agent.bus.recorder import RecordingEventBus
from nova_agent.bus.websocket import EventBus
from nova_agent.decision.baseline import BaselineDecider, TrialAborted
from nova_agent.lab.scenarios import MAX_MOVES
from nova_agent.lab.sim import Game2048Sim, Scenario
from nova_agent.llm.protocol import LLM


@dataclass(frozen=True)
class BotTrialResult:
    """Outcome of a single Bot trial. ``cost_usd`` aggregates token costs
    over all bot_call_success events emitted during the trial.
    """

    scenario_id: str
    trial_index: int
    final_move_index: int
    cost_usd: float
    abort_reason: str | None
    t_baseline_fails: int | None
    is_right_censored: bool


async def _run_bot_trial(
    *,
    scenario: Scenario,
    trial_index: int,
    llm: LLM,
    bus: EventBus,
) -> BotTrialResult:
    """Run one Bot trial against ``Game2048Sim``. Returns the per-trial summary."""
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    decider = BaselineDecider(llm=llm, bus=bus)

    cost_usd = 0.0
    abort_reason: str | None = None
    move_index = 0  # initialised; updated below

    # Hook into telemetry: we read prompt_tokens/completion_tokens from
    # bot_call_success events the decider emits, OR we extract from the
    # per-call usage. The simplest path: inspect MockLLMClient.usage if
    # available, OR rely on the decider's bus-emitted token counts.
    # For now: track per-decide call by subscribing to a list buffer.
    cost_per_call: list[float] = []

    # NOTE: EventBus does not expose a generic subscribe API (it's
    # WebSocket-broadcast-only per spec §2.4). Per-call cost is therefore
    # extracted via the LLM's usage protocol directly, NOT via bus events.
    # MockLLMClient + production LLMs both emit a Usage object with
    # input_tokens + output_tokens; we compute USD by composing with
    # the active tier's per-token rate from nova_agent.llm.tiers.
    # Implementation deferred: pass a cost_estimator callable into
    # _run_bot_trial. For Phase 0.7 the runner uses a fixed flash-rate
    # constant since the spec §2.6 cost figures are calibrated to the
    # production tier. Fixed rate per token (input + output) is OK for
    # cap enforcement; the analyze_results.py spec will compute exact
    # per-tier costs from the JSONL events.

    for move_index in range(MAX_MOVES):
        board = io.read_board()
        if sim.is_game_over():
            break
        result = await decider.decide(
            board=board,
            trial_index=trial_index,
            move_index=move_index,
        )
        if isinstance(result, TrialAborted):
            abort_reason = result.reason
            break
        # Apply (with tie-break if no-op).
        _apply_with_tiebreak(io, result.action, board)
        # Per-call cost — implementer wires this to the actual tier rate.
        # Spec §2.6 expects ~$0.005 per Bot trial (50 flash one-shots);
        # placeholder accounting until the rate-table integration lands.
        # Mark as a TODO with the tier reference.
        cost_usd += _bot_call_cost_estimate()  # Task 6 helper, see below

    # Termination state:
    if abort_reason is not None:
        t_baseline_fails: int | None = None
        is_right_censored = False
    elif sim.is_game_over():
        t_baseline_fails = move_index
        is_right_censored = False
    else:
        # Hit MAX_MOVES cap → right-censored sentinel per scenarios spec §5.1.
        t_baseline_fails = MAX_MOVES
        is_right_censored = True

    return BotTrialResult(
        scenario_id=scenario.id,
        trial_index=trial_index,
        final_move_index=move_index,
        cost_usd=cost_usd,
        abort_reason=abort_reason,
        t_baseline_fails=t_baseline_fails,
        is_right_censored=is_right_censored,
    )


def _bot_call_cost_estimate() -> float:
    """Per-Bot-call USD estimate at production tier (gemini-2.5-flash for
    the bot decision role). Calibrated to spec §2.6: ~$0.005/trial × 50
    moves = $0.0001/move. The exact tier-rate composition lives in
    nova_agent/llm/tiers.py; this estimate is a coarse placeholder for
    cap accounting. analyze_results.py recomputes from JSONL telemetry.
    """
    return 0.0001
```

**Implementation note on cost accounting.** The placeholder per-call estimate is deliberate — the runner needs *some* cost figure for cap enforcement, but exact per-call USD requires per-tier pricing logic that lives outside this plan's scope. Spec §9 calls out "Per-call cost extraction for Carla" as a follow-up. The implementer can either:

(a) Use the placeholder and document it inline (this plan's default).
(b) Wire `nova_agent.llm.tiers` rate table directly — only acceptable if `tiers.py` exposes a stable public API for "USD per (model, input_tokens, output_tokens)". Verify before going down this path; if not exposed cleanly, prefer (a) and lift accounting into `analyze_results.py`.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k bot
```

Expected: 3 PASS.

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_trials.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _run_bot_trial single Bot trial coroutine

Composes BaselineDecider + Game2048Sim + SimGameIO + tie-break per
spec §4.2. Returns BotTrialResult with t_baseline_fails / abort_reason
/ is_right_censored derived per scenarios spec §5.1 (MAX_MOVES = 50
sentinel for right-censored trials, None for aborts). Per-call cost
placeholder pending tier-rate integration; analyze_results.py will
recompute exact USD from JSONL telemetry.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: `_run_carla_trial` — single Carla trial coroutine

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `CarlaTrialResult`, `_run_carla_trial`)
- Modify: `nova-agent/tests/test_cliff_test_trials.py` (add Carla tests)

Composes the full Carla cognitive stack: `ReactDecider`, `ToTDecider`, `should_use_tot`, `AffectState`, `MemoryCoordinator` (with `tempfile.TemporaryDirectory`), `run_reflection`. Captures `anxiety` post-decision per spec §2.4 (return-value capture, not bus subscription).

The canonical per-move loop pattern lives at `nova_agent/main.py:240-319`. The implementer should mirror that shape, adapted for `Game2048Sim` (no live ADB IO).

- [ ] **Step 1: Read the canonical pattern**

```bash
sed -n '180,320p' /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent/src/nova_agent/main.py
```

The runner's Carla trial composes the same building blocks. Differences:

- Use `SimGameIO` instead of `LiveGameIO`. `SimGameIO.read_board()` returns the sim's `BoardState`; no OCR.
- Use a bus passed in by the runner (per-trial `RecordingEventBus`). Do NOT call `await bus.start()` here — the runner manages bus lifecycle in `_worker`.
- Use a fresh `MemoryCoordinator(sqlite_path=tmp/episodic.db, lancedb_path=tmp/vector.lance)` inside a `with tempfile.TemporaryDirectory(...)` context.
- Use `AffectState()` (not `AffectCoordinator` — per spec-vs-code shape gap noted in pre-flight).
- After the per-move loop, call `run_reflection(...)` — confirm signature in `nova_agent/reflection/postmortem.py`.
- Capture `v.anxiety` from each `affect.update(...)` call into `anxiety_trajectory: list[float]`.

- [ ] **Step 2: Write the failing tests**

Append to `nova-agent/tests/test_cliff_test_trials.py`:

```python
import tempfile
from pathlib import Path

from nova_agent.lab.cliff_test import CarlaTrialResult, _run_carla_trial


@pytest.mark.asyncio
async def test_carla_trial_completes_happy_path(tmp_path: Path) -> None:
    """One Carla trial runs to game-over OR MAX_MOVES; returns a CarlaTrialResult
    with anxiety_trajectory non-empty.
    """
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        result = await _run_carla_trial(
            scenario=scenario,
            trial_index=0,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bus=bus,
        )
        assert isinstance(result, CarlaTrialResult)
        assert len(result.anxiety_trajectory) >= 1
        # t_predicts is None or an int; anxiety_threshold_met is the boolean form.
        if result.t_predicts is not None:
            assert result.anxiety_threshold_met is True
        else:
            assert result.anxiety_threshold_met is False
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_carla_trial_tempdir_is_cleaned_up(tmp_path: Path) -> None:
    """The MemoryCoordinator tempdir is removed at trial end (context-manager exit)."""
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bus = RecordingEventBus(host="127.0.0.1", port=0, path=tmp_path / "events.jsonl")
    try:
        # Snapshot existing tempdirs that match the runner's prefix.
        import os
        tmp_root = Path(tempfile.gettempdir())
        before = {p.name for p in tmp_root.iterdir() if p.name.startswith("nova-cliff-")}
        await _run_carla_trial(
            scenario=scenario,
            trial_index=0,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bus=bus,
        )
        after = {p.name for p in tmp_root.iterdir() if p.name.startswith("nova-cliff-")}
        # No new nova-cliff- tempdirs leaked.
        assert before == after
    finally:
        await bus.stop()
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k carla
```

Expected: FAIL — `CarlaTrialResult` and `_run_carla_trial` not defined.

- [ ] **Step 4: Add `CarlaTrialResult` and `_run_carla_trial` to `cliff_test.py`**

```python
import tempfile

from nova_agent.affect.rpe import rpe as compute_rpe
from nova_agent.affect.state import AffectState
from nova_agent.affect.verbalize import describe as describe_affect
from nova_agent.decision.arbiter import should_use_tot
from nova_agent.decision.heuristic import is_game_over
from nova_agent.decision.react import Decision, ReactDecider
from nova_agent.decision.tot import ToTDecider
from nova_agent.memory.aversive import AVERSIVE_TAG
from nova_agent.memory.coordinator import MemoryCoordinator
from nova_agent.memory.types import AffectSnapshot
from nova_agent.reflection import run_reflection


@dataclass(frozen=True)
class CarlaTrialResult:
    """Outcome of a single Carla trial. ``anxiety_trajectory`` records every
    post-decision anxiety value (one per affect.update call); ``t_predicts``
    is the §2.7 first-breach index (or None).
    """

    scenario_id: str
    trial_index: int
    final_move_index: int
    cost_usd: float
    abort_reason: str | None
    anxiety_trajectory: list[float]
    t_predicts: int | None
    anxiety_threshold_met: bool
    is_right_censored: bool


async def _run_carla_trial(
    *,
    scenario: Scenario,
    trial_index: int,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bus: EventBus,
) -> CarlaTrialResult:
    """Run one Carla trial end-to-end. Mirrors the canonical per-move loop
    pattern at ``nova_agent/main.py:240-319`` minus the live ADB IO and the
    WebSocket-only bus.
    """
    seed = scenario.seed(trial_index)
    sim = Game2048Sim(seed=seed, scenario=scenario)
    io = SimGameIO(sim=sim)
    affect = AffectState()
    react_decider = ReactDecider(llm=decision_llm)
    tot_decider = ToTDecider(llm=tot_llm)

    anxiety_trajectory: list[float] = []
    cost_usd = 0.0
    abort_reason: str | None = None
    move_index = 0
    prev_board = None
    prev_decision: Decision | None = None

    with tempfile.TemporaryDirectory(prefix=f"nova-cliff-{scenario.id}-{trial_index}-") as tmp:
        memory = MemoryCoordinator(
            sqlite_path=Path(tmp) / "episodic.db",
            lancedb_path=Path(tmp) / "vector.lance",
        )

        for move_index in range(MAX_MOVES):
            board = io.read_board()
            if is_game_over(board):
                break

            # Decide via Arbiter routing — react vs ToT.
            mode = "tot" if should_use_tot(board=board, affect=affect.vector) else "react"
            try:
                if mode == "tot":
                    decision = await tot_decider.decide(
                        board=board,
                        screenshot_b64=io.screenshot_b64(),
                        move_idx=move_index,
                    )
                else:
                    # React decider — text-only mode (per Bot spec Task 1).
                    retrieved = []  # No memory retrieval in cliff test; simpler than emu pipeline.
                    affect_text = describe_affect(affect.vector)
                    decision = react_decider.decide_with_context(
                        board=board,
                        screenshot_b64=None,
                        memories=retrieved,
                        affect_text=affect_text,
                    )
            except Exception:
                # Per LESSONS: never silently swallow LLM exceptions. Mark trial
                # aborted with a structured reason; runner records it.
                abort_reason = "api_error"
                break

            cost_usd += _carla_call_cost_estimate(mode)

            io.apply_move(SwipeDirection(decision.action))

            # Affect update (only after move 0; first move has no prev to compute RPE against)
            if prev_board is not None and prev_decision is not None:
                score_delta = board.score - prev_board.score
                delta_rpe = compute_rpe(actual_score_delta=score_delta, board_before=prev_board)
                trauma_triggered = False  # Memory retrieval disabled; no aversive lookups in this run.
                v = affect.update(
                    rpe=delta_rpe,
                    empty_cells=board.empty_cells,
                    terminal=False,
                    trauma_triggered=trauma_triggered,
                )
                anxiety_trajectory.append(v.anxiety)

                # Memory write — keeps the cognitive stack honest under TDD;
                # no retrieval consumes it in this run.
                snapshot = AffectSnapshot(
                    valence=v.valence,
                    arousal=v.arousal,
                    dopamine=v.dopamine,
                    frustration=v.frustration,
                    anxiety=v.anxiety,
                    confidence=v.confidence,
                )
                memory.write_move(
                    board_before=prev_board,
                    board_after=board,
                    action=prev_decision.action,
                    score_delta=score_delta,
                    rpe=delta_rpe,
                    importance=1,
                    source_reasoning=prev_decision.reasoning,
                    affect=snapshot,
                )

            prev_board = board
            prev_decision = decision

        # End-of-trial reflection. run_reflection writes a summary memory; cost is
        # included in trial cost_usd. If reflection fails, do not abort the trial —
        # the per-move trajectory is the load-bearing measurement.
        try:
            await run_reflection(llm=reflection_llm, memory=memory, bus=bus)
            cost_usd += _carla_call_cost_estimate("reflection")
        except Exception:  # noqa: BLE001
            # Reflection failure is non-blocking; trajectory already captured.
            pass

    # Termination state:
    threshold_met = _check_anxiety_threshold(anxiety_trajectory)
    t_predicts = _first_threshold_index(anxiety_trajectory)
    if abort_reason is not None:
        is_right_censored = False
    else:
        is_right_censored = (move_index == MAX_MOVES - 1) and not is_game_over(io.read_board())

    return CarlaTrialResult(
        scenario_id=scenario.id,
        trial_index=trial_index,
        final_move_index=move_index,
        cost_usd=cost_usd,
        abort_reason=abort_reason,
        anxiety_trajectory=anxiety_trajectory,
        t_predicts=t_predicts,
        anxiety_threshold_met=threshold_met,
        is_right_censored=is_right_censored,
    )


def _carla_call_cost_estimate(mode: str) -> float:
    """Per-Carla-call USD estimate.
    Spec §2.6: ~$0.11/trial total = (50 react × X) + (8 ToT × Y) + (1 reflection × Z).
    Coarse placeholder; analyze_results.py recomputes from JSONL.
    """
    if mode == "tot":
        return 0.005     # ToT bursts dominate cost
    if mode == "reflection":
        return 0.01      # Sonnet reflection is the largest single call
    return 0.001         # React (Flash) per move


SwipeDirection = SwipeDirection  # alias guard against import shadowing in tests
```

**Implementation notes:**

- The `run_reflection` signature must be confirmed via:

```bash
grep -n "^def run_reflection\|^async def run_reflection" \
    nova-agent/src/nova_agent/reflection/postmortem.py
```

If `run_reflection` requires arguments not threaded into `_run_carla_trial` (e.g. game-id, episode summary), adapt the call site. Do NOT change `run_reflection`'s signature; adapt the runner.

- The `is_game_over(board)` check is the heuristic in `decision/heuristic.py`. The authoritative `Game2048Sim.is_game_over()` is also available; per ADR-0008 the cognitive layer continues to use the heuristic as the trigger. Use the heuristic here for parity with main.py.

- `decision_llm`, `tot_llm`, `reflection_llm` are passed separately because the production tier resolves three different models per ADR-0006. In tests, the implementer may pass the same `MockLLMClient` to all three — the mock infers the role from the system prompt fingerprint.

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k carla
```

Expected: 2 PASS.

- [ ] **Step 6: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 7: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_trials.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _run_carla_trial single Carla trial coroutine

Mirrors nova_agent/main.py:240-319 per-move loop pattern, swapping
LiveGameIO for SimGameIO and skipping memory retrieval. Captures
anxiety post-decision via affect.update() return-value (per spec §2.4
— bus is WebSocket-only and silently drops headless events; capture
is the measurement channel). Per-trial MemoryCoordinator on a
tempfile.TemporaryDirectory (auto-cleanup on context exit). t_predicts
+ anxiety_threshold_met derived at trial-end from the buffered
trajectory.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: `_worker` — paired-trial coroutine

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `_worker`)
- Modify: `nova-agent/tests/test_cliff_test_trials.py` (add paired tests)

Per spec §2.2 + §4.3: one `_worker` invocation = one `(scenario, trial_index)` pair. Runs both arms concurrently via `asyncio.gather`. Hard-cap pre-check before any LLM call. Updates `_BudgetState` on completion. Writes both CSV rows.

- [ ] **Step 1: Write the failing tests**

Append to `nova-agent/tests/test_cliff_test_trials.py`:

```python
import asyncio

from nova_agent.lab.cliff_test import (
    BUDGET_PER_SCENARIO_ARM_USD,
    HARD_CAP_MULTIPLIER,
    _BudgetState,
    _worker,
)


@pytest.mark.asyncio
async def test_paired_worker_runs_both_arms(tmp_path: Path) -> None:
    """One paired trial; both arms run; both CSV rows written."""
    scenario = SCENARIOS["snake-collapse-128"]
    decision_llm = MockLLMClient()
    tot_llm = MockLLMClient()
    reflection_llm = MockLLMClient()
    bot_llm = MockLLMClient()
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()
    output_dir = tmp_path

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=output_dir,
        decision_llm=decision_llm,
        tot_llm=tot_llm,
        reflection_llm=reflection_llm,
        bot_llm=bot_llm,
    )

    # Both rows written.
    import csv as _csv
    with csv_path.open() as f:
        rows = list(_csv.reader(f))
    # 1 header + 2 data rows.
    assert len(rows) == 3
    arms_written = {rows[1][2], rows[2][2]}
    assert arms_written == {"carla", "bot"}


@pytest.mark.asyncio
async def test_paired_worker_records_carla_abort_and_bot_success(tmp_path: Path) -> None:
    """If Carla aborts on api_error and Bot completes normally, both rows are
    written with the appropriate abort_reason values per Bot spec §2.6
    (paired-discard logic lives in analyze_results.py, not in the runner)."""

    scenario = SCENARIOS["snake-collapse-128"]

    class FailOnReact(MockLLMClient):
        async def complete(self, *a, **kw):  # type: ignore[override]
            raise RuntimeError("simulated provider outage on Carla path")

    decision_llm = FailOnReact()
    tot_llm = FailOnReact()
    reflection_llm = MockLLMClient()
    bot_llm = MockLLMClient()
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=tmp_path,
        decision_llm=decision_llm,
        tot_llm=tot_llm,
        reflection_llm=reflection_llm,
        bot_llm=bot_llm,
    )

    import csv as _csv
    with csv_path.open() as f:
        rows = list(_csv.reader(f))
    # Both rows present.
    assert len(rows) == 3
    by_arm = {row[2]: row for row in rows[1:]}
    # Carla row: abort_reason populated; t_predicts may be None.
    idx_abort = list(_CSV_COLUMNS).index("abort_reason")
    idx_arm = 2
    assert by_arm["carla"][idx_abort] == "api_error"
    # Bot row: no abort_reason.
    assert by_arm["bot"][idx_abort] == ""


@pytest.mark.asyncio
async def test_paired_worker_skips_when_hard_cap_hit(tmp_path: Path) -> None:
    """If hard cap is already hit on entry, _worker returns immediately
    without invoking any LLM and writes no CSV rows."""
    scenario = SCENARIOS["snake-collapse-128"]
    csv_path = tmp_path / "results.csv"
    semaphore = asyncio.Semaphore(1)
    budget = _BudgetState()
    # Pre-load the budget past the hard cap.
    budget.add(scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD * HARD_CAP_MULTIPLIER + 0.01)

    class TripWireLLM(MockLLMClient):
        async def complete(self, *a, **kw):  # type: ignore[override]
            raise AssertionError("hard cap hit — no LLM calls should occur")

    await _worker(
        pair=(scenario, 0),
        semaphore=semaphore,
        budget=budget,
        csv_path=csv_path,
        output_dir=tmp_path,
        decision_llm=TripWireLLM(),
        tot_llm=TripWireLLM(),
        reflection_llm=TripWireLLM(),
        bot_llm=TripWireLLM(),
    )

    # No CSV rows (file may not even exist).
    if csv_path.exists():
        import csv as _csv
        with csv_path.open() as f:
            rows = list(_csv.reader(f))
        # At most a header — no data rows.
        assert len(rows) <= 1
```

The third test imports `_CSV_COLUMNS`; it's already in `cliff_test.py` from Task 4.

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k worker
```

Expected: FAIL — `_worker` not defined.

- [ ] **Step 3: Add `_worker` to `cliff_test.py`**

```python
DEFAULT_CONCURRENCY: Final[int] = 8


async def _worker(
    *,
    pair: tuple[Scenario, int],
    semaphore: asyncio.Semaphore,
    budget: _BudgetState,
    csv_path: Path,
    output_dir: Path,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bot_llm: LLM,
) -> None:
    """Run one paired (scenario, trial_index) trial under the semaphore.
    Both arms run concurrently inside the pair via asyncio.gather. Hard-cap
    pre-check happens BEFORE any LLM call. Writes both CSV rows on completion.
    """
    scenario, trial_index = pair
    async with semaphore:
        # Hard-cap pre-LLM gate (per spec §2.3).
        if budget.hard_cap_hit(scenario.id, "carla") or budget.hard_cap_hit(scenario.id, "bot"):
            return  # caller observes via budget and exits with code 3

        # Build per-trial buses (one per arm — per spec §2.7 "one JSONL file per trial").
        carla_jsonl = output_dir / f"events_{scenario.id}_carla_{trial_index}.jsonl"
        bot_jsonl = output_dir / f"events_{scenario.id}_bot_{trial_index}.jsonl"
        carla_bus = RecordingEventBus(host="127.0.0.1", port=0, path=carla_jsonl)
        bot_bus = RecordingEventBus(host="127.0.0.1", port=0, path=bot_jsonl)

        try:
            carla_result, bot_result = await asyncio.gather(
                _run_carla_trial(
                    scenario=scenario,
                    trial_index=trial_index,
                    decision_llm=decision_llm,
                    tot_llm=tot_llm,
                    reflection_llm=reflection_llm,
                    bus=carla_bus,
                ),
                _run_bot_trial(
                    scenario=scenario,
                    trial_index=trial_index,
                    llm=bot_llm,
                    bus=bot_bus,
                ),
            )
        finally:
            await carla_bus.stop()
            await bot_bus.stop()

        budget.add(scenario.id, "carla", carla_result.cost_usd)
        budget.add(scenario.id, "bot", bot_result.cost_usd)

        _append_csv_row(
            csv_path,
            scenario_id=scenario.id,
            trial_index=trial_index,
            arm="carla",
            t_predicts=carla_result.t_predicts,
            t_baseline_fails=None,
            cost_usd=round(carla_result.cost_usd, 6),
            abort_reason=carla_result.abort_reason,
            anxiety_threshold_met=carla_result.anxiety_threshold_met,
            final_move_index=carla_result.final_move_index,
            is_right_censored=carla_result.is_right_censored,
        )
        _append_csv_row(
            csv_path,
            scenario_id=scenario.id,
            trial_index=trial_index,
            arm="bot",
            t_predicts=None,
            t_baseline_fails=bot_result.t_baseline_fails,
            cost_usd=round(bot_result.cost_usd, 6),
            abort_reason=bot_result.abort_reason,
            anxiety_threshold_met=None,
            final_move_index=bot_result.final_move_index,
            is_right_censored=bot_result.is_right_censored,
        )
```

`asyncio` import goes at the top of the module.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_trials.py -v -k worker
```

Expected: 3 PASS.

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_trials.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): _worker paired-trial coroutine

One worker = one (scenario, trial_index) pair. Both arms run
concurrently inside the pair via asyncio.gather. Hard-cap pre-LLM
gate per spec §2.3. Per-trial RecordingEventBus per arm produces
events_<scenario>_<arm>_<i>.jsonl. CSV rows appended on completion;
crash-resilient.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: `run_cliff_test` — top-level orchestrator

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (add `run_cliff_test` + scenario-resolution helpers)
- Modify: `nova-agent/tests/test_cliff_test_runner.py` (add orchestrator + cap-halt + pilot tests)

Builds the pair queue, gates concurrency via `Semaphore`, soft-cap-stop dequeuing, drain-in-flight, exit-code semantics.

- [ ] **Step 1: Write the failing tests**

Append to `nova-agent/tests/test_cliff_test_runner.py`:

```python
import asyncio
from pathlib import Path

import pytest

from nova_agent.lab.cliff_test import (
    BUDGET_PER_SCENARIO_ARM_USD,
    EXIT_HARD_CAP,
    EXIT_OK,
    EXIT_SOFT_CAP,
    HARD_CAP_MULTIPLIER,
    _BudgetState,
    run_cliff_test,
)
from nova_agent.lab.scenarios import SCENARIOS
from nova_agent.llm.mock import MockLLMClient


@pytest.mark.asyncio
async def test_run_cliff_test_pilot_writes_to_pilot_subdir(tmp_path: Path) -> None:
    """--pilot routes output to pilot_results/, not results/."""
    code = await run_cliff_test(
        scenarios=[SCENARIOS["snake-collapse-128"]],
        n=1,
        output_dir=tmp_path,
        concurrency=1,
        pilot=True,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
    )
    assert code == EXIT_OK
    assert (tmp_path / "pilot_results" / "cliff_test_results.csv").exists()
    assert not (tmp_path / "results" / "cliff_test_results.csv").exists()


@pytest.mark.asyncio
async def test_run_cliff_test_real_run_writes_to_results_subdir(tmp_path: Path) -> None:
    code = await run_cliff_test(
        scenarios=[SCENARIOS["snake-collapse-128"]],
        n=1,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
    )
    assert code == EXIT_OK
    assert (tmp_path / "results" / "cliff_test_results.csv").exists()


@pytest.mark.asyncio
async def test_run_cliff_test_soft_cap_drains_in_flight(tmp_path: Path) -> None:
    """Pre-load budget near soft cap. Runner should drain at most ONE more
    pair (the in-flight one), then exit with EXIT_SOFT_CAP. Some trials
    will be skipped — verify CSV row count is < N."""
    scenario = SCENARIOS["snake-collapse-128"]
    pre_loaded_budget = _BudgetState()
    pre_loaded_budget.add(scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD - 0.001)

    code = await run_cliff_test(
        scenarios=[scenario],
        n=10,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=MockLLMClient(),
        tot_llm=MockLLMClient(),
        reflection_llm=MockLLMClient(),
        bot_llm=MockLLMClient(),
        _budget_for_test=pre_loaded_budget,  # test-only injection seam
    )
    assert code == EXIT_SOFT_CAP
    csv_path = tmp_path / "results" / "cliff_test_results.csv"
    if csv_path.exists():
        rows = csv_path.read_text().splitlines()
        # Header + at most a small number of data rows.
        assert len(rows) - 1 < 20  # not all 20 (10 trials × 2 arms) ran


@pytest.mark.asyncio
async def test_run_cliff_test_hard_cap_kills_pre_LLM(tmp_path: Path) -> None:
    """Pre-load budget past hard cap. Runner exits EXIT_HARD_CAP without
    invoking any LLM."""
    scenario = SCENARIOS["snake-collapse-128"]
    pre_loaded_budget = _BudgetState()
    pre_loaded_budget.add(scenario.id, "carla", BUDGET_PER_SCENARIO_ARM_USD * HARD_CAP_MULTIPLIER + 0.01)

    class TripWireLLM(MockLLMClient):
        async def complete(self, *a, **kw):  # type: ignore[override]
            raise AssertionError("hard cap should prevent any LLM call")

    code = await run_cliff_test(
        scenarios=[scenario],
        n=5,
        output_dir=tmp_path,
        concurrency=1,
        pilot=False,
        decision_llm=TripWireLLM(),
        tot_llm=TripWireLLM(),
        reflection_llm=TripWireLLM(),
        bot_llm=TripWireLLM(),
        _budget_for_test=pre_loaded_budget,
    )
    assert code == EXIT_HARD_CAP


@pytest.mark.asyncio
async def test_run_cliff_test_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """A non-empty results dir without --force → runner raises FileExistsError."""
    scenario = SCENARIOS["snake-collapse-128"]
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "stale.csv").write_text("dummy")

    with pytest.raises(FileExistsError):
        await run_cliff_test(
            scenarios=[scenario],
            n=1,
            output_dir=tmp_path,
            concurrency=1,
            pilot=False,
            force=False,
            decision_llm=MockLLMClient(),
            tot_llm=MockLLMClient(),
            reflection_llm=MockLLMClient(),
            bot_llm=MockLLMClient(),
        )
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_runner.py -v -k run_cliff_test
```

Expected: FAIL — `run_cliff_test` and `EXIT_*` exports not yet wired.

- [ ] **Step 3: Add `run_cliff_test` to `cliff_test.py`**

```python
async def run_cliff_test(
    *,
    scenarios: list[Scenario],
    n: int,
    output_dir: Path,
    concurrency: int = DEFAULT_CONCURRENCY,
    pilot: bool = False,
    force: bool = False,
    decision_llm: LLM,
    tot_llm: LLM,
    reflection_llm: LLM,
    bot_llm: LLM,
    _budget_for_test: _BudgetState | None = None,
) -> int:
    """Top-level cliff-test orchestrator. Returns an exit code:

    - EXIT_OK (0): all pairs ran, no cap hit.
    - EXIT_SOFT_CAP (2): soft cap hit; drained in-flight; partial CSV written.
    - EXIT_HARD_CAP (3): hard cap hit; some trials never started.

    Raises FileExistsError if the target subdirectory exists, is non-empty,
    and ``force`` is False.
    """
    subdir = output_dir / ("pilot_results" if pilot else "results")
    if subdir.exists() and any(subdir.iterdir()) and not force:
        raise FileExistsError(
            f"output subdir {subdir} is non-empty; pass force=True to overwrite"
        )
    subdir.mkdir(parents=True, exist_ok=True)
    csv_path = subdir / "cliff_test_results.csv"

    budget = _budget_for_test if _budget_for_test is not None else _BudgetState()
    semaphore = asyncio.Semaphore(concurrency)

    # Pair queue: scheduling is round-robin across scenarios so soft-cap halt
    # affects all scenarios uniformly rather than running scenario A to
    # completion first.
    queue: list[tuple[Scenario, int]] = []
    for trial_index in range(n):
        for scenario in scenarios:
            queue.append((scenario, trial_index))

    soft_cap_observed = False
    hard_cap_observed = False
    in_flight: list[asyncio.Task[None]] = []

    for pair in queue:
        scenario, _ = pair
        # Soft-cap halt: stop dequeuing new pairs (in-flight finish).
        if budget.soft_cap_hit(scenario.id, "carla") or budget.soft_cap_hit(scenario.id, "bot"):
            soft_cap_observed = True
            continue
        # Hard-cap halt: do not start new workers; existing in-flight will see
        # the same condition on their pre-check and self-skip.
        if budget.hard_cap_hit(scenario.id, "carla") or budget.hard_cap_hit(scenario.id, "bot"):
            hard_cap_observed = True
            continue
        task = asyncio.create_task(
            _worker(
                pair=pair,
                semaphore=semaphore,
                budget=budget,
                csv_path=csv_path,
                output_dir=subdir,
                decision_llm=decision_llm,
                tot_llm=tot_llm,
                reflection_llm=reflection_llm,
                bot_llm=bot_llm,
            )
        )
        in_flight.append(task)

    if in_flight:
        await asyncio.gather(*in_flight, return_exceptions=False)

    # Re-check caps after drain — workers may have lifted spend past either cap.
    final_hard = any(
        budget.hard_cap_hit(s.id, arm) for s in scenarios for arm in ("carla", "bot")
    )
    final_soft = any(
        budget.soft_cap_hit(s.id, arm) for s in scenarios for arm in ("carla", "bot")
    )

    if hard_cap_observed or final_hard:
        return EXIT_HARD_CAP
    if soft_cap_observed or final_soft:
        return EXIT_SOFT_CAP
    return EXIT_OK
```

**Implementation note:** the `_budget_for_test` kwarg is a deliberate test seam (per the cap-halt tests above). Keep it underscore-prefixed and document inline that production callers do not use it.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_runner.py -v
```

Expected: 5 new tests PASS plus 3 from Task 1 still pass.

- [ ] **Step 5: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_runner.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): run_cliff_test orchestrator + cap halt + pilot routing

Top-level coroutine: builds (scenario, trial_index) pair queue
round-robin across scenarios, gates concurrency via
asyncio.Semaphore, dispatches _worker per pair via asyncio.create_task,
drains in-flight on cap halt. Returns EXIT_OK (0) / EXIT_SOFT_CAP (2)
/ EXIT_HARD_CAP (3) per spec §6.3. Pilot mode routes to
pilot_results/ subdir per spec §2.8. _budget_for_test kwarg is a
test seam for cap-halt tests; not for production callers.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: `main()` wires everything

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/cliff_test.py` (replace `main()` skeleton with full wiring)
- Modify: `nova-agent/tests/test_cliff_test_runner.py` (add e2e CLI smoke)

`main()` resolves scenarios (`--scenario all` expands to the three cliff-test scenarios; `--scenario <id>` uses `SCENARIOS[id]`). Builds production LLMs via `nova_agent.llm.factory.build_llm` with tier-resolved model names. Calls `asyncio.run(run_cliff_test(...))`. Propagates exit code via `sys.exit`.

- [ ] **Step 1: Write the failing e2e CLI smoke test**

Append to `nova-agent/tests/test_cliff_test_runner.py`:

```python
def test_cli_e2e_pilot_smoke_via_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: run the CLI as a subprocess in pilot mode against fresh-start.

    Skipped when ANTHROPIC_API_KEY / GOOGLE_API_KEY absent (we don't want a
    test that hits real providers). For production-tier validation, this
    test runs with the real keys; for the standard pytest trio it skips.
    """
    if "ANTHROPIC_API_KEY" not in os.environ or "GOOGLE_API_KEY" not in os.environ:
        pytest.skip("e2e smoke skipped: requires ANTHROPIC_API_KEY + GOOGLE_API_KEY")

    output_dir = tmp_path / "runs" / "e2e-smoke"
    result = _run_cli(
        "--scenario", "fresh-start",
        "--n", "1",
        "--pilot",
        "--concurrency", "1",
        "--output-dir", str(output_dir),
        env_overrides={"NOVA_TIER": "production"},
    )
    assert result.returncode in {0, 2, 3}, f"stderr: {result.stderr}"
    csv_path = output_dir / "pilot_results" / "cliff_test_results.csv"
    assert csv_path.exists()
```

- [ ] **Step 2: Add scenario resolution + LLM construction + main wiring**

Replace `main()` in `cliff_test.py`:

```python
import asyncio
from datetime import datetime, timezone

from nova_agent.config import get_settings
from nova_agent.lab.scenarios import SCENARIOS, load as load_scenario
from nova_agent.llm import tiers as model_tiers
from nova_agent.llm.factory import build_llm

# Cliff-test scenarios per scenarios spec §4. Excludes the "fresh-start"
# placeholder which is not part of the falsification gate.
_CLIFF_TEST_SCENARIOS: Final[tuple[str, ...]] = (
    "snake-collapse-128",
    "512-wall",
    "corner-abandonment-256",
)


def _resolve_scenarios(arg: str) -> list[Scenario]:
    if arg == "all":
        return [SCENARIOS[s] for s in _CLIFF_TEST_SCENARIOS]
    return [load_scenario(arg)]


def _default_output_dir() -> Path:
    """runs/<UTC-iso-timestamp>/."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return Path("runs") / ts


def _build_llms(tier_name: str) -> tuple[LLM, LLM, LLM, LLM]:
    """Construct the four LLMs the runner needs:
    decision (Carla react), tot (Carla deliberation), reflection
    (Carla post-game), bot (BaselineDecider).

    Models are tier-resolved per ADR-0006 / nova_agent.llm.tiers.
    Carla bot uses the same decision-role model as Carla's react path
    per Bot spec §2.4 (text-only ReactDecider); they're independent
    LLM clients for clean rate-limit isolation.
    """
    settings = get_settings()
    tier = settings.tier  # "production" | "demo" | ...
    decision_model = model_tiers.model_for(tier=tier, role="decision")
    tot_model = model_tiers.model_for(tier=tier, role="deliberation")
    reflection_model = model_tiers.model_for(tier=tier, role="reflection")
    bot_model = decision_model  # same family per Bot spec §2.4

    common_kwargs = {
        "google_api_key": settings.google_api_key.get_secret_value(),
        "anthropic_api_key": settings.anthropic_api_key.get_secret_value(),
        "daily_cap_usd": settings.daily_cap_usd,
    }
    return (
        build_llm(model=decision_model, **common_kwargs),
        build_llm(model=tot_model, **common_kwargs),
        build_llm(model=reflection_model, **common_kwargs),
        build_llm(model=bot_model, **common_kwargs),
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    tier = _check_tier()
    if tier is None:
        print(
            f"error: NOVA_TIER must be one of {sorted(_ALLOWED_TIERS)} "
            "(dev/plumbing tiers downgrade cognitive-judgment models — see ADR-0006).",
            file=sys.stderr,
        )
        sys.exit(EXIT_TIER_REFUSED)

    scenarios = _resolve_scenarios(args.scenario)
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    decision_llm, tot_llm, reflection_llm, bot_llm = _build_llms(tier)

    code = asyncio.run(
        run_cliff_test(
            scenarios=scenarios,
            n=args.n,
            output_dir=output_dir,
            concurrency=args.concurrency,
            pilot=args.pilot,
            force=args.force,
            decision_llm=decision_llm,
            tot_llm=tot_llm,
            reflection_llm=reflection_llm,
            bot_llm=bot_llm,
        )
    )
    sys.exit(code)
```

**Implementation notes:**

- The exact API surface of `nova_agent.llm.tiers.model_for(tier=, role=)` must be confirmed before this commit. If the tier table uses a different role name (e.g. `"react"` vs `"decision"`), adapt the call. If the function signature differs, adapt rather than refactor `tiers.py`.
- `Settings.daily_cap_usd` must exist; if not, the implementer threads through a CLI `--daily-cap-usd` arg or hard-codes a Phase 0.7-appropriate value (e.g. $50). Defer to existing `Settings` shape.
- Confirm `get_settings()` honors `env_ignore_empty=True` (per gotcha #3 / nova-agent rules) — it should already.

- [ ] **Step 3: Run tests to confirm they pass**

```bash
cd nova-agent
uv run pytest tests/test_cliff_test_runner.py -v
```

Expected: all CLI tests pass; the e2e smoke skips locally (no real API keys).

- [ ] **Step 4: Run /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

- [ ] **Step 5: Manual smoke (no real LLMs)**

```bash
NOVA_TIER=production uv run cliff-test --scenario fresh-start --n 1 --pilot --concurrency 1 --output-dir /tmp/cliff-test-smoke --force
```

This will fail at the LLM-build step because the runner expects production keys — that's expected. The success criterion is that the CLI parses args, validates the tier, resolves the scenario, and FAILS at the build_llm step (or runs to completion if real keys are present and the user chooses to spend ~$0.12 on the smoke). Document the observed exit code in the commit body.

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/lab/cliff_test.py \
        nova-agent/tests/test_cliff_test_runner.py
git commit -m "$(cat <<'EOF'
feat(cliff-test): main() wires argparse → run_cliff_test → exit code

Resolves --scenario (id or 'all'), builds tier-resolved LLMs via
nova_agent.llm.factory.build_llm + nova_agent.llm.tiers.model_for,
asyncio.run-s the orchestrator, propagates exit code. Default
output dir = runs/<UTC-iso-timestamp>/. cliff-test pyproject script
entry now functional end-to-end.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Final integration + green-bar verification

**Files:** none changed (verification + commit message only).

This is a no-code verification task — confirms the full surface is green and the runner behaves as documented end-to-end.

- [ ] **Step 1: Full /check-agent**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

Expected: all green. Test count delta from Task 1 baseline = ~25 new tests.

- [ ] **Step 2: Test inventory check**

```bash
uv run pytest tests/test_cliff_test_helpers.py tests/test_cliff_test_trials.py tests/test_cliff_test_runner.py -v --no-header 2>&1 | tail -30
```

Expected groups:

- `TestCheckAnxietyThreshold` × 7 (Task 2)
- `TestBudgetState` × 8 (Task 3)
- `TestAppendCsvRow` × 4 (Task 4)
- `TestApplyWithTiebreak` × 2 (Task 5)
- 3 bot trial tests (Task 6)
- 2 carla trial tests (Task 7)
- 3 paired worker tests (Task 8)
- 5 run_cliff_test orchestrator tests (Task 9)
- 3 CLI tests + 1 e2e (skipped without API keys) (Tasks 1 + 10)

- [ ] **Step 3: Verify file structure matches plan**

```bash
ls -la nova-agent/src/nova_agent/lab/cliff_test.py \
       nova-agent/tests/test_cliff_test_helpers.py \
       nova-agent/tests/test_cliff_test_trials.py \
       nova-agent/tests/test_cliff_test_runner.py
wc -l nova-agent/src/nova_agent/lab/cliff_test.py
```

Expected: cliff_test.py is roughly 400-600 lines.

- [ ] **Step 4: Spec coverage spot-check**

Verify each pinned decision in spec §2 has a test:

| Spec § | Decision | Test |
|---|---|---|
| 2.2 | Paired-trial unit-of-concurrency | `test_paired_worker_runs_both_arms` |
| 2.3 | Two-tier cost cap | `test_run_cliff_test_soft_cap_drains_in_flight`, `test_run_cliff_test_hard_cap_kills_pre_LLM` |
| 2.4 | Anxiety post-decision raw | `test_carla_trial_completes_happy_path` (anxiety_trajectory non-empty) |
| 2.5 | Per-trial memory reset via tempdir | `test_carla_trial_tempdir_is_cleaned_up` |
| 2.6 | $5 symmetric envelope | `_BudgetState` constants + `TestBudgetState` |
| 2.7 | Flat CSV row-per-trial | `TestAppendCsvRow`, `_CSV_COLUMNS` |
| 2.8 | Pilot mode same code path | `test_run_cliff_test_pilot_writes_to_pilot_subdir` |

- [ ] **Step 5: Skim for leaked secrets**

```bash
git diff origin/main..HEAD -- nova-agent/src/nova_agent/lab/cliff_test.py | grep -iE "key|secret|token|credential" | head -20
```

Expected: only `_check_tier`, `daily_cap_usd`, `get_secret_value()` references — no literal keys or tokens.

- [ ] **Step 6: Commit (only if any tweaks were needed in steps 1-5)**

If steps 1-5 produced no changes, no commit is needed. If a tweak fell out of the green-bar pass, commit:

```bash
git add -p  # stage only what changed
git commit -m "$(cat <<'EOF'
chore(cliff-test): green-bar verification fixes

<one-line description of what tweak was needed>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push**

```bash
git push
```

Expected: pre-push code-review hook runs (Layer 1.5). Findings — if any — surface as systemMessage warnings or block the push for criticals.

- [ ] **Step 8: Open the PR**

The plan + implementation are now a coherent unit (the spec already shipped in commit 0ff8449; this work delivers the runner). Open one PR titled `feat(cliff-test): Phase 0.7 cliff-test runner` covering all 11 tasks' commits + the spec commit if not yet on `main`. Use the `superpowers:finishing-a-development-branch` skill for the PR body.

---

## Out-of-scope reminders (do NOT add these)

- `analyze_results.py` — separate spec, separate PR.
- Mid-run tier downgrade — spec §2.6 explicitly forbids; operator re-runs whole suite at lower tier.
- Generic `Arm` / `Decider` / `Trial` Protocol abstractions — Q1 lock; copy-and-modify when Phase 0.8 arrives.
- Per-move budget polling — Q2 mod rejected; per-trial gating only.
- Bus subscription for anxiety measurement — Q3 lock; return-value capture only.
- Smoothed/EMA anxiety trajectory — Q3 lock; raw trajectory only.
- 3-tier JSON output — Q6 lock; flat CSV row-per-trial + JSONL only.
- Same-runner pilot via separate command — Q6 lock; `--pilot` flag on same code path.

---

## Self-review — completed before commit

This plan was self-reviewed against the spec on 2026-05-05.

**Spec coverage verified:**

- §2.1 (Q1 — Phase-0.7-only, no abstractions): no `Arm` / `Decider` / `Trial` types in plan; `_run_carla_trial` and `_run_bot_trial` are plain coroutines.
- §2.2 (Q2 — paired-trial unit): Task 8 `_worker` takes `(scenario, trial_index)` and runs both arms via `asyncio.gather`.
- §2.3 (two-tier cap): Task 3 `_BudgetState` + Task 8 hard-cap pre-check + Task 9 soft-cap halt + EXIT_SOFT_CAP/EXIT_HARD_CAP.
- §2.4 (Q3 — anxiety post-decision raw): Task 7 captures `v.anxiety` from `affect.update(...)` return; no bus subscription.
- §2.5 (Q4 — per-trial memory reset): Task 7 uses `with tempfile.TemporaryDirectory(...)`.
- §2.6 (Q5 — $5 symmetric): `BUDGET_PER_SCENARIO_ARM_USD = 5.00`, `HARD_CAP_MULTIPLIER = 1.3`. No auto tier-downgrade.
- §2.7 (Q6 — flat CSV row + JSONL): Task 4 `_CSV_COLUMNS` matches spec §2.7 table exactly. Task 8 emits one JSONL per `(scenario, arm, trial)`. No aggregate stats.
- §2.8 (pilot mode same code path): Task 9 `pilot=True` routes output to `pilot_results/`; same `run_cliff_test`.
- §3 (module shape): plan's module shape matches §3.
- §4.1 (Carla trial): Task 7 mirrors `nova_agent/main.py:240-319`.
- §4.2 (Bot trial): Task 6 mirrors §4.2 pseudocode incl. right-censor sentinel.
- §4.3 (paired worker): Task 8 incl. hard-cap pre-check + asyncio.gather.
- §6.1 (NOVA_TIER guard): Task 1 `_ALLOWED_TIERS` + tests.
- §6.2 (output directory contract): Task 9 `pilot_results/` + `results/` routing + `--force` flag.
- §6.3 (exit codes): EXIT_OK / EXIT_SOFT_CAP / EXIT_HARD_CAP all wired.
- §7.1 (anxiety threshold tests): Task 2 covers all 5 spec test cases plus boundary + empty.
- §7.2 (budget state tests): Task 3 covers all 4 spec test cases plus accumulation + concurrency.
- §7.3 (CSV writer tests): Task 4 covers all 3 spec test cases plus parent-dir creation.
- §7.4 (integration with MockLLM): Tasks 6 + 7 + 8 cover all 5 spec test cases incl. paired worker.
- §7.5 (cap halt): Task 9 covers both cap-halt scenarios via `_budget_for_test` injection seam.
- §7.6 (no production-tier LLM in unit suite): all unit tests use `MockLLMClient`; the e2e smoke is gated on env-var presence.

**Type consistency verified:**

- `_check_anxiety_threshold` signature consistent across Task 2 + 7.
- `_BudgetState.add/spent/soft_cap_hit/hard_cap_hit` signature consistent across Tasks 3 + 8 + 9.
- `_append_csv_row(csv_path, **fields)` and `_CSV_COLUMNS` consistent across Tasks 4 + 8.
- `BotTrialResult` / `CarlaTrialResult` field names consistent across Tasks 6 + 7 + 8.
- `_worker` and `run_cliff_test` LLM kwargs are named identically (`decision_llm`, `tot_llm`, `reflection_llm`, `bot_llm`).
- Exit-code constants (`EXIT_OK`, `EXIT_SOFT_CAP`, `EXIT_HARD_CAP`, `EXIT_TIER_REFUSED`) defined in Task 1 and consumed unchanged in Tasks 9 + 10 + 11.

**Placeholder scan:** no TBD / TODO / "implement later" markers in any task body. The two cost-estimate placeholders (`_bot_call_cost_estimate`, `_carla_call_cost_estimate`) are intentional and documented inline as deferred-to-`analyze_results.py`.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-05-test-runner.md`. Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration. Per `feedback_subagent_dispatch_selectivity`: Sonnet for ALL implementers (Haiku vetoed); spec-review on Task 1 + Task 11; security-reviewer Opus only if Task 11's diff introduces new LLM-content-bearing telemetry events or new bus event types (likely not — runner consumes existing telemetry, doesn't add new event types).

2. **Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batched with checkpoints.

**Which approach?**
