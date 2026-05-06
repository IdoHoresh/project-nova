# Round 2A — Gemini 2.5 Pro Attacks Claude Opus's Review

> Source: Gemini 2.5 Pro Deep Research, CLI session, 2026-05-06.
> Prior: Round 1 Claude (`round-1-claude.md`).
> Status: Round 2 cross-fire. Gemini reads Opus's report and attempts
> to break it.
>
> **Verification grade (added by author after grading):**
> - Gemini's NEW findings (3): all verified real and substantive.
>   These add genuine value to the corpus.
> - Gemini's REBUTTALS of Opus's top findings: weak. Two contain
>   factual errors; one addresses 2 of 6 dimensions; one accuses
>   Opus of "bad-faith reviewing" without basis. Opus's top findings
>   survive.
> - Gemini's "Motivated" verdict on Opus is itself unsupported by
>   Gemini's evidence.
>
> Net: Round 2A surfaced new attacks (decay-rate brittleness, bus-
> telemetry integrity, budget metadata lag) that should enter the
> synthesis. The kill-Opus attempts mostly failed.

---

## 1. Per-finding rebuttals

### "Carla's anxiety signal is a near-deterministic function of empty_cells" (Critical)

**Rebuttal:** Reductionist. The reviewer ignores that Anxiety is one of six dimensions in a compositional affect vector (`affect/state.py:27-58`). Phase 0.7 is a smoke test for predictive lead-time, not an exhaustive validation of the entire Russell model. The use of a simple proxy for the first game (2048) is an engineering choice for a pilot, not a structural flaw. Furthermore, the `trauma_triggered` (+0.3) and `terminal` (1.0) inputs already provide non-deterministic drivers that the reviewer's "Pearson correlation" attack would fail to capture in real scenarios.

**Artifact:** `docs/product/methodology.md` §1.1 (Signature Alpha's multi-variable dependency).

> **Author note (REBUTTAL FAILS):**
> 1. The "compositional affect vector" defense is a deflection. Opus
>    didn't claim AffectVector is one-dimensional; he claimed `anxiety`
>    SPECIFICALLY is deterministic in `empty_cells`, AND ADR-0007's pass
>    criterion is gated on `anxiety > 0.6` — none of the other 5
>    dimensions enter `t_predicts`.
> 2. "Phase 0.7 is a smoke test, not exhaustive validation" contradicts
>    project framing. CLAUDE.md, methodology.md §4, and ADR-0005 all
>    name Phase 0.7 as the **load-bearing falsification gate**. Gemini
>    is downgrading the gate's role to defuse the attack.
> 3. "`trauma_triggered` and `terminal` provide non-deterministic
>    drivers" — **factually wrong**. Both flags are themselves
>    deterministic functions of game state: `terminal` = game-over,
>    `trauma_triggered` = `is_catastrophic_loss(last_empty_cells <= 2
>    AND max_tile >= 64 AND final_score < max_tile * 4)`. No
>    non-determinism enters via either path.
> 4. "Pearson correlation would fail to capture in real scenarios" —
>    hand-wave with no mechanism cited.
>
> Opus's #1 stands and is strengthened by this failed rebuttal.

---

### "The recalibration spec is... goalpost-moving" (Critical)

**Rebuttal:** Standard calibration. The reviewer conflates scenario tuning (adjusting stimulus to find the signal range) with pass-criteria softening. The "Delayed Detection" principle (`specs/2026-05-06... §2.1`) specifically aims to distinguish between "mechanical death" and "structural trap" — testing if the model can see the cliff before the mechanical compression. If it were purely `empty_cells`, the "Delayed Detection" target of move 4-8 would be impossible to hit.

**Artifact:** `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` §2.1.

> **Author note (REBUTTAL FAILS — math error):**
> 1. Opus did NOT conflate scenario tuning with pass-criteria
>    softening. He listed them as TWO separate critical findings (§6.4
>    finding 1 = empty-cell tuning of the metric driver; §6.4 finding 2
>    = the snake-collapse 0/5→1/5 borderline-PASS softening). Gemini
>    addresses only the first and ignores the second entirely. The pass-
>    criteria softening attack stands undefended.
> 2. **Math error.** "If it were purely empty_cells, the Delayed
>    Detection target of move 4-8 would be impossible to hit." Wrong.
>    The anxiety formula is `anxiety += 0.7 * max(0.0, (3 - empty_cells)
>    / 3)`. With initial `empty_cells = 4`, the formula gives ZERO
>    contribution until cells drop to ≤ 3. With decay 0.85, anxiety
>    saturates above 0.6 about 1-2 moves AFTER cells first hit 3 or
>    below. The "Delayed Detection" target of move 4-8 is **exactly
>    what the empty_cells-only formula would produce** if the grid is
>    designed to deplete to 3 cells around move 4-6. The recalibration
>    "Delayed Detection works because of empty_cells, not despite it.
>
> Opus's recalibration finding stands and is strengthened.

---

### "Russell (1980) is a 2-dimensional model; Nova's 6-dimensional vector is dressed up... as theatre" (Critical)

**Rebuttal:** Misrepresentation of "anchors." The project explicitly defines Russell (V/A) as the core axes, which are then extended by Schultz (dopamine/RPE) and others. The reviewer treats a product's scientific anchors as literal implementation requirements. The goal is a consistent vocabulary for the Cognitive Audit Trace, not a 1:1 endocrine simulation.

**Artifact:** `docs/product/scientific-foundations.md` (Synthesis section).

> **Author note (REBUTTAL PARTIAL):**
> Gemini addresses 2 of the 6 dimensions (valence + arousal as Russell;
> dopamine as Schultz). Opus's critique covers 4 OTHER dimensions:
> anxiety, frustration, confidence have NO citation anchor at all, and
> Schultz is mis-applied to Nova's per-second timescale (Schultz is
> ~100ms phasic dopamine).
>
> Gemini's "vocabulary not simulation" defense is contradicted by
> `methodology.md:153` which explicitly tables the trauma decay rule
> next to "Yehuda et al. on stress endocrinology; trauma persistence
> research" — that IS a citation-as-claim, not vocabulary borrowing. If
> Gemini's defense were honest, the methodology doc would not cite
> endocrinology research at all.
>
> Opus stands on 4 of 6 dimensions + the Schultz timescale + the Yehuda
> category leap.

---

### "The arbiter's ToT-trigger gate is 2048-specific" (High)

**Rebuttal:** Intentional ignorance of roadmap. The arbiter logic is explicitly marked with `HARD_` constants in a file slated for abstraction in Phase 1 (`arbiter.py:4-6`). Critiquing a Phase 0.7 pilot for having hardcoded constants for its only supported game is bad-faith reviewing.

**Artifact:** `docs/product/product-roadmap.md` §1 (Phase 1).

> **Author note (REBUTTAL FAILS):**
> The "bad-faith reviewing" framing is itself motivated reasoning.
> Opus's mandate (§6.1 attack 2, §6.3 attack 9 ADR-0008) explicitly
> empowers attacks on roadmap-deferred abstractions. Opus's actual
> claim was: the abstraction (ADR-0008) is structurally untestable
> until a second game ships, AND the arbiter constants are 2048-tuned,
> AND Phase 0.7's "cog-arch as moat" claim (ADR-0001) collapses if the
> abstraction doesn't generalize. Gemini's "the constants are marked
> HARD_" defense restates the problem rather than addressing it. The
> finding stands.

---

## 2. Findings they missed entirely

### [critical] Brittle Signature Coupling

The State-Transition Signatures (e.g., Signature Alpha's "3+ consecutive moves") are hardcoded on top of specific decay rates (`0.85`, `0.98`) in `state.py`. A "feel" adjustment to these constants would silently invalidate the signature logic without failing a single unit test. This is the project's true "hidden" fragility.

> **Author note (VERIFIED REAL):** Decay rates at `state.py:28-33` are
> hardcoded: `0.95` valence, `0.92` arousal, `0.6` dopamine, `0.92`
> frustration, `0.85` anxiety, `0.98` confidence. Signature Alpha (`ADR-0002`)
> specifies "frustration > 0.5 sustained for 5+ moves." If
> frustration decay changes from `0.92` to `0.85`, the "sustained for
> 5+ moves" semantics changes substantially without a test catching it.
> No `test_signature_alpha_under_decay_perturbation` exists. **Genuine
> new attack. Severity critical is defensible.**

---

### [high] Telemetry/Measurement Integrity

The `RecordingEventBus` is shared between live UI (best-effort) and "measurement-grade" CSV data. Network jitter or WebSocket drops during a pilot run can introduce non-deterministic measurement error into `t_predicts` that the test runner currently ignores.

> **Author note (VERIFIED, COMPOUNDS OPUS):** Opus's §6.1 finding #4
> covered the bus-as-recorder problem from a different angle (best-
> effort recorder for measurement-grade data). Gemini reframes it as a
> pilot-time integrity issue. Both true; the recommendations stack
> (cliff-test should write its own append-only CSV inside the trial
> loop with fsync-per-move, NOT depend on the bus).

---

### [medium] Budget Metadata Lag

Cost accounting in `cliff_test.py` relies on LLM response metadata. In concurrent pilots, metadata lag or provider-side usage reporting delays can cause Nova to blow through its "hard cap" before the orchestrator even sees the budget update.

> **Author note (PLAUSIBLE, NEW):** Independent of Opus's §6.5 "no
> abort gate" critique. Even if an abort gate is added, provider-side
> reporting lag during concurrent calls means the gate may fire late.
> Recommendation: emit a per-call cost-estimate BEFORE the API call
> based on prompt-token count + a worst-case output budget; treat the
> estimate as authoritative for the cap; reconcile with metadata
> post-hoc. Worth verifying against the actual cliff_test.py cost-
> accounting code path before locking in. **Genuine new attack.**

---

## 3. Findings they got correct but underweighted

- **ToT failure rollup (`tot.py:74-89`)**: Correct, but the reviewer framed it as an "analyst workflow" issue rather than a robustness failure that hides model-specific quota exhaustion.

  > **Author note (FAIR REFRAMING):** Gemini's framing tilts the finding toward critical. Opus had it at medium. The synthesis can hold both framings.

- **Bare excepts / Broad retries**: Correct, but these are 1-hour "hygiene" fixes, not the structural "kill questions" the reviewer claimed they were.

  > **Author note (GEMINI MISREADS OPUS):** Opus called these low/medium with compounding effects on the cliff-test path (a bug masquerading as an API error gets paired-discarded silently). He did NOT call them structural kills. Gemini's correction is itself a misreading.

---

## 4. Verdict

**Motivated.** The report prioritizes academic "gotchas" and reductionist logic to satisfy the adversarial mandate, ultimately failing to distinguish between Phase 0.7 pilot-tuning and the project's foundational architectural claims.

> **Author note (VERDICT UNSUPPORTED):** "Motivated" implies Opus shaped
> findings to fit a predetermined conclusion. Gemini's evidence: Opus
> "prioritizes academic gotchas and reductionist logic." But Opus's
> review is heavy on:
> - Mechanical code citations (line numbers, exact code paths) — not
>   academic.
> - Empirical falsifiers per finding (Pearson correlation script, power
>   analysis math, ablation experiments) — anti-academic, pro-test.
> - Citations to specific ADR sections, not abstractions.
>
> A more honest verdict from Gemini's actual content would be "narrow
> on coverage but largely correct" or "thorough but academically
> framed." Calling it "Motivated" without showing motivated-reasoning
> patterns is itself motivated. Synthesis should ignore this verdict
> and grade Opus's review on its merits.
