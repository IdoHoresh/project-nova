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

**nova-agent:** `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"` required before any `uv` command (macOS Sequoia UF_HIDDEN). Gate: `/check-agent`

**nova-viewer:** `pnpm` only — `npm install` corrupts `node_modules`. Gate: `/check-viewer`

**Emulator:** see `LESSONS.md`. `pm clear` does NOT reset save state — cold-boot AVD.

---
## Branch + commit · Quality gates

- `claude/<name>` only. Never `main`. Push after every commit. Atomic. No "and" in subject.
- Conventional Commits `type(scope): subject ≤72 chars`. Body = why.
- Co-author: `Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>`

Python: `pytest + mypy strict + ruff check + gitleaks` | TS: `vitest + tsc + eslint + gitleaks`

Never `--no-verify`. Hooks run automatically; CI re-checks on push + PR.

---
## When to use which skill

| Signal | Invoke |
|--------|--------|
| New surface area / unclear scope | `superpowers:brainstorming` **(Path A — Opus first)** |
| Multi-step work, 3+ files | `superpowers:writing-plans` **(Path A — Opus first)** |
| Plan with independent atomic tasks | `superpowers:subagent-driven-development` |
| 2+ independent parallel questions | `superpowers:dispatching-parallel-agents` |
| Cognitive-layer / bus / decision code | `superpowers:test-driven-development` |
| "I think this is done" | `superpowers:verification-before-completion` |
| Non-obvious failure | `superpowers:systematic-debugging` |
| Pre-commit review (default entry) | `/review` — REVIEW.md path-matched dispatch |
| Receiving review feedback | `superpowers:receiving-code-review` |
| Wrapping up branch / opening PR | `superpowers:finishing-a-development-branch` |
| Gate trio | `/check-agent` or `/check-viewer` |

**Model rule:** see `## Model escalation` below.

---
## Model escalation — when Sonnet must offer swap to Opus

Sonnet 4.6 default. If ANY trigger fires → surface swap, wait for `/model claude-opus-4-7[1m]`. Binary signals, NOT judgment.

| Signal                                                          | Path |
|-----------------------------------------------------------------|------|
| Invoking `superpowers:brainstorming` skill                      | A — manual `/model` swap |
| Invoking `superpowers:writing-plans` skill                      | A — manual `/model` swap |
| Touching `nova_agent/{llm,perception,memory,bus}/**`            | A — manual `/model` swap |
| Drafting or rewriting `docs/decisions/NNNN-*.md`                | B — subagent dispatch `model="opus"` |
| Cross-cutting refactor: 3+ files in 2+ subsystems               | A — manual `/model` swap |
| Debugging stuck >2 attempts (no root cause found)               | B — subagent dispatch `model="opus"` |
| Methodology change in `docs/product/methodology.md`             | B — subagent dispatch `model="opus"` |
| Security review on auth / IO / LLM-content surface              | B — subagent dispatch `model="opus"` |
| User says "this is gnarly" / "I'm stuck" / "weird bug"          | A — manual `/model` swap |

After Path A → remind `/model claude-sonnet-4-6`. Detail: `feedback_session_model_selection.md`.

---
## Context hygiene — MANDATORY

**Session length is the #1 token cost driver.** Offer `/clear` after every commit + push.

> `/clear` recommended — [reason]. Handoff: `Last shipped: <sha>. Next: <task>. Read: CLAUDE.md, resume-point, git log -10`

Triggers: commit+push · PR merges · concern switch · >150k tokens · ~2h work · artifact commit.

Before artifact-cliff `/clear` → run `/handoff` first. Mid-feature >200k: `/compact`.

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

- No RL pivot — simulator not optimizer (`methodology.md §3.3`)
- No Jira-style bugs — use `docs/internal/v2.2-epsilon-spec.txt`
- No real-time / 3D promises — out of scope
- No mid-Phase pivots — each phase has exit criterion
- No pitch before Phase 0.7 passes
- No invented dollar figures — hand cohort data
- No direct commits to `main`
- No `--no-verify` without explicit same-session permission
- No `Edit` without `Read` first

---
## Active phase + next task

`~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_resume_point.md` — read first each session.
