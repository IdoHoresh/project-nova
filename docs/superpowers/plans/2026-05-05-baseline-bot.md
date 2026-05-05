# Baseline Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the LLM-based Baseline Bot decider for the Phase 0.7 cliff test, plus the `react.py` text-only-mode refactor required for Carla to run on `Game2048Sim`.

**Architecture:** New `nova_agent.decision.baseline` module exposes `BaselineDecider` (async) with `decide(board, scenario, trial_index, move_index) -> BotDecision | TrialAborted`. Per-call protocol: 3× exponential-backoff retry on API errors, 1× retry on parse failures, then trial abort. Reuses Carla's `_ReactOutput` Pydantic schema for symmetry, calls `Settings.tier.model_for("decision")` for model resolution, runs at `temperature=0`. Publishes six telemetry event types on the `EventBus` (Test Runner consumes). Companion: `react.py` `screenshot_b64` becomes `str | None = None`; image content block is conditional.

**Tech Stack:** Python 3.14 / asyncio / pydantic / pytest / structlog / `nova_agent.llm.protocol.LLM` / `nova_agent.bus.websocket.EventBus`.

**Spec source:** `docs/superpowers/specs/2026-05-05-baseline-bot-design.md` + `docs/decisions/0007-blind-control-group-for-cliff-test.md` Amendment 1.

---

## Pre-flight (do this once before Task 1)

- [ ] **Confirm environment:**

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
cd nova-agent
uv run pytest --collect-only 2>&1 | tail -3
```

Expected: collection succeeds, ~210 tests collected.

- [ ] **Confirm branch:**

```bash
git branch --show-current
```

Expected: `claude/practical-swanson-4b6468`.

- [ ] **Skim the spec:** read `docs/superpowers/specs/2026-05-05-baseline-bot-design.md` §2 (pinned decisions) and §3 (Bot specification) before starting Task 1. The plan implements those decisions; do not re-litigate them.

---

## File Structure

**New files:**
- `nova-agent/src/nova_agent/decision/baseline.py` — Bot decider, system prompt constant, `BotDecision`, `TrialAborted`, retry logic, telemetry
- `nova-agent/tests/test_decision_baseline.py` — unit tests for the Bot decider

**Modified files:**
- `nova-agent/src/nova_agent/decision/react.py:37,40-46,62-72` — `screenshot_b64: str | None = None`; conditional image block
- `nova-agent/tests/test_decision_react.py` — text-only mode tests added

**Untouched (consumed):**
- `nova-agent/src/nova_agent/decision/prompts.py` — `build_user_prompt` reused for Bot's text-only prompt
- `nova-agent/src/nova_agent/llm/protocol.py` — `LLM.complete`, `Usage`, `parse_json` consumed unmodified
- `nova-agent/src/nova_agent/bus/websocket.py` — `EventBus.publish(event, data)` consumed unmodified (string event names, no Protocol change required)
- `nova-agent/src/nova_agent/lab/sim.py` — `Game2048Sim`, `BoardState`, `Scenario` consumed unmodified

**Out of scope (Test Runner spec):**
- Per-trial loop calling `BaselineDecider.decide` repeatedly
- Invalid-move tie-break (UP > RIGHT > DOWN > LEFT) — runner detects no-op and applies; Bot decider does not see post-swipe state
- Cost-cap envelope budget figure
- `MemoryCoordinator` reset between trials for Carla

---

### Task 1: Refactor `react.py` for optional `screenshot_b64`

**Files:**
- Modify: `nova-agent/src/nova_agent/decision/react.py:37,40-46,56-72`
- Modify: `nova-agent/tests/test_decision_react.py` (add 2 tests; keep existing tests green)

- [ ] **Step 1: Read existing test file**

```bash
cat nova-agent/tests/test_decision_react.py
```

Identify the existing test that exercises the image-present path (likely uses a non-empty `screenshot_b64`). New tests will mirror its mock-LLM setup.

- [ ] **Step 2: Write the failing tests for text-only mode**

Add to `nova-agent/tests/test_decision_react.py`:

```python
def test_react_decider_handles_screenshot_none(mock_llm_returning_react_json):
    """Phase 0.7 runs on Game2048Sim which produces no pixels.
    ReactDecider must accept screenshot_b64=None without crashing.
    Verify the user-message content has no image block when screenshot omitted.
    """
    from nova_agent.decision.react import ReactDecider
    from nova_agent.perception.types import BoardState

    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)
    decider = ReactDecider(llm=mock_llm_returning_react_json)
    decision = decider.decide_with_context(
        board=board,
        screenshot_b64=None,
        memories=[],
    )
    assert decision.action in {"swipe_up", "swipe_down", "swipe_left", "swipe_right"}
    # Confirm the LLM was called with a single text content block (no image)
    last_messages = mock_llm_returning_react_json.last_messages
    assert len(last_messages) == 1
    assert last_messages[0]["role"] == "user"
    assert all(block.get("type") != "image" for block in last_messages[0]["content"])


def test_react_decider_handles_screenshot_empty_string(mock_llm_returning_react_json):
    """Empty string is treated identically to None."""
    from nova_agent.decision.react import ReactDecider
    from nova_agent.perception.types import BoardState

    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)
    decider = ReactDecider(llm=mock_llm_returning_react_json)
    decision = decider.decide_with_context(
        board=board,
        screenshot_b64="",
        memories=[],
    )
    assert decision.action in {"swipe_up", "swipe_down", "swipe_left", "swipe_right"}
    last_messages = mock_llm_returning_react_json.last_messages
    assert all(block.get("type") != "image" for block in last_messages[0]["content"])
```

Ensure the existing test that exercises `screenshot_b64="some_real_b64_str"` keeps the `image` block — that's the regression coverage. If no such test exists, add one named `test_react_decider_preserves_image_when_screenshot_present` mirroring the structure above with a non-empty string and asserting `any(block["type"] == "image" for block in ...)`.

If `mock_llm_returning_react_json` is not the existing fixture name, use whatever fixture currently exists in `test_decision_react.py` (likely a `MockLLM` instance configured to return a valid `_ReactOutput` JSON). The fixture must record the last `messages` argument it was called with — extend the fixture if needed.

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd nova-agent
uv run pytest tests/test_decision_react.py -v 2>&1 | tail -20
```

Expected: 2 new tests FAIL with errors like `pydantic.ValidationError: data should be a valid base64 string` or `screenshot_b64 must be a string` or similar — the current code requires a non-empty `screenshot_b64`.

- [ ] **Step 4: Update `ReactDecider.decide` and `decide_with_context` signatures + message construction**

Edit `nova-agent/src/nova_agent/decision/react.py` lines 37, 40-46, 56-72:

```python
class ReactDecider:
    def __init__(self, *, llm: LLM):
        self.llm = llm

    def decide(
        self, *, board: BoardState, screenshot_b64: str | None = None
    ) -> Decision:
        return self.decide_with_context(
            board=board, screenshot_b64=screenshot_b64, memories=[]
        )

    def decide_with_context(
        self,
        *,
        board: BoardState,
        screenshot_b64: str | None = None,
        memories: list[RetrievedMemory],
        affect_text: str = "",
    ) -> Decision:
        if affect_text.strip():
            user_text = build_user_prompt_v3(
                grid=board.grid,
                score=board.score,
                memories=memories,
                affect_text=affect_text,
            )
        else:
            user_text = build_user_prompt_v2(
                grid=board.grid, score=board.score, memories=memories
            )

        content_blocks: list[dict[str, Any]] = []
        if screenshot_b64:
            content_blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64,
                    },
                }
            )
        content_blocks.append({"type": "text", "text": user_text})

        messages = [{"role": "user", "content": content_blocks}]

        text, _usage = self.llm.complete(
            system=SYSTEM_PROMPT_V1,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
            response_schema=_ReactOutput,
        )
        parsed = parse_json(text, _ReactOutput)
        return Decision(
            action=parsed.action,
            observation=parsed.observation,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )
```

Add `from typing import Any` at the top of the file if not already imported.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd nova-agent
uv run pytest tests/test_decision_react.py -v 2>&1 | tail -20
```

Expected: all tests in `test_decision_react.py` PASS, including the 2 new text-only tests AND any pre-existing tests covering the image-present path.

- [ ] **Step 6: Run the full nova-agent gate**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: pytest green (~212 tests), mypy clean, ruff clean.

- [ ] **Step 7: Commit**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
# Update the pre-commit checklist for THIS commit before staging anything
# (overwrite .claude/pre-commit-checklist.md with current-commit boxes checked)
git add nova-agent/src/nova_agent/decision/react.py nova-agent/tests/test_decision_react.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
refactor(react): make screenshot_b64 optional for Phase 0.7 text-only mode

ReactDecider now accepts screenshot_b64=None|"" and constructs the
user-message content with no image block in that case. Required by the
Phase 0.7 cliff test which runs on Game2048Sim (matrix output, no
pixels). Production live-emulator path always passes a real screenshot,
so this is a code-hygiene improvement that documents text-only as a
supported mode rather than a runtime crash.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md §5.1.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

The pre-commit checklist must be filled out before each commit per the project's discipline; mark each item `[x]` with a one-line reason and stage the checklist alongside the code.

---

### Task 2: Bot module skeleton — types, constants, system prompt

**Files:**
- Create: `nova-agent/src/nova_agent/decision/baseline.py`
- Create: `nova-agent/tests/test_decision_baseline.py`

- [ ] **Step 1: Write the failing tests for type construction and constants**

Create `nova-agent/tests/test_decision_baseline.py`:

```python
"""Tests for the Phase 0.7 Baseline Bot decider.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md
"""

import pytest


def test_baseline_module_exports_expected_symbols():
    from nova_agent.decision import baseline
    assert hasattr(baseline, "BotDecision")
    assert hasattr(baseline, "TrialAborted")
    assert hasattr(baseline, "BaselineDecider")
    assert hasattr(baseline, "BASELINE_SYSTEM_PROMPT")
    assert hasattr(baseline, "BASELINE_MAX_TOKENS")
    assert hasattr(baseline, "BASELINE_TEMPERATURE")


def test_baseline_constants_match_spec():
    from nova_agent.decision import baseline
    assert baseline.BASELINE_MAX_TOKENS == 500
    assert baseline.BASELINE_TEMPERATURE == 0.0


def test_baseline_system_prompt_matches_adr_0007_amendment_1():
    from nova_agent.decision import baseline
    text = baseline.BASELINE_SYSTEM_PROMPT
    assert "You are an AI agent playing 2048" in text
    assert "maximize score" in text
    assert '"observation"' in text
    assert '"reasoning"' in text
    assert '"action"' in text
    assert '"confidence"' in text
    assert "swipe_up" in text and "swipe_down" in text
    assert "swipe_left" in text and "swipe_right" in text


def test_bot_decision_is_immutable_and_has_required_fields():
    from nova_agent.decision.baseline import BotDecision
    d = BotDecision(
        action="swipe_up",
        observation="empty board",
        reasoning="any direction works",
        confidence="low",
    )
    assert d.action == "swipe_up"
    with pytest.raises(Exception):  # frozen dataclass
        d.action = "swipe_down"  # type: ignore[misc]


def test_trial_aborted_carries_reason():
    from nova_agent.decision.baseline import TrialAborted
    a = TrialAborted(reason="api_error", last_move_index=12)
    assert a.reason == "api_error"
    assert a.last_move_index == 12

    a2 = TrialAborted(reason="parse_failure", last_move_index=0)
    assert a2.reason == "parse_failure"


def test_trial_aborted_reason_is_constrained_to_known_values():
    """Misconfiguration guard: the only reasons are 'api_error' and
    'parse_failure'. Tie-break and right-censoring do not abort trials."""
    from nova_agent.decision.baseline import TrialAborted, AbortReason
    # AbortReason should be a Literal type — verify the literal members are exactly these
    import typing
    args = typing.get_args(AbortReason)
    assert set(args) == {"api_error", "parse_failure"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -15
```

Expected: all 6 tests FAIL with `ModuleNotFoundError: No module named 'nova_agent.decision.baseline'`.

- [ ] **Step 3: Implement the skeleton**

Create `nova-agent/src/nova_agent/decision/baseline.py`:

```python
"""Phase 0.7 Baseline Bot — purely-logical score-maximizer (ADR-0007).

The Baseline Bot is the control arm of the cliff test. It calls the LLM
once per move with no affect, no memory, no Tree-of-Thoughts, no
reflection. Its only job is to commit a move that maximizes score from
the current grid + score.

Per-call protocol:
  - 3x exponential-backoff retry on API errors → trial abort
  - 1x retry on parse failures → trial abort
  - Invalid-move handling lives in the Test Runner (UP > RIGHT > DOWN >
    LEFT tie-break per scenarios spec §2.3); the Bot does not see
    post-swipe state.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md
ADR:  docs/decisions/0007-blind-control-group-for-cliff-test.md (Amendment 1)
"""

from dataclasses import dataclass
from typing import Any, Literal

from nova_agent.bus.websocket import EventBus
from nova_agent.decision.react import _ReactOutput
from nova_agent.llm.protocol import LLM


# ADR-0007 prompt (verbatim) extended with JSON-output instructions matching
# the shared schema (Q4 / A1.3). Schema is _ReactOutput from decision/react.py.
BASELINE_SYSTEM_PROMPT = """\
You are an AI agent playing 2048. Your only goal is to maximize score.
Compute the next move. Emit strict JSON only (no prose around it):
{
  "observation": "5-10 word fragment, what you see on the board",
  "reasoning":   "5-15 word fragment, why this move maximizes score",
  "action":      "swipe_up" | "swipe_down" | "swipe_left" | "swipe_right",
  "confidence":  "low" | "medium" | "high"
}
"""

# Per Q4 / A1.3 — Bot temp=0 (greedy max-prob), max_tokens=500 (Bot needs
# no thinking budget; 500 leaves room for short reasoning + small JSON
# payload).
BASELINE_TEMPERATURE: float = 0.0
BASELINE_MAX_TOKENS: int = 500


AbortReason = Literal["api_error", "parse_failure"]


@dataclass(frozen=True)
class BotDecision:
    """Successful per-call output from BaselineDecider."""

    action: Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right"]
    observation: str
    reasoning: str
    confidence: Literal["low", "medium", "high"]


@dataclass(frozen=True)
class TrialAborted:
    """Returned by BaselineDecider.decide when retries exhaust.

    Per A1.5: aborted trials are not re-run (Bot at temp=0 + fixed seed
    reproduces the same failure deterministically). The Test Runner
    records the abort and applies paired-discard logic (A1.6) for test 2.
    """

    reason: AbortReason
    last_move_index: int


class BaselineDecider:
    """LLM-based one-shot per-move decider for the Phase 0.7 control arm.

    Call signature mirrors ReactDecider's text-only mode (no screenshot).
    Implementation in subsequent tasks: Task 3 (happy path), Task 4
    (API error retry), Task 5 (parse failure retry), Task 6 (telemetry).
    """

    def __init__(self, *, llm: LLM, bus: EventBus | None = None):
        self.llm = llm
        self.bus = bus

    async def decide(
        self,
        *,
        board: Any,  # BoardState — typed in Task 3
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        raise NotImplementedError("Implemented in Task 3")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -15
```

Expected: all 6 skeleton tests PASS.

- [ ] **Step 5: Run the gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
# Update pre-commit checklist for this commit
git add nova-agent/src/nova_agent/decision/baseline.py nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(baseline): add module skeleton — types, constants, system prompt

Adds nova_agent.decision.baseline with BotDecision, TrialAborted (with
AbortReason Literal), BaselineDecider stub, BASELINE_SYSTEM_PROMPT
verbatim from ADR-0007 + JSON-output instructions matching the shared
_ReactOutput schema, BASELINE_TEMPERATURE=0.0, BASELINE_MAX_TOKENS=500.

decide() raises NotImplementedError; subsequent tasks implement happy
path, retries, and telemetry.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md §3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

### Task 3: Implement happy-path `BaselineDecider.decide`

**Files:**
- Modify: `nova-agent/src/nova_agent/decision/baseline.py:91-100` (replace `NotImplementedError`)
- Modify: `nova-agent/tests/test_decision_baseline.py` (add happy-path test)

- [ ] **Step 1: Write the failing test for the happy path**

Add to `nova-agent/tests/test_decision_baseline.py`:

```python
import pytest

from nova_agent.llm.protocol import Usage
from nova_agent.perception.types import BoardState


class _RecordingMockLLM:
    """Minimal LLM stub that records calls and returns scripted responses."""

    def __init__(self, responses: list[str], model: str = "claude-sonnet-4-6"):
        self.model = model
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> tuple[str, Usage]:
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("MockLLM ran out of scripted responses")
        text = self._responses.pop(0)
        return text, Usage(input_tokens=100, output_tokens=50, model=self.model)


@pytest.mark.asyncio
async def test_baseline_decide_returns_decision_on_valid_response():
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    valid_json = (
        '{"observation": "two corner",'
        ' "reasoning": "consolidate left",'
        ' "action": "swipe_left",'
        ' "confidence": "medium"}'
    )
    llm = _RecordingMockLLM(responses=[valid_json])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_left"
    assert result.observation == "two corner"
    assert result.confidence == "medium"
    # Verify the LLM was called with the right config
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["temperature"] == 0.0
    assert call["max_tokens"] == 500
    assert call["response_schema"].__name__ == "_ReactOutput"
    # Verify text-only message structure
    assert len(call["messages"]) == 1
    assert call["messages"][0]["role"] == "user"
    assert all(b.get("type") != "image" for b in call["messages"][0]["content"])
    # Verify the system prompt is the canonical Bot prompt
    assert "maximize score" in call["system"]
```

`pytest-asyncio` is already a project dependency (used by ToTDecider tests).

- [ ] **Step 2: Run test to verify it fails**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py::test_baseline_decide_returns_decision_on_valid_response -v 2>&1 | tail -10
```

Expected: FAIL with `NotImplementedError: Implemented in Task 3`.

- [ ] **Step 3: Implement the happy path**

Replace the body of `BaselineDecider.decide` in `nova-agent/src/nova_agent/decision/baseline.py`:

```python
import asyncio  # add to imports
from nova_agent.decision.prompts import build_user_prompt
from nova_agent.llm.structured import parse_json
from nova_agent.perception.types import BoardState  # replace `Any` typing


class BaselineDecider:
    def __init__(self, *, llm: LLM, bus: EventBus | None = None):
        self.llm = llm
        self.bus = bus

    async def decide(
        self,
        *,
        board: BoardState,
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]

        # Happy path: single LLM call, single parse. Retry logic added in
        # Tasks 4 and 5; telemetry added in Task 6.
        text, _usage = self.llm.complete(
            system=BASELINE_SYSTEM_PROMPT,
            messages=messages,
            max_tokens=BASELINE_MAX_TOKENS,
            temperature=BASELINE_TEMPERATURE,
            response_schema=_ReactOutput,
        )
        parsed = parse_json(text, _ReactOutput)
        return BotDecision(
            action=parsed.action,
            observation=parsed.observation,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -15
```

Expected: all baseline tests PASS, including the new happy-path test.

- [ ] **Step 5: Run the gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/decision/baseline.py nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(baseline): implement happy-path BaselineDecider.decide

Single LLM call per move with text-only prompt (build_user_prompt from
decision/prompts), system=BASELINE_SYSTEM_PROMPT, temperature=0.0,
max_tokens=500, response_schema=_ReactOutput. Returns BotDecision on
success. Retries and telemetry added in subsequent tasks.

Spec: docs/superpowers/specs/2026-05-05-baseline-bot-design.md §3.3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

### Task 4: API error retry logic (3× exponential backoff, then trial abort)

**Files:**
- Modify: `nova-agent/src/nova_agent/decision/baseline.py:decide` (wrap LLM call in retry loop)
- Modify: `nova-agent/tests/test_decision_baseline.py` (add 2 retry tests)

- [ ] **Step 1: Identify the LLM API error type**

```bash
grep -rn "APIError\|class.*Error" nova-agent/src/nova_agent/llm/ 2>/dev/null | head -10
```

Note the exception class(es) raised by `LLM.complete` on API failure. Likely `httpx.HTTPError` or provider-specific (`anthropic.APIError`, `google.api_core.exceptions.GoogleAPIError`). For the retry test, use a lightweight stand-in: define a local `class _SimulatedAPIError(Exception): pass` in the test file and configure the `BaselineDecider` retry to catch a specific exception class declared in `baseline.py` (e.g., a tuple `_RETRYABLE_API_EXCEPTIONS`).

If the existing codebase has an established retryable-error tuple (check `nova_agent/llm/factory.py` or `nova_agent/llm/anthropic.py`), reuse it. Otherwise, define a minimal:

```python
# in baseline.py
_RETRYABLE_API_EXCEPTIONS: tuple[type[BaseException], ...] = (Exception,)
```

This is conservative — narrow it in a follow-up commit if a more specific class hierarchy exists. Document the choice in the commit message.

- [ ] **Step 2: Extend the mock to script exceptions and write the failing tests**

Add to `nova-agent/tests/test_decision_baseline.py`:

```python
class _RetryingMockLLM:
    """Mock that raises scripted exceptions before scripted text responses."""

    def __init__(
        self,
        scripted: list[str | BaseException],
        model: str = "claude-sonnet-4-6",
    ):
        self.model = model
        self._scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> tuple[str, Usage]:
        self.calls.append(kwargs)
        if not self._scripted:
            raise AssertionError("MockLLM ran out of scripted items")
        item = self._scripted.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item, Usage(input_tokens=100, output_tokens=50, model=self.model)


@pytest.mark.asyncio
async def test_baseline_decide_retries_on_api_error_then_succeeds():
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    valid_json = (
        '{"observation": "x", "reasoning": "y",'
        ' "action": "swipe_up", "confidence": "low"}'
    )
    llm = _RetryingMockLLM(
        scripted=[RuntimeError("transient 503"), valid_json]
    )
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_up"
    assert len(llm.calls) == 2  # 1 failed + 1 succeeded


@pytest.mark.asyncio
async def test_baseline_decide_aborts_after_three_api_errors(monkeypatch):
    from nova_agent.decision.baseline import (
        BaselineDecider,
        TrialAborted,
    )

    # Patch asyncio.sleep so the test doesn't actually wait the backoff intervals
    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(
        scripted=[
            RuntimeError("err 1"),
            RuntimeError("err 2"),
            RuntimeError("err 3"),
        ]
    )
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=12)

    assert isinstance(result, TrialAborted)
    assert result.reason == "api_error"
    assert result.last_move_index == 12
    assert len(llm.calls) == 3


async def _noop_sleep(_seconds: float) -> None:
    return None
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py::test_baseline_decide_retries_on_api_error_then_succeeds tests/test_decision_baseline.py::test_baseline_decide_aborts_after_three_api_errors -v 2>&1 | tail -15
```

Expected: both FAIL — first with the unhandled `RuntimeError`, second with `RuntimeError` propagating instead of being caught.

- [ ] **Step 4: Implement the API retry loop**

Replace `BaselineDecider.decide` in `nova-agent/src/nova_agent/decision/baseline.py`:

```python
_API_RETRY_LIMIT = 3
_RETRYABLE_API_EXCEPTIONS: tuple[type[BaseException], ...] = (Exception,)


class BaselineDecider:
    def __init__(self, *, llm: LLM, bus: EventBus | None = None):
        self.llm = llm
        self.bus = bus

    async def decide(
        self,
        *,
        board: BoardState,
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]

        text = await self._call_with_api_retry(messages=messages)
        if text is None:
            return TrialAborted(reason="api_error", last_move_index=move_index)

        parsed = parse_json(text, _ReactOutput)  # parse-failure retry added in Task 5
        return BotDecision(
            action=parsed.action,
            observation=parsed.observation,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )

    async def _call_with_api_retry(
        self, *, messages: list[dict[str, Any]]
    ) -> str | None:
        """Call LLM with up to _API_RETRY_LIMIT attempts and exponential backoff.

        Returns the response text on success, None on retry exhaustion.
        Backoff: 2s, 4s, 8s after attempts 1, 2, 3 respectively (matches
        spec §3.3 pseudocode).
        """
        for attempt in range(_API_RETRY_LIMIT):
            try:
                text, _usage = self.llm.complete(
                    system=BASELINE_SYSTEM_PROMPT,
                    messages=messages,
                    max_tokens=BASELINE_MAX_TOKENS,
                    temperature=BASELINE_TEMPERATURE,
                    response_schema=_ReactOutput,
                )
                return text
            except _RETRYABLE_API_EXCEPTIONS:
                if attempt + 1 < _API_RETRY_LIMIT:
                    await asyncio.sleep(2 ** (attempt + 1))
                # else: fall through; loop ends; return None below
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -15
```

Expected: all baseline tests PASS, including the 2 new retry tests.

- [ ] **Step 6: Run the gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add nova-agent/src/nova_agent/decision/baseline.py nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(baseline): add API-error retry loop (3x exponential backoff, then abort)

Wraps LLM.complete in _call_with_api_retry; on RETRYABLE_API_EXCEPTIONS
sleeps 2/4/8 seconds before next attempt; after 3 failed attempts
returns TrialAborted(reason="api_error"). _RETRYABLE_API_EXCEPTIONS is
deliberately broad (Exception) for now — narrow in a follow-up once the
LLM provider exception hierarchy is audited.

Spec: A1.5 / §3.3 — no fallback to tie-break on api_error abort.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

### Task 5: Parse failure retry logic (1× retry, then trial abort)

**Files:**
- Modify: `nova-agent/src/nova_agent/decision/baseline.py:decide` (wrap parse in retry)
- Modify: `nova-agent/tests/test_decision_baseline.py` (add 2 parse-retry tests)

- [ ] **Step 1: Write the failing tests**

Add to `nova-agent/tests/test_decision_baseline.py`:

```python
@pytest.mark.asyncio
async def test_baseline_decide_retries_once_on_parse_failure_then_succeeds(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider, BotDecision

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    invalid = "not json"
    valid = (
        '{"observation": "x", "reasoning": "y",'
        ' "action": "swipe_down", "confidence": "high"}'
    )
    llm = _RetryingMockLLM(scripted=[invalid, valid])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=0)

    assert isinstance(result, BotDecision)
    assert result.action == "swipe_down"
    assert len(llm.calls) == 2  # 1 unparseable + 1 valid


@pytest.mark.asyncio
async def test_baseline_decide_aborts_after_two_parse_failures(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider, TrialAborted

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(scripted=["bad json", "still bad"])
    decider = BaselineDecider(llm=llm)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    result = await decider.decide(board=board, trial_index=0, move_index=8)

    assert isinstance(result, TrialAborted)
    assert result.reason == "parse_failure"
    assert result.last_move_index == 8
    assert len(llm.calls) == 2  # original + 1 retry per A1.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py::test_baseline_decide_retries_once_on_parse_failure_then_succeeds tests/test_decision_baseline.py::test_baseline_decide_aborts_after_two_parse_failures -v 2>&1 | tail -15
```

Expected: both FAIL — first with `StructuredOutputError` not retried, second with the same uncaught exception.

- [ ] **Step 3: Wrap parse in a retry loop**

Update `BaselineDecider.decide` in `nova-agent/src/nova_agent/decision/baseline.py`:

```python
from nova_agent.llm.structured import StructuredOutputError  # add import

_PARSE_RETRY_LIMIT = 2  # 1 original attempt + 1 retry per A1.5


class BaselineDecider:
    # __init__ unchanged

    async def decide(
        self,
        *,
        board: BoardState,
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]

        for parse_attempt in range(_PARSE_RETRY_LIMIT):
            text = await self._call_with_api_retry(messages=messages)
            if text is None:
                return TrialAborted(reason="api_error", last_move_index=move_index)
            try:
                parsed = parse_json(text, _ReactOutput)
                return BotDecision(
                    action=parsed.action,
                    observation=parsed.observation,
                    reasoning=parsed.reasoning,
                    confidence=parsed.confidence,
                )
            except StructuredOutputError:
                continue  # try once more with same prompt
        return TrialAborted(reason="parse_failure", last_move_index=move_index)
```

Note: at temp=0 with the same prompt, the retry's response is deterministic — but cheap insurance against transient model-version-routing variance. Documented in the Bot spec §3.3 inline comment.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -15
```

Expected: all baseline tests PASS.

- [ ] **Step 5: Run the gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
git add nova-agent/src/nova_agent/decision/baseline.py nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(baseline): add parse-failure retry (1x, then abort)

Wraps the parse_json call in a 2-iteration loop: original attempt + 1
retry. On StructuredOutputError both times, returns
TrialAborted(reason="parse_failure"). Retry shares the same prompt — at
temperature=0 the retry is deterministic but cheap insurance against
transient model-version-routing variance.

Spec: A1.5 / §3.3 — no fallback to tie-break on parse_failure abort.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

### Task 6: Telemetry events via `EventBus.publish`

**Files:**
- Modify: `nova-agent/src/nova_agent/decision/baseline.py:decide,_call_with_api_retry` (publish events)
- Modify: `nova-agent/tests/test_decision_baseline.py` (telemetry assertion test)

⚠️ **Per `.claude/rules/security.md`: new bus event types require `security-reviewer` invocation.** Run `/security-review` (or invoke the security-reviewer subagent manually) on this task's diff before committing. The event payloads contain `prompt_tokens`, `completion_tokens`, latency, and an `error_type` string — verify no API keys, raw env values, or full LLM responses leak into the payloads.

- [ ] **Step 1: Write the failing telemetry test**

Add to `nova-agent/tests/test_decision_baseline.py`:

```python
class _CapturingBus:
    """Minimal stand-in for EventBus that captures published events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, event: str, data: Any) -> None:
        self.events.append((event, data))


@pytest.mark.asyncio
async def test_baseline_telemetry_events_emit_on_success():
    from nova_agent.decision.baseline import BaselineDecider

    valid = (
        '{"observation": "x", "reasoning": "y",'
        ' "action": "swipe_up", "confidence": "low"}'
    )
    llm = _RetryingMockLLM(scripted=[valid])
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=3, move_index=7)

    event_names = [name for name, _data in bus.events]
    assert "bot_call_attempt" in event_names
    assert "bot_call_success" in event_names

    success = next(d for n, d in bus.events if n == "bot_call_success")
    assert success["trial"] == 3
    assert success["move_index"] == 7
    assert success["action"] == "swipe_up"
    assert "prompt_tokens" in success
    assert "completion_tokens" in success
    assert "latency_ms" in success


@pytest.mark.asyncio
async def test_baseline_telemetry_emits_api_error_and_trial_aborted(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(
        scripted=[RuntimeError("e1"), RuntimeError("e2"), RuntimeError("e3")]
    )
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=0, move_index=10)

    api_errors = [d for n, d in bus.events if n == "bot_call_api_error"]
    assert len(api_errors) == 3
    aborted = [d for n, d in bus.events if n == "bot_trial_aborted"]
    assert len(aborted) == 1
    assert aborted[0]["reason"] == "api_error"
    assert aborted[0]["last_move_index"] == 10


@pytest.mark.asyncio
async def test_baseline_telemetry_emits_parse_failure_and_trial_aborted(monkeypatch):
    from nova_agent.decision.baseline import BaselineDecider

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    llm = _RetryingMockLLM(scripted=["junk", "still junk"])
    bus = _CapturingBus()
    decider = BaselineDecider(llm=llm, bus=bus)
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)

    await decider.decide(board=board, trial_index=1, move_index=4)

    parse_fails = [d for n, d in bus.events if n == "bot_call_parse_failure"]
    assert len(parse_fails) == 2
    aborted = [d for n, d in bus.events if n == "bot_trial_aborted"]
    assert aborted[0]["reason"] == "parse_failure"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -20
```

Expected: 3 new tests FAIL — `bus.events` is empty since no events are published yet.

- [ ] **Step 3: Wire telemetry into `BaselineDecider`**

Update `nova-agent/src/nova_agent/decision/baseline.py`:

```python
import time  # add to imports


class BaselineDecider:
    def __init__(self, *, llm: LLM, bus: EventBus | None = None):
        self.llm = llm
        self.bus = bus

    async def decide(
        self,
        *,
        board: BoardState,
        trial_index: int,
        move_index: int,
    ) -> BotDecision | TrialAborted:
        user_text = build_user_prompt(grid=board.grid, score=board.score)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]

        for parse_attempt in range(_PARSE_RETRY_LIMIT):
            call_result = await self._call_with_api_retry(
                messages=messages,
                trial_index=trial_index,
                move_index=move_index,
            )
            if call_result is None:
                await self._emit("bot_trial_aborted", {
                    "trial": trial_index,
                    "reason": "api_error",
                    "last_move_index": move_index,
                })
                return TrialAborted(reason="api_error", last_move_index=move_index)

            text, usage, latency_ms = call_result
            try:
                parsed = parse_json(text, _ReactOutput)
                await self._emit("bot_call_success", {
                    "trial": trial_index,
                    "move_index": move_index,
                    "action": parsed.action,
                    "latency_ms": latency_ms,
                    "prompt_tokens": usage.input_tokens,
                    "completion_tokens": usage.output_tokens,
                })
                return BotDecision(
                    action=parsed.action,
                    observation=parsed.observation,
                    reasoning=parsed.reasoning,
                    confidence=parsed.confidence,
                )
            except StructuredOutputError:
                await self._emit("bot_call_parse_failure", {
                    "trial": trial_index,
                    "move_index": move_index,
                    "raw_response_excerpt": text[:200],
                    "attempt_n": parse_attempt + 1,
                })

        await self._emit("bot_trial_aborted", {
            "trial": trial_index,
            "reason": "parse_failure",
            "last_move_index": move_index,
        })
        return TrialAborted(reason="parse_failure", last_move_index=move_index)

    async def _call_with_api_retry(
        self,
        *,
        messages: list[dict[str, Any]],
        trial_index: int,
        move_index: int,
    ) -> tuple[str, "Usage", float] | None:
        for attempt in range(_API_RETRY_LIMIT):
            await self._emit("bot_call_attempt", {
                "trial": trial_index,
                "move_index": move_index,
                "attempt_n": attempt + 1,
            })
            t0 = time.monotonic()
            try:
                text, usage = self.llm.complete(
                    system=BASELINE_SYSTEM_PROMPT,
                    messages=messages,
                    max_tokens=BASELINE_MAX_TOKENS,
                    temperature=BASELINE_TEMPERATURE,
                    response_schema=_ReactOutput,
                )
                latency_ms = (time.monotonic() - t0) * 1000
                return text, usage, latency_ms
            except _RETRYABLE_API_EXCEPTIONS as exc:
                await self._emit("bot_call_api_error", {
                    "trial": trial_index,
                    "move_index": move_index,
                    "error_type": type(exc).__name__,
                    "attempt_n": attempt + 1,
                })
                if attempt + 1 < _API_RETRY_LIMIT:
                    await asyncio.sleep(2 ** (attempt + 1))
        return None

    async def _emit(self, event: str, data: dict[str, Any]) -> None:
        if self.bus is not None:
            await self.bus.publish(event, data)
```

Add to imports: `from nova_agent.llm.protocol import LLM, Usage`.

Telemetry payloads contain ONLY: trial / move indices, action enum value, token counts, latency, error class name, raw-response excerpt (first 200 chars). They do NOT contain: API keys, env values, full LLM responses, prompts, or memory contents. This is the security-reviewer auditable surface (per security.md "no secrets in error messages, logs, or exception chains").

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py -v 2>&1 | tail -20
```

Expected: all baseline tests PASS.

- [ ] **Step 5: Invoke security-reviewer on the telemetry surface**

Per `.claude/rules/security.md`: new bus event types must be reviewed. Run:

```bash
/security-review
```

Or manually invoke the `security-reviewer` subagent with the prompt: *"review the telemetry-event surface added in `nova_agent/decision/baseline.py:decide,_call_with_api_retry,_emit`. Verify event payloads contain no API keys, env values, full LLM responses, or memory contents. The five new event names: `bot_call_attempt`, `bot_call_success`, `bot_call_api_error`, `bot_call_parse_failure`, `bot_trial_aborted`. Audit `raw_response_excerpt` truncation (200 chars) — verify a leaked token in a prompt-injection response could not exceed that bound and end up persisted."*

- [ ] **Step 6: Run the gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add nova-agent/src/nova_agent/decision/baseline.py nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(baseline): add telemetry events for Test Runner consumption

Wires five new bus event types into BaselineDecider via EventBus.publish:
bot_call_attempt, bot_call_success, bot_call_api_error,
bot_call_parse_failure, bot_trial_aborted. Payloads carry trial/move
indices, action enum value, token counts, latency, error class name,
and a 200-char raw-response excerpt — no secrets, no full prompts, no
memory contents. Security-reviewer audited the surface.

Test Runner spec (forthcoming) will subscribe and persist these events
for paired-discard accounting and cost-cap enforcement.

Spec: §3.4 — telemetry contract.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

### Task 7: Integration test — Bot + Game2048Sim full trial

**Files:**
- Modify: `nova-agent/tests/test_decision_baseline.py` (add integration test)

- [ ] **Step 1: Verified `Game2048Sim` interface signature**

The interface relevant to this test (verified in `nova-agent/src/nova_agent/lab/sim.py`):
- `Game2048Sim(seed: int, scenario: Scenario | None = None)`
- `sim.board -> BoardState` (property; constructs fresh on each access)
- `sim.apply_move(direction: SwipeDirection) -> bool` — returns True on legal move, False on no-op
- `sim.is_game_over() -> bool`

Action translation: the Bot decider returns `BotDecision.action` as a `Literal["swipe_up" | "swipe_down" | "swipe_left" | "swipe_right"]`. `SwipeDirection` (in `nova_agent.action.adb:19-23`) is a `str, Enum` whose member values are exactly those strings. Translation is `SwipeDirection(result.action)`.

- [ ] **Step 2: Write the failing integration test**

Add to `nova-agent/tests/test_decision_baseline.py`:

```python
@pytest.mark.asyncio
async def test_baseline_runs_full_trial_against_game2048sim_with_mock_llm(monkeypatch):
    """Integration: Bot decides, runner-style loop applies the swipe to
    Game2048Sim, until game-over OR MAX_MOVES=50.

    Mock LLM cycles through valid responses. This is NOT the Test Runner
    (no scenario, no paired logic, no telemetry persistence), but it
    verifies BaselineDecider integrates with the sim contract.
    """
    from nova_agent.action.adb import SwipeDirection
    from nova_agent.decision.baseline import BaselineDecider, BotDecision
    from nova_agent.lab.scenarios import SCENARIOS
    from nova_agent.lab.sim import Game2048Sim

    monkeypatch.setattr("nova_agent.decision.baseline.asyncio.sleep", _noop_sleep)

    # Cycle through all four directions to avoid getting stuck on any single one.
    cycling_responses = [
        '{"observation": "x", "reasoning": "y", "action": "swipe_up", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_right", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_down", "confidence": "low"}',
        '{"observation": "x", "reasoning": "y", "action": "swipe_left", "confidence": "low"}',
    ] * 20  # max 80 calls, well above MAX_MOVES=50
    llm = _RetryingMockLLM(scripted=cycling_responses)

    scenario = SCENARIOS["fresh-start"]
    sim = Game2048Sim(seed=scenario.seed_base, scenario=scenario)
    decider = BaselineDecider(llm=llm)

    MAX_MOVES = 50
    moves_taken = 0
    while not sim.is_game_over() and moves_taken < MAX_MOVES:
        result = await decider.decide(
            board=sim.board, trial_index=0, move_index=moves_taken
        )
        assert isinstance(result, BotDecision), (
            f"unexpected abort at move {moves_taken}"
        )
        sim.apply_move(SwipeDirection(result.action))
        moves_taken += 1

    # Either game-over OR right-censored at MAX_MOVES. Both acceptable.
    assert sim.is_game_over() or moves_taken == MAX_MOVES
```

- [ ] **Step 3: Run the integration test**

```bash
cd nova-agent
uv run pytest tests/test_decision_baseline.py::test_baseline_runs_full_trial_against_game2048sim_with_mock_llm -v 2>&1 | tail -20
```

Expected: PASS. The `fresh-start` scenario starts on an empty grid and the cycling four-direction LLM should drive the sim to either game-over (rare in 50 moves on an empty start) or hit the MAX_MOVES=50 cap (more likely). Both are acceptable per the assertion.

If the test fails on a `Scenario` validator (e.g., `fresh-start` is no longer in `SCENARIOS` after the cliff-test scenarios spec migration), substitute another known-loadable scenario from `SCENARIOS`.

- [ ] **Step 4: Run the full nova-agent gate trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings 2>&1 | tail -10 && uv run mypy 2>&1 | tail -5 && uv run ruff check 2>&1 | tail -5
```

Expected: green. Total test count should be ~219 (210 baseline + 2 react text-only + 6 baseline skeleton + 2 api-retry + 2 parse-retry + 3 telemetry + 1 integration = 226 — adjust if existing react tests are extended in place rather than added).

- [ ] **Step 5: Commit**

```bash
git add nova-agent/tests/test_decision_baseline.py .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
test(baseline): integration test — Bot + Game2048Sim full trial

Runs BaselineDecider against fresh-start scenario in a runner-style
loop until game-over or MAX_MOVES=50. Uses cycling mock-LLM responses
across all four directions. Validates the Bot/sim contract end-to-end
without paying production-tier LLM costs (real cliff-test execution
lives in the Test Runner spec, gated by ADR-0006 cost discipline).

Spec: §7.3 — sim-integration tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## Plan completion checklist

After Task 7 commits land:

- [ ] All baseline + react tests green: `cd nova-agent && uv run pytest -v 2>&1 | tail -5`
- [ ] mypy strict + ruff clean: `cd nova-agent && uv run mypy && uv run ruff check`
- [ ] All commits pushed to `claude/practical-swanson-4b6468`
- [ ] No uncommitted changes: `git status` is clean
- [ ] PR-cadence check: branch state is a coherent unit ("Baseline Bot decider implementation"). Open a PR titled `feat(baseline): Phase 0.7 Baseline Bot decider`. Layer 2 (`claude-code-action`) auto-reviews.
- [ ] After PR merge, propose `/clear` with handoff prompt: *"Last shipped: Baseline Bot decider PR. Next task: Test Runner spec (`superpowers:brainstorming`) per CLAUDE.md 'Active phase + next task'. Read: CLAUDE.md, project_nova_resume_point memory, recent git log."*

## Out-of-scope (deliberate, per spec)

- Test Runner — separate spec; consumes `BaselineDecider`, `BotDecision`, `TrialAborted`, the telemetry events
- Paired-discard logic across N=20 trials — Test Runner concern
- Cost-cap envelope (budget figure $X) — Test Runner concern
- Invalid-move tie-break (UP > RIGHT > DOWN > LEFT) — Test Runner concern; Bot does not see post-swipe state
- Carla-side `MemoryCoordinator` reset between trials — Test Runner concern (scenarios spec §2.6)
- Production-tier LLM tests — manual calibration runs in the Test Runner spec; not part of the unit gate
- Anxiety sampling cadence — Test Runner concern
- Parallelization across the 60 trials per scenario — Test Runner concern
- `_RETRYABLE_API_EXCEPTIONS` narrowing from `(Exception,)` to provider-specific classes — follow-up commit after auditing `nova_agent/llm/anthropic.py`, `nova_agent/llm/gemini.py` exception hierarchies

## References

- Spec: `docs/superpowers/specs/2026-05-05-baseline-bot-design.md`
- ADR: `docs/decisions/0007-blind-control-group-for-cliff-test.md` (Amendment 1)
- Scenarios spec: `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md`
- Sim spec: `docs/superpowers/specs/2026-05-04-game2048sim-design.md`
- LLM protocol: `nova-agent/src/nova_agent/llm/protocol.py`
- Carla's act-step (template for symmetry): `nova-agent/src/nova_agent/decision/react.py`
- Bus protocol: `nova-agent/src/nova_agent/bus/websocket.py`
