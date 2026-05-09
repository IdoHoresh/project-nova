# Test 6 Results — Pearson Contamination Math + Memory-Silence Diagnostic

**Date:** 2026-05-09
**Script:** `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-pearson.py`
**Input:** Phase 0.7a Carla JSONL events
(`docs/external-review/phase-0.7a-raw-2026-05-09/results/events_*_carla_*.jsonl`)
**Cost:** $0
**Purpose:** Settle Layer 2 reviewer's "single attack you should not be allowed to dodge" — run the contamination math before locking H6 (or any other position) on the rewrite axis.

---

## Pearson computations

```
Pearson(frustration, 1/empty_cells_pre)        = -0.1126
Pearson(frustration, 0.7*max(0,(3-ec)/3))      = -0.1231
```

**Interpretation against Layer 2 reviewer's gating thresholds:**

- `|r| < 0.5` → RPE composite proceeds in rewrite ADR
- `|r| > 0.8` → RPE composite REJECTED, propose alternative
- `0.5 ≤ |r| ≤ 0.8` → hybrid axis with residualisation against `empty_cells`

**Result: |r| ≈ 0.12 — RPE composite axis is viable per the gating threshold.**
Red team's load-bearing collinearity claim (predicted `r > 0.8`) is empirically false.

The sign is also informative: `r` is *negative*. Frustration is slightly higher when `empty_cells` is higher (board less locked), the OPPOSITE direction of the red team's predicted "frustration accumulates on locked boards" mechanism.

---

## Frustration distribution

| Statistic | Value |
|---|---|
| count | 658 events |
| min | 0.000000 |
| max | 0.052353 |
| mean | 0.002699 |
| stdev | 0.006816 |
| nonzero events | **180 / 658 (27.4%)** |
| nonzero mean | 0.009865 |
| nonzero max | 0.052353 |

**The adjudication memo's "frustration at effectively 0.0 across 658 observations" was an aggregation that hid signal.** Frustration was non-zero on 27.4% of events.

---

## Per-scenario frustration

| Scenario | n events | nonzero count | nonzero % | max |
|---|---|---|---|---|
| 512-wall | 199 | 0 | 0.0% | 0.000 |
| snake-collapse-128 | 250 | 60 | 24.0% | 0.052 |
| corner-abandonment-256 | 209 | 120 | **57.4%** | 0.038 |
| **Total** | 658 | 180 | 27.4% | 0.052 |

The "effectively 0.0" framing is true ONLY on 512-wall. On snake-collapse-128 and corner-abandonment-256, frustration was firing regularly. The chain is producing low-amplitude signal — peak ~0.05 when a typical anxiety-firing threshold needs ~0.6.

---

## empty_cells_pre distribution

| empty_cells | count | % of events |
|---|---|---|
| 0 | 61 | 9.3% |
| 1 | 52 | 7.9% |
| 2 | 72 | 10.9% |
| 3 | 100 | 15.2% |
| 4 | 152 | 23.1% |
| 5 | 107 | 16.3% |
| 6 | 49 | 7.4% |
| 7 | 41 | 6.2% |
| 8 | 15 | 2.3% |
| 9 | 9 | 1.4% |

**Carla hit `empty_cells = 0` on 9.3% of events (61 / 658).** Point-blank cliff conditions occurred 61 times across the run. The architecture saw them. Anxiety stayed at 0.0 anyway (because the empty_cells term was nulled and no other driver was firing).

---

## Confirmed silent

| Signal | Value |
|---|---|
| `trauma_intensity` | 0.0 on every one of 658 events |
| `tot_fired` | false on every one of 658 events |

---

## Confirmed firing but undersized (NEW finding from this test)

| Signal | Status |
|---|---|
| `frustration` | Fires 27.4% of events; peaks at 0.052; threshold-crossing requires ~0.6 |

**~12× scaling deficit.** The frustration mechanism is alive but produces values an order of magnitude smaller than the anxiety formula would need to register a threshold crossing.

---

## Memory retrieval — what we CANNOT see from this data

Per_move events log `trauma_intensity` (the OUTPUT of cosine-weighted aversive recall via ADR-0012) but NOT the retrieval attempts themselves. From this JSONL we cannot distinguish:

- (a) no aversive memories existed in the lookback window
- (b) retrieval happened, cosine threshold filtered everything out
- (c) retrieval returned matches but aggregated trauma_intensity = 0

All we know: `trauma_intensity = 0` on every event.

**Side finding:** Phase 0.7a instrumentation did not capture memory retrieval inputs. Future runs need to log retrieval attempts to make the silence diagnosable.

---

## Subsequent confirmation (NOT part of original test 6)

A follow-up grep across `nova-agent/src/nova_agent/` produced a finding test 6 alone did not surface but which the test 6 numbers point at:

**There is NO frustration → anxiety linkage in the code.** All anxiety-write sites in `state.py`:

- Line 37: `anxiety = v.anxiety * 0.85` (decay)
- Line 50: `anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)` (gated by `null_empty_cells_term`)
- Line 51: `anxiety += 0.3 * _clamp(trauma_intensity, 0.0, 1.0)`
- Line 53: `anxiety = 1.0  # if terminal`

Frustration is computed (line 44: `frustration += min(1.0, -rpe * 0.6)`) but **never feeds anxiety**.

This explains why frustration's 0.05 peak amplitude didn't matter — even if it were 1.0, the anxiety formula has no coefficient on frustration. The "RPE-via-frustration" claim in the methodology document and the Phase 0.7a adjudication memo is not implemented in the code.

This is the load-bearing finding for Layer 2 round 2.
