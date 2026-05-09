# Red-Team Response: RPE/Frustration Affect Pivot

**Date:** 2026-05-09
**Branch:** `claude/phase-08-run`
**Triggered by:** External red-team review of the implied "RPE composites + frustration plateaus + within-game trauma triggers" rewrite path mentioned in the Phase 0.7a §7 R1 failure-path text.
**Skill invoked:** `redteam` (full 7-section protocol; Opus inline).
**Status:** Awaiting user approval on Option A / B / C before any spec or code change.
**Phase 0.7a run state at time of analysis:** in flight on `claude/phase-08-run`, ~17 min in, no completions yet, anxiety / trauma / frustration / `tot_fired` all at 0.0 / `false` across the first 12 moves of all 3 trial-0s — strong R1 signal landing but not yet adjudicated.

---

## 1. Steelman — what the red team is actually claiming

**Load-bearing claim:** the proposed RPE/frustration affect rewrite does NOT solve C1; it merely obscures it.

In 2048 specifically, sustained negative RPE / frustration plateau is a *physical consequence* of low `empty_cells`: a locked board cannot produce merges geometrically, so score-delta drops to zero, RPE goes negative, frustration accumulates. Therefore swapping `empty_cells` for `frustration` moves the same signal one derivative away. The cognitive layer remains a pass-through; Phase 0.7 still passes mechanically by a different name.

**Sub-claims:**

1. **Frustration ≡ 1/empty_cells (collinearity).** Failing to merge is the structural consequence of running out of empty cells. `Pearson(frustration, 1/empty_cells)` is hypothesised to exceed 0.8 on existing pilot data → the rewrite is the same formula in different clothes.
2. **`rpe.py:14-18` axis bias (Synthesis M-16).** The `value_heuristic` counts horizontally adjacent equal pairs only; vertical merges are excluded. Building an RPE-driven architecture on this signal feeds the cognitive layer axis-biased garbage. Carla would "panic" on vertical-heavy boards and feel "confident" on horizontal-heavy boards.
3. **Per-move trauma triggers break K=2 session isolation → death spiral.** The current architecture relies on `tag_aversive` firing only at game-over (`main.py:96`). Per-move close-call triggers tag a close call → next move retrieves it as trauma → anxiety spike → ToT route → if the board can't be resolved (likely on a hard board), tag *another* close call → paralysis. The "exposure-extinction halving" defense doesn't fire because the agent hasn't survived yet.
4. **Signature Alpha is conjunction-of-thresholds, not a cognitive primitive.** ADR-0002 abandoned 1:1 mappings as not "scientifically defensible". The replacement is just three thresholds AND'd together (Confidence ↓, Anxiety ↑, Frustration > 0.5). Same false-positive distribution as the 1:1 mapping, scaled by conjunction probability.
5. **Schultz timescale category error worsens** if RPE becomes more load-bearing. 100ms phasic dopamine ↔ 1-3s agentic timescale gap remains.

**The single attack the author cannot dodge:** *"Prove your new frustration metric contains information independent of grid density before writing a single line of code."*

---

## 2. Where the red team is right

- **(a) The Pearson test is the right gate.** Before committing to RPE/frustration as the rewrite path, run `Pearson(frustration, 1/empty_cells)` on the morning-pilot CSV. Methodologically correct: prove independence first, write code second.
- **(b) The `rpe.py:14-18` axis bias** — needs verification, but if true it is a real bug compromising any RPE-driven architecture. Already on Synthesis M-16.
- **(c) Mid-game trauma triggers vs game-over isolation** — the architecture relies on `tag_aversive` firing only at game-over. A per-move trigger needs an explicit consolidation / off-policy retrieval mechanism.
- **(d) Signature Alpha vs ADR-0002 critique has logical force** — the conjunction is three thresholds, not a state-machine primitive.
- **(e) "Do nothing in code yet" implication** — committing the rewrite ADR without the Pearson test is premature.

---

## 3. Where the red team is weaker than they framed

- **(a) The `r > 0.8` claim is a hypothesis, not data.** They didn't run the test. Frustration carries TEMPORAL integration (decay 0.85, multi-move accumulation) that `empty_cells` (a snapshot) does not. A brief `empty_cells` dip with recovery wouldn't elevate frustration; sustained sub-optimality across 4-6 moves would. Empirical `r` could be 0.4-0.6, in which case independent signal exists.
- **(b) The collinearity argument assumes optimal play.** A weak or random agent gets score-delta from accidental merges on cluttered boards — score-delta is mediated by policy quality, not just geometry. Pearson on Carla's actual play data is needed, not theoretical inference from rules-of-the-game.
- **(c) "In 2048" framing is a domain-narrowing rebuttal, not architecture-fatal.** They concede this themselves at the end (*"Is 2048 too geometrically constrained?"*). Project Nova's commercial pitch is multi-game (Snake, FlappyBird per the roadmap) — if 2048's geometry is the constraint, the rewrite still works on games where score and density are decoupled.
- **(d) Death-spiral argument treats K=2 isolation as the only defense.** ADR-0012 cosine-relevance gating on retrieval is another layer. If the threshold is set correctly, mid-game close-calls don't trigger immediate trauma retrieval unless the new state is highly similar.
- **(e) Schultz critique is partially handled.** The Yehuda citation has been struck (`cc3416b`, `a5423f6`). Russell/Schultz reframing is owed but not on the Phase 0.7a critical path. The methodology has been actively *distancing* from Schultz, not adding load on it.
- **(f) Signature Alpha bar moves goalposts.** "Correlate with human churn better than random forest on raw telemetry" — random forests are non-interpretable. The whole point of the cognitive model is comparable accuracy with interpretable axes, not crushing the RF baseline.

---

## 4. Costs of the implied fixes

| Fix | Cost ($) | Time | Risk |
|---|---:|---|---|
| `Pearson(frustration, 1/empty_cells)` on morning-pilot CSV | $0 | ~30 min | Low — analysis on existing data |
| Fix `rpe.py:14-18` axis bias | $0 + ~$0.50 regression | ~2h with TDD + ADR amend | Medium — could shift Carla behavior, may re-confound the upcoming N=5 Sonnet pilot if landed mid-flight |
| Off-policy memory replay (consolidation during rest) | substantial | 5-10 dev-days | HIGH — touches memory + affect + decision; new ADR territory |
| Random forest baseline for Signature Alpha | depends on data | weeks | Defer — Project Nova does not have human churn data on tap |

---

## 5. Options on the table

### Option A — Ratify status quo. Run finishes. Add Pearson test as rewrite-ADR precondition.

- **Benefit:** pre-registration discipline preserved; R1 verdict bulletproof; the Pearson test runs free on existing data BEFORE any rewrite code is touched.
- **Cost:** spend ~$1.40 more to finish the run. Does not address the in-flight `rpe.py` bug for the upcoming Sonnet pilot — that becomes a §7 R1-rewrite precondition.

### Option B — Halt run NOW. Run Pearson on the morning-pilot CSV. Decide based on `r`.

- **Benefit:** saves ~$1.40 + ~15 min. Forces the methodologically correct gate before any rewrite spend.
- **Cost:** breaks pre-registration on Phase 0.7a (halt at N=3 partial because an external argument lands = the same goalpost-shift the pre-registration is supposed to prevent — applies in both directions). The R1/R2/R3 verdict becomes contestable: any future reviewer can argue "halted because the early signal favored R1, not because the discipline allowed it."

### Option C — Halt run. Fix `rpe.py` axis bias. Re-launch Phase 0.7a with corrected RPE.

- **Benefit:** cleaner counterfactual data; tests the architecture as it should be, not as it is broken.
- **Cost:** ~$1.40 of in-flight spend wasted; ~$1.50 on rerun (net wash on $); 2-3h dev time; tests a *different architecture* than the morning pilot, which confounds C6B disambiguation. The whole point of Phase 0.7a was running THIS architecture (post-recalibration grids, null `empty_cells`) against the morning-pilot model surface.

---

## 6. Recommendation

**Recommend Option A — ratify status quo + Pearson test as rewrite-ADR precondition.**

Reasoning:

1. **The red team's load-bearing claim is empirically testable but untested.** Running Pearson on the morning-pilot CSV (~30 min, $0) AFTER the run completes satisfies *"what kills the finding"* without halting in-flight pre-registration.
2. **Halting Phase 0.7a now wastes pre-registration AND the in-flight spend.** Pre-registration applies in both directions — not halting early to favor R1, AND not halting early because an external argument lands. Caving on the methodology because someone made a strong attack IS the failure mode pre-registration prevents.
3. **The collinearity attack (#1) and the `rpe.py` bug (#2) both apply to the REWRITE, not to Phase 0.7a's null-empty-cells counterfactual.** Phase 0.7a tests *"does the architecture have non-empty_cells signal?"* — the answer is independent of whether RPE/frustration is the right rewrite axis. The data is informative either way.
4. **The mid-game trauma death-spiral concern (#3) is Phase 0.8 territory** (trauma ablation spec). Correctly captured there, not on the Phase 0.7a critical path.
5. **Signature Alpha (#4) and Schultz (#5) are methodology / pitch concerns** — defended in spec writeups, not blockers for adjudication.

### Action sequence under Option A

1. **Run finishes naturally.** R1/R2/R3 adjudicated honestly with the full N=15 dataset.
2. **After the R1 adjudication memo:** run `Pearson(frustration, 1/empty_cells)` on the morning-pilot CSV (separate analysis script, ~30 min, $0).
3. **After the Pearson test:** draft the rewrite ADR with the test result baked in:
   - If `r > 0.8`: the ADR explicitly rules out RPE/frustration and proposes alternative axes (board volatility, memory-retrieval composite weighted by aversive-tag relevance, recovery-rate metric, ToT-branch-disagreement as an uncertainty signal).
   - If `r < 0.5`: the ADR proceeds with the RPE composite proposal, citing the red-team challenge + Pearson result as evidence the new signal carries independent information.
   - If `0.5 ≤ r ≤ 0.8`: the ADR proposes a hybrid axis — RPE composite with explicit decorrelation (residualisation against `empty_cells`) and a new non-density driver added in parallel.
4. **`rpe.py:14-18` axis bias** gets its own fix-PR AFTER Phase 0.7b (separate from the rewrite ADR to keep the changes orthogonal). The fix is small (5 lines + tests + an ADR-amend bullet), so it does not need to gate the rewrite. If Phase 0.7b runs before the fix lands, the rewrite must explicitly note that the RPE signal feeding the new architecture is the corrected (two-axis) version.

---

## 7. Approval request

**Approval needed before any changes.** Pick an option (or propose another) and I will proceed. No spec / ADR / code edits until you confirm.

---

## Insights to harvest after resolution

These do NOT ship until after the user picks an option, but flagging now so the signal isn't lost:

- **`LESSONS.md` candidate:** *"Before authoring an architectural rewrite ADR, prove the new signal contains information independent of the deprecated signal. A correlated replacement is not a fix; it is renaming the bug."* Generalisable beyond Project Nova.
- **Methodology-doc defense candidate** (`docs/product/methodology.md`): *"When a game proves geometrically constrained, the architecture's general claim survives only on a non-collinear domain. The multi-game roadmap (Snake, FlappyBird) is the falsifier; if the same collinearity reproduces there, the architecture's commercial claim fails."*
- **A/B-test note for the rewrite ADR's "Alternatives considered" section:** the red team's *"random forest beats Signature Alpha on raw telemetry"* bar is a moving goalpost (RF is non-interpretable; the cognitive model trades comparable accuracy for interpretable axes). The ADR's defense should explicitly address this and propose a different bar — e.g., "comparable AUC to RF on a held-out cohort while preserving per-axis legibility."
