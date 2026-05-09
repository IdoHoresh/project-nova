"""Item-2 (frustration → anxiety) validation per shape-check spec §4.

Replays Phase 0.7a per-move frustration trajectories under candidate K values
and reports whether any K satisfies the acceptance criteria:

- (a) crossing_within_5 ≥ 4/5 per scenario, on both scenarios independently
- (b) false_positive_crossings ≤ 1/5 per scenario, on both scenarios independently
- (c) cap_saturation_freq < 0.50 of crossing events

Spec: docs/superpowers/specs/2026-05-09-3rd-driver-shape-check-design.md §4
Source data: docs/external-review/phase-0.7a-raw-2026-05-09/results/
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

ANXIETY_THRESHOLD: float = 0.6
ANXIETY_DECAY: float = 0.85
ANXIETY_CAP: float = 1.0
WINDOW_LAST_MOVES: int = 5
FALSE_POSITIVE_GAP_MOVES: int = 5
CAP_TOLERANCE: float = 1e-9
CROSSING_THRESHOLD_FRACTION: float = 4 / 5
FALSE_POSITIVE_THRESHOLD_RATE: float = 1 / 5
CAP_SATURATION_THRESHOLD: float = 0.50

K_SWEEP: tuple[float, ...] = (0.5, 1.0, 1.73, 2.5, 5.0, 7.5, 10.0)
SCENARIOS: tuple[str, ...] = ("snake-collapse-128", "corner-abandonment-256")
TRIALS_PER_SCENARIO: tuple[int, ...] = (0, 1, 2, 3, 4)


class PerMoveFrustration(BaseModel):
    move_index: int
    frustration: float


class TrialMetrics(BaseModel):
    scenario: str
    trial: int
    k: float
    final_move_index: int
    crossing_within_5: bool
    false_positive_crossings: int
    cap_saturation_freq: float
    max_simulated_anxiety: float


class ScenarioVerdict(BaseModel):
    scenario: str
    k: float
    crossing_rate: float
    false_positive_rate: float
    cap_saturation_freq: float
    passes_a: bool
    passes_b: bool
    passes_c: bool


class KVerdict(BaseModel):
    k: float
    snake_verdict: ScenarioVerdict
    corner_verdict: ScenarioVerdict
    passes: bool


def load_per_move_frustration(path: Path) -> list[PerMoveFrustration]:
    """Read Phase 0.7a per_move events; return frustration trajectory."""
    events: list[PerMoveFrustration] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("event") != "per_move":
            continue
        data = record["data"]
        events.append(
            PerMoveFrustration(
                move_index=data["move_index"],
                frustration=data["affect_vector"]["frustration"],
            )
        )
    return events


def simulate_anxiety_trajectory(events: list[PerMoveFrustration], k: float) -> list[float]:
    """Replay anxiety under Items-1+2 only formula:

    anxiety_t = ANXIETY_DECAY * anxiety_{t-1} + k * clamp(frustration_t, 0, 1)

    No empty_cells term (Item 1 = remove); no trauma_intensity (was 0/658 on
    Phase 0.7a). Capped at ANXIETY_CAP.
    """
    anxiety = 0.0
    trajectory: list[float] = []
    for ev in events:
        clamped_frustration = max(0.0, min(1.0, ev.frustration))
        anxiety = ANXIETY_DECAY * anxiety + k * clamped_frustration
        anxiety = min(ANXIETY_CAP, anxiety)
        trajectory.append(anxiety)
    return trajectory


def compute_trial_metrics(
    events: list[PerMoveFrustration], k: float, scenario: str, trial: int
) -> TrialMetrics:
    """Compute (a), (b), (c) per spec §4.1."""
    trajectory = simulate_anxiety_trajectory(events, k)
    if not trajectory:
        return TrialMetrics(
            scenario=scenario,
            trial=trial,
            k=k,
            final_move_index=-1,
            crossing_within_5=False,
            false_positive_crossings=0,
            cap_saturation_freq=0.0,
            max_simulated_anxiety=0.0,
        )

    final_move_index = events[-1].move_index

    # (a) crossing_within_5 — anxiety reaches threshold in last WINDOW_LAST_MOVES
    window_start = max(0, len(trajectory) - WINDOW_LAST_MOVES - 1)
    window_anxiety = trajectory[window_start:]
    crossing_within_5 = any(a >= ANXIETY_THRESHOLD for a in window_anxiety)

    # (b) false_positive_crossings — distinct crossings (rising edges) where
    #     final_move_index - t >= FALSE_POSITIVE_GAP_MOVES
    false_positives = 0
    in_crossing = False
    for t, a in enumerate(trajectory):
        if a >= ANXIETY_THRESHOLD:
            if not in_crossing:
                in_crossing = True
                if (len(trajectory) - 1 - t) >= FALSE_POSITIVE_GAP_MOVES:
                    false_positives += 1
        else:
            in_crossing = False

    # (c) cap_saturation_freq — fraction of above-threshold events at the cap
    crossing_events = [a for a in trajectory if a >= ANXIETY_THRESHOLD]
    if crossing_events:
        cap_saturated = sum(1 for a in crossing_events if a >= ANXIETY_CAP - CAP_TOLERANCE)
        cap_saturation_freq = cap_saturated / len(crossing_events)
    else:
        cap_saturation_freq = 0.0

    return TrialMetrics(
        scenario=scenario,
        trial=trial,
        k=k,
        final_move_index=final_move_index,
        crossing_within_5=crossing_within_5,
        false_positive_crossings=false_positives,
        cap_saturation_freq=cap_saturation_freq,
        max_simulated_anxiety=max(trajectory),
    )


def aggregate_scenario(trials: list[TrialMetrics]) -> ScenarioVerdict:
    """Aggregate 5 trials into a per-K-per-scenario verdict.

    Spec §4.2 acceptance criteria parallelism:
    - (a) crossing_within_5 ≥ 4/5 → fraction of trials with crossing_within_5
    - (b) false_positive_crossings ≤ 1/5 → fraction of trials with ANY false
          positive (≤ 1 trial out of 5 may have any false-positive crossing)
    - (c) cap_saturation_freq < 0.50 → averaged across trials that crossed
    """
    n = len(trials)
    crossing_rate = sum(1 for t in trials if t.crossing_within_5) / n
    false_positive_rate = sum(1 for t in trials if t.false_positive_crossings > 0) / n
    crossing_trials_cap_freqs = [t.cap_saturation_freq for t in trials if t.crossing_within_5]
    cap_saturation_freq = (
        sum(crossing_trials_cap_freqs) / len(crossing_trials_cap_freqs)
        if crossing_trials_cap_freqs
        else 0.0
    )
    return ScenarioVerdict(
        scenario=trials[0].scenario,
        k=trials[0].k,
        crossing_rate=crossing_rate,
        false_positive_rate=false_positive_rate,
        cap_saturation_freq=cap_saturation_freq,
        passes_a=crossing_rate >= CROSSING_THRESHOLD_FRACTION,
        passes_b=false_positive_rate <= FALSE_POSITIVE_THRESHOLD_RATE,
        passes_c=cap_saturation_freq < CAP_SATURATION_THRESHOLD,
    )


def run_validation(results_dir: Path) -> list[KVerdict]:
    """One KVerdict per K in K_SWEEP."""
    verdicts: list[KVerdict] = []
    for k in K_SWEEP:
        scenario_verdicts: list[ScenarioVerdict] = []
        for scenario in SCENARIOS:
            trials: list[TrialMetrics] = []
            for trial_idx in TRIALS_PER_SCENARIO:
                path = results_dir / f"events_{scenario}_carla_{trial_idx}.jsonl"
                events = load_per_move_frustration(path)
                trials.append(compute_trial_metrics(events, k, scenario, trial_idx))
            scenario_verdicts.append(aggregate_scenario(trials))
        snake_v, corner_v = scenario_verdicts
        passes = (
            snake_v.passes_a
            and snake_v.passes_b
            and snake_v.passes_c
            and corner_v.passes_a
            and corner_v.passes_b
            and corner_v.passes_c
        )
        verdicts.append(
            KVerdict(k=k, snake_verdict=snake_v, corner_verdict=corner_v, passes=passes)
        )
    return verdicts


def format_verdict_table(verdicts: list[KVerdict]) -> str:
    """Markdown table of K-sweep results."""
    lines = [
        "| K     | snake (a/b/c) | corner (a/b/c) | passes |",
        "|------:|:--------------|:---------------|:------:|",
    ]
    for v in verdicts:
        sv = v.snake_verdict
        cv = v.corner_verdict
        snake_cell = (
            f"a={sv.crossing_rate:.2f} {'✓' if sv.passes_a else '✗'} / "
            f"b={sv.false_positive_rate:.2f} {'✓' if sv.passes_b else '✗'} / "
            f"c={sv.cap_saturation_freq:.2f} {'✓' if sv.passes_c else '✗'}"
        )
        corner_cell = (
            f"a={cv.crossing_rate:.2f} {'✓' if cv.passes_a else '✗'} / "
            f"b={cv.false_positive_rate:.2f} {'✓' if cv.passes_b else '✗'} / "
            f"c={cv.cap_saturation_freq:.2f} {'✓' if cv.passes_c else '✗'}"
        )
        passes_cell = "✓" if v.passes else "✗"
        lines.append(f"| {v.k:>5} | {snake_cell} | {corner_cell} | {passes_cell} |")
    return "\n".join(lines)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    results_dir = repo_root / "docs/external-review/phase-0.7a-raw-2026-05-09/results"
    if not results_dir.is_dir():
        raise FileNotFoundError(f"Phase 0.7a results dir not found: {results_dir}")

    verdicts = run_validation(results_dir)

    print("# Item-2 Validation — K-sweep verdict\n")
    print(format_verdict_table(verdicts))
    print()
    passing_ks = [v.k for v in verdicts if v.passes]
    if passing_ks:
        print(f"## Overall: ITEM-2 VALIDATION PASSES for K ∈ {passing_ks}")
    else:
        print("## Overall: ITEM-2 VALIDATION FAILS")
        print(
            "No K satisfies all three criteria on both scenarios. "
            "Per spec §4.3: Q2 is NOT empirically closed by Item 2 alone. "
            "Halt; convene fresh redteam round."
        )

    print("\n## Per-trial detail")
    for v in verdicts:
        print(f"\n### K = {v.k}")
        print(
            f"  snake: crossing_rate={v.snake_verdict.crossing_rate:.2f}, "
            f"false_positive_rate={v.snake_verdict.false_positive_rate:.2f}, "
            f"cap_sat_freq={v.snake_verdict.cap_saturation_freq:.2f}"
        )
        print(
            f"  corner: crossing_rate={v.corner_verdict.crossing_rate:.2f}, "
            f"false_positive_rate={v.corner_verdict.false_positive_rate:.2f}, "
            f"cap_sat_freq={v.corner_verdict.cap_saturation_freq:.2f}"
        )


if __name__ == "__main__":
    main()
