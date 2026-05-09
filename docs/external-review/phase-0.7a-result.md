# Phase 0.7a Counterfactual — Adjudication

**Date:** 2026-05-09
**Branch:** `claude/phase-08-run`
**Spec:** [`docs/superpowers/specs/2026-05-09-phase-0.7a-counterfactual-design.md`](../superpowers/specs/2026-05-09-phase-0.7a-counterfactual-design.md)
**Plan:** [`docs/superpowers/plans/2026-05-09-phase-0.7a-counterfactual-impl.md`](../superpowers/plans/2026-05-09-phase-0.7a-counterfactual-impl.md)
**Raw output:** [`docs/external-review/phase-0.7a-raw-2026-05-09/`](./phase-0.7a-raw-2026-05-09/) (commit `6eb58e5`)
**Related red-team:** [`docs/external-review/2026-05-09-redteam-rpe-pivot-response.md`](./2026-05-09-redteam-rpe-pivot-response.md)

---

## Erratum (2026-05-09, posted same day)

**This memo's framing of the verdict was wrong as originally written.** Two sub-verdicts must be distinguished. Per `docs/external-review/decisions/2026-05-09-rpe-pivot-layer2-round2.md` finding 1 ([critical]), correcting before any rewrite ADR cites this memo.

### What was wrong

The memo states (§"Per-move trajectory observations" + §"Implication for the rewrite ADR"):

> "the architecture's *non-`empty_cells`* anxiety drivers — trauma_intensity (memory retrieval composite) and the RPE → frustration → anxiety chain — produced zero predictive signal across 658 in-domain observations."

> "The drivers spec §7 names as candidates (a) RPE plateau (frustration-derived) and (b) memory-retrieval composite are *currently in the formula and currently silent*."

The "currently silent" framing for the RPE → frustration → anxiety chain is **factually incorrect**. A grep of `nova-agent/src/nova_agent/affect/state.py` shows that all anxiety-write sites are:

```python
# Line 37 — decay
anxiety = v.anxiety * 0.85

# Line 49-50 — empty_cells term, gated by counterfactual flag
if not self._null_empty_cells_term:
    anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)

# Line 51 — trauma_intensity term
anxiety += 0.3 * _clamp(trauma_intensity, 0.0, 1.0)

# Line 52-53 — terminal override
if terminal:
    anxiety = 1.0
```

**Frustration is computed (line 44) but never appears in any anxiety-write expression in any file under `nova-agent/src/nova_agent/`.** The "RPE → frustration → anxiety" driver named in this memo and elsewhere in `methodology.md` is **not implemented in the code as shipped to Phase 0.7a**. It cannot be "silent" — it does not exist.

This is not a tone correction. It is a verdict-scope correction.

### Two sub-verdicts (replacing the original "C1 fully confirmed")

**(a) C1-as-implemented: confirmed.** With the `empty_cells` term nulled, the architecture as shipped to Phase 0.7a has only one remaining anxiety driver (`trauma_intensity` via line 51) and decay (line 37). `trauma_intensity` was 0.0 across all 658 per-move events (no aversive memories existed mid-game). Decay alone cannot drive anxiety to threshold from 0.0. Therefore anxiety stayed at 0.0 across the run and `t_predicts != None` was structurally impossible. R1 fired as designed against the architecture-as-shipped.

**(b) C1-as-specified: untested.** Phase 0.7a does NOT tell us whether the architecture-as-described in `methodology.md` (with frustration → anxiety wired, the RPE chain functioning) would have produced `t_predicts != None`. The counterfactual could not test a driver that did not exist in the code. Whether wiring the linkage produces predictive lead-time is a separate empirical question, partially addressed by `docs/external-review/decisions/2026-05-09-rpe-pivot-desk-demo.py` (which finds wiring + scaling produces a saturating signal on snake-collapse-128 + corner-abandonment-256 but cannot fire on 512-wall under any function family because frustration was 0/199 nonzero events on that scenario).

### What this erratum does NOT do

- Does NOT retract the empirical finding that the architecture-as-shipped fails to produce predictive lead-time without `empty_cells`. That finding stands.
- Does NOT retract R1's mechanical applicability. R1 fires on the architecture-as-coded.
- Does NOT excuse the original wording. Per `LESSONS.md` §4.2 (no retro-rationalization): the original "currently silent" wording was wrong. It should have been written as "the RPE → frustration → anxiety chain claimed in `methodology.md` is not wired in the code, and the only implemented non-`empty_cells` driver (`trauma_intensity` via memory retrieval) was 0.0 across the run." That is the correct framing. This erratum does not dress up the original framing as a typo or as "what I meant"; it concedes the original was wrong.

### What changes downstream

- The rewrite ADR's preamble cites THIS erratum, not the original "C1 fully confirmed" framing.
- The methodology audit (separate spec, ≤4h timebox per round 2 finding 3) is now mandatory before the rewrite ADR can be drafted, because at least one `methodology.md` claim has been shown to be code-fictional and other claims may be too. Audit priority list: see `docs/external-review/decisions/2026-05-09-rpe-pivot-layer2-round2.md` finding 5.
- The memo's "Recommendations" §4 (last bullet on `rpe.py:14-18` axis bias) is also misframed — the axis treatment is documented design intent, not a bug. The fix is a methodology debate (whether the design is correct), not a bug repair. Out of scope for this erratum; will be addressed in the rewrite ADR if it intersects the new scope.

### Cross-references for the corrected reading

- `docs/external-review/decisions/2026-05-09-rpe-pivot-test6-results.md` — Pearson + frustration distribution + grep finding
- `docs/external-review/decisions/2026-05-09-rpe-pivot-desk-demo.py` — wiring + scaling does not pass spec R2 on 512-wall under any function family
- `docs/external-review/decisions/2026-05-09-rpe-pivot-layer2-round2.md` — Layer 2 round 2 review that prompted this erratum
- `nova-agent/src/nova_agent/affect/state.py` lines 37, 49-53 — the load-bearing code excerpt

---

## Pre-registered decision rule (spec §3)

The decision rule was committed pre-execution. No goalpost moves.

- **R1 (kill):** any single scenario produces fewer than 4 of 5 trials with `t_predicts is not None` → C1 fully confirmed → architecture rewrite ADR mandatory; Phase 0.7b dies.
- **R2 (salvage strict):** all 3 scenarios independently satisfy ≥4/5 `t_predicts is not None` AND ≥4/5 `(game_over_move - t_predicts) ≥ 2` AND within-scenario `t_predicts` stdev ≥ 1.5 moves → N=5 Sonnet pilot proceeds AFTER reweighting ADR + smoke re-test.
- **R3 (ambiguous):** anything else → halt + fresh `/redteam` Opus subagent.

---

## Run summary

| Metric | Value |
|---|---|
| Tier | `phase_0_7a` (gemini-2.5-pro on every cognitive role; commits `ccb7aec`, `a5e2d95`) |
| Counterfactual flag | `NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM=1` |
| Trials | N=5 × 3 scenarios = 15 Carla, 15 Bot |
| Wall clock | 03:34:48 → 05:05:18 UTC (~90 min) |
| Total LLM cost | ~$0.66 (under $1.50 spec §5.3 expected; well under $7 hard cap) |
| Per-call cost-abort gate | Never tripped |
| Bot arm | All 15 trials aborted at move 0 (`parse_failure`); Pro returned empty visible output on the bot prompt. Spec §2.3 declared bot a no-op for this counterfactual; bot data is excluded from adjudication. Pro/bot incompatibility logged for Phase 0.8. |

---

## Per-scenario results — Carla arm

`t_predicts` is computed per spec §2.7: first move where `anxiety > 0.6` for ≥2 consecutive moves. `final_move_index` is the last move played; `is_right_censored=True` means the game hit `MAX_MOVES=50` without a natural game-over.

### `512-wall` (initial empty_cells = 4 post-recalibration)

| Trial | `t_predicts` | `final_move_index` | `is_right_censored` |
|---:|:-:|---:|:-:|
| 0 | None | 47 | False (natural game-over) |
| 1 | None | 49 | True (MAX_MOVES) |
| 2 | None | 47 | False (natural game-over) |
| 3 | None | 5 | False (natural game-over) |
| 4 | None | 49 | True (MAX_MOVES) |

**`t_predicts != None` count: 0 / 5.** Below R1's 4/5 threshold.

### `snake-collapse-128` (initial empty_cells = 4 post-recalibration)

| Trial | `t_predicts` | `final_move_index` | `is_right_censored` |
|---:|:-:|---:|:-:|
| 0 | None | 49 | True |
| 1 | None | 49 | True |
| 2 | None | 49 | True |
| 3 | None | 49 | True |
| 4 | None | 49 | True |

**`t_predicts != None` count: 0 / 5.** Below R1's 4/5 threshold. All 5 trials right-censored at MAX_MOVES.

### `corner-abandonment-256` (initial empty_cells = 4 post-recalibration)

| Trial | `t_predicts` | `final_move_index` | `is_right_censored` |
|---:|:-:|---:|:-:|
| 0 | None | 49 | True |
| 1 | None | 49 | True |
| 2 | None | 49 | True |
| 3 | None | 35 | False (natural game-over) |
| 4 | None | 24 | False (natural game-over) |

**`t_predicts != None` count: 0 / 5.** Below R1's 4/5 threshold.

---

## Verdict — R1 fires on all three scenarios

**0 of 15 Carla trials produced `t_predicts != None`.** Each scenario lands at 0/5 — below R1's "fewer than 4 of 5" threshold by a wide margin.

R1 fires independently on all three scenarios, simultaneously. **C1 is fully confirmed.**

The cognitive architecture's anxiety signal is mechanically dependent on the `empty_cells` term. With that term nulled, the architecture produces no scenario-discriminative predictive signal — not on snake-collapse-128 (the C1-ablation "ambiguous, cognitive contribution not ruled out" scenario), not on corner-abandonment-256 (the cliff that saw morning-pilot `t_predicts ∈ {0, 1}`), not on 512-wall.

---

## Per-move trajectory observations (load-bearing for the rewrite ADR)

Every Carla trial published a `per_move` event for every move played (per spec §2.4). Total: **658 `per_move` events across 15 trials**. The full distribution of three load-bearing fields:

| Field | Distribution across all 658 per-move events |
|---|---|
| `anxiety` | **0.0 on every event.** Anxiety never moved off baseline in any of the 15 trials × ~50 moves × 3 scenarios. |
| `trauma_intensity` | **0.0 on every event.** Memory-retrieval-derived trauma intensity surfaced zero aversive recall passing the ADR-0012 cosine relevance threshold across the entire run. |
| `tot_fired` | **`false` on every event.** Tree-of-Thoughts never deliberated; Carla ran the pure-react path the entire run (consistent with `should_use_tot` being gated on the same anxiety threshold the formula never crossed). |
| `frustration` | Tiny non-zero values ~0.0008–0.0012 on a handful of events; effectively 0.0 across the run. RPE-via-frustration produced no decision-relevant signal. |
| `valence` / `dopamine` | Did vary across moves (valence ~0.0–0.42, dopamine variable). RPE updates valence and dopamine; these fire correctly. The RPE chain to anxiety is broken. |

**Implication for the rewrite ADR.** The architecture's *non-`empty_cells`* anxiety drivers — trauma_intensity (memory retrieval composite) and the RPE → frustration → anxiety chain — produced zero predictive signal across 658 in-domain observations. This is *not* a "Phase 0.7a falsified the empty_cells driver, look for a replacement" finding; it is a "Phase 0.7a falsified the empty_cells driver AND every non-empty_cells driver currently wired into the formula" finding.

The most striking single observation: **trial 3 of 512-wall died at move 5** (`final_move_index=5`, `is_right_censored=False`). The game-over board state was reached. The architecture's pre-game-over anxiety remained 0.0 throughout the 5 moves. The architecture saw the cliff at point-blank range and did not predict it.

---

## What this rules out (and what it does not)

### Rules out

- **C1 ambiguity on snake-collapse-128.** The C1 ablation (`c1-ablation-result.md`) marked snake at stdev=2.07 as "ambiguous; cognitive contribution not ruled out." Phase 0.7a rules it out. With `empty_cells` nulled, snake produces 0/5 `t_predicts != None`, identical to corner and 512-wall. The original stdev=2.07 was empty-cells-depletion-crossing variance, not cognitive variance.
- **C6B (Gemini-Pro-specific reasoning failure).** The morning pilot ran Pro and saw `t_predicts ∈ {0, 1}` on corner + 512-wall. Phase 0.7a ran Pro on the *post-recalibration* grids (4 empty cells everywhere) with the empty_cells term nulled. Result: `t_predicts = None` everywhere. C6B is dead — Gemini Pro is not the bottleneck; the architecture is.
- **The "non-empty_cells anxiety driver already exists, wire it in" salvage path.** Trauma_intensity stayed at 0.0 across 658 observations; frustration stayed effectively at 0.0. The drivers spec §7 names as candidates (a) RPE plateau (frustration-derived) and (b) memory-retrieval composite are *currently in the formula and currently silent*. The rewrite is not "wire in the existing driver"; it's "introduce a driver that does not currently exist, or rewire the existing drivers to actually fire."

### Does not rule out

- **The trauma-tagging mechanism itself (Phase 0.8).** Phase 0.7a runs do not tag aversive memory mid-trial (per `main.py:96` game-over-only contract). Trauma_intensity at 0.0 across this run reflects "no within-trial aversive recall," not "trauma tagging is broken." Phase 0.8 trauma ablation is a separate spec on a separate critical path.
- **The full methodology.** Cognitive Audit Trace (Brain Panel) and the State-Transition Signatures survive as product surfaces. Phase 0.7a falsifies the *as-deployed empty_cells-driven anxiety formula's predictive lead-time claim*. It does not falsify the project.
- **The Carla persona itself.** Carla's pure-react path *did play the games* — most trials survived 50 moves on the recalibrated grids. The decision LLM is functional; the affect formula is the layer that failed.

---

## Cross-link — red-team challenge to the natural rewrite path

A red-team review of the implied "RPE composites + frustration plateaus" rewrite path was filed mid-run: [`2026-05-09-redteam-rpe-pivot-response.md`](./2026-05-09-redteam-rpe-pivot-response.md). The red team's load-bearing claim is that *in 2048*, sustained negative RPE / frustration plateau is a physical consequence of low `empty_cells` (locked board → no merges geometrically possible), so swapping `empty_cells` for `frustration` moves the same signal one derivative away.

Phase 0.7a's per-move data **provides initial empirical support for the red team's claim** on Carla's actual play data: with empty_cells nulled, frustration also stayed effectively at 0.0 across 658 observations. The collinearity hypothesis is not yet quantified (`Pearson(frustration, 1/empty_cells)` against the morning-pilot CSV is the gating test the red team named), but the Phase 0.7a data is consistent with the claim that the two signals are coupled by the game's geometry.

This finding makes the Pearson test a hard precondition for any rewrite ADR that names RPE/frustration as a candidate driver (per the recommended Option A path in the red-team response, currently awaiting user approval).

---

## Recommendations (mandatory under R1, per spec §7)

R1 firing requires the following sequence before any new pilot is authorized. Numbered per spec §7 R1 rewrite-must clauses, with annotations capturing what the Phase 0.7a data adds.

1. **Reduce the `empty_cells` coefficient from 0.7 to ≤ 0.3 (or remove the term entirely).** Phase 0.7a is the maximal removal (coefficient 0). Any reweighting must be paired with at least one new non-density driver — the existing non-density drivers are silent on these scenarios.
2. **Introduce a non-`empty_cells` anxiety driver.** Spec §7 names three candidates:
   - **(a) RPE plateau (frustration-derived).** Conditional on the Pearson test ruling out collinearity per the red-team response (Option A pending). If Pearson `r > 0.8`, this candidate is rejected and the rewrite ADR must propose a different axis.
   - **(b) Memory-retrieval composite (cosine-weighted aversive recall, partially in place via ADR-0012).** Phase 0.7a data shows this driver at 0.0 across 658 observations — currently wired but currently silent. The rewrite ADR must either re-tune the cosine relevance floor, change the within-game retrieval contract (Phase 0.8 territory; risk of death-spiral per red-team #3), or fold this into a different aggregation scheme that surfaces signal at the timescale Phase 0.7's t_predicts gate operates on.
   - **(c) Board-volatility metric independent of free-space counting.** This is the one Phase 0.7a does not pre-falsify. Candidates worth ADR-level evaluation: tile-distribution entropy, max-tile-locality measure, recovery-rate metric (Δ score across last K moves vs. K-move history), ToT-branch-disagreement as an uncertainty signal.
3. **Re-run the C1 ablation on the new formula against the morning-pilot CSV to confirm `empty_cells` no longer dominates.** Plus run `Pearson(frustration, 1/empty_cells)` on the same CSV as the red-team-named precondition (Option A).
4. **Re-run Phase 0.7a on the new formula before any new pilot is authorized.** Same N=5 × 3 scenarios cadence; same `phase_0_7a` tier; same cost guardrails. Spec §9 acceptance for Phase 0.7b is unchanged: R2 is required.

### Side fixes that do not gate the rewrite ADR but should not be forgotten

- **`rpe.py:14-18` axis bias** (Synthesis M-16, red-team #2). 5-line fix + tests. Land it AFTER Phase 0.7b in a separate PR so the change does not re-confound the upcoming pilot.
- **Bot/Pro `parse_failure` issue.** All 15 bot trials aborted at move 0; Pro returned empty visible output on the bot prompt. Likely Pro's thinking budget interacting with the bot's smaller `max_output_tokens`. Out of Phase 0.7a scope (spec §2.3 made bot a no-op); fix is Phase 0.8 territory or earlier if a Pro-tier bot run becomes load-bearing.

---

## What this adjudication does NOT do

- Does not authorize Phase 0.7b. The N=5 Sonnet pilot is **not authorized** per spec §9 acceptance — R2 was not produced. The rewrite ADR + the §7 sequencing above is the gate.
- Does not author the rewrite ADR itself. That is the next artifact, drafted via `superpowers:writing-plans` (Path A — Opus required) once the user picks an option from the red-team response.
- Does not deviate from pre-registration. The 15 Carla trials ran to completion; the verdict is computed against the §3 R1/R2/R3 rules as committed.
- Does not propose ad-hoc additional counterfactuals (per spec §7 "*Do not author a third counterfactual variant*"). The next gate is the rewrite ADR, NOT another counterfactual axis.

---

## Status next

1. **This memo committed:** `docs(phase-0.7a): pre-registered adjudication`.
2. **Red-team response committed separately:** `docs(external-review): RPE pivot red-team response` (or merged into this memo's commit; awaiting user decision on the Option A/B/C question).
3. **ONE PR for the Phase 0.7a unit** opened against `main` per spec §8 step 8 + workflow.md PR cadence. Bundle: spec (`595d5b9`) + plan (`8f2f8f3`) + impl Task 1 (`b2f11f9`) + impl Task 2 (`ef927b4`) + cost-abort gate (`ef4989b`) + handoff (`86eb1b4`) + tier wiring (`ccb7aec`) + `thinking_budget` fix (`a5e2d95`) + raw output (`6eb58e5`) + this memo + red-team memo.
4. **Rewrite ADR drafting** is post-PR work — Path A trigger fires (`nova_agent/affect/**` rewrite + load-bearing decision); user must `/model claude-opus-4-7[1m]` and confirm Option A/B/C from the red-team response before drafting begins.
