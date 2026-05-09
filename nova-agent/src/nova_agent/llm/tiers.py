"""Five model tiers selected by NOVA_TIER (§6.6). Default `dev`.

plumbing   — UI-dev / smoke / infra-only mode. Flash-Lite EVERYWHERE.
             SAFE only because every JSON-required callsite passes a
             pydantic `response_schema` (see ADR-0006); Flash-Lite drifts
             on prompt-only JSON mode but Gemini's OpenAPI 3.0 schema
             enforcement guarantees structural validity. Use ONLY for
             UI work, bus plumbing, integration smoke tests — NEVER for
             tuning Arbiter thresholds, evaluating Tree-of-Thoughts
             quality, or any cognitive-judgment work; Flash-Lite trims
             multi-step deliberation and produces shallow reasoning.
dev        — Flash-everywhere (reverted from Haiku 2026-05-08: Anthropic
             529 overloaded errors killed pilot mid-run; Flash quota resets
             daily at midnight Pacific and is sufficient for one full pilot
             run ~4K calls). Flash-Lite kept for importance_rating.
production — Week 5–6 §8 acceptance: Flash for decision/bot, Sonnet 4.6
             for tot + reflection. ToT moved Pro → Sonnet 4.6 in
             ADR-0006 Amendment 1 (2026-05-06) — the 1000 RPD daily
             quota on Gemini Pro is too tight for the cliff-test
             workload; Sonnet has no per-day call cap and avoids the
             rate-limit-clustering failure mode surfaced in the
             2026-05-06 pilot.
demo       — Week 6 LinkedIn recording: Sonnet 4.6 everywhere.
phase_0_7a — One-shot tier for the Phase 0.7a counterfactual run
             (spec docs/superpowers/specs/2026-05-09-phase-0.7a-
             counterfactual-design.md §2.2). Gemini 2.5 Pro PAID-tier on
             every cognitive role to reproduce the 2026-05-06 morning-
             pilot model surface while testing the
             null_empty_cells_anxiety_term ablation. Paid tier required:
             N=15 trial × ~105 calls/trial ≈ 1575 requests > 1000 RPD
             free-tier limit (§5.1). Cost guardrails: per-call abort
             $0.50 (NOVA_PER_CALL_COST_ABORT_USD), session cap $5–7
             (NOVA_SESSION_CAP_USD). DO NOT use for production, demo,
             or any non-counterfactual run — daily-quota and per-call-
             cost tradeoffs make this tier unsuitable for sustained
             work. ADR-0006 Amendment 1 still governs all other tiers.
"""

from __future__ import annotations

import os
from typing import Literal, TypedDict, get_args

TierName = Literal["plumbing", "dev", "production", "demo", "phase_0_7a"]


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
        # ADR-0006 Amendment 1 (2026-05-06): ToT moved from gemini-2.5-pro
        # to claude-sonnet-4-6. Pro's 1000 RPD shared daily quota cannot
        # absorb a Phase 0.7 N=20 run (~4× over budget) and rate-limit
        # clustering at any non-trivial concurrency produced a 20% Carla
        # trial-abort rate in the 2026-05-06 pilot. Sonnet has no per-day
        # call cap, comparable reasoning depth, and ~1.9× per-call cost —
        # which keeps the full Phase 0.7 run under the spec §2.6 cap.
        "tot": "claude-sonnet-4-6",
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
    "phase_0_7a": {
        "decision": "gemini-2.5-pro",
        "tot": "gemini-2.5-pro",
        "tot_branches": 4,
        "reflection": "gemini-2.5-pro",
        "perception_fallback": "gemini-2.5-pro",
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
