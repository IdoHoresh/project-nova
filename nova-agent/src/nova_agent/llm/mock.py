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

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, ValidationError


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class _RoleSpec(BaseModel):
    """Registered role: how to detect it + schema + response factory."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    system_fingerprint: str  # substring of system prompt that identifies the role
    schema_model: type[BaseModel]  # Pydantic model the response must conform to
    factory: Callable[[dict[str, Any]], dict[str, Any]]  # build a response dict from call context


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


class _DecisionResponse(BaseModel):
    observation: str
    reasoning: str
    action: str
    confidence: str
    memory_citation: dict[str, Any] | None = None


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
    _RoleSpec(
        name="decision",
        system_fingerprint="emit Observation, Reasoning, Action",
        schema_model=_DecisionResponse,
        factory=_decision_factory,
    ),
    _RoleSpec(
        name="tot_branch",
        system_fingerprint="evaluating ONE candidate move",
        schema_model=_ToTBranchResponse,
        factory=_tot_branch_factory,
    ),
    _RoleSpec(
        name="reflection",
        system_fingerprint="generate a short.*postmortem",
        schema_model=_ReflectionResponse,
        factory=_reflection_factory,
    ),
    _RoleSpec(
        name="importance",
        system_fingerprint="rate this event 1.10 for memorability",
        schema_model=_ImportanceResponse,
        factory=_importance_factory,
    ),
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

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 200,
        temperature: float = 0.7,
    ) -> tuple[str, _Usage]:
        last_text = self._extract_last_user_text(messages)
        ctx = {
            "system": system,
            "messages": messages,
            "last_text": last_text,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Escape hatches first
        if self.script:
            response = self.script.pop(0)
        elif (
            keyed := next((v for k, v in self.keyed.items() if k in last_text), None)
        ) is not None:
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
                role = _ROLES[0]
            factory = self.factories.get(role.name, role.factory)
            payload = factory(ctx)
            try:
                role.schema_model.model_validate(payload)
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
                    return str(part.get("text", ""))
            return ""
        return content if isinstance(content, str) else ""
