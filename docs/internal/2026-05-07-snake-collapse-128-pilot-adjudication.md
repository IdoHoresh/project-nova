# Pilot Adjudication: snake-collapse-128 — N=5 FAIL

**Date:** 2026-05-07  
**Branch:** claude/scenarios-recalibration-code  
**Run directory:** nova-agent/runs/2026-05-07-n5/  
**ADR authority:** ADR-0010

---

## Results CSV

```
scenario_id,trial_index,arm,t_predicts,t_baseline_fails,cost_usd,abort_reason,anxiety_threshold_met,final_move_index,is_right_censored
snake-collapse-128,0,carla,0,,0.252,,True,49,True
snake-collapse-128,0,bot,,24,0.0024,,,24,False
snake-collapse-128,1,carla,0,,0.144,,True,49,True
snake-collapse-128,1,bot,,50,0.005,,,49,True
snake-collapse-128,2,carla,0,,0.017,,True,3,False
snake-collapse-128,2,bot,,24,0.0024,,,24,False
snake-collapse-128,3,carla,,,0.011,,False,1,False
snake-collapse-128,3,bot,,50,0.005,,,49,True
snake-collapse-128,4,carla,,,0.011,,False,1,False
snake-collapse-128,4,bot,,40,0.004,,,40,False
```

Total cost: ~$0.46 (under $5 M-07 cap; gate never fired)

---

## ADR-0010 adjudication

| Criterion | Threshold | Result | Detail |
|---|---|---|---|
| C1 Bot calibration | ≥3/5 in window (11,16) | **FAIL** | 0/5 in window; actual game-overs at moves 24, 24, 40; 2 right-censored |
| C2 Cap discipline | 0/5 strict | PASS | 0 violations |
| C3 Carla deferral | median t_predicts ≥ 4; none ∈ {0,1} | **FAIL** | all valid t_predicts = 0; fast-reaction failure |
| C4 Operational health | 0 aborts | PASS | 0 aborts |
| C5 Prediction-validity surrogate | ≥4/5 finite t_predicts ∉ {0,1} AND lead ≥ 2 | **FAIL** | 0/5 meet condition |

**PILOT VERDICT: FAIL** (C1, C3, C5 failed; C2, C4 passed)

Option-B σ check: σ(t_predicts) = 0.000 (degenerate — fast-react fires identically across all valid trials); σ(final_move_index carla) = 25.938 (not zero — right-censoring did not kill all variance).

---

## Root cause analysis

**C1 failure — cliff window mismatch:**  
Expected bot game-overs in window (11, 16). Actual: 24, 24, 40 (outside window), 2 right-censored (no game-over within move budget). The recalibrated grid is less constrained than designed for the bot arm — collapse happens later than the (11, 16) window predicts, or not at all within the 50-move budget.

**C3/C5 failure — fast-reaction failure:**  
All valid `t_predicts = 0`. Carla's anxiety threshold fires at the initial board state (before any moves). Per ADR-0010 C3: this indicates the grid is still miscalibrated — the board is so alarming from move 0 that the affect system fires immediately rather than building through gameplay dynamics. Two trials (3, 4) end at move 1 — Carla makes a single move that leads to game-over, while the bot escapes to moves 40-49. This is consistent with the LESSONS.md "packed snake grid → 0 empty cells → game-over at move 1" known footgun.

**Diagnostic question (open):**  
Is fast-react failure (t_predicts=0) isolated to snake-collapse-128 (packed grid artifact) or architecture-wide? Cannot be answered from snake-collapse data alone.

---

## Next step: horizontal de-risk

Per redteam review (2026-05-07), run N=1 smokes on the two remaining scenarios before re-recalibrating snake-collapse:

- `corner-abandonment-256` — different grid topology (corner-trap pattern, more empty cells)
- `512-wall` — different grid topology (high-tile wall, more empty cells)

Cap: `NOVA_SESSION_CAP_USD=3.0` per run.

**Interpretation of smoke results:**
- Both t_predicts > 1 → fast-react isolated to snake-collapse; proceed to re-recalibrate snake grid
- Either fires t_predicts ∈ {0,1} → grid-dependent behavior; broaden recalibration scope
- Both fire at t_predicts = 0 → escalate to architecture review (Opus debug session on affect/ToT deliberation loop)

Results will be recorded in a follow-up adjudication document.
