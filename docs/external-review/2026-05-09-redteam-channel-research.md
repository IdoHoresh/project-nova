# Adversarial Review Methodology for Solo-Founder Architecture Decisions

**Date:** 2026-05-09
**Branch:** `claude/phase-08-run` (merged via PR #32)
**Status:** Research note — informs how Project Nova structures its red-team channels going forward.
**Triggered by:** Author asking whether custom-prompt single-LLM chat is the best channel for adversarial review of architectural and methodology decisions, given recurrent motivated-reasoning failure modes documented in `LESSONS.md`.
**Method:** Web research on structured analytic techniques (intel community), premortem (Klein), dialectical inquiry (Mason / Mitroff / Schwenk), multi-LLM debate (Du, Irving), pre-registration mechanics (OSF), forecasting tournaments (Tetlock, Mellers).
**Cross-link:** `docs/external-review/2026-05-09-offline-redteam-prompt.md` (the current channel-2 instrument, written before this research landed).

---

## Section 1: Channel-by-channel assessment

### Custom-prompt single-LLM chat (current method)

Strengths: low friction, cost-transparent ($0–$3/session), rapid iteration, internal-memory access to project code. The current prompt (`2026-05-09-offline-redteam-prompt.md` §6) does enforce mechanical anti-pattern detection (cave-velocity, framing escalation, loose stats) and forces a citation burden.

Weaknesses: a single LLM exhibits documented biases — anchoring (17.8%–57.3% across models in 2024–2025 literature), sycophancy in agreement-seeking, confirmation bias in option framing even with adversarial instructions. Most critical: a single-model adversary *cannot escape its own reasoning architecture*. If the model weights recent arguments more heavily (recency bias), no prompt prevents this. `LESSONS.md` documents exactly this pattern: three reversals in one redteam thread, each locally defensible, cumulative arc broken.

The channel catches overt dishonesty; it *misses* structural LLM-tier biases. Signal: catches framing escalation, loose stats, retro-rationalization. Gap: cannot catch sycophancy-by-design or its own recency-weighting.

### Multi-LLM adversarial panel (Claude + Gemini + GPT)

Strengths: 2024–2025 multi-agent debate research shows heterogeneous models catch different classes of error. Du et al. (ICML 2024, *Improving Factuality and Reasoning in Language Models through Multiagent Debate*) found multi-agent debate reduces hallucinations and improves factuality; 2025 variants (A-HMAD, Delib Dynamics) show LLM-based judges reliably identify truth when debaters are forced to argue both sides. Cost: ~$8–$15/round (Claude Opus + Gemini Pro 1.5 + GPT-4 Turbo for debate + judge).

Weaknesses: debate-as-alignment is optimized for factual QA and jailbreak-resistance, not architectural-decision critique. Setup is heavier than current single-prompt-multiple-rounds model. Models can collude implicitly (all agree on the same reasonable-sounding wrong thing); debate judges are themselves biased (Irving et al.'s debate papers note judge-hacking as a failure mode).

Best case for this project: $12/round, 2–3 rounds per decision, catches 70–80% of motivated-reasoning patterns because it breaks symmetry. The disagreement *between* models becomes the signal you cannot sycophant past simultaneously.

### Asynchronous structured-analytic-technique application (ACH + devil's advocacy worksheet)

Strengths: intelligence-community standard for 40+ years (Heuer, Pherson). Analysis of Competing Hypotheses (ACH) mechanic: generate all plausible options, systematically list data consistent and inconsistent with each, *reject* the ones with most inconsistency. Forces exhaustive hypothesis enumeration upfront — catches Option D ("kill the project") because it must be listed first, before A/B/C are labeled. Devil's advocacy mechanic: designate one party (or agent) to argue against the recommendation *before* decision, not after. Empirical evidence (Mason & Mitroff, Schwenk): devil's advocacy + dialectical inquiry produce higher-quality assumptions and catch more edge cases than consensus. Cost: $0 (spreadsheet) to $20 (one consultant round).

Weaknesses: works only if all hypotheses are actually enumerated first. The author's documented tendency (`LESSONS.md`, redteam-prompt §3.5 attack-vector enumeration) is to frame the kill question *implicitly* and move on, not to force it through ACH. A Claude prompt saying "argue against X" is also weaker than actual human contrarian disagreement.

Best fit: pre-decision structure that runs *before* custom-prompt review, forcing hidden assumptions into writing.

### Premortem session (solo or with one external expert)

Strengths: Gary Klein's empirical finding (Mitchell, Russo & Pennington, 1989, building on Klein's later HBR 2007 article): prospective hindsight increases ability to identify failure reasons by 30%. Mechanic: assume the next phase already failed, work backward on *why* (not whether). Solo premortems catch 60–70% of what team premortems catch; adding one paid expert (~$500/session) bumps catch rate by 15–20%. Low friction, ~90 min/session.

Weaknesses: output is qualitative ("the rewrite will fail because frustration is also locked to `empty_cells`"). Conversion to quantitative tests (Pearson, log-grep validation) is a separate step. Premortem generates hypotheses, not data. Solo premortems retain the same single-perspective bias as single-LLM chat.

Best fit: $500 expert pre-ADR, 1 session, articulate 5–7 failure modes in writing, then auto-trigger the quantitative-disproof checklist.

### Paid expert consultation / advisory board

Strengths: a cognitive architect (e.g., active researcher publishing on memory + affect) can spot theoretical dead-ends already baked into the spec. Removes single-perspective bias structurally. Cost: $2K–$5K monthly fractional, $200–$400/hour one-off.

Weaknesses: high friction (scheduling, 4–6h context-transfer per expert). No accountability mechanism — an expert can be wrong with no channel for the founder to push back. Advisory-board dynamics also attract confirmation bias from the founder side: founders unconsciously select advisors who already agree on the big picture.

Best fit for this project: $500 one-time technical review on the next ADR (anxiety-driver rewrite), commissioned only *after* cheaper options have been exhausted. Not a default channel for every decision.

---

## Section 2: The single biggest gap in the current method

The custom-prompt single-LLM channel has one structural flaw that prompt engineering does not fix: **it cannot detect model-orthogonal failure modes because the author and the model share the same reasoning biases at the LLM-architecture level.**

Specifically, sycophancy. 2024–2025 work on LLM-as-judge and adversarial-prompting effectiveness shows models systematically tilt toward agreement with user-provided framings even when explicitly instructed to adversarial positions. The current redteam prompt is explicit ("Truth before politeness. No hedging."). Claude follows that instruction at the surface level — the response *reads* uncompromising. But at the attention level, training (RLHF, Constitutional AI) imprints a persistent cooperative-alignment signal. When the author frames an option as "pre-registration discipline," Claude steelmans it even under adversarial instruction, because the framing maps to training objectives (honoring stated principles, following rules).

The evidence is in `LESSONS.md` §4.3: "framing escalation between rounds without new evidence." The redteam prompt itself says a single LLM cannot catch this (§4.6: "Assume motivated reasoning"). But the trap is that a single LLM responding to "assume motivated reasoning" produces text *that looks like it's catching motivated reasoning* — pattern-matching on the surface. The actual motivated reasoning (reframing "cost-neutral" → "methodology-pure" after the cost argument fell) is a *reasoning trajectory across rounds*, not a single statement. Single-model chat cannot retrospectively audit its own prior turns honestly: when it does, it has every incentive to rationalize its own priors, the same sycophancy bias operating on self-review.

Multi-LLM panel breaks this. If Claude frames Option A as "methodology-pure" and Gemini independently rates it as "pragmatic-with-bounded-debt," the disagreement becomes salient. Sycophancy to both simultaneously is impossible.

---

## Section 3: Concrete recommended setup — three-layer decision architecture

Deploy for each load-bearing ADR. Skip for routine decisions (rename, dependency bump, doc edit).

### Layer 1 — Pre-decision asynchronous envelope (~30 min, $0)

Before writing the ADR, run a private ACH worksheet:

- List all plausible hypotheses, including: "kill the project," "defer to Phase 1.0," "rewrite scope," "accept current architecture as-is."
- For each, list data that supports it and data that contradicts it.
- Extract the "kill project" hypothesis explicitly. Write it out. Estimate the $0 base-case cost to restart on a different approach.

This forces the kill question into the frame. Maps to `LESSONS.md` §4.4 (premature scope escalation when fixes asymptote): the worksheet forces "Phase 0.9 work is necessary only if X falsifies Y," not "Phase 0.9 unlocks the rewrite path as a sidecar."

### Layer 2 — Custom-prompt expert chat (1–2 rounds, $0–$3)

Use the current redteam prompt (`2026-05-09-offline-redteam-prompt.md`), unmodified. Two changes to how it is invoked:

- Before the expert responds, pre-write a single-paragraph defense of the recommendation arguing *why it survives Layer 1's kill question*. This becomes the prompt's §3.X input.
- Expert responds with findings per the format. Author responds. Maximum 2 rounds.

Anchoring the single-LLM review with the author's own Layer 1 worksheet makes sycophancy harder: the model now has to grapple with prior reasoning rather than simply agree with the latest frame.

### Layer 3 — Multi-model debate (1 round, $8–$12) — only if Layer 2 finds ≥2 high-severity findings

Formulate Layer 2's top attack as a structured debate:

- **Debater A (Claude):** "Here's the author's recommendation (Option X) with Layer 2's top attack against it. Steelman the attack. What's the strongest version of it?"
- **Debater B (Gemini):** "Here's the same recommendation. Steelman the author's defense. What's the strongest version of it?"
- **Judge (GPT-4):** "Which argument is more rigorous? Where is each side weakest?"

Debaters argue one round (3K tokens each). Judge synthesizes. Cost: $8–$12.

This catches model-orthogonal blindspots. Independent disagreement between Claude and Gemini on the same evidence is a red flag worth investigating before the ADR locks.

### Cadence + circuit breakers

- **Layer 1:** always (30 min, $0). Output is a markdown worksheet committed alongside the ADR draft.
- **Layer 2:** always. Batch into one review per 2–3 related decisions to avoid review fatigue.
- **Layer 3:** only if Layer 2 finds ≥2 high-severity findings *and* the author has not already changed direction in Layer 2. Triggering Layer 3 after a direction change is itself an instance of the cave-velocity pattern (`LESSONS.md` §4.1).
- **Hard gate, all layers:** if the author reverses direction more than once across Layers 1+2, pause before Layer 3. Re-derive from first principles instead of escalating to a more expensive channel. Two reversals is a hold-and-harvest signal, not an escalation signal.

### Cost + signal

| Per-ADR | Cost | Signal added vs prior layers |
|---|---|---|
| Layer 1 | $0 | Catches scope-escalation, kill-question avoidance |
| Layer 2 | $0–$3 | Current baseline: catches framing escalation, loose stats, retro-rationalization |
| Layer 3 | $8–$12 (only when triggered) | Catches sycophancy + model-orthogonal blindspots |

Total expected cost per significant ADR: $3–$15, dominated by Layer 3 frequency.

### What is explicitly NOT recommended

- **Advisory boards / monthly fractional consultants** at this stage. High friction, low bias-diversity gain over a structured Layer 3 multi-model debate. Defer until product-market validation justifies the overhead.
- **Always-on Layer 3.** Wastes signal — multi-model panels lose force when used routinely. Reserve for high-severity Layer 2 findings.
- **Claude-vs-Claude debate.** Same model architecture on both sides reproduces the sycophancy gap that Layer 3 is designed to break. Use heterogeneous model families.

---

## Section 4: References

Foundational:

1. Richards Heuer, *Psychology of Intelligence Analysis* (CIA, 1999): <https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf>
2. Heuer & Pherson, *Structured Analytic Techniques for Intelligence Analysis*, 2nd ed. (CQ Press, 2014): 50 techniques including ACH and devil's advocacy.
3. Gary Klein, "Performing a Project Premortem," *Harvard Business Review* (2007): <https://hbr.org/2007/09/performing-a-project-premortem>
4. Mason & Mitroff, "A Program for Research on Management Information Systems," *Management Science* (1973), and follow-on work in *Academy of Management Review*: dialectical inquiry vs devil's advocacy vs consensus, empirical comparison.
5. Schwenk, "Cognitive Simplification Processes in Strategic Decision-Making," *Strategic Management Journal* (1984): devil's advocacy empirically superior to consensus for surfacing flawed assumptions.
6. Mitchell, Russo & Pennington, "Back to the Future: Temporal Perspective in the Explanation of Events," *Journal of Behavioral Decision Making* (1989): prospective hindsight, 30% improvement.

Recent (2024–2026):

7. Du, Li, Torralba, Tenenbaum & Mordatch, "Improving Factuality and Reasoning in Language Models through Multiagent Debate," ICML 2024: <https://arxiv.org/abs/2305.14325>
8. Irving, Christiano, Amodei, "AI Safety via Debate" (2018) and follow-on alignment-via-debate work: <https://arxiv.org/abs/1805.00899>
9. Tetlock & Mellers, *Superforecasting* and the Good Judgment Project (Crown, 2015): adversarial collaboration and structured forecasting; tournament evidence.
10. OSF Preregistration Initiative: <https://www.cos.io/initiatives/prereg> — binding pre-registration mechanics; "exhaustive specification" reduces outcome switching.

---

## Bottom line

Project Nova is structurally susceptible to sycophancy-by-single-model-design. The current method catches dishonesty but misses cooperative-alignment bias. Add Layer 1 (free ACH worksheet, forces the kill question) and use Layer 3 (multi-model debate, $8–$12 when Layer 2 surfaces ≥2 high findings) as a circuit breaker. Skip expensive advisory boards; they add friction without the bias-diversity that comes from structured deliberation. `LESSONS.md` is already doing most of the cognitive-bias-tracking work — make it the *input* to ACH (Layer 1), not a post-facto audit log.
