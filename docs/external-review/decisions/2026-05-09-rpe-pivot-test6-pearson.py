"""Test 6 — contamination math + memory-silence diagnostic on Phase 0.7a JSONL.

Computes:
- Pearson(frustration, 1/empty_cells_pre) — Claude's proposed proxy
- Pearson(frustration, max(0, (3 - empty_cells_pre) / 3)) — the ACTUAL formula term
- trauma_intensity distribution across all per_move events
- frustration distribution across all per_move events

Run: python3 docs/external-review/decisions/2026-05-09-rpe-pivot-test6-pearson.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

RESULTS_DIR = Path(
    "/Users/idohoresh/Desktop/a/docs/external-review/"
    "phase-0.7a-raw-2026-05-09/results"
)


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("need matched non-empty vectors")
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def empty_cells_term(empty_cells_pre: int) -> float:
    """The actual driver in the formula at affect/state.py:50."""
    return 0.7 * max(0.0, (3 - empty_cells_pre) / 3)


def main() -> None:
    carla_files = sorted(RESULTS_DIR.glob("events_*_carla_*.jsonl"))
    assert len(carla_files) == 15, f"expected 15 carla files, got {len(carla_files)}"

    frustration: list[float] = []
    empty_pre: list[int] = []
    empty_term_vals: list[float] = []
    trauma: list[float] = []
    tot_fired: list[bool] = []
    per_scenario: dict[str, list[float]] = {
        "512-wall": [],
        "snake-collapse-128": [],
        "corner-abandonment-256": [],
    }

    for path in carla_files:
        scenario = path.stem.split("_")[1]
        for line in path.read_text().splitlines():
            evt = json.loads(line)
            if evt["event"] != "per_move":
                continue
            d = evt["data"]
            f = d["affect_vector"]["frustration"]
            ep = d["empty_cells_pre"]
            t = d["trauma_intensity"]
            frustration.append(f)
            empty_pre.append(ep)
            empty_term_vals.append(empty_cells_term(ep))
            trauma.append(t)
            tot_fired.append(d["tot_fired"])
            per_scenario[scenario].append(f)

    n = len(frustration)
    print(f"Total per_move events: {n}")
    print(f"Files loaded: {len(carla_files)}")
    print()

    # Distributions
    print("=== Frustration distribution ===")
    print(f"  count   : {n}")
    print(f"  min     : {min(frustration):.6f}")
    print(f"  max     : {max(frustration):.6f}")
    print(f"  mean    : {mean(frustration):.6f}")
    print(f"  stdev   : {stdev(frustration):.6f}" if n > 1 else "  stdev   : n/a")
    nonzero = [x for x in frustration if x > 0]
    print(f"  nonzero : {len(nonzero)} ({100 * len(nonzero) / n:.1f}%)")
    if nonzero:
        print(f"  nonzero mean: {mean(nonzero):.6f}")
        print(f"  nonzero max : {max(nonzero):.6f}")
    print()

    print("=== empty_cells_pre distribution ===")
    ec_counts = Counter(empty_pre)
    for v in sorted(ec_counts):
        print(f"  {v:2d} cells: {ec_counts[v]:4d} events ({100 * ec_counts[v] / n:.1f}%)")
    print()

    print("=== trauma_intensity distribution ===")
    print(f"  min     : {min(trauma):.6f}")
    print(f"  max     : {max(trauma):.6f}")
    print(f"  mean    : {mean(trauma):.6f}")
    print(f"  nonzero : {sum(1 for x in trauma if x > 0)} / {n}")
    print()

    print("=== tot_fired ===")
    print(f"  fired   : {sum(tot_fired)} / {n}")
    print()

    # Pearson computations
    print("=== Pearson computations ===")
    inv_empty = [1.0 / max(ep, 0.5) for ep in empty_pre]
    r1 = pearson(frustration, inv_empty)
    r2 = pearson(frustration, empty_term_vals)
    print(f"  Pearson(frustration, 1/empty_cells_pre)        = {r1:.4f}")
    print(f"  Pearson(frustration, 0.7*max(0,(3-ec)/3))      = {r2:.4f}")
    print()
    print("Note on r1: undefined where empty_cells=0; substituted 0.5 to keep")
    print("the inverse finite. With true zeros, r is conceptually infinite — but")
    print("there are likely no zero-empty_cells events on recalibrated grids.")
    zero_ec = sum(1 for ep in empty_pre if ep == 0)
    print(f"Actual events with empty_cells=0: {zero_ec}")
    print()

    print("=== Per-scenario frustration spread ===")
    for sc, vals in per_scenario.items():
        if vals:
            print(
                f"  {sc:30s} n={len(vals):3d} "
                f"max={max(vals):.6f} nonzero={sum(1 for x in vals if x > 0)}"
            )
    print()

    # Interpretation guide
    print("=== Interpretation against Layer 2 reviewer's gating thresholds ===")
    print(f"  |r1| or |r2| < 0.5  → RPE composite proceeds in rewrite ADR")
    print(f"  |r1| or |r2| > 0.8  → RPE composite REJECTED, propose alternative")
    print(f"  0.5 ≤ |r| ≤ 0.8     → hybrid axis with residualisation against ec")
    print()
    print("Decision-relevant readouts:")
    if abs(r2) > 0.8:
        print(f"  r2 = {r2:.4f}: STRONG collinearity → reject RPE/frustration as axis")
    elif abs(r2) > 0.5:
        print(f"  r2 = {r2:.4f}: moderate collinearity → hybrid required")
    else:
        print(f"  r2 = {r2:.4f}: independence holds → RPE composite candidate viable")

    print()
    print("=== ADR-0012 memory retrieval — what we CAN'T see from this data ===")
    print("Per_move events log trauma_intensity (the OUTPUT of cosine-weighted")
    print("aversive recall) but NOT the retrieval attempts themselves. From this")
    print("JSONL we cannot distinguish:")
    print("  (a) no aversive memories existed in the lookback window")
    print("  (b) retrieval happened, cosine threshold filtered everything out")
    print("  (c) retrieval returned matches but aggregated trauma_intensity = 0")
    print("All we know: trauma_intensity = 0 on every event.")
    print("This is itself a finding — Phase 0.7a instrumentation did not capture")
    print("memory retrieval inputs. Future runs need to log retrieval attempts")
    print("to make the silence diagnosable.")


if __name__ == "__main__":
    main()
