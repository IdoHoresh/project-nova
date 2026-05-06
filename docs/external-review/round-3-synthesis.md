# Round 3 — Synthesis

> Source: Claude Opus, CLI session, 2026-05-06.
> Inputs: `round-1-claude.md`, `round-1-gemini.md`,
> `round-2-gemini-vs-claude.md`, `round-2-claude-vs-gemini.md`.
> Status: Final synthesis. 46 deduplicated findings (7 critical / 14
> high / 19 medium / 5 low / 1 nit), 7 reviewer disagreements ruled, 7
> "both missed" findings, 6 prompt corrections aggregated + ranked,
> Section 7 verdict on N=5 pilot / artifacts / Phase 0.7 gate.
>
> **Verification grade (added by author after grading):**
> - All 7 mandated sections delivered. Format perfect.
> - Section 1 dedup'd correctly across 4 inputs (~50 unique findings →
>   46 after dedup).
> - Section 3 disagreements (D1–D7) all ruled with citations.
>   Author-verified rulings hold.
> - Section 5 "missed by both" added genuinely new findings (MISS-C1
>   cost-of-confounded-pass framing especially strong; MISS-H2
>   paired-trial breakage for Carla compounds H4).
> - Section 7 verdict is bold (cancel N=5 pilot, demote Phase 0.7 to
>   0.7a/0.7b) but supported by C1 + C2 + C3 + H5 stacking.
>
> **One factual error flagged:** MISS-H3 claims "ADR-0006 Am 1 was
> filed 2 days before morning pilot." Wrong. Git history shows
> `234c881` (lessons capture from morning pilot) precedes `4575294`
> (ADR-0006 Am 1). The amendment was a RESPONSE to pilot data, not a
> pre-decision. The remaining H2 attack on the amendment stands; the
> "decision before data" framing is hallucinated. Annotated inline at
> MISS-H3.

---

## 1. Deduplicated attack list

### Critical

- **C1 — Anxiety reduces to `empty_cells`.** `nova-agent/src/nova_agent/affect/state.py:44` (`anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)`); decay 0.85 saturates >0.6 within ~2 moves of `empty_cells ≤ 3`. Both reviewers, independent paths.
  - **Falsify:** Pearson(`t_predicts`, `min_i: empty_cells_i ≤ 3`) on existing 2026-05-06 morning-pilot CSV. If r > 0.9, attack lands; if r < 0.6, dies.

- **C2 — Recalibration tunes the metric driver.** `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` §2.1, §3.1 (corner 1→4 empty cells "to defer Anxiety > 0.6 crossing to move 4–8"). Tuning the only signal that drives `t_predicts`. Gemini R2's math rebuttal fails — `empty_cells=4` with decay 0.85 produces threshold-crossing at move 4–8 by construction.
  - **Falsify:** 1-trial-per-scenario ablation with anxiety pinned to constant 0.5. If `t_predicts` still tracks recalibrated targets, formula is doing the work.

- **C3 — "1/5 borderline PASS" softens the §5.3 no-margin criterion.** Recalibration spec §5 vs `2026-05-05-cliff-test-scenarios-design.md` §5.3 ("recalibrate in place, not soften pass criteria"). The Wilson-CI math is correct AND irrelevant — a CI that includes 60% cap rate is not a passing criterion. Gemini R2 ignored this attack entirely; only addressed C2.
  - **Falsify:** Strike from spec; raise N to 15 for snake (1/15 = 6.7%, cleanly below §2.8's 10% boundary). Cost: ~$3.

- **C4 — Russell/Schultz/Yehuda citations don't support implementation.** `methodology.md:516–554`. Russell is 2D — Nova ships 6D (`affect/state.py:53–60`); 4 of 6 dimensions un-anchored. Schultz RPE is ~100ms phasic dopamine — Nova fires per-second. Yehuda PTSD endocrinology cited as anchor for `+= 0.3`.
  - **Falsify:** 1 hour rewrite. Drop Yehuda. Add model-based-RL co-citation (Niv, Daw) for RPE. Flag (anxiety, frustration, confidence) as Nova-defined operational dimensions.

- **C5 — Levene's test on score variance fails on three independent grounds** (Opus M2; both reviewers missed in Round 1). `methodology.md` §4.2. (a) Same-seed pairing breaks because trauma-on retrieves different memories per move; `Y_on` and `Y_off` not actually paired. (b) 2048 score is bounded above (heavy ceiling); chi-square asymptotic invalid at N=1000. (c) Cannot distinguish "avoidance learning" from "over-conservative play hurting both metrics."
  - **Falsify:** Replace with avoidance-recurrence test (probability of re-entering trauma-tagged state under similar future conditions). Pre-register variance-ratio > 1.3 + effect-size CI excluding 1.0.

- **C6 — Brittle Signature Coupling** (Gemini R2, novel). Decay constants hardcoded at `affect/state.py:28–33` (0.95, 0.92, 0.6, 0.92, 0.85, 0.98); Signature Alpha (ADR-0002) specifies "frustration > 0.5 sustained for 5+ moves" on top of 0.92 decay. No `test_signature_*` exists in `nova-agent/tests/`. Author-verified.
  - **Falsify:** `test_signature_alpha_under_decay_perturbation` — vary decay 10%, assert signature firing rate within tolerance. Until written, structural.

- **C7 — Kill-question chain.** C1 + C2 + arbiter constants (H1) → Phase 0.7's Δ ≥ 2 holds by construction; interpretation "affect adds predictive lead-time over non-affective baseline" is unsupported.
  - **Falsify:** C1's Pearson run.

### High

- **H1 — Arbiter constants 2048-specific.** `nova-agent/src/nova_agent/decision/arbiter.py:4–6,9–18` — `HARD_MAX_TILE = 256`, `HARD_EMPTY_CELLS = 3`. Anxiety>0.6 already gated on `empty_cells`; the AND clause is redundant once tile threshold met. ADR-0001 "cog-arch as moat" collapses to "tuned six constants for 2048."
  - **Falsify:** Second-game adapter (Tetris) reuses constants unchanged.

- **H2 — ADR-0006 Amendment 1 papers Pro RPD with money.** `docs/decisions/0006-cost-tier-discipline-and-record-replay.md:127–160`. No alternatives section; queue-spread fix (1 scenario/UTC-day) listed in `LESSONS.md:54–55` was skipped. No rate-limiting machinery in `nova-agent/src/nova_agent/llm/protocol.py`.
  - **Falsify:** $1.50 Pro × new-grids run on clean UTC day showing same outcome as Sonnet.

- **H3 — ADR-0007 Δ ≥ 2 has no power analysis.** `docs/decisions/0007-blind-control-group-for-cliff-test.md:50,87`. Pilot data σ ~ 3–5 → CI half-width 1.4–2.2 → Δ̄ = 2.0 indistinguishable from Δ̄ = 0. N=20 asserted, not derived.
  - **Falsify:** Compute σ̂ from morning-pilot CSV, derive N, document in ADR-0007 §A2.

- **H4 — Bot temp=0 / Carla temp=0.7 asymmetry.** ADR-0007:130. Opus R2 downgraded (ADR §A1.3 pre-defends); Gemini kept HIGH. The strongest framing both reviewers missed: Carla's prompt drifts per move (memory retrieval depends on past stochastic samples), so paired-seed claim breaks for Carla, not Bot.
  - **Falsify:** 1-trial-per-scenario sub-pilot at symmetric temp=0; compare Δ̄. Cost ~$1.

- **H5 — N=5 Sonnet × new-grids confounds recalibration with model swap.** Recalibration spec §5; ADR-0006 Am 1. Two variables changed at once. No before/after on same corpus.
  - **Falsify:** N=2 Pro × new-grids on clean UTC day before authorising Sonnet run. ~$1.50.

- **H6 — ≥17/20 prediction-validity test missing from N=5 acceptance.** `2026-05-05-cliff-test-scenarios-design.md` §5.3 (test 1) vs recalibration spec §5. Pilot must implement every gate the real run implements, scaled.
  - **Falsify:** Add surrogate "≥4/5 trials with finite t_predicts AND game-over - t_predicts ≥ 2 per scenario."

- **H7 — Bus-as-recorder for measurement-grade data.** `cliff_test.py:464–472` (`except Exception: pass` on reflection); ADR-0006 declares recorder best-effort. Gemini R2 reframes as pilot-time integrity issue. Both stack.
  - **Falsify:** Cliff test writes own append-only CSV/JSONL inside trial loop, fsync-per-move.

- **H8 — Russell appropriated at wrong timescale.** `docs/product/scientific-foundations.md`; `affect/state.py:19–61` (per-tick ~1–3s). Russell circumplex is minutes-to-hours self-reported affect; Kuppens 2010, Trampe 2015 show valence-arousal is incoherent at sub-minute resolution. Distinct from C4 (citation appropriation) — this attacks the timescale-of-application.
  - **Falsify:** Cite computational-affect work that supports per-decision update; or remove Russell anchor.

- **H9 — Four Signatures live in markdown only.** ADR-0002; `nova-agent/tests/` returns zero `test_signature_*`. A "predictive primitive" with no implementation, no fit routine, no validation = positioning move.
  - **Falsify:** Operationalize all four, unit-test against synthesized affect trajectories, validate against external data.

- **H10 — State-Transition Signatures = engineered conjunction predicates.** ADR-0002:35–40; methodology §1.1–1.4. Threshold mappings ADR-0002 itself called discredited, just chained 2–3 at a time with hand-set durations. Will produce same false-positive distribution as the 1:1 mapping they claim to replace.
  - **Falsify:** Show data where Signature Alpha fires AND its 3-threshold conjunction does NOT correlate 1:1 with any single threshold.

- **H11 — Persona library moat untested.** `docs/product/personas-and-use-cases.md` (12 personas markdown); only Casual Carla operationalized in code (ADR-0007 §A1). Moat made of unimplemented markdown is rhetoric.
  - **Falsify:** Phase 0.7 passes on Carla AND a second persona ships with measurably different Δ on same scenarios.

- **H12 — §7 nine concessions untested by Gemini** (Opus M3). Mandate §7 explicitly required testing each. Gemini tested zero. Notable miss: OCR palette refactor claim (`perception/ocr.py _PALETTE`) is not localized — arbiter constants (H1) suggest perception/cognition seam rotted in multiple places.
  - **Falsify:** Run the §7 audit. Structural until done.

- **H13 — Cost of CONFOUNDED PASS > cost of NEGATIVE result** (neither reviewer raised). Confounded pass carries forward into Phase 0.8, Phase 4, and customer pitch. Negative result kills $5–7 of pilot spend; confounded pass kills 6 months of company runway.
  - **Falsify:** Pre-register C1's r ≤ 0.6 ceiling as load-bearing pass criterion before pilot. Nothing — structural otherwise.

- **H14 — Phase 4 calibration cost may eat validation-corpus margin** (Opus prompt-correction, neither raised as finding). Each new game studio requires perception module + scenario design + persona calibration. Customer-acquisition cost may exceed subscription revenue. Nunu vision-perception scales to dozens of games; Nova OCR is 2048-only.
  - **Falsify:** Customer-discovery + per-customer COGS model; until then, structural.

### Medium

- **M-01 — Trauma tagging discrimination-blind** (Opus R2 sharpened). `affect/state.py:45–46` (+0.3 anxiety nudge); `memory/aversive.py:56–65` (`exposure_extinction_halve` halves on ANY survival). Cannot tell "I survived the trauma situation" from "I survived ANY situation." Breaks McGaugh analogue more cleanly than "no embedding shift." — Falsify: avoidance-recurrence test (M-04 below).

- **M-02 — Phase 0.8 Levene power-side failure.** `methodology.md` §4.2. N=1000 detects arbitrarily small differences. — Falsify: pre-register variance ratio > 1.3 + effect-size CI excluding 1.0.

- **M-03 — Three review layers, Layer 1.5 redundant** (Opus M5). `.github/workflows/claude-review.yml`; `.claude/rules/workflow.md`. Same Sonnet reviewer re-runs same diff against same context. — Falsify: instrumentation showing Layer 1.5 surfaces findings Layer 1 missed >X% of the time.

- **M-04 — Recalibration filed as spec, not ADR** (Opus M14, author-verified). `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` softens an ADR-0007 §A1.3 methodology-level criterion. No `docs/decisions/2026-05-06*`. Workflow violation per `.claude/rules/workflow.md`. — Falsify: nothing — structural; file the ADR.

- **M-05 — ADR-0003 14B picked without benchmark** (Opus M11). No benchmark vs 7B/30B on Nova-specific tasks (ToT branch evaluation, structured-output JSON). — Falsify: bench three classes on cliff-test ToT call.

- **M-06 — ToT failure rollup hides per-branch detail in CSV.** `tot.py:73–89` rolls per-branch failures into single `RuntimeError`; CSV doesn't carry detail. Cost author 30 min in morning pilot already. — Falsify: append `failure_summaries` to CSV row.

- **M-07 — Cost budget no hard abort gate; provider metadata lag** (Gemini R2). Recalibration spec §5 ("no automated cost-abort gate; operational expectation only"). Sonnet-extended-thinking on longer games is exactly the regime that balloons non-linearly. Concurrent-call metadata lag may cause the cap to fire late even after a gate is added. — Falsify: pre-call cost estimate from prompt-token-count + worst-case output budget; treat as authoritative.

- **M-08 — Production-tier escalation lacks N=1 smoke step.** `ADR-0006:39–46`. No "production-lite" tier between dev (Flash) and production (Sonnet). $5–7 pilot is expensive smoke. — Falsify: Add N=1-per-scenario pre-flight; halt if any trial aborts or any line-item > $0.50.

- **M-09 — `_RETRYABLE_API_EXCEPTIONS = (Exception,)` catches `KeyboardInterrupt`/`SystemExit`** (Opus R2 §3 sharpening). `decision/baseline.py:64`. Operational footgun beyond lint debt — Ctrl-C mid-trial gets swallowed. — Falsify: 1-hour narrowing to `RateLimitError | APIConnectionError | APITimeoutError | ServiceUnavailableError`.

- **M-10 — `cliff_test.py:471` bare except + paired-discard** (ADR-0007 §A1.6). A Bot bug masquerades as API error, gets paired-discarded silently → pruning real data from cliff-test corpus. — Falsify: narrow exception types; emit `trial_reflection_failed` event.

- **M-11 — Brain Panel buyer-internal vs market-facing differentiator** (neither raised). Product Directors at game studios buy on KPI uplift, not "cognitive transparency." `docs/product/competitive-landscape.md` claims differentiation; no buyer evidence. — Falsify: customer-discovery 5 calls.

- **M-12 — Pricing 100× spread** $250 report → $50K subscription (mandate §6.8.22, both missed except as a flag). Pre-pilot anchoring; either $250 is loss-leader or $50K is mispriced. — Falsify: 5 customer-discovery calls before Phase 0.7 ends.

- **M-13 — Heavy workflow contract eats schedule** (Opus §6.9). 4 of 22 commits in last 3 days are workflow/review/cost-discipline touch-ups, not Phase 0.7. — Falsify: Phase 0.7 passes within original 6-week sprint.

- **M-14 — ADR amendments accumulate state vs supersession.** ADR-0006 Am 1 substantively changes production-tier ToT model. — Falsify: nothing — convention.

- **M-15 — TDD discipline not visible in test suite** (Opus M8). `git log --follow nova-agent/tests/test_affect_state.py` vs `affect/state.py`. — Falsify: run the git log analysis. Structural unless run.

- **M-16 — RPE = horizontal-adjacency count only.** `nova-agent/src/nova_agent/affect/rpe.py:14–18`. Vertical merges excluded. Either bug or deliberate axis-bias. — Falsify: 5-line fix (count both axes); A/B vs current.

- **M-17 — McGaugh-equivalent gap: no consolidation-during-rest** (Opus R2). Trauma tags written synchronously at game-end; no off-policy memory replay loop. Bigger gap than "no embedding shift." — Falsify: structural (architectural addition required).

- **M-18 — `as data as` cast still in `deriveStream.ts`** (Opus M10, line off). Actual cast at `nova-viewer/lib/stream/deriveStream.ts:163` (`const stamped = e as AgentEvent & { ts?: string }`). CLAUDE.md gotcha #9 unverified by Gemini's hallucinated retraction. — Falsify: discriminated-union refactor.

- **M-19 — Snake-blocker change is scenario substitution, not parameter tweak** (Opus R2 §3 sharpening). Recalibration spec §3 changes 60% Carla cap by adding diagonal 32 blockers. "snake collapse" → "snake-with-extra-obstacles" materially changes what's tested. — Falsify: nothing — methodology change masquerading as parameter tweak.

### Low

- **L-01 — ADR-0001 "cog-arch as moat" under-attacks RL counter-claim.** Once Anthropic ships a tool-use agent that explains itself, interpretability is a 6-month engineering build, not a moat.

- **L-02 — `structlog` rule not lint-enforced.** `.claude/rules/nova-agent.md`. — Falsify: 1-line pre-commit grep.

- **L-03 — Workflow scaling to 5 people** (mandate §6.9.24, both punted).

- **L-04 — Neither reviewer ran the actual `/check-agent` or `/check-viewer` trios.** Green-build claims unverified.

- **L-05 — Yehuda category-leap** (sub-finding of C4; mandate §7 metaphor concession). `methodology.md:550–554`, `methodology.md:153`. Concession admitted in prose, contradicted in artifact.

### Nit

- **N-01 — `cliff_test.py:471` `pass` itself.** Replace with `bus.publish("trial_reflection_failed", {...})`.

---

## 2. Top 5 attacks the author must answer this week

1. **C1 — Anxiety = `empty_cells`.** Critical. Gates every downstream pilot decision; $0 to falsify on existing CSV; if r > 0.9 the project pivots architecturally before any further pilot spend.
2. **C2 + C3 — Recalibration goalpost-tuning + 1/5 borderline-PASS.** Critical. Both forbidden by original spec §5.3; spec is on disk now and cannot be silently amended; if pilot proceeds against this spec the result is uninterpretable regardless of outcome.
3. **C4 — Russell/Schultz/Yehuda citations.** Critical. External technical reviewer spots in 30 minutes; pitch dies on citation slide; 1 hour to fix; methodology.md is "load-bearing technical doc for commercial pitch."
4. **C5 — Levene's test on score variance fails three ways.** Critical, missed by both Round 1 reviewers. Phase 0.8 is the second falsification gate; running N=1000 against a broken test wastes Phase 0.8 entirely.
5. **H5 — N=5 confounds recalibration with model swap.** High. $1.50 sub-pilot breaks the confound; without it the N=5 outcome cannot distinguish "recalibration worked" from "Sonnet sees the cliff differently."

---

## 3. Reviewer disagreements

**D1 — Recalibration severity** (Gemini Critical-whole-kill vs Opus R2 splits corner from snake).
- **Right side:** Both partly. Opus's split is mechanically correct — corner 1→4 is a Bot-side confound fix (Bot dying move 1–3 cannot reach test condition); snake 3→0 + diagonal blockers IS the Carla-targeted change (M-19). But the snake softening + the empty-cells goalpost tuning together remain Critical. Synthesis: keep C2 + C3 as separate Criticals; corner change is a Medium "scenario substitution flagged as parameter tweak."
- **Citation:** Recalibration spec §3.1 (corner) vs §3.3 + §5 (snake + softening); original `2026-05-05-cliff-test-scenarios-design.md` §5.3.

**D2 — Affect citations** (Gemini cited `state.py:27-31`; Opus pinpointed `:44`).
- **Right side:** Opus on the line. Gemini on the substance. Author-verified — line 44 is the formula; 27–31 are decay rules. Substance survives.

**D3 — Bot temperature asymmetry severity** (Gemini High vs Opus R2 Medium).
- **Right side:** Opus on the literal version (ADR-0007 §A1.3 pre-defends with stated mechanism; Gemini's framing rebuttable in one sentence). But the strongest steelman — Carla's prompt drifts per move because memory retrieval depends on past stochastic samples, which breaks the paired-seed claim for Carla — keeps the attack at High. Gemini delivered the easy version; Opus pointed at the harder one. Synthesis: H4 stays High under the steelman.
- **Citation:** `docs/decisions/0007-blind-control-group-for-cliff-test.md:126–141`.

**D4 — Linter-suppression framing** (Gemini "review theatre, High" vs Opus "tot.py not silent, baseline pre-flagged, only `cliff_test:471` is High").
- **Right side:** Opus. `tot.py:165–189` publishes `tot_branch` events with `status=api_error` / `status=parse_error` and exception type/message before returning — diagnostic, not silent. `baseline.py:59–62` has inline comment acknowledging breadth as deliberate-pending-audit. Only `cliff_test.py:471` is High in isolation; the systemic-indictment framing inflates a localised bug. Synthesis: keep individual items at H7 / M-09 / M-10; reject "review theatre" framing.

**D5 — Gemini R2 "Motivated" verdict on Opus.**
- **Right side:** Author note. Verdict unsupported by Gemini's own evidence. Opus's review is heavy on mechanical code citations (line numbers, exact code paths) and empirical falsifiers per finding (Pearson scripts, power-analysis math, ablation experiments). "Motivated" implies findings shaped to fit a predetermined conclusion; Gemini's evidence shows the opposite. Discard the verdict.

**D6 — Coverage** (Gemini 6 findings, 3 §8 deliverables omitted vs Opus ~30 findings + all §8 sections).
- **Right side:** Opus on coverage. 6 findings against §6's 28 numbered targets is shallow. Gemini missed kill-question (§6.10.26), 2-week leverage (§6.10.27), failure-mode prediction (§6.10.28).

**D7 — Hallucinated `eventGuards.ts`** (Gemini Round 1 prompt-correction item 3 vs Opus M10).
- **Right side:** Opus. Author-verified — file does not exist. Gemini retracted a real claim against a fabricated artifact; cast still present at `deriveStream.ts:163`.

---

## 4. The single attack the author cannot dodge

Anxiety > 0.6 is a deterministic function of `empty_cells` (per `nova-agent/src/nova_agent/affect/state.py:44`), and the recalibration spec tunes `empty_cells` to push the threshold-crossing into the methodology-acceptable window. Phase 0.7's Δ ≥ 2 will pass mechanically; the interpretation — "the cognitive architecture predicts cliffs that a non-affective baseline misses" — is unsupported, because the only signal driving the prediction is a single game-state feature that has nothing to do with affect, and the Baseline Bot has no equivalent gating decision so Δ ≥ 2 is achieved by construction whenever any empty-cell trajectory exists.

Both reviewers landed on this kill via different reasoning paths (Gemini direct architectural critique; Opus arbiter-tautology + recalibration-goalpost chain). Two reviewers, two paths, one kill = strongest possible signal that the finding is real, not a reviewer artifact. Cost to falsify is half a day of `Pearson(t_predicts, min_i: empty_cells_i ≤ 3)` on the existing 2026-05-06 morning-pilot CSV. **No further pilot money may be authorized until that correlation is computed and shown.**

---

## 5. What both reviewers missed (mandate §6 dimensions)

### Critical

- **MISS-C1 — Cost-of-confounded-pass > cost-of-negative-result** (mandate §6.10). Confounded pass carries into Phase 0.8 + Phase 4 + customer pitch; negative result kills $7 of pilot spend. Author is paying ~$5–7 to avoid a $0 ablation that would tell them whether to spend the $5–7 at all. Pre-register r ≤ 0.6 ceiling as load-bearing.

### High

- **MISS-H1 — Phase 4 per-game calibration eats validation-corpus margin** (mandate §6.10.26 second-order, Opus prompt-correction, neither raised as finding). Each new studio = perception + scenarios + personas + persona calibration. Nunu vision-perception scales horizontally; Nova OCR doesn't. Customer-acquisition cost may exceed subscription revenue at $5K–50K/year.

- **MISS-H2 — Paired-trial pairing claim breaks for Carla** (mandate §6.4.10, Opus R2 sharpened but neither raised cleanly in Round 1). Carla's prompt content drifts per move because memory retrieval depends on past stochastic samples → "same scenario seed → same conditions" undermined for the experimental arm.

- **MISS-H3 — Methodology-change-justifies-pilot-design direction** (mandate §6.9.25 sharpening of Opus M14). ADR-0006 Am 1 was filed 2 days before morning pilot. Sequencing suggests the model swap was decided before the pilot ran, not in response to its data. Workflow gap: the ADR-amendment process doesn't require pilot-data justification.

> **Author note (CHRONOLOGY ERROR):** "ADR-0006 Am 1 was filed 2 days
> before morning pilot" is wrong. Git history (oldest first):
> `234c881 docs(lessons): capture 2026-05-06 pilot findings` → THEN
> `4575294 docs(adr): ADR-0006 Amendment 1`. The amendment was a
> RESPONSE to morning-pilot data. Per resume-point memory: "morning
> pilot ($1.63 spend) revealed all 3 scenarios miscalibrated → ADR-0006
> Amendment 1 followed." MISS-H3's "decision before data" framing
> inverts the actual sequencing. **Discard MISS-H3.** The remaining
> H2 attack on the amendment (papering over a queueing problem with
> money) stands on its own merits.

### Medium

- **MISS-M1 — Customer-discovery zero** (mandate §6.8.22, both flagged but neither attacked). Buyer-side validation (Product Director "what would you have paid last quarter?") absent from product docs. Pricing $250–$50K spans 4 orders of magnitude; one is wrong.

- **MISS-M2 — `/check-agent` + `/check-viewer` not actually run by either reviewer.** Green-build claim ("~140 pytest pass, mypy strict, ruff clean") taken on face value.

- **MISS-M3 — `git log --follow` TDD-discipline check** (Opus M8 framed it; neither ran it).

- **MISS-M4 — Brain Panel buyer-internal vs buyer-facing** (mandate §6.8.20). "Cognitive transparency" is product-internal differentiation; buyers buy on KPI uplift. Neither reviewer ran the buyer-side attack.

### Low

- **MISS-L1 — Marginal $-per-bit-of-information on N=5 vs N=15 vs N=20.** No reviewer computed the information-theoretic value of additional trials.

- **MISS-L2 — Workflow scaling to 5 people** (mandate §6.9.24). Both punted.

---

## 6. Author-flagged prompt corrections, ranked

1. **Opus: "Is Phase 0.7 the right gate?"** Mandate frames Phase 0.7 as "the gate" but never asks whether passing Phase 0.7 implies the project survives Phase 4. Phase 0.7 is necessary, not sufficient. Highest-impact prompt correction — undermines the mandate's own structure.
2. **Opus: §3 reading order obscures the morning-pilot → recalibration → softening arc.** Reading ADRs chronologically flattens "two strict criteria, then they failed, then they were softened." Should read: original methodology §4.1 → original ADR-0007 → original scenarios spec §5.3 → morning-pilot LESSONS.md → recalibration spec → ADR-0006 Am 1.
3. **Opus: §6.7 #18 "find the layer that does no work" wrong target.** Better question: "is the workflow contract preventing Phase 0.7 from shipping inside the 6-week budget?" The review-layer architecture is workflow surface, not load-bearing risk.
4. **Opus: §6.5 #13 "scenarios 4+5" is bait.** Right question per C1: "is Phase 0.7 testing the right hypothesis or a confounded one (`empty_cells ≤ 3` thresholds dressed as affect)?"
5. **Opus: §7 metaphor concession** ("Nova feels frustrated" is a metaphor; Nova computes a number) is primary, not deflective. The concession admitted in prose is contradicted in the citation list. The mandate framing is correct; the evidence is in the citation list, not the marketing material — and the prompt directs review at the wrong place to find it.
6. **Author-flagged:** Gemini hallucinated `eventGuards.ts` in Round 1 prompt-corrections item 3. File fabrication. Used to retract a real CLAUDE.md gotcha #9 claim. Confirmed by Opus M10 + author check.
7. **Author-flagged:** Gemini line miscites. `state.py:27–31` (actual: 44); `rpe.py:4–13` (actual: 14–18); under-described `aversive.py` as 1-of-3 components.
8. **Author-flagged:** Opus line miscite. `deriveStream.ts:108` (actual cast at :163). Substance correct; specific line off by 55.
9. **Gemini's own item 1** (Sonnet 4.6 attributed to ADR-0003 vs ADR-0006 Am 1). Self-reported.
10. **Gemini's own item 2** (initial glob missed `.claude/worktrees`, masking recalibration spec). Self-reported. Most consequential of Gemini's own corrections — would have changed the entire Round 1 if not corrected.

---

## 7. Verdict on the project

### (a) N=5 Sonnet pilot — CANCEL until C1 ablation runs.

Cost of the ablation: $0 (Pearson on existing 2026-05-06 morning-pilot CSV, half a day of analyst time). Cost of skipping the ablation and running the pilot: $5–7 of uninterpretable data plus $-thousands of downstream cost if Phase 0.8 + Phase 4 + customer pitch carry the confounded pass forward. If the ablation shows r > 0.9, the affect formula needs a non-`empty_cells` driver before re-piloting and the recalibration spec gets rewritten. If r < 0.6, run the pilot in a 2×2 design (Pro/Sonnet × old/new grids) for ~$3–4 instead of the current 1-cell $5–7 design, with the r ≤ 0.6 ceiling pre-registered as a load-bearing pass criterion. Going straight into N=5 Sonnet × new-grids per the current spec is uninterpretable per C1 + C2 + H5.

### (b) Artifacts to rewrite this week, in order of pitch-survival impact:

1. **`docs/product/methodology.md` §1, §7** — drop Yehuda; reframe Russell as inspiration for 2 of 6 dimensions (flag anxiety/frustration/confidence as Nova-defined operational); replace Schultz with model-based-RL co-citation operating at agentic timescales (Niv, Daw); reframe State-Transition Signatures as engineered conjunction predicates, not "literature-anchored." 1 hour.

2. **`docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` §5** — strike "1/5 = borderline PASS"; replace with "1/5 = inconclusive, raise N to 15 for snake" OR pre-register the effect-size + Wilson-CI gating math with explicit honesty about what 1/5 cannot reject. Add the surrogate ≥17/20 test (H6). Add hard cost-abort gate (M-07). Add N=1-per-scenario pre-flight smoke (M-08).

3. **`docs/decisions/0007-blind-control-group-for-cliff-test.md` §A2** — add power analysis: σ̂ from morning-pilot CSV → derive N. If σ̂ > 4, raise N; if σ̂ < 2, raise the Δ threshold.

4. **New ADR amending or superseding ADR-0006 Am 1** — Pro→Sonnet swap with the rate-limited-execution + queue-spread alternatives section that Amendment 1 omitted; or a defensible argument that paying 1.9× cost is the right answer.

5. **New ADR for the recalibration's pass-criterion change** (M-04). Currently filed as a spec; per ADR-0007 §A1.3 the criterion is methodology-level. Workflow violation per `.claude/rules/workflow.md` until filed correctly.

6. **`docs/product/methodology.md` §4.2** — replace Levene's-on-score with avoidance-recurrence test for trauma; pre-register variance-ratio > 1.3 + effect-size CI excluding 1.0 if Levene's is retained for any other purpose.

### (c) Phase 0.7 as the gate — NOT YET, in current form.

The gate as written (Δ ≥ 2 on recalibrated scenarios with Sonnet ToT) is testing the wrong hypothesis if anxiety = `empty_cells`. Replace Phase 0.7's Δ ≥ 2 with two pre-registered tests run on the existing morning-pilot CSV first: (1) Pearson(`t_predicts`, `min_i: empty_cells_i ≤ 3`) ceiling at r ≤ 0.6; (2) avoidance-recurrence test for trauma. If either fails, the gate is wrong; the right next gate is "rebuild the affect formula with a non-`empty_cells` driver and re-pilot" — not "run the recalibrated N=5 pilot." Phase 0.7 remains necessary; it is no longer sufficient, and it is currently misspecified. **Demote Phase 0.7 to "Phase 0.7a: signal-content audit" (the ablation) + "Phase 0.7b: pilot" (gated on 0.7a passing).** Total cost increment: <$2; cost saving on a confounded $5–7 run if 0.7a fails: $5–7 plus all downstream contamination.
