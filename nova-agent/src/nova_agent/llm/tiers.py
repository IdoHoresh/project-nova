"""Four model tiers selected by NOVA_TIER (§6.6). Default `dev`.

plumbing   — UI-dev / smoke / infra-only mode. Flash-Lite EVERYWHERE.
             SAFE only because every JSON-required callsite passes a
             pydantic `response_schema` (see ADR-0006); Flash-Lite drifts
             on prompt-only JSON mode but Gemini's OpenAPI 3.0 schema
             enforcement guarantees structural validity. Use ONLY for
             UI work, bus plumbing, integration smoke tests — NEVER for
             tuning Arbiter thresholds, evaluating Tree-of-Thoughts
             quality, or any cognitive-judgment work; Flash-Lite trims
             multi-step deliberation and produces shallow reasoning.
dev        — daily Flash-everywhere (Flash-Lite is rejected for decisions
             due to documented JSON reliability issues; kept for
             importance_rating only).
production — Week 5–6 §8 acceptance: Flash + Pro + Sonnet 4.6.
demo       — Week 6 LinkedIn recording: Sonnet 4.6 everywhere.
"""

from __future__ import annotations

import os
from typing import Literal, TypedDict, get_args

TierName = Literal["plumbing", "dev", "production", "demo"]


class TierConfig(TypedDict):
    decision: str
    tot: str
    tot_branches: int
    reflection: str
    perception_fallback: str
    importance_rating: str


TIERS: dict[TierName, TierConfig] = {
    "plumbing": {
        "decision": "gemini-2.5-flash-lite",
        "tot": "gemini-2.5-flash-lite",
        "tot_branches": 2,  # cheaper still — branch count drives cost linearly
        "reflection": "gemini-2.5-flash-lite",
        "perception_fallback": "gemini-2.5-flash-lite",
        "importance_rating": "gemini-2.5-flash-lite",
    },
    "dev": {
        "decision": "gemini-2.5-flash",
        "tot": "gemini-2.5-flash",
        "tot_branches": 3,
        "reflection": "gemini-2.5-flash",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating": "gemini-2.5-flash-lite",
    },
    "production": {
        "decision": "gemini-2.5-flash",
        "tot": "gemini-2.5-pro",
        "tot_branches": 4,
        "reflection": "claude-sonnet-4-6",
        "perception_fallback": "gemini-2.5-flash",
        "importance_rating": "gemini-2.5-flash-lite",
    },
    "demo": {
        "decision": "claude-sonnet-4-6",
        "tot": "claude-sonnet-4-6",
        "tot_branches": 4,
        "reflection": "claude-sonnet-4-6",
        "perception_fallback": "claude-sonnet-4-6",
        "importance_rating": "gemini-2.5-flash-lite",
    },
}


_TIER_NAMES: tuple[TierName, ...] = get_args(TierName)


def current_tier() -> TierName:
    val = os.environ.get("NOVA_TIER", "dev")
    for name in _TIER_NAMES:
        if val == name:
            return name
    raise ValueError(f"NOVA_TIER must be one of {list(_TIER_NAMES)}, got {val!r}")


def model_for(role: str) -> str | int:
    cfg = TIERS[current_tier()]
    if role not in cfg:
        raise KeyError(f"unknown role {role!r}; valid: {list(cfg)}")
    value: str | int = cfg[role]  # type: ignore[literal-required]
    return value
