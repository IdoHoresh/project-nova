# ADR-0009: production-tot-model-sonnet-over-pro

**Status:** Accepted  
**Date:** 2026-05-06  
**Supersedes:** ADR-0006 Amendment 1 (Pro→Sonnet swap, 2026-05-06)  
**Deciders:** ihoresh07@gmail.com (solo founder), synthesis red-team review (2026-05-06)

---

## Context

ADR-0006 set the `production` tier's ToT model to `gemini-2.5-pro`. Amendment 1 to ADR-0006
(same date as this ADR) swapped Pro → `claude-sonnet-4-6` after the 2026-05-06 pilot exposed
two operational failures:

1. **Hard 1000 RPD quota.** Gemini 2.5 Pro's free-tier API key has a shared 1000 requests-per-day
   ceiling. A full cliff-test pilot (3 scenarios × 5 trials × 2 arms × 4 ToT branches) consumes
   ~956 Pro calls — essentially the full daily budget. The Phase 0.7 formal N=20 run needs
   ~3200+ Pro calls, requiring 3+ consecutive days and introducing inter-day confounds.

2. **Clustered rate-limit failures.** The pilot at concurrency=8 produced 78× empty-response
   (`tokens_out=0`) plus 20× tenacity-exhausted `RetryError[ClientError]` events. All four ToT
   branches in a single decision failed within <1 s of each other — joint failure probability
   far above the per-branch independence model. Trial-level abort rate: ~20%, too high for
   paired-discard semantics at N=20.

Amendment 1 captured the operational decision but omitted a complete alternatives analysis.
The synthesis red-team (2026-05-06) flagged this as a methodology gap: a reader cannot verify
that the amendment chose the right option without seeing what was ruled out. This ADR closes
that gap and stands as the authoritative record, superseding the amendment.

---

## Decision

**Keep `production` tier ToT on `claude-sonnet-4-6`.** The 1.9× per-call cost premium over Pro
is justified because all alternative approaches that preserve a same-day, coherent, N=20
cliff-test run introduce either operational infeasibility, experimental confounds, or
infrastructure scope that is out of proportion to the premium.

### What changes from the original ADR-0006 production tier

| callsite | before | after |
|----------|--------|-------|
| `production` tier `tot` | `gemini-2.5-pro` | `claude-sonnet-4-6` |
| all other production-tier mappings | unchanged | unchanged |

`decision = gemini-2.5-flash`, `reflection = claude-sonnet-4-6`, `tot_branches = 4` are
all unchanged.

### Cost accounting

| metric | Pro | Sonnet |
|--------|-----|--------|
| input price | $1.25 / Mtok | $3.00 / Mtok |
| output price | $10.00 / Mtok | $15.00 / Mtok |
| per ToT call (~460 in + 70 out tokens) | ~$0.00128 | ~$0.00243 |
| multiplier | — | ~1.9× |
| formal N=20 run (3 scenarios, both arms) | ~$6.60 est. | ~$12 est. |
| delta | — | +~$5.40 |
| within spec §2.6 $5/scenario/arm soft cap? | yes | yes |
| within 6-week sprint budget envelope? | yes | yes |

The 1.9× per-call increase is +$5.40 on the formal run. That is within the Phase 0.7 budget
envelope and within the cliff-test spec's per-scenario cost cap. The premium buys elimination
of the failure mode that aborted ~20% of trials in the pilot.

### Operational implications

- **No daily quota wall.** Anthropic's API has no shared daily call cap; the only ceiling is
  the Stripe-credit balance (already funded per CLAUDE.md gotcha #4). Two consecutive
  formal-run days are possible without calendar coordination.
- **Rate limiting.** Anthropic returns standard 429s with an explicit `Retry-After` header.
  The existing `tenacity wait_exponential(min=1, max=8)` on `RateLimitError` absorbs transient
  pressure. No clustered-failure pattern observed on the Anthropic path in the pilot.
- **Schema enforcement.** ToT branches move from Gemini generation-time schema enforcement
  to `parse_json` post-validation only (Anthropic accept-and-ignore path). This is acceptable:
  the post-validation has been the defense-in-depth path since ADR-0006; we lose only the
  redundant generation-time check on this one callsite. Sonnet is reliable on JSON-mode at
  the `_ReactOutput` schema shape.
- **Reasoning quality.** Sonnet 4.6 ≥ Pro 2.5 on tactical multi-step deliberation over small
  constrained search spaces (the 2048 ToT branch-value workload). No quality regression expected.

---

## Alternatives considered

### 1. Rate-limited execution — cap concurrency to stay under 1000 RPD

Reduce concurrency until Pro call rate fits the daily quota (≤1000/day).

Formal-run call budget: 3 scenarios × 20 trials × 2 arms × 4 branches = 480 calls minimum
(no retries). With retries at the observed 20% abort rate, actual calls ≈ 480 × 1.25 ≈ 600.
A single formal day is under 1000 RPD.

**Why rejected.** A single scenario at the formal N is feasible, but two scenarios in the same
day are not (600 × 2 = 1200 > 1000). The recalibration spec §3 requires 3 scenarios per run.
Spreading across 3 days introduces a time-varying confound: model checkpoints can change,
prompt-caching cold-start behavior changes between calendar days, and any retry that spills
from day N's budget into day N+1 creates a heterogeneous-provider window within what should
be a coherent run. The 1000 RPD cap is a hard API constraint, not a soft throughput one;
lowering concurrency does not increase the daily allowance.

Also: the clustered failure pattern (§Context, point 2) is not a concurrency artifact alone —
the pilot at c=8 hit the cluster pattern because of how Gemini handles rate-limit pressure
across co-issued requests. Even at c=1, the 20% abort rate from empty responses in the
observed window would persist as long as Pro is under burst pressure from other users on
the shared API key. The RPD cap and the clustering are independent failure modes; solving
the cap does not solve the clustering.

### 2. Queue-spread across multiple days

Schedule the formal run as a batch job that issues calls at ≤50 RPM and spreads over 3-4
calendar days, each well under 1000 RPD.

**Why rejected.** This solves the quota wall but introduces inter-day experimental confounds
at exactly the layer that must be clean for methodology integrity:

- **Model drift.** Gemini 2.5 Pro's checkpoint is not pinned to a specific model hash via the
  public API. A checkpoint update between day 1 and day 3 produces a mixed-model run with no
  way to detect or flag the seam in the CSV.
- **Prompt-cache cold starts.** The first call of each day hits a cold prompt cache. Latency
  and cost distribution differ from warmed-cache calls. At N=20 per scenario, 3-day spread
  means each scenario has 2-3 cold-start trials mixed with warm-cache trials — a systematic
  positional confound.
- **Board-state reproducibility.** The seeding guarantees same board spawn sequence, not same
  LLM random state. Across days, any shared global state in the Gemini API that affects
  temperature sampling (even at T=0 for the Bot arm) is not guaranteed to be stable. The Bot
  arm at T=0 should be deterministic, but Carla at T=0.7 has genuine sampling variance; the
  variance distribution is not guaranteed constant across days.
- **Operational fragility.** A 3-day distributed run requires a scheduler, state persistence
  across re-runs, and resume logic that the current harness doesn't have. Building this is more
  scope than the +$5.40 per run alternative.

### 3. Google Cloud Vertex AI — paid tier with higher Pro quota

Move from the Gemini API free tier to Vertex AI's Pro endpoint, which has higher (or
customer-configurable) quotas and a pinned model version.

**Why rejected.** Vertex AI migration is its own infrastructure project:

- Different SDK (`google-cloud-aiplatform` vs `google-generativeai`) — not a one-line swap.
- Service account credentials, IAM setup, project/region selection.
- Response schema shape differences that require `LLM.complete()` Protocol changes.
- Vertex Pro pricing is $7/Mtok input vs Pro API's $1.25/Mtok — a 5.6× premium over the
  current Pro path, making Sonnet's 1.9× look conservative by comparison.

The Vertex path is the right re-evaluation trigger if Nova scales to a commercial synthetic-
playtesting service and needs pinned models + SLAs. Phase 0.7 is not that scale.

### 4. Mixed-model fallback — Pro until quota exhausted, then Flash

Run ToT on Pro until the daily 1000 RPD cap is hit, then fall back to gemini-2.5-flash for
remaining calls in the same run.

**Why rejected.** This introduces model heterogeneity within a single run — some trials have
Pro-quality ToT branch evaluation, others have Flash-quality. The Δ metric depends on Carla's
per-trial `t_predicts` values, which depend on ToT branch quality. A mixed-quality run produces
a biased Δ distribution with no clean way to separate the quality effect from the affect signal.
The methodology section's external-review defense requires a coherent same-quality run.

### 5. Reduce tot_branches to 2 for the Pro path (stay under cap at N=20)

Halve the branching factor to cut Pro calls by 50%, staying under 1000 RPD per day for a
single-scenario run.

**Why rejected.** `tot_branches = 4` is load-bearing per ADR-0007 Amendment 1 §A1.4 (bundle
attribution). ToT is one of affect's deployed channels — `arbiter.should_use_tot()` gates ToT
on the affect vector. Reducing branches below the deployed configuration creates a mismatched
test: the cliff-test Carla is not the deployed Carla. The methodology defense "we tested the
deployed architecture" breaks. The pass-criterion gate for pass criterion 1 is calibrated on
the N=4-branch architecture.

Separately, reducing branches trades quality degradation in the deliberation path for cost
savings — the same problem as the plumbing-tier footgun that ADR-0006 was written to prevent.

---

## Consequences

**Positive**

- Eliminates the 1000 RPD ceiling as a cliff-test blocker. Two formal runs in the same UTC
  day are possible without calendar coordination.
- Eliminates the clustered-failure pattern observed in the pilot. Anthropic 429s are
  individually retried; the all-four-branches-fail-within-1s joint failure mode does not
  occur on the Anthropic rate-limit path.
- Reasoning quality maintained or improved for the 2048 ToT workload.
- External-review defense is cleaner: "we use Gemini Flash at the high-frequency cheap
  callsites (both arms, ~50× per trial) and Anthropic Sonnet at the cognitive callsite
  (Carla ToT, once per Carla decision). Cross-provider proof is preserved where it costs
  nothing; the quota-constrained callsite moves to the provider with no daily cap."

**Negative**

- +~$5.40 per formal N=20 run. Acceptable at Phase 0.7 scale; re-evaluate if Phase 0.8
  ablation (N=2000 games) routes through production tier (it should not — ablation is a
  separate cost-tier decision per ADR-0006).
- ToT branches lose generation-time schema enforcement (Anthropic accept-and-ignore path).
  `parse_json` post-validation in `tot.py` becomes the only schema guarantee for ToT output.
  Risk is low (Sonnet reliable on `_ReactOutput` JSON shape); defense-in-depth is preserved.

**Neutral**

- `dev` and `plumbing` tiers unchanged — both stay all-Gemini.
- `demo` tier unchanged — already all-Sonnet.
- `Settings.deliberation_model` default for non-tier fallback mode remains `gemini-2.5-pro`.
  Non-tier mode is the live-agent-against-emulator path; the cliff-test always uses
  `NOVA_TIER=production`. The amendment is scoped correctly.

**Reversibility**

One-line change in `tiers.py`. Reverting to Pro is trivial if Google relaxes the 1000 RPD
cap on a future paid tier upgrade. This ADR documents the operational evidence that prompted
the swap so a future engineer doesn't re-run the same pilot to rediscover it.

---

## References

- ADR-0006 — cost-tier-discipline-and-record-replay (original four-tier definition; Amendment
  1 to this ADR is superseded by ADR-0009)
- ADR-0007 Amendment 1 §A1.3 — temperature discipline (establishes T=0 for Bot, T=0.7 for
  Carla; this ADR's alternatives analysis presupposes those values)
- ADR-0007 Amendment 1 §A1.4 — bundle-attribution rationale (establishes why `tot_branches = 4`
  is load-bearing and cannot be reduced for cost; grounds rejection of alternative 5 above)
- `nova_agent/llm/tiers.py` — the one-line change this ADR ratifies
- `nova_agent/decision/arbiter.py:should_use_tot` — the affect channel that makes ToT
  bundle-load-bearing (cited in alternative 5 rejection)
- 2026-05-06 pilot CSVs — `runs/2026-05-06-pilot/pilot_results/cliff_test_results.csv`
  (production tier c=8, ~20% abort rate from Pro quota pressure); `runs/2026-05-06-pilot-c4/`
  (c=4, confounded by quota exhaustion before data collection)
- Synthesis red-team report 2026-05-06 — flagged missing alternatives section in Amendment 1
- LESSONS.md entry 2026-05-06: "Gemini Pro 2.5 has a hard 1000 RPD daily quota..." — the
  empirical trigger for this ADR
