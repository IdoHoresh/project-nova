# ADR-0005: defer-v1-demo-until-phase-0.7

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** ihoresh07@gmail.com (solo founder)

---

## Context

The 30-day validation sprint as originally written (see `product-roadmap.md` Week 0) gates on shipping a v1.0.0 demo recording in Week 0 — a ≤4-minute screen recording that narrates the cognitive architecture's *Why* (decision reasoning, ToT branch deliberation, post-game reflection) over a real 2048 playthrough. Demo Day = Day 5 of Week 0 (originally 2026-05-08). v1.0.0 git tag was tied to the demo recording.

Several forces have changed since that plan was written:

1. **Pivot lock-in.** The product positioning (ADR-0004) is now firmly the **Cognitive Audit & Prediction Platform** sold to Product Directors / UA Managers, counter-positioned against nunu.ai (vision-based QA Replacement sold to QA Directors). The 2048-only cognitive-architecture demo records the *cognitive architecture demo*, not the *methodology proof* the product story rests on.
2. **Phase 0.7 is the load-bearing claim.** Per ADR-0001 (cognitive architecture as moat) and ADR-0002 (state-transition signatures), every Nova claim about predicting human behavior depends on the cliff test passing — affect peaks must precede the documented failure point by ≥ 2 moves in > 80% of trials. Without this, Nova narrates outcomes; with it, Nova predicts them. The product story works only post-cliff-test.
3. **`docs/product/methodology.md`'s own rule.** "Don't sell before Phase 0.7 passes" is a standing constraint. A v1.0.0 demo posted to LinkedIn before Phase 0.7 is, in practice, a sale — it positions the architecture as proven before the falsification criterion has run.
4. **Scope creep risk.** Phase 1+ adds the multi-game adapter, persona portfolio, and KPI report layer. Recording a 2048-only demo now and re-recording when the platform layer ships is double work; better to record once after the platform layer exists.
5. **Forcing-function risk.** The original plan's strongest argument was that demos surface UX gaps. Solo dev + research-driven build risks "everything working" becoming a moving target. Without a hard new gate, demo deferral is a trap.

The decision is: defer the v1.0.0 demo recording, OR keep it on Day 5 of Week 0 and absorb the costs above.

## Decision

**Defer the v1.0.0 demo recording. Set Phase 0.7 cliff test passing as the new demo gate.**

Specifically:

1. **Drop demo recording from Week 0.** Days 3–7 originally allocated to demo prep + recording are reallocated to direct Phase 0.7 work (build `Game2048Sim` early, start cliff-test runs).
2. **Park the v1.0.0 git tag.** Re-tag when demo records.
3. **New demo gate** (binary, no judgment call): the Phase 0.7 cliff test passes — affect peak precedes documented failure point by ≥ 2 moves in > 80% of trials, on at least 3 of the 3-5 documented hard 2048 scenarios.
4. **Demo content shifts.** The demo recorded post-Phase-0.7 narrates not just the cognitive architecture *Why* but also the *cliff-test result* — affect curves on a real hard scenario, with the failure-precede-prediction relationship visible. This is a stronger artifact than the cognitive-architecture-only demo.
5. **Until Phase 0.7 passes:** no LinkedIn post, no pitch conversations, no "v1.0.0" anything. The architecture is interesting but unproven. Talk about it privately with research peers if the question comes up; do not lead.

This decision applies until Phase 0.7 passes (proceed-to-demo) OR fails (re-derive the RPE weights branch begins per the roadmap's Week 1 fail path; no demo until the rework completes and a follow-up cliff test passes).

## Alternatives considered

- **Keep the original Day-5 demo, ship a v1.0.0 demo without Phase 0.7.** Rejected — directly violates the methodology's "Don't sell before Phase 0.7 passes" rule and risks anchoring external opinion on the unproven architecture story. If the cliff test later fails, retroactively walking back the demo claims is more expensive than not recording.

- **Record a 2048-only "preview" demo now, plan a v2.0.0 platform demo later.** Rejected — two demos = double the production work for solo dev (script, OBS setup, dry runs, recording, editing each time), and the 2048-only preview crowds out the platform-shaped demo when it eventually ships. The early demo also competes with itself for attention if the second demo's narrative differs.

- **Defer demo with no new gate ("demo when everything is working").** Rejected — moving target. "Everything working" never converges for solo dev + research agent. Would let demo slip indefinitely, lose the discipline of a milestone, and erode the rest of the roadmap's gating structure.

- **Use Phase 0.8 (trauma ablation) as the demo gate instead.** Rejected — Phase 0.7 is the hard one. Phase 0.8 is the differentiation story (trauma-tagging earns its keep), but Phase 0.7 is the survival test. If Phase 0.7 passes, the demo can record on the cognitive-architecture-plus-cliff-test result; if Phase 0.8 also passes by the time we're done editing, the demo becomes stronger. Gating on Phase 0.8 would needlessly delay the demo when 0.7 is what people actually need to see.

## Consequences

**Positive**

- Demo records the *full story*: cognitive architecture + falsification-test passed. Stronger artifact for LinkedIn and any pitch conversation that follows.
- No risk of having to retract claims in public if the cliff test fails.
- Days 3–7 of Week 0 free up for direct Phase 0.7 work — `Game2048Sim` build can start earlier than the original Week 1 plan, compressing the 30-day timeline by up to 4 days.
- Counter-positioning against nunu.ai gets stronger: the demo can lead with "we predict, we don't replace QA" backed by concrete cliff-test data.

**Negative**

- LinkedIn / portfolio gap. Current build (cognitive architecture + brain panel + emotion + ToT + memory + reflection + trauma tagging + reflection layer) is genuinely impressive on its own. Sitting on it = nobody knows you built it until Phase 0.7 lands. Best-case: 2-3 weeks. Worst-case (cliff test fails, rework branch): 4-6 weeks.
- Loss of the demo's UX-forcing-function. Without the recording deadline, brain-panel polish drift is a real risk. Mitigation: schedule a synthetic "demo dry run" (no recording, just walk-through) at the end of Week 0 to surface UX gaps the same way an actual recording would.
- v1.0.0 tag delays. Anything tooling- or process-wise that anchored on the v1.0.0 milestone (CI gates, release notes scaffolding) needs to anchor on Phase 0.7 instead, or stay un-anchored until then.

**Neutral**

- The demo-recording skill set (script writing, OBS dry runs, narration tone) doesn't depreciate. Whatever was learned planning the original demo carries over to the post-Phase-0.7 demo unchanged.
- Phase 0.7 was always going to ship; this decision just changes its position relative to the demo, not its scope or criteria.

**Reversibility**

- Easily reversible. If circumstances change (a real pitch opportunity arrives, an investor specifically asks for a video, a portfolio deadline appears), this ADR is superseded by a new one and the demo records on whatever timeline is required. No code change, no architecture change, no contract that locks in the deferral.

## References

- ADR-0001 — cognitive architecture as product moat (the moat is unproven without Phase 0.7)
- ADR-0002 — state-transition signatures (the methodology that Phase 0.7 tests)
- ADR-0004 — product positioning (Cognitive Audit & Prediction Platform; demo content must reflect the positioning, not the 2048 architecture in isolation)
- `docs/product/methodology.md` §3 — "Don't sell before Phase 0.7 passes"
- `docs/product/product-roadmap.md` Week 0 (this ADR rewrites that section) and Phase 0.7 (the new demo gate)
- `docs/product/competitive-landscape.md` — nunu.ai counter-positioning (the demo's narrative depends on this)
