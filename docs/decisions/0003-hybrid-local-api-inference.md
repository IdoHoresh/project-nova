# ADR-0003: Hybrid local + API inference (System 1 / System 2 routing)

**Status:** Accepted (for Phase 1+ implementation)
**Date:** 2026-05-02
**Deciders:** Founder + AI red-team brainstorm

---

## Context

Nova currently runs all LLM inference through cloud APIs (Gemini Flash
for ReAct decisions, Gemini Pro for ToT branches, Anthropic Sonnet for
reflection). At small scale this is fine — ~$0.0004 per ReAct call,
~$0.005 per ToT call.

At production scale (50 personas × 100 sessions/month × 10 studios =
50K sessions/month), the API costs reach ~$2.5K-5K/month. More
importantly, latency is 1-2s per ReAct call which adds up over a 50-
move game, and Pro has a 1000 RPD per-model daily quota that's already
been exhausted in heavy testing.

Two extreme alternatives:

1. **Stay all-API.** Higher cost at scale, latency, rate limits.
2. **Move all-local.** Need ~70B+ model for sufficient reasoning depth,
   requires expensive hardware (>$5K data-center GPU or rented cloud
   GPU at $1-3/hour), still has setup complexity.

## Decision

**Hybrid local + API stack mirroring Kahneman's dual-process cognition:**

| Path | Model | Where it runs | Why |
|------|-------|----------------|-----|
| **System 1 (ReAct)** — 90% of moves: routine decisions | Qwen 2.5 14B Instruct or Phi-4 14B (via vLLM) | Local GPU (RTX 4090 or M-series Mac, 12-16GB VRAM) | Fast, intuitive, ~250-500ms inference, zero marginal cost |
| **System 2 (ToT branches)** — 5-10% of moves: deliberation | Claude Haiku 4.5 (or Gemini Pro fallback) | Frontier API | Branches need real reasoning; rare enough that API cost is bounded |
| **System 2 (Reflection)** — 1 call per game-over | Claude Sonnet 4.6 | Frontier API | Postmortem narration benefits from frontier reasoning + long context |
| **Cheap vision (OCR fallback)** | Gemini 2.5 Flash-Lite | Frontier API | Used only for games without SDK perception |

The reliability mechanism that makes 14B local viable: **vLLM
`guided_decoding` with JSON-schema constraints.** Schema constraints
are enforced at sampling time — the model literally cannot emit tokens
that produce malformed JSON. Parse-error rate drops to **literal zero**
by construction, not "drastically lower."

## Alternatives considered

- **All-API (rejected for production).** Rejected for the cost +
  latency + rate-limit reasons listed in Context. Acceptable for the
  Week 0–4 validation sprint because volume is low.
- **All-local with 70B model (rejected).** Strengths: zero per-move
  marginal cost, no rate limits, full data privacy. Rejected because:
  requires $5K+ hardware OR cloud GPU rental that's more expensive than
  the API at low traffic; small-team operational complexity (vLLM
  serving, model management, hardware monitoring); 14B-class with
  guided decoding is sufficient for ReAct quality; frontier reasoning
  STILL needed for ToT and reflection.
- **All-local with 14B model (rejected).** Same hardware cost story
  but lower quality. Rejected because ToT branches and reflection
  genuinely benefit from frontier reasoning depth that 14B doesn't
  provide.

## Consequences

**Positive:**

- ~95% of inference moves local (no marginal cost; no rate limits;
  no data leaves the studio's infrastructure for the routine path).
- API cost stays bounded — only the rare deliberation + reflection
  calls hit the API.
- Studios with strict IP protection on pre-launch builds can run the
  System 1 path entirely on their own hardware; only ToT calls hit a
  third party. Significantly lowers the trust barrier for sales.
- Graceful degradation: if local model fails, fall back to API; if API
  rate-limited, fall back to cheaper API tier.
- The dual-process framing maps cleanly to Kahneman, which is a
  recognizable intellectual reference for sophisticated buyers.

**Negative:**

- Hardware requirement (~$1.5K consumer GPU or M-series Mac) for any
  studio that wants to self-host the local tier.
- Implementation complexity: another LLM adapter (`LocalLLMAdapter`
  using vLLM), routing logic, fallback chains.
- Per-game-quality difference: a ReAct decision via local 14B is
  measurably (though not dramatically) less sharp than via Gemini Flash.
  We accept this tradeoff for the cost + privacy gains.

**Neutral:**

- LLM provider abstraction is already in place via the `LLM` protocol
  in `nova_agent/llm/protocol.py`. Adding the local adapter is a 1-week
  port, not a rewrite.

**Reversibility:**

- Reversible. If the local tier produces unacceptable quality, fall
  back to all-API. The adapter pattern makes this a config change.

## References

- `docs/product/methodology.md` §3 (Inference architecture) for full
  technical detail.
- ADR-0001 (cognitive architecture as moat) — this ADR mitigates the
  cost downside of that decision.
- `nova_agent/src/nova_agent/llm/protocol.py` for the existing
  abstraction.
- vLLM docs on `guided_decoding`:
  https://docs.vllm.ai/en/latest/usage/structured_outputs.html
- Kahneman, D. (2011). *Thinking, Fast and Slow*. (Bibliography in
  `docs/product/scientific-foundations.md`.)
