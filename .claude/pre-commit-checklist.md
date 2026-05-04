# Pre-Commit Checklist

> Before EVERY commit, work through this list and check each item.
> The pre-commit framework runs `scripts/check-claude-checklist.sh`
> which **blocks the commit** if any item is left unchecked.
>
> After a successful commit, `scripts/reset-checklist.sh` runs at the
> post-commit stage and resets every box back to `[x]` so the next
> commit starts fresh.
>
> If a step doesn't apply, write a one-sentence reason after the
> bracket (e.g. mark `[x]` and add `/review — skipped, doc-only change`)
> and check the box. Silent skipping is forbidden.

## Branch + scope

- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — single file `docs/product/product-roadmap.md` (Phase 1 hard constraints + Phase 5 hosting strategy sections inserted, ~80 lines net)
- [x] Atomic commit — single logical change: capture three load-bearing scope-clamp decisions surfaced by the principal engineer's red-team sweep into the roadmap so they are committed-to before the relevant phase begins (rather than re-derived under pressure later)

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; roadmap-doc only
- [x] `nova-agent/` not touched — N/A, doc-only change
- [x] `nova-viewer/` not touched — N/A, doc-only change
- [x] Docs / config — Phase 1 entry gains a "Phase 1 hard constraints" subsection covering (a) the Zero-PII guarantee for the Unity SDK (allowlist of permitted payload fields, rejection-on-violation contract, the 3-month sales-cycle compression rationale because Nova bypasses the typical AI-vendor DPA negotiation entirely), and (b) the Unity 2022.3 LTS version lock (single-version MVP scope clamp, upgrade-criteria gate). Phase 5 entry gains a "Phase 5 hosting strategy" subsection naming Modal as the serverless-Python default + RunPod as the GPU fallback, with the per-second billing rationale that fits the lumpy ablation-run demand shape and the explicit escalation triggers (sustained >1000 concurrent containers, platform engineer on team, compliance regime requiring VPC isolation) for when to move to managed Kubernetes.

## Review

- [x] `/review` dispatched on staged diff — N/A: `docs/**` is the "skip with reason: doc-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, doc-only addition with no executable logic
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. Note: the Zero-PII guarantee added to Phase 1 IS a security commitment, but it commits FUTURE design (Phase 1 SDK code that does not yet exist) and does not change current code paths

## Documentation

- [x] LESSONS.md — N/A; the rationale for each constraint is captured inline in the roadmap section
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha (CLAUDE.md "Active phase + next task" gets refreshed in commit 3 of tonight's plan)
- [x] ARCHITECTURE.md — N/A, system topology unchanged; these are future-phase commitments
- [x] New ADR — deferred. Each of the three Phase 1 + Phase 5 commitments will get its own ADR at the start of the relevant phase (when the decision is being implemented and the consequences are concrete). Capturing them now in the roadmap is sufficient to lock the scope; the ADR will follow at implementation time

## Commit message

- [x] Conventional Commits format: `docs(roadmap): add Phase 1 hard constraints (Zero-PII, Unity 2022.3 LTS) and Phase 5 hosting strategy (Modal/RunPod)`
- [x] Body explains *why* — principal engineer's red-team sweep on 2026-05-04 surfaced three blind spots in the long-tail roadmap that, if not committed-to in advance, become urgent decisions made under pressure. Zero-PII guarantee and Unity LTS lock collapse the Phase 1 sales-cycle and engineering-scope respectively; Modal/RunPod replaces the implicit "AWS by default" assumption with a pay-per-second model that fits the lumpy ablation-run demand shape and a solo dev's ops capacity.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
