# CLAUDE.md — Project Nova

> Auto-loaded every session. Quick-reference card.
> Deep context: `ARCHITECTURE.md` · `docs/product/README.md` · `LESSONS.md`

---

## What this project is

Project Nova: cognitive audit platform — simulated player personas test game design hypotheses. Working demo: memory + affect + ToT deliberation + reflection + brain-panel viewer on 2048/Android emulator. Product layer (multi-game, persona KPIs) is roadmap, not current state.

---

## Repository layout

```
nova-agent/      # Python cognitive architecture (pytest + mypy strict + ruff)
nova-viewer/     # Next.js 16 + React 19 brain panel (vitest + tsc + eslint)
nova-game/       # Unity 2048 APK build artifacts
docs/product/    # strategic dossier: methodology, roadmap, personas, science
docs/decisions/  # ADRs
.claude/         # settings, agents, rules, plans, skills
```

Unity fork: `~/Desktop/2048_Unity/`. APK: `~/Desktop/2048_Unity/build/nova2048.apk`.

---

## Build + test

### nova-agent (Python)

**Set this env var every session — required before any `uv` command:**
```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
```
macOS Sequoia UF_HIDDEN hides editable `.pth` files → `uv run nova` fails without this.

```bash
# from nova-agent/
uv sync --extra dev
uv run pytest --tb=short -p no:warnings   # ~140 tests, ~5s
uv run mypy                                # strict
uv run ruff check
```
Gate trio shortcut: `/check-agent`

### nova-viewer (Next.js)

**Use `pnpm` — `npm install` crashes on pnpm-shaped `node_modules`.**

```bash
# from nova-viewer/
pnpm install
pnpm test           # vitest ~47 tests
npx tsc --noEmit    # type-check
pnpm run lint       # eslint
pnpm run dev        # localhost:3000
```
Gate trio shortcut: `/check-viewer`

### Unity 2048 emulator

```bash
~/Library/Android/sdk/emulator/emulator @Pixel_6 -no-snapshot &
adb wait-for-device
adb shell pm clear com.idohoresh.nova2048
adb shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
scrcpy --serial emulator-5554
```
`pm clear` does NOT reset save state — cold-boot the AVD to fully reset.

---

## Branch + commit conventions

- **Branch:** `claude/practical-swanson-4b6468`. Never commit to `main`.
- **Push immediately** after every commit.
- **Conventional Commits:** `type(scope): subject ≤72 chars`. Body = why, not what.
- **Co-author tag:** `Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>`
- **Atomic:** one logical change per commit. "and" in subject = split it.

---

## Quality gates (must pass before commit)

Python: `pytest + mypy strict + ruff check + gitleaks`
TypeScript: `vitest + tsc --noEmit + eslint + gitleaks`

Never `--no-verify`. Pre-commit hooks auto-run on staged files; CI re-runs on every push + PR.

**Pre-commit checklist** (`.claude/pre-commit-checklist.md`): unchecked box blocks commit; post-commit hook auto-resets. Silent skip forbidden.

First-time setup (one-shot per clone):
```bash
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type post-commit
git config merge.ours.driver true
```

---

## Common gotchas

1. **UF_HIDDEN venv** — `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"` every session. See Build section.
2. **Gemini Pro RPD limit** — 1000/day; exhausts at ~250 ToT calls. Workaround: `NOVA_DELIBERATION_MODEL=gemini-2.5-flash` in `.env`.
3. **Empty shell env shadows `.env`** — `ANTHROPIC_API_KEY=""` in shell beats `.env`. Fixed via `env_ignore_empty=True`; check `printenv | grep ANTHROPIC` on API key errors.
4. **Anthropic API needs paid credits** — "Credit grant" rows ≠ API access. Need "Credit purchase", status "Paid".
5. **Unity ignores `adb shell input swipe`** — DPAD keyevents only (19/20/21/22). `ADB.swipe()` already uses these.
6. **OCR palette must match Unity colors** — `_PALETTE` in `nova_agent/perception/ocr.py`. 64 + 256 unsampled; missing tiles → silent wrong perception.
7. **`pm clear` doesn't reset Unity save state** — cold-boot AVD to fully reset.
8. **Viewer = pnpm, not npm** — `npm install` crashes.
9. **AgentEvent catch-all defeats TS narrowing** — `{event: string; data: unknown}` arm blocks discriminated narrowing; `as` casts in `deriveStream.ts` until fixed.

---

## When to use which skill

| Signal | Invoke |
|--------|--------|
| New surface area / unclear scope | `superpowers:brainstorming` **(Path A — switch to Opus first)** |
| Multi-step work, 3+ files | `superpowers:writing-plans` **(Path A — switch to Opus first)** |
| Plan with independent atomic tasks | `superpowers:subagent-driven-development` |
| 2+ independent parallel questions | `superpowers:dispatching-parallel-agents` |
| Cognitive-layer / bus / decision code | `superpowers:test-driven-development` |
| "I think this is done" | `superpowers:verification-before-completion` |
| Non-obvious failure | `superpowers:systematic-debugging` |
| Pre-commit review (default entry) | `/review` — REVIEW.md path-matched dispatch |
| Receiving review feedback | `superpowers:receiving-code-review` |
| Wrapping up branch / opening PR | `superpowers:finishing-a-development-branch` |
| Gate trio | `/check-agent` or `/check-viewer` |

**Model rule:** brainstorm + plan = Opus required (refuse to start on Sonnet; tell user `/model claude-opus-4-7[1m]` first, swap back after). All other work = Sonnet default.

---

## Context hygiene — MANDATORY

**Session length is the #1 token cost driver.** 700+ lines auto-loaded × every turn × long sessions = daily quota burn.

**Claude MUST offer `/clear` after every commit + push.** Do not wait for the user to ask. Pattern:
> "`/clear` recommended — [trigger reason]. Handoff: `Last shipped: <sha + 1-line>. Next: <task from resume-point memory>. Read: CLAUDE.md, resume-point memory, git log --oneline -10`"

**All `/clear` triggers (non-negotiable):**
- After every commit + push — check every single time
- After PR merges to `main`
- Switching to a different concern
- Context >150k tokens (check `/usage`)
- ~2h continuous work
- After any artifact commit (spec, plan, implementation)

**Before artifact-cliff `/clear`:** write a Context Checkpoint to `project_nova_resume_point.md` first (architectural intent + edge-case warnings + rejected alternatives). Format in `feedback_session_hygiene.md` memory.

`/compact` = mid-feature continuity when context heavy (>200k) but work still ongoing.

---

## Pre-task checklist

- [ ] On correct branch (`git branch --show-current`)
- [ ] `docs/product/methodology.md` read if cognitive-arch change
- [ ] Planning artifact exists (spec, ADR, or roadmap entry)
- [ ] Relevant ADRs checked in `docs/decisions/`
- [ ] Tests exist or will be written (TDD)
- [ ] Clear acceptance criterion

---

## Things NOT to do

- No RL pivot — Nova is a simulator, not an optimizer. See `methodology.md §3.3`.
- No Jira-style bug reports — use `docs/internal/v2.2-epsilon-spec.txt`.
- No real-time or 3D promises — out of scope.
- No mid-Phase pivots — each phase has an exit criterion.
- No pitch before Phase 0.7 passes.
- No invented dollar figures in reports — hand cohort data, let studio compute UA impact.
- No direct commits to `main`.
- No `--no-verify` without explicit user permission in same session.
- No `Edit` without `Read` first.

---

## Active phase + next task

Lives in: `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_resume_point.md`

Read it first each session. CLAUDE.md does NOT duplicate it (resume-point changes per-session; CLAUDE.md doesn't).

---

## When in doubt

Architecture → `ARCHITECTURE.md` + `docs/product/methodology.md`
Strategy → `docs/product/README.md`
Roadmap → `docs/product/product-roadmap.md`
Decisions → `docs/decisions/`
Memory → `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/`

Unclear? Ask explicitly. Don't guess on load-bearing decisions.
