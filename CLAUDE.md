# CLAUDE.md — Project Nova

> **Read this first, every session.** This file is auto-loaded by Claude Code
> on session start. It tells you what Nova is, where things live, how to
> build/test, and what gotchas have already cost time.
>
> **For strategic / product context** (positioning, roadmap, methodology,
> personas, competitive landscape), read [`docs/product/README.md`](./docs/product/README.md)
> first, then [`docs/product/methodology.md`](./docs/product/methodology.md).
>
> **For architecture context**, read [`ARCHITECTURE.md`](./ARCHITECTURE.md).
>
> **Before starting work in any area**, skim [`LESSONS.md`](./LESSONS.md)
> for hard-won knowledge — gotchas, design decisions, failure modes that
> have already cost time. Add a lesson when you've learned something that
> cost time. Better to over-capture than under-capture.

---

## What this project is

Project Nova: **The Cognitive Audit & Prediction Platform** — a
product-decision tool to test game design and economy hypotheses with
simulated player personas. Currently a working cognitive architecture
demo on 2048 in an Android emulator; evolving into a synthetic
playtesting service for game studios.

The cognitive architecture (memory + affect + Tree-of-Thoughts
deliberation + post-game reflection + brain-panel viewer) is shipped
and functional on `claude/practical-swanson-4b6468`. The product layer
(multi-game, persona-based, KPI reporting) is on the roadmap, not the
current state.

---

## Repository layout

```
.
├── CLAUDE.md                # this file
├── LESSONS.md               # engineering retrospective (gotchas + decisions)
├── ARCHITECTURE.md          # system architecture overview
├── README.md                # public repo README
├── SECURITY.md              # security disclosure policy
├── CONTRIBUTING.md          # contribution conventions (even for solo)
├── LICENSE                  # MIT
├── .editorconfig            # consistent indentation across editors
├── .pre-commit-config.yaml  # gitleaks + ruff + mypy + eslint hooks
├── .github/
│   ├── workflows/ci.yml     # GitHub Actions: tests, lint, types, security
│   └── pull_request_template.md
├── .claude/
│   ├── settings.json        # team-wide Claude Code settings (committed)
│   ├── settings.local.json  # personal settings (gitignored)
│   └── commands/            # slash commands
├── docs/
│   ├── product/             # strategic dossier (v2.2; six MD files)
│   │   ├── README.md
│   │   ├── methodology.md   # 4 Signatures, KPI translations, Levene's test
│   │   ├── product-roadmap.md
│   │   ├── competitive-landscape.md
│   │   ├── personas-and-use-cases.md
│   │   ├── scientific-foundations.md
│   │   └── external-review-brief.md
│   ├── decisions/           # ADRs (Architecture Decision Records)
│   ├── internal/            # work-in-progress specs not yet promoted
│   │   └── v2.2-epsilon-spec.txt
│   └── specs/               # original implementation plans
├── nova-agent/              # Python cognitive architecture
│   ├── src/nova_agent/
│   ├── tests/               # 140+ pytest, mypy strict, ruff
│   ├── pyproject.toml
│   └── README.md
├── nova-viewer/             # Next.js 16 + React 19 brain panel
│   ├── app/
│   ├── lib/
│   ├── package.json         # pnpm-managed
│   ├── AGENTS.md            # nova-viewer-specific Claude rules
│   └── CLAUDE.md            # symlink/include of AGENTS.md
└── nova-game/               # build artifacts for the Unity 2048 fork
```

The Unity 2048 fork itself lives at `~/Desktop/2048_Unity/` (not in this
repo); APK is at `~/Desktop/2048_Unity/build/nova2048.apk`.

---

## Build + test commands (per subproject)

### nova-agent (Python)

**Important — set this env var EVERY session before any `uv` command.**
The repo lives under `~/Desktop/`, where macOS Sequoia auto-flags files
with `UF_HIDDEN`, which Python 3.14 then ignores. Without this, `uv run
nova` fails with `ModuleNotFoundError: nova_agent`. See
`nova-agent/README.md` for the full backstory.

```bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
```

Then from `nova-agent/`:

```bash
uv sync --extra dev          # install / refresh
uv run pytest                # ~140 tests, ~5s
uv run mypy                  # strict mode
uv run ruff check            # lint
uv run nova                  # run the live agent (needs adb device)
```

The full check trio (use the `/check-agent` slash command):

```bash
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

### nova-viewer (Next.js)

**Important — use `pnpm`, not `npm`.** The viewer ships a `pnpm-lock.yaml`
+ `pnpm-workspace.yaml`. `npm install` will crash on the existing
pnpm-shaped `node_modules`. From `nova-viewer/`:

```bash
pnpm install
pnpm test                    # vitest, ~47 tests
pnpm run dev                 # localhost:3000
pnpm run build               # production build
pnpm run lint                # eslint
npx tsc --noEmit             # type-check (no separate script)
```

The full check trio (use the `/check-viewer` slash command):

```bash
pnpm test && npx tsc --noEmit && pnpm run lint
```

### Unity 2048 fork

The agent talks to it via ADB on a Pixel 6 API 34 AVD (named
`Pixel_6` in Android Studio). To boot from terminal:

```bash
~/Library/Android/sdk/emulator/emulator @Pixel_6 -no-snapshot &
adb wait-for-device
adb shell pm clear com.idohoresh.nova2048    # reset save state
adb shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
```

scrcpy mirrors the device window: `scrcpy --serial emulator-5554`.

---

## Branch + commit conventions

- **Active branch:** `claude/practical-swanson-4b6468`. All work happens
  here. No direct commits to `main`.
- **Push immediately after every commit.** This is established cadence;
  do not wait to batch.
- **Conventional Commits format.** `feat(scope): ...`, `fix(scope): ...`,
  `docs(scope): ...`, `test(scope): ...`, `chore(scope): ...`. Scope is
  the affected area (e.g., `viewer`, `nova-agent`, `product`, `methodology`).
  Subject ≤72 chars; body explains the *why* not the *what*.
- **Co-author tag** on Claude-generated commits:
  `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- **Atomic commits.** One logical change per commit. If you find yourself
  writing "and" in the subject, split it.

### Gitleaks pre-commit

The repo has a gitleaks pre-commit hook (now formalized in
`.pre-commit-config.yaml`). Don't disable it. If it screams about a
"secret," treat it as serious until you've inspected the line.

---

## Quality gates (must pass before commit)

For Python changes: `pytest + mypy strict + ruff check + gitleaks`. For
TypeScript changes: `vitest + tsc --noEmit + eslint + gitleaks`.

**Never green-skip.** If a test breaks, fix it or update it deliberately
with a commit message explaining why. The `--no-verify` flag is forbidden
without explicit user permission.

The pre-commit framework (`.pre-commit-config.yaml`) auto-runs these on
staged files. CI (`.github/workflows/ci.yml`) re-runs the full suite on
every push and PR.

### Pre-commit checklist (Claude pair)

`.claude/pre-commit-checklist.md` is a per-commit checklist that the
pre-commit framework enforces: any `- [ ]` (unchecked) item **blocks the
commit**. After a successful commit, the post-commit hook auto-resets
every box back to `- [ ]` so the next commit starts fresh.

Pattern adopted from the Gibor app workflow. Catches the failure mode of
"Claude commits without verifying" by making verification a physical
artifact, not a vibes-based discipline.

**First-time setup per clone** (one-shot):

```bash
pre-commit install                      # installs the standard hooks
pre-commit install --hook-type commit-msg
pre-commit install --hook-type post-commit  # required for the auto-reset
```

If a checklist item legitimately doesn't apply, check the box and add a
one-sentence reason inline (e.g. `- [x] /review — skipped, doc-only
change`). Silent skipping is forbidden.

---

## Common gotchas (have already cost time)

1. **UF_HIDDEN venv issue.** Repo on `~/Desktop` → macOS hides editable
   `.pth` files → Python 3.14 skips them → `uv run nova` fails. Fix:
   `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"`.
   Documented in `nova-agent/README.md`.
2. **Gemini Pro 1000 RPD limit.** Pro daily quota exhausts after ~250
   ToT calls (4 branches per call). Active workaround in `.env`:
   `NOVA_DELIBERATION_MODEL=gemini-2.5-flash` (overrides Pro for ToT).
3. **Empty shell env vars shadow `.env`.** Pydantic-settings reads
   process env first, `.env` second. If a shell exports
   `ANTHROPIC_API_KEY=""` (empty), it shadows the populated `.env`.
   Fixed via `env_ignore_empty=True` in `Settings` config; if you see
   confusing "no API key" errors, check `printenv | grep ANTHROPIC`.
4. **Anthropic API requires actual paid credits, not just grants.**
   "Credit grant" rows on console.anthropic.com don't unlock the API.
   Need a real Stripe purchase ("Credit purchase" row, status "Paid").
5. **Unity 2048 fork ignores `adb shell input swipe`.** Only DPAD
   keyevents (19/20/21/22) work. `ADB.swipe()` in nova-agent already
   uses keyevents internally.
6. **OCR palette must match the Unity fork colors.** Empirically
   sampled. If new tile values appear that aren't in `_PALETTE` (in
   `nova_agent/perception/ocr.py`), nearest-neighbor classifier maps
   them to wrong values and the agent's perception goes silently wrong.
   Currently sampled: 0/2/4/8/16/32/128. 64 and 256 unsampled.
7. **`pm clear` doesn't reset Unity 2048 save state.** Unity stores
   game state outside app data. Cold-boot the AVD to fully reset.
8. **The viewer uses `pnpm`, not `npm`.** `npm install` crashes on the
   existing pnpm node_modules. Don't run npm here.
9. **AgentEvent type catch-all defeats discriminated narrowing.** The
   `{event: string; data: unknown}` arm in the union means TypeScript
   narrowing doesn't work; we use `as data as` casts in `deriveStream.ts`.
   This is being fixed in Week 0 Day 1; until then, be aware.

---

## Pre-task checklist (use for any non-trivial change)

Before starting work on a non-trivial change:

- [ ] Read [`docs/product/methodology.md`](./docs/product/methodology.md)
      if the change touches the cognitive architecture
- [ ] Read [`docs/product/product-roadmap.md`](./docs/product/product-roadmap.md)
      to confirm which phase this work belongs to
- [ ] Confirm there's a planning artifact (spec, ADR, or roadmap entry).
      If none exists, write one before coding.
- [ ] Check [`docs/decisions/`](./docs/decisions/) for relevant ADRs
- [ ] Confirm tests exist or will be written (TDD discipline)
- [ ] Confirm the change has a clear acceptance criterion
- [ ] Branch state check: `git status` — no uncommitted work from prior session

For larger changes, use the workflow:

1. **Brainstorm** — `superpowers:brainstorming` skill if creating new
   surface area
2. **Plan** — `superpowers:writing-plans` skill for multi-step work
3. **Implement** — `superpowers:subagent-driven-development` skill for
   dispatching fresh subagents per task with formal review cycles
4. **Verify** — pytest + mypy + ruff (Python) or vitest + tsc + lint
   (TS) before commit
5. **Commit** — atomic, conventional, with co-author tag, push immediately

---

## Things to NOT do

- **Don't pivot to RL.** RL produces optimizers; Nova produces
  simulators. The cognitive architecture is the moat. See
  `docs/product/methodology.md` §3.3 for full rationale.
- **Don't issue Jira-style bug reports.** Bug-handling stays in
  `docs/internal/v2.2-epsilon-spec.txt` until promoted (Week 4+,
  gated on Phase 0.7 + 0.8 passes).
- **Don't promise real-time games or 3D.** Out of scope for the
  current architecture.
- **Don't pivot mid-Phase.** Each phase has a defined exit criterion.
  Mid-phase pivots compound complexity.
- **Don't sell before Phase 0.7 passes.** No pitch conversations until
  the cliff test demonstrates affect predicts (or doesn't).
- **Don't invent dollar figures in reports.** No "fix this bug or
  lose $10K UA spend" claims. Hand the studio observable cohort data
  and let them compute UA-spend impact themselves.
- **Don't direct-commit to `main`.** All work via PRs from feature
  branches. (Currently `claude/practical-swanson-4b6468` IS the
  feature branch; eventual cleanup will retarget at `main`.)
- **Don't `--no-verify` skip pre-commit hooks.** Treat hook failures
  as real failures; fix the issue, then commit.
- **Don't skip the `Read` tool before `Edit`.** Edit will fail if you
  haven't read the file in this session, and the discipline catches
  stale-write bugs.

---

## Active phase + next task

**As of 2026-05-02:** Week 0 of the 30-day validation sprint
about to begin. v1.0.0 demo + AgentEvent type cleanup + demo
recording pending. See [`docs/product/product-roadmap.md`](./docs/product/product-roadmap.md)
"30-day validation sprint" section for the day-by-day plan.

**Tomorrow morning's first task:** dispatch a research agent on
**CasterAI** (the AI red-team flagged them as a real competitor in
the persona/affect simulation space). Output to
`docs/product/casterai-deep-dive.md`. While that runs, scaffold the
AgentEvent runtime validator (remove `{event: string; data: unknown}`
catch-all + add hand-written predicates in `useNovaSocket`).

Detailed pickup state lives in
`~/.claude/projects/-Users-idohoresh-Desktop-a/memory/project_nova_resume_point.md`.

---

## When in doubt

- Architecture questions → [`ARCHITECTURE.md`](./ARCHITECTURE.md) +
  [`docs/product/methodology.md`](./docs/product/methodology.md)
- Strategic / business questions → [`docs/product/README.md`](./docs/product/README.md)
- Roadmap / phase questions → [`docs/product/product-roadmap.md`](./docs/product/product-roadmap.md)
- Decision history → [`docs/decisions/`](./docs/decisions/)
- Build/test commands → this file (above)
- Common gotchas → this file (above)
- Memory across sessions → `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/`

When still unclear, ask the user explicitly. Don't guess on
load-bearing decisions.
