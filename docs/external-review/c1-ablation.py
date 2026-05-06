"""C1 ablation — does anxiety > 0.6 reduce to empty_cells ≤ 3?

The synthesis (round-3-synthesis.md §4) calls for:
    Pearson(t_predicts, min_i: empty_cells_i ≤ 3)

The morning-pilot CSV at nova-agent/runs/2026-05-06-pilot/pilot_results/
contains t_predicts per trial but NOT per-move empty_cells trajectories
(JSONL only logs tot_branch / tot_selected events).

The exact Pearson test cannot be run as written. The data DOES permit a
weakened-but-still-informative test:

  - All 3 scenarios start with empty_cells <= 4 (close to or already at
    the ≤3 trigger threshold).
  - If anxiety is a deterministic function of empty_cells, then within a
    given scenario t_predicts should have NEAR-ZERO variance across the
    5 Carla trials (the LLM stochasticity at temp=0.7 should not move
    t_predicts — the formula does).
  - And t_predicts should differ systematically BETWEEN scenarios as a
    function of initial empty_cells (lower initial cells → earlier
    t_predicts).

If both hold, C1 is empirically supported on the available data.
If t_predicts varies meaningfully WITHIN a scenario, that's evidence
the LLM/affect-vector layer is contributing variance the formula can't
account for, and C1 is weakened (not killed — the synthesis ablation
with constant-anxiety counterfactual would still be needed).

Output: per-scenario t_predicts statistics + interpretation.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[2] / (
    "nova-agent/runs/2026-05-06-pilot/pilot_results/cliff_test_results.csv"
)

# Initial empty_cells per scenario (counted from scenarios.py initial_grid).
INITIAL_EMPTY_CELLS = {
    "corner-abandonment-256": 1,
    "512-wall": 1,
    "snake-collapse-128": 4,
}


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found at {CSV_PATH}")

    rows = list(csv.DictReader(CSV_PATH.open()))
    print(f"Total rows in CSV: {len(rows)}")
    print()

    # Filter Carla trials only
    carla_rows = [r for r in rows if r["arm"] == "carla"]
    print(f"Carla trials: {len(carla_rows)}")
    print()

    # Group by scenario
    by_scenario: dict[str, list[dict[str, str]]] = {}
    for r in carla_rows:
        by_scenario.setdefault(r["scenario_id"], []).append(r)

    print("=" * 78)
    print("Per-scenario t_predicts statistics (Carla arm only)")
    print("=" * 78)
    print()
    print(f"{'scenario':<30} {'init_empty':>10} {'n':>4} "
          f"{'mean':>8} {'stdev':>8} {'median':>8} {'min':>4} {'max':>4} "
          f"{'finite':>7}")
    print("-" * 95)

    for scenario_id, trials in sorted(by_scenario.items()):
        init_cells = INITIAL_EMPTY_CELLS.get(scenario_id, "?")
        t_preds_raw = [r["t_predicts"] for r in trials]
        t_preds_finite = [int(v) for v in t_preds_raw if v not in ("", None)]
        finite_count = f"{len(t_preds_finite)}/{len(trials)}"
        if t_preds_finite:
            mean = statistics.mean(t_preds_finite)
            stdev = (
                statistics.stdev(t_preds_finite) if len(t_preds_finite) > 1 else 0.0
            )
            median = statistics.median(t_preds_finite)
            mn = min(t_preds_finite)
            mx = max(t_preds_finite)
            print(
                f"{scenario_id:<30} {init_cells:>10} "
                f"{len(trials):>4} {mean:>8.2f} {stdev:>8.2f} {median:>8.1f} "
                f"{mn:>4} {mx:>4} {finite_count:>7}"
            )
        else:
            print(
                f"{scenario_id:<30} {init_cells:>10} "
                f"{len(trials):>4} {'-':>8} {'-':>8} {'-':>8} "
                f"{'-':>4} {'-':>4} {finite_count:>7}"
            )

        print(f"  raw t_predicts values: {t_preds_raw}")
        print()

    print("=" * 78)
    print("Interpretation")
    print("=" * 78)
    print()
    print("C1's prediction (anxiety = empty_cells):")
    print("  - Within a scenario, t_predicts variance should be near-zero.")
    print("  - Between scenarios, t_predicts should track initial empty_cells")
    print("    (corner+512 cells=1 → very early; snake cells=4 → later).")
    print()
    print("Within-scenario stdev of t_predicts is the load-bearing metric.")
    print("  stdev < 1.0 move = anxiety is deterministic given scenario,")
    print("    LLM/affect-vector layer adds no variance — C1 strongly supported.")
    print("  stdev > 2.0 moves = anxiety responds to factors beyond initial cells,")
    print("    LLM/memory/RPE adds real variance — C1 weakened.")
    print("  1.0 < stdev < 2.0 = ambiguous, needs the full synthesis ablation")
    print("    (1-trial-per-scenario constant-anxiety counterfactual).")


if __name__ == "__main__":
    main()
