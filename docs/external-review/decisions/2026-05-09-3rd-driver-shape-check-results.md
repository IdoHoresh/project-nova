# 3rd-Driver Shape-Check — Results

**Date:** 2026-05-09
**Spec:** [`docs/superpowers/specs/2026-05-09-3rd-driver-shape-check-design.md`](../../superpowers/specs/2026-05-09-3rd-driver-shape-check-design.md)
**Branch:** `claude/redteam-discipline-system`
**Wall time:** ~3 min (analysis) + ~30 min (derivations write-up)
**Cost:** $0 (existing-data analysis + structural derivations; no LLM calls)

---

## Executive verdict

**Item-2 validation FAILS across all K ∈ {0.5, 1.0, 1.73, 2.5, 5.0, 7.5, 10.0}** on both `snake-collapse-128` and `corner-abandonment-256`.

Per shape-check spec §4.3: **Q2 is NOT empirically closed by Item 2 alone.** β-equal's "§3 = Q1-only" framing collapses. Protocol revisits. The fork between five branches — (i) §3 expands, (ii) Item-2 spec changes, (iii) methodology-narrowing, (iv) kill (publishable negative result), (v) hold per §4.1 — is now open and unresolved.

The empirical structural finding is stronger than "validation failed." It is: **the K range that produces any anxiety crossing on existing scenarios is the same K range that produces no predictive lead-time** — see §Output 2. The formula has no admissible operating point on the scenarios as they currently sit.

Cumulative round-1–8 evidence (Phase 0.7a empty_cells driver fires mechanically; round-2 frustration→anxiety wiring missing in code; round-3 audit of trauma_intensity disabled-by-harness + multiple ADR-0002 surfaces spec-only; round-7+8 validation showing the planned Item-2 rewrite has no admissible operating point) constitutes four consecutive layer-deeper structural problems. That is the §4.4 diagnostic signal; (iv) is now a substantive branch, not a procedural footnote.

The downstream §5 (Option 2 structural kill) and §6 (Option 3 proxy invalidity) derivations stand independent of Item-2's verdict and are documented below for any future ADR-0013 draft if branch (i) or (ii) is adopted.

---

## Output 1 — Item-2 K-sweep verdict

Source data: `docs/external-review/phase-0.7a-raw-2026-05-09/results/events_{snake-collapse-128,corner-abandonment-256}_carla_{0..4}.jsonl` (10 trials, ~500 per_move events per scenario).

Replay rule (spec §4.1): `anxiety_t = 0.85 × anxiety_{t-1} + K × clamp(frustration_t, 0, 1)`, capped at 1.0. No empty_cells term (Item 1), no trauma_intensity (was 0/658 across run).

| K | snake (a/b/c) | corner (a/b/c) | passes |
|--:|:--------------|:---------------|:------:|
|  0.5 | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | ✗ |
|  1.0 | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | ✗ |
| 1.73 | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | ✗ |
|  2.5 | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | a=0.00 ✗ / b=0.00 ✓ / c=0.00 ✓ | ✗ |
|  5.0 | a=0.00 ✗ / b=0.20 ✓ / c=0.00 ✓ | a=0.00 ✗ / b=0.20 ✓ / c=0.00 ✓ | ✗ |
|  7.5 | a=0.00 ✗ / b=0.20 ✓ / c=0.00 ✓ | a=0.20 ✗ / b=0.20 ✓ / c=0.00 ✓ | ✗ |
| 10.0 | a=0.00 ✗ / b=0.20 ✓ / c=0.00 ✓ | a=0.20 ✗ / b=0.40 ✗ / c=0.27 ✓ | ✗ |

**(a)** crossing_within_5: fraction of trials where simulated anxiety ≥ 0.6 in last 5 moves. Acceptance ≥ 4/5 per scenario.
**(b)** false_positive_rate: average count of pre-final crossings ≥ 5 moves before `final_move_index`. Acceptance ≤ 1/5 per scenario.
**(c)** cap_saturation_freq: fraction of above-threshold events at the cap. Acceptance < 0.50.

No K row clears criterion (a) on either scenario. Snake never produces a within-window crossing at any K. Corner produces a within-window crossing on a single trial at K ≥ 7.5 (1/5 = 0.20, below the 4/5 threshold). At K = 10 corner picks up false positives (2/5 trials) but still fails within-window crossings.

Reproducibility: `uv run python -m nova_agent.lab.shape_check_item2_validation` (script at `nova-agent/src/nova_agent/lab/shape_check_item2_validation.py`).

---

## Output 2 — Why validation fails (mechanism)

Frustration distribution across all 658 Carla per-move events on Phase 0.7a (computed 2026-05-09):

| stat       | value    |
|-----------:|:---------|
| min        | 0.000000 |
| median     | 0.000000 |
| mean       | 0.002699 |
| p90        | 0.009475 |
| p95        | 0.016985 |
| p99        | 0.034505 |
| max        | 0.052353 |
| non-zero % | 27.4%    |

Frustration is bursty, not sustained: 72.6% of per-move events register exactly zero frustration; the non-zero tail is short (~0.01–0.05 peaks).

Anxiety steady-state under decay 0.85 with sustained input `F = K × frustration` is `F / (1 - 0.85) = F / 0.15 ≈ 6.67 × F`. For `anxiety_ss ≥ 0.6` at p95 frustration ≈ 0.017, K must satisfy `K × 0.017 × 6.67 ≥ 0.6 ⇒ K ≥ 5.3`. But:

- Sustained frustration ≈ 0.017 is a *p95* claim, not a typical event. Per-trial sustained-frustration is closer to mean (~0.003), where K ≥ 30 is needed for steady-state crossing.
- Bursty frustration (27% non-zero events at typical magnitudes ~0.01–0.05) decays out between events at 0.85 per move, never reaching steady-state.
- At K ≈ 1.5–2, cap-saturation begins on max-frustration events (K=2 × max-frustration=0.052 = 0.10 ⇒ anxiety contribution per peak event = 0.10, and bursty accumulation can stack); at K ≥ 5, cap-saturation collapses the signal whenever multiple non-zero events stack.

The validation result confirms the structural issue empirically: at K=5.0 zero crossings; at K=7.5 corner produces 1/5 (single-trial crossing on a single bursty trial); at K=10.0 cap_saturation_freq on corner climbs to 0.27 while crossing-rate stays at 1/5 — the formula has entered the "any frustration spike instantly maxes anxiety" regime without producing the predictive 4/5-of-trials signal. **The K range that produces any anxiety crossing is the same K range that produces no predictive lead-time.** No K satisfies criterion (a) on either scenario across the swept range.

**Root cause observable in the existing code surface:** `rpe.py:14-18` `value_heuristic` counts horizontal-adjacent-equal pairs scaled by tile value. On the three Phase 0.7a scenarios as currently calibrated (4 empty cells everywhere, post-recalibration), the dominant tile clusters often lack horizontal-adjacent-equal pairs in the geometry being played. `value_heuristic` is small or zero ⇒ `rpe = score_delta - value_heuristic` is rarely strongly negative ⇒ `frustration += min(1.0, -rpe × 0.6)` accumulator rarely fires. The bursty 27.4% non-zero rate reflects transient negative-RPE windows where Carla missed an expected horizontal merge, not the geometric stall the methodology claims as the predictive lead-time signal.

This is the round-7 redteam walkthrough confirmed empirically: frustration is silent on snake + corner for the same structural reason it is silent on 512-wall — `value_heuristic` is geometrically thin on tile distributions without horizontal pairs. Item 2 wiring (frustration → anxiety) does not close Q2 because its upstream input (RPE-via-`value_heuristic`) does not produce non-trivial sustained frustration on the existing scenarios.

---

## Output 3 — Option 2 (score-velocity) structural kill

Per shape-check spec §5: `score_velocity_t = (1/K) × Σ score_delta_i` shares the `score_delta` input with frustration via `rpe = score_delta - value_heuristic(board_pre)`. Both are smoothed transforms (geometric-decay 0.85 vs rectangular-window K) of the same primary input minus a slow-moving baseline (`value_heuristic`, `positive_part` asymmetry on frustration). Decorrelation budget: small. `Pearson(frustration, score_velocity)` is bounded above ~0.7 structurally on any data-generating process where (i) `value_heuristic` is slow-moving and (ii) frustration's `positive_part` gate fires meaningfully. §4.7 Pearson three-band rule fails by construction at the strict-reject end (`r > 0.8`) for any realistic K and decay.

**Verdict:** Option 2 is **killed by structural derivation**. No empirical run is required. ADR-0013's Alternatives Considered section will document this with the math derivation.

(The empirical Pearson on 658-event existing data is unstable due to floor effects — both signals near zero — but the structural argument does not depend on the empirical Pearson; it depends on the input-sharing math.)

---

## Output 4 — Option 3 (tile-distribution entropy) proxy invalidity

Per shape-check spec §6: tile-distribution entropy decomposes informally into occupancy (captured by `empty_cells`) + value-spread (independent axis). The Phase 0.7a JSONL records `empty_cells_pre/post` but not `board_grid` or per-cell tile values. Any entropy proxy computable from the JSONL is necessarily a 1D function of `empty_cells` and contains zero information about value-spread.

`empty_cells` IS the deprecated driver from Phase 0.7a R1. A monotonic transform of `empty_cells` (any candidate proxy from existing data) would:

- Pass shape-check trivially: `empty_cells` mechanically drives anxiety to the cliff in the pre-counterfactual formula, producing top-decile clustering near `final_move_index` by construction.
- Pass Pearson three-band's lower band: `Pearson(empty_cells, frustration) ≈ +0.12` per round-3 already-run inverse correlation, well below 0.5.

Both gates "pass" not because tile-entropy carries independent signal, but because the proxy is the deprecated driver under a new name. Pinning §3 on a passed proxy commits to a candidate based on a measurement that does not distinguish entropy from `empty_cells`.

**Verdict:** Option 3 **cannot be evaluated on Phase 0.7a 658-event existing data**. ADR-0013's Alternatives Considered section will document the proxy-invalidity argument; the evaluation route (if §3 enters Branch I per spec §7) is targeted re-collection of `board_grid` data via Phase 0.7a-tier harness re-run.

---

## Implications — protocol revisits

Item-2 validation failure triggers spec §4.3. The original spec listed three branches; the post-validation redteam pass (final round of the rounds-1–8 thread) flagged that the three-branch enumeration was itself a §4.4 escalation pattern (every branch was a rewrite-bigger / rewrite-deeper / methodology-narrower, with no kill option named). Two branches added, for symmetry:

- **(i) §3 expands to answer Q2 in addition to Q1.** Item 2 wiring is not sufficient on snake + corner; the rewrite ADR's predictive-lead-time scope expands to include scenario-discriminative drivers on snake + corner that fire when frustration is silent there. *Pattern shape: rewrite-bigger.*
- **(ii) Item 2's spec changes.** Three sub-options: (a) change `value_heuristic` to include vertical merges (the round-2 `rpe.py:14-18` axis-bias side-fix, deferred per `docs/external-review/phase-0.7a-result.md` Side fixes), (b) change the RPE input shape (e.g., `score_velocity_deviation` instead of `score_delta - value_heuristic`), (c) change frustration's accumulator (different decay, different gate condition, different scale). Each sub-option is its own ADR-territory rewrite. *Pattern shape: rewrite-deeper.*
- **(iii) Methodology-narrowing extends to snake + corner.** Drop all three Phase 0.7 scenarios from the falsification gate. Phase 0.7b runs against either zero scenarios (full retract) or fresh scenarios designed for the architecture's primitives (requires fresh scenario-design spec). *Pattern shape: methodology-narrow.*
- **(iv) Kill the predictive-lead-time thesis (publishable negative result).** Cumulative evidence across rounds 1–8: Phase 0.7a empty_cells driver fires mechanically (LESSONS.md 2026-05-06); round-2 grep of frustration→anxiety wiring missing in code; round-3 audit of trauma_intensity disabled-by-harness + ADR-0002 Signatures Beta/Gamma/Delta spec-only + three-channel decay spec-only + reflection-to-decision not wired; round-7+8 validation showing the planned Item-2 rewrite has no admissible operating point on existing scenarios. Four consecutive rounds of "the next layer's fix will work." That is the §4.4 diagnostic signal at full strength, not a setback awaiting one more tweak. Outcome: retire the cliff-test predictive-lead-time claim, retire ADR-0007 (cliff-test pilot pass criteria), keep the architecture as a descriptive UX surface (Brain Panel + ToT visualization + multi-game roadmap), publish the negative result with the round-1–8 discipline as the contribution. *Pattern shape: kill.*
- **(v) Hold without adopting any branch (§4.1 discipline).** This is reversal #2 or #3 of the thread depending on counting. §4.1 hard line: hold the position pending independent assessment for ≥24 hours before adopting any branch. The four substantive branches (i)–(iv) are all live; the disciplined response to a load-bearing falsification mid-session is to commit the artifacts and not adjudicate the fork in the same hour. *Pattern shape: procedural hold.*

**Per spec §4.3:** *"Each branch is its own redteam round. Do NOT pick from inside this spec's adjudication; halt."* The pre-committed response is "protocol revisits" — more general than the three-branch frame and inclusive of (iv) kill and (v) hold.

The deferred `rpe.py:14-18` vertical-merge axis fix (a sub-option of branch (ii)) is a candidate to test before adjudicating between (ii)/(iii)/(iv). It is **not pre-committed in this thread** as an A/B/C gate for the rewrite — the round-7 redteam thread did not pin a kill condition on its outcome. If (ii)(a) is run as a precondition, the pre-commit must be written before the run, with the outcome conditions honestly stated, and only run if the kill condition can be honored if the data goes against the rewrite.

---

## What this verdict does NOT do

- Does NOT retract the §5 Option 2 structural kill or the §6 Option 3 proxy-invalidity derivation. Those derivations stand and will appear in ADR-0013 (if drafted) regardless of Item-2 outcome.
- Does NOT pre-commit to any of the five §4.3 branches. The fork between (i)/(ii)/(iii)/(iv)/(v) is open; this memo provides the data, not the verdict.
- **Does NOT keep Items 1 + 2 in "locked" status.** Item 2's empirical sufficiency on the test scenarios is exactly what the validation measured and what failed. The earlier round-6 framing that "Items 1 + 2 are well-defended and their commit is not contingent on item 3" was contingent on Item 2 producing a valid empirical signal; that contingency now fails. Item 2's status downgrades from *locked* to *pending re-validation* until either (a) a branch (ii) sub-option is run that produces a passing K-sweep, or (b) branch (iv)/(iii) is adopted, in which case Item 2 either ships under a narrowed scope or does not ship at all. *(Earlier draft framed this as "Item 2's necessity remains intact" — that framing was the §4.9 pragmatic-with-bounded-debt pattern flagged by the post-validation redteam pass; struck.)*
- Does NOT alter the harness decision (`docs/external-review/decisions/2026-05-09-phase-0.7b-harness-decision.md` Option B, trauma=0). That decision is independent of §3 driver choice.

---

## Cross-references

- Spec: `docs/superpowers/specs/2026-05-09-3rd-driver-shape-check-design.md`
- Validation script: `nova-agent/src/nova_agent/lab/shape_check_item2_validation.py`
- Smoke test: `nova-agent/tests/test_shape_check_item2_validation.py`
- Source data: `docs/external-review/phase-0.7a-raw-2026-05-09/results/`
- Phase 0.7a result memo (per-move trajectory observations): `docs/external-review/phase-0.7a-result.md`
- P6 re-derivation: `docs/external-review/decisions/2026-05-09-rpe-pivot-first-principles-rederivation.md`
- Round-2 finding on `rpe.py:14-18` axis bias: `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-results.md`
- Methodology audit: `docs/external-review/decisions/2026-05-09-methodology-code-audit-results.md`
- Phase 0.7b harness decision: `docs/external-review/decisions/2026-05-09-phase-0.7b-harness-decision.md`
- Trauma=0 preamble obligation memory: `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_adr_0013_preamble_obligation.md`

---

## Next step

**Hold per §4.1.** The disciplined response to a load-bearing mid-session falsification on a thread already at reversal #2 or #3 is to commit the artifacts under an honest title, then sit with the five-branch fork (i)/(ii)/(iii)/(iv)/(v) for ≥24 hours before adopting any of them.

Do not draft ADR-0013 §3 or any Item-2 amendment within the same session as this verdict. The next adjudication is for the user, on a fresh session, with this memo as input — not for another in-thread redteam round.

The patterns flagged by the round-1–8 redteam thread (§4.4 escalation-without-kill, §4.6 asymmetric-pass/fail-response, §4.9 necessity-vs-sufficiency framing) are codified above; future adjudications should screen for them in their own framings.
