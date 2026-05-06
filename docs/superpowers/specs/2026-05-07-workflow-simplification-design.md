# Workflow Simplification — Design

> Status: design approved, awaiting implementation plan
> Author: Ido + Claude Opus 4.7
> Source: research dossier (`compass_artifact_wf-9a1cd258-7482-4adb-92ad-ea233af4e7a7_text_markdown.md`) cross-referenced with current `workflow.md`, `CLAUDE.md`, `REVIEW.md`, `pre-commit-checklist.md`, and `.claude/settings.json`.

## 1. Goal

Cut workflow rule density and per-turn token load by ~40–55% while holding the current quality bar. Make the workflow followable in a single pass — fewer steps, clearer triggers, and binary signals that do not depend on judgment under fatigue.

## 2. Why now

Three reported pains, one shared root cause:

1. **"Too much is happening."** Eighteen pre-commit steps, three review layers, six memory channels, ten model-selection sub-rules. No tier separation. Every step marked "ABSOLUTE — never skip."
2. **"Tokens used too fast."** ~700 lines auto-loaded per turn (`CLAUDE.md` + `workflow.md` + `REVIEW.md` + `MEMORY.md` index + memory files). All-day sessions cross 150k context routinely. Default model = Sonnet 4.6 *1M tier* on routine work. Layer 1.5 Haiku LLM gate fires on every push.
3. **"Can't follow the steps."** Direct consequence of (1). Rule density forces partial reads, partial reads breed silent skips, silent skips trigger guilt + over-correction (more rules added). Cycle.

Root cause: workflow defends every-step compliance by elevating every step. Result: no signal-to-noise gradient, so the brain rejects the whole document.

## 3. Design principles

- **Tier rules.** Tier 1 = invariants that protect the project (no main commits, no `--no-verify`, push-after-commit). Tier 2 = advisory / nice-to-have. Demote or delete what hooks already enforce.
- **Hooks own deterministic checks.** Do not duplicate hook logic in human checklists.
- **Path-or-keyword triggers, not judgment.** Whenever possible, encode "when does this apply" as a path glob or a keyword match, not a vibes call.
- **One-page workflow.** Target `workflow.md` ≤ 80 lines. CLAUDE.md ≤ 130 lines.
- **Two-strikes additions only.** New rules added when the same mistake recurs, not preemptively.

## 4. Target flow — five-stage loop

Source: research consensus across Boris Cherny, Jesse Vincent (Superpowers), Anthropic engineering docs.

```
Brainstorm → Plan → Implement (TDD) → Review → Ship
```

Per stage:

| Stage | Default model | Skill / artifact | Auto-checks |
|-------|---------------|------------------|-------------|
| Brainstorm | Opus 4.7 (Path A) | `superpowers:brainstorming`, spec → `docs/superpowers/specs/` | skill blocks if Sonnet |
| Plan | Opus 4.7 (Path A) | `superpowers:writing-plans`, plan → spec dir | skill blocks if Sonnet |
| Implement | Sonnet 4.6 main + Haiku 4.5 subagent | `superpowers:test-driven-development` for cognitive layer | TDD discipline + plan checkboxes |
| Review | Sonnet (routine), Opus (auth/IO/cog-layer) | `/review` orchestrator on path-matched triggers | pre-commit hooks + Layer 2 PR action |
| Ship | n/a | `/commit-push-pr` (new) | Layer 1.5 deterministic gate + Layer 2 PR action |

## 5. Concrete changes (ten items, ordered for execution)

### Step 0 — Add model-escalation triggers to `CLAUDE.md`

Insert ~15-line section: "Model escalation — when Sonnet must offer swap to Opus." Binary trigger table (path globs, keywords, scope checks). Sonnet's job becomes *match diff path against table*, which is reliably executable. Three defense layers documented: skill-level auto-block (existing), CLAUDE.md trigger table (new), user-side 30-second pre-task ritual (process).

### Step 1 — Delete `pre-commit-checklist.md` + post-commit reset hook

Free hooks (`gitleaks`, `ruff`, `mypy`, `biome`, `tsc`) already enforce what the checklist does. Hook-enforced ceremony adds friction without quality lift on a one-person team.

### Step 2 — Drop Layer 1.5 Haiku push-gate

Remove the `agent`-type pre-push hook from `.claude/settings.json`. Keep the deterministic command portion (regex secret grep, diff stat, PR-overdue warning, post-merge `/clear` hint). LLM-per-push burns tokens; Layer 2 (Opus on PR open) catches architectural drift better at coherent diff scope.

### Step 3 — Add `/commit-push-pr` slash command

Boris Cherny pattern. Single command runs `git status` + `git diff --cached` + commit (Conventional Commits + co-author tag) + push, with optional PR-open. Replaces the 14-step pre-commit ceremony with one invocation that runs the deterministic checks inline.

### Step 4 — Add `/handoff` slash command

Writes the Context Checkpoint format (architectural intent + edge-case warnings + rejected alternatives + what's next) to `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_resume_point.md` before `/clear`. Replaces ad-hoc handoff prose currently inlined by hand. Format already exists in `feedback_session_hygiene.md` memory.

### Step 5 — Path-filter Layer 2 PR action

Edit `.github/workflows/claude-review.yml`. Two jobs:
- **routine-review**: Sonnet 4.6, runs on all PRs except doc-only (path filter excludes `docs/**`, `*.md`). `.github/workflows/**` is intentionally NOT excluded — CI config is exactly the surface where a misconfiguration silently disables the safety net, so it must self-review.
- **deep-review**: Opus 4.7, runs only when paths match `nova-agent/**/{config,llm,bus,perception,memory}/**` or `.env*`. (Nova has no `auth/` surface today; trigger expands if one is added.)

Mirrors `REVIEW.md` taxonomy. Cuts Layer 2 cost ~50–70% depending on PR mix.

### Step 6 — Default subagent model to Haiku 4.5

Add to `.claude/settings.local.json` (gitignored — personal override):

```json
{ "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4-5-20251001" } }
```

Detailed plans + Haiku implementer is research-backed (Jesse Vincent, Superpowers 4). Falls back to Sonnet if Haiku reports out-of-depth. Override per-dispatch (`model: "sonnet"`) for cognitive-layer tasks. Trial run; revert if any subagent task ships incorrect work.

### Step 7 — Update `feedback_session_model_selection.md` memory

Default main = Sonnet 4.6 *200k* (not 1M). Escalate to `[1m]` only when reasoning across nova-agent + nova-viewer + Unity at the same time. ~95% of Nova work fits 200k; 1M tier is a per-token premium that should be a conscious escalation.

### Step 8 — Rewrite `.claude/rules/workflow.md` lean

Target ≤ 80 lines. Tier-1 invariants only (no main commits, no `--no-verify`, push-after-commit, atomic, ADR-for-load-bearing, TDD on cognitive layer, two-strikes for rule additions). Demote Tier-2 stuff to references (`see CLAUDE.md`). Delete duplicated content.

### Step 9 — Trim `CLAUDE.md` to ~120 lines

Move "Common gotchas" section to `LESSONS.md`. Keep stack + commands + branch + tier-1 don'ts + model escalation table (Step 0). Two-strikes rule for future additions.

## 6. Out of scope (do not change)

- Superpowers plugin install (already correct).
- ADRs in `docs/decisions/` (research-aligned).
- `pre-commit` hooks (`gitleaks`, `ruff`, `mypy`, `biome`, `tsc`) — keep as-is.
- `REVIEW.md` path-matched taxonomy (load-bearing for `/review` orchestrator).
- `/check-agent` / `/check-viewer` gate trios.
- TDD discipline on cognitive-layer code, decision logic, bus protocol.
- Branch protection on `main`.
- Conventional Commits + co-author tag conventions.
- Auto-memory system (just trim feedback files that overlap, not the system itself).
- Layer 2 (Opus on PR) discipline — only the path filter is changing, not the layer.

## 7. Estimated impact

| Lever | Estimated saving |
|-------|------------------|
| `CLAUDE.md` + `workflow.md` trim (Steps 8, 9) | ~30% per-turn auto-load |
| Drop Layer 1.5 Haiku push-gate (Step 2) | one LLM call per push removed |
| Default Sonnet 200k vs 1M (Step 7) | ~15–25% per main-session token |
| Haiku implementer subagents (Step 6) | ~70% on implementer subagent line |
| Path-filter Layer 2 (Step 5) | ~50–70% on PR review line |
| Delete `pre-commit-checklist.md` (Step 1) | ~$0 saving; cognitive load only |
| Add `/commit-push-pr` (Step 3) | replaces 14 manual steps with one |
| Add `/handoff` (Step 4) | replaces ad-hoc prose with one command |
| Step 0 model triggers | prevents costly mis-routed Opus-territory work |

Net plausible monthly token spend cut: 40–55%, same quality bar.

## 8. Risks + mitigations

| Risk | Mitigation |
|------|-----------|
| Drop Layer 1.5 → architectural drift slips to PR | Layer 2 Opus catches at PR open within hours; ADR discipline blocks load-bearing changes |
| Haiku subagent drifts on cognitive-layer code | Per-dispatch override `model: "sonnet"` for cognitive-layer tasks; Layer 2 catches what slips |
| Trim `workflow.md` → forget invariant | Tier-1 invariants stay; Tier-2 stuff that gets forgotten = the stuff that did not matter |
| Sonnet defaults misjudge a complex task | Three defense layers (skill auto-block, CLAUDE.md trigger table, user 30-sec ritual) + Layer 2 PR review backstop |
| Default Sonnet 200k truncates large context need | `/model claude-sonnet-4-6[1m]` swap takes 2 sec; cheap to escalate |
| `/commit-push-pr` skips secret scan | Command runs `gitleaks` + `git diff --cached --stat` + secret-pattern grep inline; pre-commit hook re-runs at commit time |

## 9. Success criteria

- `workflow.md` ≤ 80 lines.
- `CLAUDE.md` ≤ 130 lines (currently ~200 post-recent-trim).
- Total auto-loaded per-turn context drops by ≥ 30% on first measurement after the batch lands.
- One PR per coherent unit cadence preserved (no regression on `workflow.md` PR-cadence rule).
- Quality bar held — rollback trigger: 2 or more Layer 2 BLOCK findings across the next 5 PRs, OR any single BLOCK finding diagnosed as model-quality (e.g., "Haiku missed state-machine edge case", "Sonnet 200k truncated cross-file context"). Coarse counts alone are too noisy on a 5-PR window when baseline BLOCK rate is near zero; the diagnostic clause is the actual attribution mechanism. BLOCK findings tied to spec drift, missing tests, or naming do NOT count toward the trigger.
- Subjective: Ido reports the workflow is followable in a single pass.

## 10. Implementation discipline

- One commit per change (10 atomic commits — Step 0 included). Easy revert if any step feels wrong.
- Branch: `claude/methodology-trauma-rewrite` (current).
- Order respects dependency: Step 0 first (trigger table sets the rule the rest operates under); Step 8 before Step 9 (workflow.md rewrite informs CLAUDE.md trim); deletes before additions; additions before rewrites.
- After Step 9, swap `/model claude-sonnet-4-6` for routine work going forward.
- One PR for the entire batch — coherent unit, single story ("simplify workflow per research dossier").

### Ordered rollback procedure (if Section 9 trigger fires post-merge)

Steps 6 (Haiku implementer default) and 7 (Sonnet 200k main default) land in the same batch despite affecting different surfaces (subagent quality vs main-session quality). If the Section 9 trigger fires, attribution is recoverable but requires ordered rollback rather than a simultaneous revert:

1. **Revert Step 6 first** (`git revert <Step 6 sha>` on the `settings.local.json` commit). Step 6 is the higher-variance change — Sonnet → Haiku is a larger quality jump than Sonnet 1M → Sonnet 200k.
2. **Run the next 3 PRs.** If BLOCK rate normalizes (no new model-quality BLOCKs, count drops below trigger), root cause = Step 6. Re-introduce Step 6 with tighter per-dispatch overrides forcing `model: "sonnet"` on cognitive-layer subagent tasks.
3. **If BLOCK rate still elevated after 3 PRs, revert Step 7** (`git revert <Step 7 sha>` on the `feedback_session_model_selection.md` memory edit). Root cause = Step 7. Diagnose context-truncation patterns from the offending PR diffs before re-introducing.
4. **Document the failing diff and the diagnostic in `LESSONS.md`** before re-introducing either step. Do not re-introduce both simultaneously a second time.
