"""Desk demonstration — round 2 reviewer's un-dodgeable attack.

For each candidate function f(frustration, decay, trauma_intensity), simulate
the anxiety dynamic on the existing 658-event Phase 0.7a data and check
whether anxiety crosses 0.6 for ≥2 consecutive moves (t_predicts != None
per spec §2.7) on at least 4 of 5 trials in any scenario.

Honest input set: trauma_intensity = 0.0 on every event, so any function
f(frustration, decay, trauma) reduces to f(frustration, decay). Decay enters
through the dynamic anxiety_t = 0.85 * anxiety_{t-1} + new_term, so it's
the formula's recurrence, not an independent input.

Candidate functions tested:
  f1: anxiety_t = 0.85*anxiety_{t-1} + K * frustration_t            (linear)
  f2: anxiety_t = 0.85*anxiety_{t-1} + K * sqrt(frustration_t)      (sqrt)
  f3: anxiety_t = 0.85*anxiety_{t-1} + K * (frustration_t)**2       (quadratic)
  f4: anxiety_t = 0.85*anxiety_{t-1} + K * cumulative_frustration_t (running)

For each, sweep K and report the lowest K that produces t_predicts != None
on ≥4/5 trials in at least one scenario.

Run: python3 docs/external-review/decisions/2026-05-09-rpe-pivot-desk-demo.py
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Callable

RESULTS_DIR = Path(
    "/Users/idohoresh/Desktop/a/docs/external-review/"
    "phase-0.7a-raw-2026-05-09/results"
)
DECAY = 0.85
THRESHOLD = 0.6
CONSECUTIVE_REQUIRED = 2  # spec §2.7: anxiety > 0.6 for ≥2 consecutive moves


def t_predicts_for_anxiety_series(anxiety: list[float]) -> int | None:
    """Spec §2.7: first move where anxiety > THRESHOLD for ≥2 consecutive moves."""
    for i in range(len(anxiety) - CONSECUTIVE_REQUIRED + 1):
        if all(anxiety[j] > THRESHOLD for j in range(i, i + CONSECUTIVE_REQUIRED)):
            return i
    return None


def simulate_trial(
    frustration_series: list[float],
    contribution_fn: Callable[[float, list[float], int], float],
) -> int | None:
    """Run anxiety_t = DECAY * anxiety_{t-1} + contribution_fn(...)."""
    anxiety = 0.0
    series: list[float] = []
    cumulative = 0.0
    for i, f in enumerate(frustration_series):
        cumulative += f
        contribution = contribution_fn(f, frustration_series, i)
        anxiety = DECAY * anxiety + contribution
        anxiety = max(0.0, min(1.0, anxiety))  # _clamp like state.py
        series.append(anxiety)
    return t_predicts_for_anxiety_series(series)


def load_trials() -> dict[str, list[list[float]]]:
    """Per scenario, list of frustration time series (one per trial)."""
    trials: dict[str, list[list[float]]] = defaultdict(list)
    for path in sorted(RESULTS_DIR.glob("events_*_carla_*.jsonl")):
        scenario = path.stem.split("_")[1]
        series = []
        for line in path.read_text().splitlines():
            evt = json.loads(line)
            if evt["event"] != "per_move":
                continue
            series.append(evt["data"]["affect_vector"]["frustration"])
        trials[scenario].append(series)
    return trials


def evaluate_function(
    name: str,
    contribution_fn: Callable[[float, list[float], int], float],
    trials: dict[str, list[list[float]]],
) -> dict[str, dict[str, int | float]]:
    """For each scenario, compute t_predicts hits and stats."""
    out: dict[str, dict[str, int | float]] = {}
    for scenario, series_list in trials.items():
        hits = 0
        max_anx = 0.0
        for series in series_list:
            # Reproduce simulate_trial inline to capture max anxiety
            anxiety = 0.0
            anx_series = []
            for i, f in enumerate(series):
                contribution = contribution_fn(f, series, i)
                anxiety = max(0.0, min(1.0, DECAY * anxiety + contribution))
                anx_series.append(anxiety)
            max_anx = max(max_anx, max(anx_series))
            if t_predicts_for_anxiety_series(anx_series) is not None:
                hits += 1
        out[scenario] = {"hits": hits, "n": len(series_list), "max_anx": max_anx}
    return out


def main() -> None:
    trials = load_trials()
    n_scenarios = len(trials)
    n_total_trials = sum(len(s) for s in trials.values())
    print(f"Loaded {n_scenarios} scenarios, {n_total_trials} trials total")
    print(f"Threshold: anxiety > {THRESHOLD} for ≥{CONSECUTIVE_REQUIRED} consec moves")
    print(f"Anxiety dynamics: a_t = {DECAY} * a_{{t-1}} + contribution_t")
    print(f"Pass criterion: ≥4/5 trials in at least one scenario")
    print()

    # Sweep K for each function family
    print("=" * 70)
    print("f1 — LINEAR: contribution = K * frustration")
    print("=" * 70)
    for K in [1, 5, 10, 12, 15, 20, 30, 50, 100]:
        result = evaluate_function(
            f"linear K={K}",
            lambda f, s, i, K=K: K * f,
            trials,
        )
        worst_hits = min(r["hits"] for r in result.values())
        best_hits = max(r["hits"] for r in result.values())
        max_anx = max(r["max_anx"] for r in result.values())
        passing_scenarios = sum(1 for r in result.values() if r["hits"] >= 4)
        verdict = "PASS" if passing_scenarios >= 1 else "FAIL"
        print(
            f"  K={K:3d}: max_anx={max_anx:.4f}  hits per scenario "
            f"= {[r['hits'] for r in result.values()]}  → {verdict}"
        )

    print()
    print("=" * 70)
    print("f2 — SQRT: contribution = K * sqrt(frustration)")
    print("=" * 70)
    for K in [1, 2, 3, 5, 10, 20]:
        result = evaluate_function(
            f"sqrt K={K}",
            lambda f, s, i, K=K: K * math.sqrt(f),
            trials,
        )
        max_anx = max(r["max_anx"] for r in result.values())
        passing_scenarios = sum(1 for r in result.values() if r["hits"] >= 4)
        verdict = "PASS" if passing_scenarios >= 1 else "FAIL"
        print(
            f"  K={K:3d}: max_anx={max_anx:.4f}  hits per scenario "
            f"= {[r['hits'] for r in result.values()]}  → {verdict}"
        )

    print()
    print("=" * 70)
    print("f3 — QUADRATIC: contribution = K * frustration^2")
    print("=" * 70)
    for K in [10, 100, 500, 1000, 5000]:
        result = evaluate_function(
            f"quad K={K}",
            lambda f, s, i, K=K: K * f * f,
            trials,
        )
        max_anx = max(r["max_anx"] for r in result.values())
        passing_scenarios = sum(1 for r in result.values() if r["hits"] >= 4)
        verdict = "PASS" if passing_scenarios >= 1 else "FAIL"
        print(
            f"  K={K:5d}: max_anx={max_anx:.4f}  hits per scenario "
            f"= {[r['hits'] for r in result.values()]}  → {verdict}"
        )

    print()
    print("=" * 70)
    print("f4 — CUMULATIVE: contribution = K * (sum of frustration so far)")
    print("=" * 70)
    cum_state: dict[int, float] = {}

    def cum_fn(f: float, s: list[float], i: int, K: int) -> float:
        # Reset cumulative per trial; trial boundary detected by index reset
        if i == 0:
            cum_state[K] = 0.0
        cum_state[K] = cum_state.get(K, 0.0) + f
        return K * cum_state[K]

    for K in [0.01, 0.05, 0.1, 0.5, 1.0]:
        cum_state.clear()
        result = evaluate_function(
            f"cum K={K}",
            lambda f, s, i, K=K: cum_fn(f, s, i, int(K * 1000)),
            trials,
        )
        max_anx = max(r["max_anx"] for r in result.values())
        passing_scenarios = sum(1 for r in result.values() if r["hits"] >= 4)
        verdict = "PASS" if passing_scenarios >= 1 else "FAIL"
        print(
            f"  K={K:5.2f}: max_anx={max_anx:.4f}  hits per scenario "
            f"= {[r['hits'] for r in result.values()]}  → {verdict}"
        )

    print()
    print("=" * 70)
    print("INTERPRETATION (per round 2 reviewer):")
    print("=" * 70)
    print(
        "Pass criterion: max_anx ≥ 0.6 AND ≥4/5 trials in at least one\n"
        "scenario produce t_predicts != None.\n"
        "\n"
        "If at least one (function, K) combination passes →\n"
        "  P5 wiring-only scope is closer to sufficient than round 2 credits.\n"
        "  Lock P5 wiring-only.\n"
        "\n"
        "If NO (function, K) combination passes →\n"
        "  P5 is missing the magnitude axis. Rewrite ADR has 2 scope items:\n"
        "  (1) wiring + (2) magnitude restructure (e.g., scaling, accumulation,\n"
        "  threshold lowering, OR a new driver entirely independent of\n"
        "  the frustration distribution).\n"
        "\n"
        "WARNING about saturation (round 2 §4.5 risk):\n"
        "  A function that hits max_anx = 1.0 only at the absolute peak of\n"
        "  frustration is not 'predictive lead-time' — it's mechanical sync\n"
        "  with the worst-case board. Look for max_anx that crosses 0.6 a\n"
        "  few moves before the natural game-over, not just at it.\n"
    )


if __name__ == "__main__":
    main()
