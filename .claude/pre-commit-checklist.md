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
- [x] `git diff --cached --stat` reviewed — single file `.claude/settings.json` (3 small edits: explanation comment update, `model: "claude-sonnet-4-6"` field added to the agent hook, timeout 120s → 180s for Sonnet's slower turnaround, statusMessage suffix updated)
- [x] Atomic commit — single logical change: bump Layer 1.5 pre-push agent hook from default Haiku 4.5 to Sonnet 4.6 for stronger architectural recall on every push, per user "best results" preference

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; settings.json adds a model name string only
- [x] `nova-agent/` not touched — N/A, Claude-config-only change
- [x] `nova-viewer/` not touched — N/A, Claude-config-only change
- [x] Docs / config — `.claude/settings.json` agent hook gains `"model": "claude-sonnet-4-6"` (was using the schema default Haiku 4.5). Timeout bumped from 120s to 180s to accommodate Sonnet's longer turnaround on the deeper-rubric pass. `_hooks_explanation` comment updated to reflect the new model + cost line (~$0.06-0.12 per push, ~$38 over the 6-week sprint at 10 pushes/day) and to make explicit the layered-model story (Sonnet at L1.5 backstop / Opus at L2 final gate). JQ schema validated: `.hooks.PreToolUse[].hooks[].model = "claude-sonnet-4-6"`, `.timeout = 180`. JSON parses cleanly.

## Review

- [x] `/review` dispatched on staged diff — N/A: `.claude/settings.json` is the "skip with reason: Claude-tooling-only" row of REVIEW.md path-matched trigger taxonomy
- [x] `code-reviewer` subagent — N/A, covered by skip reason above
- [x] `security-reviewer` — N/A, no secrets / env / LLM / bus paths touched. Note: this is a model UPGRADE for security-relevant analysis at push time (Sonnet > Haiku on subtle prompt-injection-adjacent and bus-protocol-violation patterns). Defense improves.

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the inline `_hooks_explanation` comment in `.claude/settings.json` documents the model choice + cost trade-off + the layered-model story so a future contributor reading the JSON doesn't downgrade back to Haiku without seeing the reasoning
- [x] CLAUDE.md "Common gotchas" — N/A, no new gotcha; the hook re-activation requirement (`/hooks` reload OR session restart so the settings watcher picks up the new model field) is the same caveat that already applies to any settings.json change
- [x] ARCHITECTURE.md — N/A, system topology unchanged; the three-layer review model now is Sonnet/L1.5 → Sonnet/Opus L1 (operator-tuned) → Opus/L2 (final gate)
- [x] New ADR — N/A, this is a model-tuning change inside the existing Layer 1.5 hook shipped under ADR-0006's cost-tier discipline. Could be considered a minor amendment to ADR-0006 but doesn't rise to a new ADR; the `_hooks_explanation` comment captures the trade-off

## Commit message

- [x] Conventional Commits format: `feat(claude): bump pre-push hook model to Sonnet 4.6`
- [x] Body explains *why* — user expressed "not confident in Haiku" preference and asked for the strongest reasonable model at every-push cadence. Sonnet is the right middle: meaningfully more capable than Haiku on multi-file synthesis and subtle architectural smells; ~5x cheaper than Opus per push; preserves the layered model story (Layer 1.5 backstop at every push, Layer 2 Opus at every PR for the final gate). Cost goes from ~$13 sprint cost on the hook to ~$38 — well within the $110-130 sprint LLM budget. Bumping all the way to Opus would have created redundant flagship reasoning between Layer 1.5 and Layer 2 (Opus reviews a diff, then Opus reviews the same diff again on PR open) without proportional value. Sonnet at L1.5 + Opus at L2 is the right asymmetry: catch fast at push, deep at PR.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
