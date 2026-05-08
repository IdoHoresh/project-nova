# ADR-0012: Graded Affect Response and Empirical Retrieval Floor for Trauma Tagging

**Status:** Accepted
**Date:** 2026-05-08
**Deciders:** Ido Horesh (with three rounds of /redteam review during brainstorm)

---

## Context

Phase 0.8 (`docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md`) introduced a §3.2b "rationality gate" — a calibration check that verifies trauma tagging produces *specific* avoidance rather than *generalized* paranoia. The gate runs Y_on on a deliberately trivial board (`golden-easy-win-1024`, two 1024 tiles staged for a one-move 2048 merge) and asserts that mean anxiety stays at the Y_off baseline (which is exactly 0 across 10 calibration sessions on the same board).

The 2026-05-08 pilot run hit the gate's pass criteria for move count (`moves_to_merge_Y_on = 1 ≤ threshold = 1`) but failed on anxiety (`mean_anxiety_Y_on = 0.157 > threshold = 0.0`). The failure is a real positive — the gate caught generalized paranoia leaking from game-1 trauma into game-2 on the trivial golden board, which would have confounded the §4.2 trap-recurrence DV in the main run.

Tracing the failure surfaced two coupled defects in the cognitive layer:

**Defect A — Step-function input feeding smooth affect output.** `nova-agent/src/nova_agent/main.py:274` and `nova_agent/lab/trauma_ablation.py:384` compute `trauma_triggered` as a boolean:

```python
trauma_triggered = any(AVERSIVE_TAG in m.record.tags for m in retrieved)
```

`affect/state.py:46` then applies a constant `+0.3` anxiety bump whenever the boolean is True. A single aversive memory in the top-k retrieval — regardless of similarity to the current board — produces the same anxiety amplitude as a wall-to-wall trap-similar board. This is a category error: a step-function gate feeds a smooth amplitude attenuator. The downstream 0.85/step decay smooths in *time* but never reduces a fire that was inappropriate-sized to begin with.

**Defect B — Permissive retrieval surface.** `retrieval.py:81` uses `cosine(query_embedding, rec.embedding)` with `AVERSIVE_RELEVANCE_FLOOR = 0.4` (`retrieval.py:51`) as the gate for the aversive boost branch. LLM-embedding cosine in the 0.4–0.6 range between random board states is permissive — it surfaces aversive memories on boards that are not behaviorally trap-similar. The 0.4 floor was chosen pre-Phase-0.8 without empirical calibration against a strict-zero specificity null.

The intent of §3.2b — "trauma must be specific, not generalized" — is correctly encoded by a strict-zero null. The fix must preserve the gate and address the upstream defects.

## Decision

Two layered changes, plus an instrumentation precheck that defends one of the chosen constants empirically.

### Change 1 — Graded affect amplitude (Defect A)

Replace the boolean `trauma_triggered` with a continuous `trauma_intensity ∈ [0, 1]` computed from the highest-scoring aversive memory in retrieval:

```python
aversive_in_retrieval = [m for m in retrieved if AVERSIVE_TAG in m.record.tags]
if aversive_in_retrieval:
    best = max(
        aversive_in_retrieval,
        key=lambda m: m.record.aversive_weight * m.relevance,
    )
    trauma_intensity = best.record.aversive_weight * best.relevance
else:
    trauma_intensity = 0.0
```

`affect/state.py:46` becomes:

```python
anxiety += 0.3 * trauma_intensity
```

The formula multiplies two existing values: `aversive_weight` (decay-tracked, halved on each survival via `aversive.py:64`) and `relevance` (cosine, plumbed through `RetrievedMemory`). It introduces no new constants, no new metric, and no internal threshold. The amplitude scales smoothly with both context-similarity and time-decay.

### Change 2 — Empirical retrieval floor (Defect B)

`AVERSIVE_RELEVANCE_FLOOR` is raised from the current 0.4 to a value chosen empirically from instrumented golden-Y_on cosine distributions. The instrumentation precheck:

1. Add per-retrieval logging to `retrieval.py` capturing `(record_id, aversive_tag_present, cosine, score)` for every candidate. ~20 LOC + test, behind a `--log-retrievals` flag so production paths are unaffected.
2. Re-run the golden Y_on arm with the patch enabled. ~$2 at production tier, ~10 min wall-clock.
3. Inspect the cosine distribution of aversive-tagged candidates surfaced on the golden board.
4. Set the new floor to the smallest value that excludes all observed leak-fires while preserving headroom for legitimate cliff-board surfacing (verified against existing pilot logs).

The floor is documented in the source with the empirical justification (e.g., "raised 0.4 → 0.62 to exclude the 0.41–0.58 leak band observed in golden Y_on instrumented run, retain >0.65 for cliff-board legitimate surfacing"). This defends the constant via data rather than round-number choice.

### Change 3 — Strict-zero golden gate retained

`_lock_golden_thresholds` in `nova_agent/lab/trauma_ablation.py` continues to compute `anxiety_threshold = μ_anxiety + 2σ_anxiety`. With the Y_off baseline at 0, this remains 0 — a knife-edge that requires Y_on to surface zero aversive memories on the golden board. No ε-tolerance softening. The gate's intent (specificity null = no false positives on trivial inputs) is preserved.

After Change 1 + Change 2 ship, the expected Y_on outcome on golden is: retrieval surfaces no aversive candidates above the new floor → `trauma_intensity = 0` on every move → `mean_anxiety = 0.0` → gate passes.

## Alternatives considered

- **Status quo + ratify the gate failure.** Document binary `trauma_triggered` as known-cosmetic and proceed to surrogate. **Rejected** — methodological own-goal. The gate caught real generalization; demoting the result to "cosmetic noise" requires a behavioral test that the golden board (one move, no fork) cannot provide. Calibration ≠ behavioral; downgrading the calibration result to a behavioral question is a category error (see LESSONS.md "Calibration gates are not behavioral gates," 2026-05-08).

- **Soften the gate with ε-tolerance floor.** Compute `anxiety_threshold = max(μ + 2σ, 0.05)` so any single-fire post-extinction bump is absorbed. **Rejected** — the gate's intent encodes the spec ("trauma must be specific, not generalized"). Adding ε advocates softening rather than fixing the leak. Math also did not support ε=0.05: the actual Y_on test population is just-tagged (`aversive_weight=1.0`), not 3-survival post-extinction (`aversive_weight=0.125`); raw multiply with weight=1.0 × relevance=0.7 produces bump=0.21 with 5-move mean ≈ 0.13, blowing past ε=0.05 anyway. The constant defended a population that doesn't exist in the test (see LESSONS.md "Cross-check formulas across bullets," 2026-05-08).

- **Floor + graded with collision at threshold 0.5.** Linear ramp `bump = 0.3 × max(0, (cosine − 0.5)/0.5)` plus retrieval floor 0.5. **Rejected** — both fixes live at the same boundary in affect amplitude (ramp gives 0 below 0.5, floor cuts off below 0.5); floor is redundant with ramp threshold. Layered-redundant, not independent insurance.

- **A priori floor 0.6 + graded above (skip empirical precheck).** Same as the chosen design but with 0.6 picked as a round number. **Rejected** — defends the constant via assertion rather than data. ~3h savings is not worth a weaker ADR defense and the risk of cutting legitimate cliff-board surfacing.

- **Anchor-grid retrieval gate at retrieval surface.** Replace cosine in `retrieval.py:81` with a board-state metric (e.g., `min_orbit_distance` from spec §3.2). **Deferred to Phase 0.9** — couples core memory module to lab-domain `Game2048Sim` board metrics, which is a layering concern requiring its own ADR. The current design uses cosine retrieval with empirical floor as the trauma-surfacing gate; the cosine-vs-anchor-grid mismatch is named explicitly here as a known limitation rather than papered over (see LESSONS.md "Verify the metric you claim alignment with," 2026-05-08).

- **Full trauma model redesign (extinction rate + initial weight + retrieval + amplitude).** **Rejected** — extinction halve rate (0.5/survival) and initial weight (1.0) are not implicated by the golden-gate failure trace. The defect is fire-condition shape (binary) and surfacer permissiveness (cosine 0.4 floor), not decay or initial amplitude. Opening that scope is premature without evidence those mechanisms are broken.

## Consequences

**Positive:**

- Restores Phase 0.8 §3.2b gate to PASS without weakening the gate's specificity intent.
- Replaces a step-function input with smooth amplitude, eliminating the category error in the cognitive layer's affect pipeline.
- Empirical floor defense reads stronger in pitch ("derived from instrumented cosine distribution on Y_on golden") than round-number defenses.
- Reuses existing values (`aversive_weight`, `relevance`); introduces no new architectural constants.
- Preempts external-reviewer mechanism question via "graded affective response" framing.
- Decouples affect amplitude from retrieval permissiveness — independent surfaces, layered defense.

**Negative:**

- Phase 0.8 ship delay: 2–3 days (1 day for instrumentation patch + re-run + observe; 1–2 days for graded amplitude + tests + ADR review).
- New plumbing required: `RetrievedMemory.relevance` must be exposed (currently only `score` is), with mypy-strict types throughout the call chain.
- The cosine-vs-anchor-grid limitation is now an explicit Phase 0.9 follow-up. Future spec must address it; reviewer cannot read past it.
- Strict-zero gate remains brittle to any future change that surfaces aversive memories on trivial boards. Acceptable because the gate is doing its job; the brittleness is the spec's specificity claim.

**Neutral:**

- `aversive_weight` decay (`exposure_extinction_halve` halve rate 0.5) and `AVERSIVE_INERT_THRESHOLD` (0.02) are unchanged. The graded amplitude formula composes with the existing decay; no double-counting.
- Production behavior (outside Phase 0.8 lab) gets the graded amplitude as a side effect. Production has no current calibration gate that would surface a regression; this is acceptable because graded ≤ binary at every input (the new bump is `0.3 × weight × relevance ≤ 0.3 × 1 × 1 = 0.3`, the old binary fire amplitude).
- Reflection (`main.py:104`) is unchanged. Semantic-rule learning remains constant across the IV — see Phase 0.8 spec §1.3(ii).

**Reversibility:** Easy. The graded amplitude change is a 30-LOC patch on `affect/state.py:46` + `main.py:274` + `lab/trauma_ablation.py:384` + `retrieval.py` plumbing; revert restores binary behavior. The empirical floor is a single constant; revert to 0.4 if the new value proves too tight on cliff boards (would manifest as Phase 0.8 surrogate stage's `rate_y_on ≥ rate_y_off` direction-flip on actually-trap-similar boards). The instrumentation logging is gated behind a flag; off by default in production paths.

## References

- Phase 0.8 spec: `docs/superpowers/specs/2026-05-07-phase-0.8-trauma-ablation-design.md` §3.2b (golden-gate rationality check), §1.4 (Y_on vs Y_off IV), §1.5 (force_trauma_on_game_over)
- Methodology: `docs/product/methodology.md` §4.2 (dual-DV gating), §4.3 (within-game adaptation)
- ADR-0010: cliff-test pilot pass criteria (smoke→pilot→main pattern reused for Phase 0.8 stages)
- Source surfaces:
  - `nova-agent/src/nova_agent/main.py:274` — production trauma_triggered call site
  - `nova-agent/src/nova_agent/lab/trauma_ablation.py:384` — Phase 0.8 runner trauma_active call site
  - `nova-agent/src/nova_agent/affect/state.py:32–48` — anxiety update rule (decay + empty-cells + trauma bump + clamp)
  - `nova-agent/src/nova_agent/affect/state.py:46` — `+0.3` constant trauma anxiety bump
  - `nova-agent/src/nova_agent/memory/retrieval.py:51` — `AVERSIVE_RELEVANCE_FLOOR = 0.4` (raised by this ADR)
  - `nova-agent/src/nova_agent/memory/retrieval.py:81` — `cosine(query_embedding, rec.embedding)`
  - `nova-agent/src/nova_agent/memory/aversive.py:17` — `AVERSIVE_INITIAL_WEIGHT = 1.0` (unchanged)
  - `nova-agent/src/nova_agent/memory/aversive.py:64` — `exposure_extinction_halve` (unchanged)
- Run artifacts:
  - `nova-agent/runs/2026-05-08-phase08-run/golden/halt_reason.json` — gate failure record
  - `nova-agent/runs/2026-05-08-phase08-run/pilot/locked_T.json` — locked T=22 (T-calibration pass)
  - `nova-agent/runs/2026-05-08-phase08-run/pilot/golden_calibration.json` — Y_off baseline (μ=0, σ=0)
- Process artifacts:
  - LESSONS.md 2026-05-08 entries: "Calibration gates are not behavioral gates," "When calibration baseline is strict-zero, tighten the upstream surfacer," "Verify the metric you claim alignment with before drafting the ADR," "Cross-check formulas across bullets when sizing magnitude-bounded fixes"
- Brainstorm rounds: three /redteam cycles (round 1 — magnitude/behavioral framing; round 2 — D-collision rejection; round 3 — D-different-surface reopen + math cross-check)
