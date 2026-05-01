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

AVERSIVE_TAG = "aversive"
AVERSIVE_INITIAL_WEIGHT = 1.0
AVERSIVE_INERT_THRESHOLD = 0.02


def is_catastrophic_loss(*, final_score: int, max_tile_reached: int, last_empty_cells: int) -> bool:
    """Catastrophic iff the board was contested (few empty cells) AND the
    score under-performed relative to the max tile achieved.
    """
    return last_empty_cells <= 2 and max_tile_reached >= 64 and final_score < max_tile_reached * 4


def tag_aversive(
    *, precondition_records: list[MemoryRecord], was_catastrophic: bool
) -> list[MemoryRecord]:
    """Mark precondition boards aversive after a catastrophic loss.

    Importance bumped by +3 with a floor of 7 (so a low-importance
    precondition still clears the vector-store retrieval threshold), capped
    at 10. Tags merged with `aversive` + `loss_precondition`,
    aversive_weight set to AVERSIVE_INITIAL_WEIGHT.
    """
    if not was_catastrophic:
        return precondition_records

    tagged: list[MemoryRecord] = []
    for r in precondition_records:
        new_tags = list(dict.fromkeys([*r.tags, AVERSIVE_TAG, "loss_precondition"]))
        new_importance = min(10, max(7, r.importance + 3))
        tagged.append(
            replace(
                r,
                tags=new_tags,
                importance=new_importance,
                aversive_weight=AVERSIVE_INITIAL_WEIGHT,
            )
        )
    return tagged


def exposure_extinction_halve(record: MemoryRecord) -> MemoryRecord:
    """Defense B (primary, deterministic): halve aversive_weight on each survival.

    After ~6 survivals the weight is < 0.02 and is treated as inert by
    retrieval. The spiral terminates mathematically, not via LLM cooperation.
    """
    if AVERSIVE_TAG not in record.tags:
        return record
    new_weight = max(0.0, record.aversive_weight * 0.5)
    return replace(record, aversive_weight=new_weight)


def is_inert(record: MemoryRecord) -> bool:
    return AVERSIVE_TAG in record.tags and record.aversive_weight < AVERSIVE_INERT_THRESHOLD
