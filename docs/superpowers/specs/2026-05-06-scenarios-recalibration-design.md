# Phase 0.7 Cliff-Test Scenarios — Recalibration After 2026-05-06 Pilot

**Status:** Ready for implementation (user-approved 2026-05-06)
**Date:** 2026-05-06
**Author:** ihoresh07@gmail.com (solo founder), with per-scenario red-team review (two rounds) on the 2026-05-06 pilot evidence
**Supersedes:** §4.1, §4.2, §4.3 of `2026-05-05-cliff-test-scenarios-design.md` (the three scenario-grid sections only). The framework, dataclass invariants, measurement contract, and sourcing discipline from the original spec are unchanged.

---

## 1. Context

The 2026-05-06 pilot ran 15 paired trials (3 scenarios × 5 trials × 2 arms) at production tier with Pro for ToT. Per-trial data lives in `nova-agent/runs/2026-05-06-pilot/pilot_results/cliff_test_results.csv`. Summary:

| scenario | window | Bot in-window / N | Bot at cap / N | Carla median `t_predicts` |
|---|---|---|---|---|
| corner-abandonment-256 | (12, 18) | 0/5 | 0/5 | 0–1 (fast-react) |
| snake-collapse-128 | (11, 16) | 1/5 | 3/5 | 6 ✓ |
| 512-wall | (12, 17) | 1/5 | 1/5 | 0–1 (fast-react) |

Three failure modes:

1. **§7.4 calibration violation across all 3 scenarios.** None meet the "≥ 3/5 Bot game-overs in `expected_cliff_window`" pilot calibration check.
2. **Snake-collapse cap rate 3/5.** Exceeds the §2.8 "more than 2 of N=20 → broken" threshold (extrapolates to ≈12/20).
3. **Fast-reaction failure on corner + 512.** Carla's `t_predicts ∈ {0, 1}` on these scenarios is the rigor failure captured in LESSONS (move-0 anxiety = panicking, not predicting). Snake-collapse's median 6 is a real predictive lead-time and must not break under recalibration.

The right response per the original spec's no-margin condition (§5.3) is recalibrate in place, not soften pass criteria. This document specifies the recalibrated grids; the framework, dataclass invariants, measurement contract, and sourcing discipline of `2026-05-05-cliff-test-scenarios-design.md` stay in force.

## 2. Pinned decisions (this round)

### 2.1 "Delayed Detection" — refined Illusion-of-Hope

The 2026-05-06 red-team round refined the Illusion-of-Hope constraint of the original spec (§2.1) into a per-scenario actionable principle: each grid must give Bot 4–8 mechanical-merge moves before the structural trap forecloses, AND must defer Carla's `Anxiety > 0.6` threshold-crossing to move 4–8 (not move 0–1). "Delayed Detection" is shorthand: the cliff is structurally present from move 0 (ToT can see it), but the move-by-move state offers genuine maneuvering until the trap manifests.

This is **not** a methodology amendment. It is a per-scenario calibration target. The original `t_predicts` measurement (`Anxiety > 0.6 AND ≥ 2 consecutive moves`, spec §2.7) is unchanged; only the grid design now targets a threshold-crossing move-index in `[4, 8]`.

### 2.2 Per-scenario calibration targets

| scenario | Bot target | Carla anxiety target | Cap-rate target |
|---|---|---|---|
| corner-abandonment-256 | dies move 12–17 | crosses move 4–8 | 0/20 |
| snake-collapse-128 | dies move 11–16 | preserve median ≈6 | <2/20 |
| 512-wall | dies move 12–17 | crosses move 4–8 | 0/20 |

### 2.3 Snake-collapse Carla logic — preserved

The 2026-05-06 pilot showed snake-collapse's Carla side already produces real predictive lead-time (median `t_predicts` = 6; Δ_i of 12–15 on uncensored Bot trials). The recalibration touches the Bot side only — blockers, density. The broken-snake structural cue ToT detects is preserved verbatim.

### 2.4 Canon citations — unchanged

Per spec §2.4, every scenario must cite a public canon. The recalibration changes only the magnitudes/positions of supporting tiles; the named patterns (corner-abandonment, snake-collapse, high-tile-wall) and their sourcing remain the cited references. URL pinning per §9 is still deferred.

## 3. The three revised scenarios

Each grid satisfies all `Scenario.__post_init__` invariants per spec §3 (4×4, in-palette, `initial_score` matches minimum-implied-score, `expected_cliff_window[0] >= 11`, `< MAX_MOVES = 50`). All admit ≥ 1 legal move at start (covered by `test_scenario_admits_at_least_one_legal_move`).

### 3.1 corner-abandonment-256

```
[  0,   4,   0,   0]
[  4,   8,   4,   2]
[  0,  16,   8, 128]
[ 64, 256, 128,  32]
```

| field | new | old | delta |
|---|---|---|---|
| `initial_score` | `3868` | `4364` | −496 |
| `expected_cliff_window` | `(12, 17)` | `(12, 18)` | upper bound −1 |
| empty cells | 4 | 1 | +3 |

**Pattern rationale.** 64 in the bottom-left corner; 256 dislocated to `(3,1)`; the diagonal-128 trap at `(2,3)` and `(3,2)` is preserved (2048 disallows diagonal merges, so the 256→512 ladder via 128+128 is unreachable). Four empty cells in the upper-left region admit 4–8 mechanical merges before spawn pressure compresses upper rows against the immutable bottom-row trap. All four directions (UP, DOWN, LEFT, RIGHT) are legal at move 0; the current scenario admits only UP and LEFT, which is what kills Bot at move 4–5.

**Carla anxiety deferral.** ToT-detectable cascade (256 unreachable from corner; bottom-row gridlock structurally present) is stable from move 0, but the upper-region mobility softens immediate `Anxiety` spikes — threshold-crossing target moves to 4–8 once spawn fills the empties.

### 3.2 snake-collapse-128

```
[ 16,   4,   8,  16]
[  4,  32,   4,   4]
[  8,   4,  32,   4]
[  2,   8,  64, 128]
```

| field | new | old | delta |
|---|---|---|---|
| `initial_score` | `1512` | `1308` | +204 |
| `expected_cliff_window` | `(11, 16)` | `(11, 16)` | unchanged |
| empty cells | 0 | 3 | −3 |

**Pattern rationale.** Bottom-row broken snake (`2 → 8 → 64 → 128`, skipping the 16 + 32 rungs) is preserved verbatim — this is the ToT-detectable structural cue Carla currently sees at median `t_predicts = 6`. The recalibration targets the Bot side: zero empty cells (vs current 3) plus two unmergeable diagonal 32s at `(1,1)` and `(2,2)` plus mid-grid scattered 4s create a non-monotonic terrain that defeats Bot's "push everything to corner" heuristic. Limited merge entry-points (4+4 pairs at row 1 cols 2-3 and via UP into col 3) collapse within 2–3 moves; subsequent spawns into the dense board exhaust legal moves by move 11–16. Cap-violation rate falls from 3/5 in pilot to <2/20 in expectation.

**Carla side preserved.** The structural cue (broken snake, gap between 8 and 64) is identical to the original; ToT's detection mechanism does not depend on the upper-row tile values.

### 3.3 512-wall

```
[  0,   4,   8,   0]
[  4,   8,  16,  32]
[  8,  16,  32, 128]
[256,  32, 128, 512]
```

| field | new | old | delta |
|---|---|---|---|
| `initial_score` | `7960` | `8152` | −192 |
| `expected_cliff_window` | `(12, 17)` | `(12, 17)` | unchanged |
| empty cells | 2 | 1 | +1 |

**Pattern rationale.** 512 anchored bottom-right; 256 dislocated bottom-left; supporting stacks (rows 1–2) ascending-but-structurally-disorganized — pattern unchanged from original. Two adjustments:

1. **Upper-right relief cell** (`(0,3) = 0`, was 2): defers Carla's anxiety threshold-crossing from move 0–1 to move 4–8 by giving her one upper-region move of "not yet under siege" before spawn pressure compresses.
2. **Wall tightened** (`(3,1) = 32`, was 64): the 32 is structurally trapped — no adjacent partner (`(3,0)=256`, `(3,2)=128`, `(2,1)=16` all ≠ 32). Removes the 64+64 ladder Bot's heuristic occasionally exploited to escape into a 50-move cap (1/5 pilot rate). Bot death pulled to <20 reliably.

## 4. Code-side deltas

### 4.1 `nova-agent/src/nova_agent/lab/scenarios.py`

Three `Scenario(...)` literal updates: `initial_grid`, `initial_score`, `expected_cliff_window` per the matrices above. The `seed_base`, `pattern_name`, `high_tile_magnitude`, and `source_citation` fields are unchanged on every scenario. Preserving `seed_base` keeps cross-pilot trial-seed comparability for any future before/after analysis.

### 4.2 `nova-agent/tests/lab/test_scenarios.py`

Existing tests (per spec §7.1–§7.3) auto-cover the new grids:

- `test_all_scenarios_load_without_error` — exercises `__post_init__` validators on the new grids
- `test_all_scenarios_satisfy_illusion_of_hope_lower_bound` — `expected_cliff_window[0] ∈ {11, 12} ≥ 11` ✓
- `test_scenario_initial_state_loads_into_sim` — verifies sim accepts the grid
- `test_scenario_admits_at_least_one_legal_move` — verifies ≥ 1 legal move at start

Any test with hardcoded grid values from the prior spec (if such tests exist) updates to the new matrices. The full `/check-agent` trio (pytest + mypy + ruff) must be clean before commit.

### 4.3 No ADR amendment

No methodology, no measurement contract, no sourcing-discipline change. Spec-level recalibration only. ADR-0006, ADR-0007, and `docs/product/methodology.md` are unchanged.

## 5. Pilot re-calibration target

After the recalibration ships, re-run the pilot:

- **Configuration:** N=5 paired trials × 3 scenarios × 2 arms (15 paired trials), production tier, concurrency=8, Sonnet 4.6 ToT (per ADR-0006 Amendment 1; `claude-sonnet-4-6`).
- **Wall budget:** ~30 min. **Cost budget:** ~$5–7 — buffered above empirical Pro-tier pilot total ($1.63 sum of `cost_usd` in 2026-05-06-pilot CSV × 1.9 Sonnet multiplier per ADR-0006 Am 1 ≈ $3.14) with verbosity headroom for Sonnet 4.6 branch-output growth on the recalibrated longer-running games. No automated cost-abort gate; this budget is operational expectation only.

**Acceptance criteria** (all must hold to authorise the real N=20 run; small-N corrections per 2026-05-06 red-team operational addendum):

1. **§7.4 calibration:** ≥ 3/5 Bot game-overs in `expected_cliff_window` per scenario.
2. **§2.8 cap discipline (tiered for N=5):**
   - `corner-abandonment-256`: **0/5 strict** (any cap = fail).
   - `512-wall`: **0/5 strict** (any cap = fail).
   - `snake-collapse-128`: **0/5 target; 1/5 = borderline PASS, flag for user review (do not auto-fail); 2+/5 = fail.** Rationale: §2.8 declares scenarios broken at `>2/20` cap rate, which extrapolates to `>0.5/5` in N=5. A single cap-violation in N=5 is small-N statistical noise (point estimate 4/20, but the 95% CI from Wilson-score on 1/5 spans 0–60%); it does not invalidate the recalibration. The strict floor for snake stays 0/5 as the real-run target; 1/5 in pilot earns a hold-and-flag, not a re-author.
3. **Carla deferral:** median `t_predicts ∈ [4, 8]` for `corner-abandonment-256` and `512-wall`; preserved at ≥ 4 for `snake-collapse-128`.
4. **Operational:** **0 Carla aborts** in pilot N=15. (The original draft said "abort rate < 5%"; that is mathematically equivalent to 0 aborts at N=15 since 5% × 15 = 0.75 < 1, but the percentage notation is misleading at small-N. Spec uses absolute count to avoid ambiguity.)

If any criterion fails, the affected scenario gets a second-round recalibration; this document is amended in place (Amendment 1) with the second-round matrix and the pilot re-runs.

## 6. Out of scope (deferred)

- **`analyze_results.py` spec** — write after this pilot's CSV produces clean samples (per Test Runner spec §9 ordering).
- **N=20 real run** — gated on this pilot's acceptance.
- **Scenarios 4–5** — only consider after the existing 3 calibrate.
- **URL pinning** for source citations — still per spec §9.

## 7. Implementation handoff

Next step: invoke `superpowers:writing-plans` to produce the `scenarios.py` + `test_scenarios.py` edit plan with TDD discipline (failing assertion → minimal fix → green → commit), followed by the pilot re-run and acceptance check against §5.
