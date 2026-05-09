"""Smoke test for Item-2 K-sweep validation.

Per shape-check spec §10 step 2: lab-tier code, smoke test on synthetic
per_move JSONL is sufficient.
"""

from __future__ import annotations

import json
from pathlib import Path

from nova_agent.lab.shape_check_item2_validation import (
    ANXIETY_DECAY,
    ANXIETY_THRESHOLD,
    PerMoveFrustration,
    aggregate_scenario,
    compute_trial_metrics,
    load_per_move_frustration,
    simulate_anxiety_trajectory,
)


def _write_synthetic_jsonl(path: Path, frustration_trajectory: list[float]) -> None:
    lines: list[str] = []
    for i, frustration in enumerate(frustration_trajectory):
        record = {
            "t": 0.0,
            "event": "per_move",
            "data": {
                "move_index": i,
                "empty_cells_pre": 4,
                "empty_cells_post": 4,
                "affect_vector": {
                    "valence": 0.0,
                    "arousal": 0.0,
                    "dopamine": 0.0,
                    "frustration": frustration,
                    "anxiety": 0.0,
                    "confidence": 0.5,
                },
                "trauma_intensity": 0.0,
                "tot_fired": False,
                "chosen_action": "swipe_up",
            },
        }
        lines.append(json.dumps(record))
    path.write_text("\n".join(lines) + "\n")


def test_load_per_move_frustration_skips_non_per_move(tmp_path: Path) -> None:
    f = tmp_path / "events.jsonl"
    f.write_text(
        '{"t":0,"event":"other","data":{}}\n'
        '{"t":1,"event":"per_move","data":{"move_index":0,'
        '"empty_cells_pre":4,"empty_cells_post":4,'
        '"affect_vector":{"frustration":0.1,"valence":0,"arousal":0,'
        '"dopamine":0,"anxiety":0,"confidence":0},'
        '"trauma_intensity":0,"tot_fired":false,"chosen_action":"swipe_up"}}\n'
    )
    events = load_per_move_frustration(f)
    assert len(events) == 1
    assert events[0].move_index == 0
    assert events[0].frustration == 0.1


def test_simulate_anxiety_trajectory_matches_recurrence() -> None:
    events = [
        PerMoveFrustration(move_index=0, frustration=0.5),
        PerMoveFrustration(move_index=1, frustration=0.5),
        PerMoveFrustration(move_index=2, frustration=0.5),
    ]
    traj = simulate_anxiety_trajectory(events, k=1.0)
    # t=0: 0.85*0 + 1.0*0.5 = 0.5
    # t=1: 0.85*0.5 + 0.5 = 0.925
    # t=2: 0.85*0.925 + 0.5 = 1.28625 → cap 1.0
    assert traj[0] == 0.5
    assert traj[1] == 0.85 * 0.5 + 0.5
    assert traj[2] == 1.0  # capped


def test_simulate_anxiety_trajectory_clamps_negative_frustration() -> None:
    events = [PerMoveFrustration(move_index=0, frustration=-0.5)]
    traj = simulate_anxiety_trajectory(events, k=1.0)
    assert traj[0] == 0.0


def test_compute_trial_metrics_no_crossing(tmp_path: Path) -> None:
    events = [PerMoveFrustration(move_index=i, frustration=0.001) for i in range(10)]
    m = compute_trial_metrics(events, k=0.5, scenario="test", trial=0)
    assert m.final_move_index == 9
    assert m.crossing_within_5 is False
    assert m.false_positive_crossings == 0
    assert m.cap_saturation_freq == 0.0
    assert m.max_simulated_anxiety < ANXIETY_THRESHOLD


def test_compute_trial_metrics_crossing_in_window() -> None:
    # Frustration spikes at last few moves so anxiety crosses inside window.
    events = [PerMoveFrustration(move_index=i, frustration=0.0) for i in range(10)]
    events.extend(PerMoveFrustration(move_index=10 + i, frustration=1.0) for i in range(5))
    m = compute_trial_metrics(events, k=1.0, scenario="test", trial=0)
    assert m.final_move_index == 14
    assert m.crossing_within_5 is True


def test_compute_trial_metrics_false_positive_crossing() -> None:
    # Crossing at move 0..2 (early), then fall off, then no crossing near end.
    events = [PerMoveFrustration(move_index=i, frustration=2.0) for i in range(3)]
    events.extend(PerMoveFrustration(move_index=3 + i, frustration=0.0) for i in range(20))
    m = compute_trial_metrics(events, k=1.0, scenario="test", trial=0)
    # Anxiety crosses 0.6 at move 0; final is move 22; gap = 22 → false positive.
    assert m.false_positive_crossings >= 1
    # Last 5 moves: anxiety has decayed to 0 → no crossing in window.
    assert m.crossing_within_5 is False


def test_compute_trial_metrics_cap_saturation_high() -> None:
    # Sustained high frustration → anxiety saturates.
    events = [PerMoveFrustration(move_index=i, frustration=1.0) for i in range(10)]
    m = compute_trial_metrics(events, k=10.0, scenario="test", trial=0)
    assert m.crossing_within_5 is True
    # Most crossing events should be at cap.
    assert m.cap_saturation_freq > 0.5


def test_aggregate_scenario_passes_when_4_of_5_cross() -> None:
    trials = [
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.5) for i in range(10)],
            k=1.0,
            scenario="test",
            trial=trial_idx,
        )
        for trial_idx in range(4)
    ]
    trials.append(
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.001) for i in range(10)],
            k=1.0,
            scenario="test",
            trial=4,
        )
    )
    verdict = aggregate_scenario(trials)
    assert verdict.crossing_rate == 4 / 5
    assert verdict.passes_a is True


def test_aggregate_scenario_fails_when_3_of_5_cross() -> None:
    trials = [
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.5) for i in range(10)],
            k=1.0,
            scenario="test",
            trial=trial_idx,
        )
        for trial_idx in range(3)
    ]
    trials.extend(
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.001) for i in range(10)],
            k=1.0,
            scenario="test",
            trial=trial_idx,
        )
        for trial_idx in range(3, 5)
    )
    verdict = aggregate_scenario(trials)
    assert verdict.crossing_rate == 3 / 5
    assert verdict.passes_a is False


def test_anxiety_decay_constant_matches_state_py() -> None:
    """Sanity: the decay constant matches state.py:37."""
    assert ANXIETY_DECAY == 0.85


def test_aggregate_scenario_false_positive_rate_is_binary_per_trial() -> None:
    """Spec §4.2(b) — fraction of trials with ANY false positive, not avg count.

    Build 5 trials where one trial has 3 false positives and others have 0.
    Per-trial-binary aggregation: 1/5 = 0.20 (passes ≤ 1/5 threshold).
    Avg-count aggregation would be: 3/5 = 0.60 (would fail 0.20 threshold).
    """
    # Trial 0: 3 distinct early crossings (3 false positives), then quiet.
    early_burst_events = [PerMoveFrustration(move_index=i, frustration=10.0) for i in range(2)]
    early_burst_events.extend(
        PerMoveFrustration(move_index=2 + i, frustration=0.0) for i in range(5)
    )
    early_burst_events.extend(
        PerMoveFrustration(move_index=7 + i, frustration=10.0) for i in range(2)
    )
    early_burst_events.extend(
        PerMoveFrustration(move_index=9 + i, frustration=0.0) for i in range(5)
    )
    early_burst_events.extend(
        PerMoveFrustration(move_index=14 + i, frustration=10.0) for i in range(2)
    )
    early_burst_events.extend(
        PerMoveFrustration(move_index=16 + i, frustration=0.0) for i in range(20)
    )

    multi_fp_trial = compute_trial_metrics(early_burst_events, k=1.0, scenario="test", trial=0)
    assert multi_fp_trial.false_positive_crossings >= 2

    # Trials 1–4: quiet — zero false positives.
    quiet_trials = [
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.001) for i in range(20)],
            k=1.0,
            scenario="test",
            trial=trial_idx,
        )
        for trial_idx in range(1, 5)
    ]
    trials = [multi_fp_trial, *quiet_trials]
    verdict = aggregate_scenario(trials)
    assert verdict.false_positive_rate == 1 / 5
    assert verdict.passes_b is True


def test_aggregate_scenario_false_positive_rate_fails_when_two_trials_have_fps() -> None:
    """Two trials with FPs → 2/5 rate → fails ≤ 1/5 threshold."""
    fp_trial_events = [PerMoveFrustration(move_index=i, frustration=2.0) for i in range(3)]
    fp_trial_events.extend(PerMoveFrustration(move_index=3 + i, frustration=0.0) for i in range(20))

    fp_trials = [
        compute_trial_metrics(fp_trial_events, k=1.0, scenario="test", trial=i) for i in range(2)
    ]
    quiet_trials = [
        compute_trial_metrics(
            [PerMoveFrustration(move_index=i, frustration=0.001) for i in range(20)],
            k=1.0,
            scenario="test",
            trial=i,
        )
        for i in range(2, 5)
    ]
    verdict = aggregate_scenario([*fp_trials, *quiet_trials])
    assert verdict.false_positive_rate == 2 / 5
    assert verdict.passes_b is False


def test_compute_trial_metrics_false_positive_boundary_at_5_moves() -> None:
    """Exactly 5 moves between an early crossing and final → counts as FP.

    Spec §4.1: false_positive_crossings = crossings ≥ 5 moves before
    final_move_index. The boundary inclusive.
    """
    events = [
        PerMoveFrustration(move_index=0, frustration=2.0),
        PerMoveFrustration(move_index=1, frustration=0.0),
        PerMoveFrustration(move_index=2, frustration=0.0),
        PerMoveFrustration(move_index=3, frustration=0.0),
        PerMoveFrustration(move_index=4, frustration=0.0),
        PerMoveFrustration(move_index=5, frustration=0.0),
    ]
    m = compute_trial_metrics(events, k=1.0, scenario="test", trial=0)
    # Crossing happens at t=0; final is t=5; gap = 5 → FALSE_POSITIVE_GAP_MOVES
    # is met inclusive.
    assert m.false_positive_crossings == 1


def test_compute_trial_metrics_false_positive_below_boundary_at_4_moves() -> None:
    """4 moves between an early crossing and final → does NOT count as FP."""
    events = [
        PerMoveFrustration(move_index=0, frustration=2.0),
        PerMoveFrustration(move_index=1, frustration=0.0),
        PerMoveFrustration(move_index=2, frustration=0.0),
        PerMoveFrustration(move_index=3, frustration=0.0),
        PerMoveFrustration(move_index=4, frustration=0.0),
    ]
    m = compute_trial_metrics(events, k=1.0, scenario="test", trial=0)
    # Crossing at t=0; final t=4; gap=4 < FALSE_POSITIVE_GAP_MOVES → not FP.
    assert m.false_positive_crossings == 0
