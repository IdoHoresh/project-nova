# Workflow Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the 10-change workflow-simplification batch agreed in `docs/superpowers/specs/2026-05-07-workflow-simplification-design.md` — cut per-turn context load and token cost ~40–55% while holding the current quality bar.

**Architecture:** Pure config / doc / slash-command changes. No production code. Verification model = JSON/YAML parse checks, line counts, slash-command dry-runs, GitHub Actions workflow validation, post-merge Layer 2 BLOCK-rate observation. One atomic commit per task → 10 commits → one PR for the entire batch.

**Tech Stack:** Markdown (CLAUDE.md, workflow.md, slash commands), JSON (Claude Code settings.json), YAML (.github workflows, .pre-commit-config.yaml), bash scripts, Claude Code memory files (frontmatter + markdown).

**Branch:** Current — `claude/methodology-trauma-rewrite`. Do NOT commit to `main`.

**Pre-flight:**

```bash
cd /Users/idohoresh/Desktop/a
git branch --show-current   # expect: claude/methodology-trauma-rewrite
git status                   # expect: only the spec + LESSONS.md edits from the design phase pending or already committed
```

If the design spec edits + LESSONS.md edit from the design phase are not yet committed, commit them as Task -1 (one combined `docs:` commit) before starting Task 0.

**Two deviations from the spec doc, flagged for awareness:**

1. **Task 6 home.** Spec Section 5 Step 6 says `.claude/settings.local.json` (gitignored). This plan moves it to the committed `.claude/settings.json` `env` field instead, so the change is git-revertable consistent with the Section 10 ordered-rollback procedure. Solo-dev context = settings.local.json's "personal override" framing does not apply.
2. **Task 7 rollback mechanism.** Spec Section 10 says "git revert <Step 7 sha>" but `feedback_session_model_selection.md` is a Claude Code memory file (path-mangled, NOT in git). The rollback for Task 7 is therefore a manual file edit, not git revert. Plan documents the manual revert command. The spec's intent (revert order + diagnostic loop) is preserved.

Both deviations are paragraph-level and do not require re-approval. They get captured as a footnote to LESSONS.md after the batch lands.

---

## File structure

| File | Task | Action |
|------|------|--------|
| `CLAUDE.md` | Task 0, Task 9 | modify (insert section, then trim whole) |
| `.claude/pre-commit-checklist.md` | Task 1 | delete |
| `scripts/check-claude-checklist.sh` | Task 1 | delete |
| `scripts/reset-checklist.sh` | Task 1 | delete |
| `.pre-commit-config.yaml` | Task 1 | modify (remove local checklist hooks block) |
| `.claude/settings.json` | Task 2, Task 6 | modify (drop Haiku push-gate hook; add `env` field) |
| `.claude/commands/commit-push-pr.md` | Task 3 | create |
| `.claude/commands/handoff.md` | Task 4 | create |
| `docs/superpowers/handoffs/.gitkeep` | Task 4 | create (handoff dir) |
| `.github/workflows/claude-review.yml` | Task 5 | modify (split into two jobs) |
| `~/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md` | Task 7 | modify (default Sonnet 200k) |
| `.claude/rules/workflow.md` | Task 8 | rewrite (≤80 lines) |

---

## Task 0: Insert model-escalation trigger table into CLAUDE.md

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/CLAUDE.md`

**Why:** Default model is moving from Sonnet[1m] to Sonnet 200k (Task 7). User needs binary triggers Sonnet can match against to surface "swap to Opus" recommendations before starting heavy work. Three-layer defense: Layer 1 (skill auto-block, existing) + Layer 2 (this trigger table) + Layer 3 (user-side 30-second pre-task ritual).

**Insertion anchor:** end of the existing `## When to use which skill` section, immediately before `## Active phase + next task`.

- [ ] **Step 1: Locate insertion anchor**

```bash
grep -n "^## Active phase + next task" /Users/idohoresh/Desktop/a/CLAUDE.md
```

Expected: one line number. Insertion goes immediately before that line, with a blank line separating sections.

- [ ] **Step 2: Insert the trigger section**

Use the Edit tool with `old_string` matching the closing line of the "When to use which skill" section + the section break before "Active phase + next task". The content to insert is exactly:

```markdown
---

## Model escalation — when Sonnet must offer swap to Opus

Sonnet 4.6 is the default. Before starting a task, Claude must check
the triggers below. If ANY trigger fires, surface a swap recommendation
and WAIT for the user to run `/model claude-opus-4-7[1m]` before
continuing. Triggers are binary path-or-keyword signals, NOT judgment.

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

If unsure → Sonnet asks the user before starting. After a Path A task
completes, Sonnet reminds: `/model claude-sonnet-4-6` to swap back.

Source of truth for path-vs-skill mapping detail:
`feedback_session_model_selection.md` memory.
```

- [ ] **Step 3: Verify insertion**

```bash
grep -A 2 "^## Model escalation" /Users/idohoresh/Desktop/a/CLAUDE.md | head -5
wc -l /Users/idohoresh/Desktop/a/CLAUDE.md
```

Expected: section header found; line count up by ~28 from prior baseline.

- [ ] **Step 4: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(claude): add model-escalation trigger table

Binary path-or-keyword signals Sonnet matches against to surface
"swap to Opus" recommendations before starting heavy work. Layer
2 of the three-layer defense (skill auto-block + trigger table +
user pre-task ritual). Step 0 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit succeeds, pre-commit hooks green, push succeeds.

---

## Task 1: Delete pre-commit-checklist + post-commit reset hook

**Files:**
- Delete: `/Users/idohoresh/Desktop/a/.claude/pre-commit-checklist.md`
- Delete: `/Users/idohoresh/Desktop/a/scripts/check-claude-checklist.sh`
- Delete: `/Users/idohoresh/Desktop/a/scripts/reset-checklist.sh`
- Modify: `/Users/idohoresh/Desktop/a/.pre-commit-config.yaml`

**Why:** The free pre-commit hooks (`gitleaks`, `ruff`, `mypy`, `biome`, `tsc`, `conventional-pre-commit`) already enforce the substantive checks. The Claude-specific checklist + the post-commit reset hook + the two enforcement scripts are ceremony police that add friction on a one-person team without proportionate quality lift.

- [ ] **Step 1: Delete the three files**

```bash
cd /Users/idohoresh/Desktop/a
git rm .claude/pre-commit-checklist.md
git rm scripts/check-claude-checklist.sh
git rm scripts/reset-checklist.sh
```

Expected: three `rm` lines printed. Files removed from index.

- [ ] **Step 2: Remove the local hook block from .pre-commit-config.yaml**

Use the Edit tool. The block to remove (lines starting at the comment header `# ─── Claude Code pre-commit checklist enforcement ──`) covers:

- The full comment block (5 lines including blank lines)
- The `- repo: local` block with the two hooks (`claude-checklist-check` + `claude-checklist-reset`)

Old string to match (exact, multi-line):

```
  # ─── Claude Code pre-commit checklist enforcement ──────────────────────────
  # Blocks commits if any item in .claude/pre-commit-checklist.md is unchecked,
  # then resets the checklist after a successful commit. Pattern adopted from
  # the Gibor app workflow.
  #
  # First-time setup (per clone): the post-commit hook needs explicit install:
  #   pre-commit install --hook-type post-commit
  - repo: local
    hooks:
      - id: claude-checklist-check
        name: Claude pre-commit checklist (block on unchecked)
        language: system
        pass_filenames: false
        always_run: true
        entry: bash scripts/check-claude-checklist.sh

      - id: claude-checklist-reset
        name: Claude pre-commit checklist (reset after commit)
        language: system
        pass_filenames: false
        always_run: true
        stages: [post-commit]
        entry: bash scripts/reset-checklist.sh

```

Replace with empty string. Keep the surrounding `# Default settings` block intact.

- [ ] **Step 3: Validate the YAML still parses**

```bash
cd /Users/idohoresh/Desktop/a
python3 -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))" && echo "YAML valid"
pre-commit validate-config 2>&1 | tail -3
```

Expected: `YAML valid` printed; `pre-commit validate-config` exits clean (or prints a "validates against schema" message — depends on pre-commit version).

- [ ] **Step 4: Optionally uninstall the post-commit hook**

```bash
pre-commit uninstall --hook-type post-commit 2>&1 | head -3
```

Expected: removes `.git/hooks/post-commit` if it was installed. Skip if it errors — the hook will simply no-op without a config to call.

- [ ] **Step 5: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .pre-commit-config.yaml
git commit -m "$(cat <<'EOF'
chore(workflow): drop pre-commit-checklist + reset hook

Remove .claude/pre-commit-checklist.md, the post-commit reset
hook, and the two enforcement scripts. Free pre-commit hooks
(gitleaks, ruff, mypy, eslint, tsc, conventional-pre-commit)
cover the substantive checks. The Claude-specific checklist was
ceremony for a one-person team with no proportionate quality
lift. Step 1 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit succeeds (the deleted check-claude-checklist hook can no longer block its own removal commit because the file it checks is gone in this same commit; pre-commit framework handles missing-hook-script gracefully). Push succeeds.

---

## Task 2: Drop Layer 1.5 Haiku push-gate

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/.claude/settings.json`

**Why:** LLM-per-push burns tokens for marginal lift over the deterministic command portion. Layer 2 (Opus on PR open) catches architectural drift better at the coherent-diff scope. Keep the deterministic portion (regex secret grep + diff stat) and the PR-cadence + post-merge `/clear`-hint hooks. Drop the agent-type Haiku hook only.

- [ ] **Step 1: Verify current settings.json structure**

```bash
cd /Users/idohoresh/Desktop/a
jq '.hooks.PreToolUse[0].hooks | length' .claude/settings.json
```

Expected: `4` (four hooks under the Bash matcher: deterministic command, agent Haiku gate, PR-overdue check, post-merge clear hint).

- [ ] **Step 2: Remove the agent-type hook**

Use the Edit tool. Remove the entire JSON object spanning from `{` of the agent-type hook through its closing `},`, identified by the field `"type": "agent"` and the model `"claude-haiku-4-5-20251001"`. The block to delete starts immediately after the closing `},` of the first command hook and ends immediately before the next command hook (the PR-overdue one).

Old string to match in `.claude/settings.json` (the complete second hook object plus its trailing comma):

```
          {
            "type": "agent",
            "if": "Bash(git push:*)",
            "model": "claude-haiku-4-5-20251001",
            "prompt": "Pre-push architectural gate for Project Nova. Run fast — most pushes will be clean and exit early.\n\n1. Check upstream exists: `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null`. Empty → output {\"continue\":true,\"systemMessage\":\"no upstream — Haiku gate skipped\"} and stop.\n2. Count changed lines: `git diff @{u}..HEAD --numstat 2>/dev/null | awk '{s+=$1+$2} END {print s+0}'`. Store as LINES.\n3. Check cognitive paths: `git diff @{u}..HEAD --name-only 2>/dev/null | grep -cE 'nova_agent/(llm|perception|memory|bus)|AgentEvent|MemoryCoordinator'`. Store as COG.\n4. If LINES < 80 AND COG is 0 → output {\"continue\":true,\"systemMessage\":\"diff <80 lines, no cognitive paths — Haiku gate skipped\"} and stop.\n5. Run `git diff @{u}..HEAD` and scan for: (a) secrets gitleaks may miss — base64-dense 20+ char strings, key/token/secret assigned non-env-var values; (b) game logic leaking into cognitive layer — tile values/board arrays/score math in nova_agent/ outside game adapter; (c) MemoryCoordinator bypass — direct lancedb/sqlite write outside coordinator; (d) bus contract gap — new event type without matching TypeScript discriminated-union entry; (e) load-bearing seam (new Protocol/subsystem) without ADR reference in commit.\n6. CRITICAL = real secret committed or cognitive-layer crash bug. WARN = architectural drift, bus gap, missing ADR.\n7. Output JSON only, no prose:\n   - CRITICAL: {\"continue\":false,\"stopReason\":\"<one line>\",\"systemMessage\":\"<file:line + brief>\"}\n   - Otherwise: {\"continue\":true,\"systemMessage\":\"Haiku gate: <N> lines, <M> cognitive paths. <WARN findings or clean>\"}",
            "timeout": 60,
            "statusMessage": "Haiku architectural gate (large/cognitive diffs)..."
          },
```

Replace with empty string. Make sure the resulting JSON keeps the comma-separation correct between the remaining hooks.

- [ ] **Step 3: Validate JSON parse**

```bash
cd /Users/idohoresh/Desktop/a
jq . .claude/settings.json > /dev/null && echo "JSON valid"
jq '.hooks.PreToolUse[0].hooks | length' .claude/settings.json
jq '[.hooks.PreToolUse[0].hooks[] | .type] | sort | unique' .claude/settings.json
```

Expected: `JSON valid`; hook count = 3; types = `["command"]` only (no `"agent"` left).

- [ ] **Step 4: Update the explanatory `_hooks_explanation` string**

Use the Edit tool to replace the existing `_hooks_explanation` value with one that no longer references the Haiku gate. New string:

```
"Pre-commit framework (.pre-commit-config.yaml) handles formatting + linting + gitleaks on commit; CI (.github/workflows/ci.yml) handles full test/lint/type runs on push. The pre-push command hook is a fast deterministic gate: regex secret grep + diff stat + PR-cadence warning + post-merge /clear hint. No LLM agent runs at push time — token cost ~$0/push. Quality judgment (logic bugs, missing tests, design issues) is deferred to Layer 2 (Opus 4.7) at PR open, where it earns its keep on a coherent diff. PostToolUse formatters intentionally NOT added — they create read/write race conditions with Claude's edit cycle. Personal hooks can be added in settings.local.json."
```

- [ ] **Step 5: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .claude/settings.json
git commit -m "$(cat <<'EOF'
chore(hooks): drop Layer 1.5 Haiku push-gate

Remove the agent-type pre-push hook (claude-haiku-4-5) from
.claude/settings.json. Keep the deterministic command portion
(secret grep, diff stat, PR-overdue warning, post-merge /clear
hint). LLM-per-push burns tokens for marginal lift; Layer 2
(Opus on PR open) catches architectural drift better at the
coherent-diff scope. Step 2 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed. The deterministic command hook still runs on this push and reports its usual stat.

---

## Task 3: Add /commit-push-pr slash command

**Files:**
- Create: `/Users/idohoresh/Desktop/a/.claude/commands/commit-push-pr.md`

**Why:** Boris Cherny pattern — single command runs `git status` + `git diff --cached` + commit (Conventional Commits + co-author tag) + push, with optional PR-open. Replaces 14-step pre-commit ceremony with one invocation.

- [ ] **Step 1: Create the command file**

Use the Write tool to create `/Users/idohoresh/Desktop/a/.claude/commands/commit-push-pr.md` with this exact content:

```markdown
---
description: Stage, commit, and push the current change in one shot. Generates a Conventional Commits message from the staged diff. Optionally opens a PR if the branch has commits ahead of origin/main and no open PR exists.
allowed-tools: Bash, Read, Edit
---

Run the full ship sequence in one shot. Each step gates on the prior step's output.

**Steps:**

1. Show repo state in parallel:
   ```bash
   git status
   git diff --cached --stat
   git log --oneline -5
   ```
   If `git diff --cached` is empty, stop and tell the user "nothing staged — `git add <files>` first."

2. Scan the staged diff for secrets:
   ```bash
   git diff --cached | grep -E '^[+].*(ANTHROPIC_API_KEY|OPENAI_API_KEY|sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{35}|aws_(access|secret)_key|password\s*=\s*"[^"]')' | head -5
   ```
   Any match → STOP and surface to the user. Do not proceed without explicit "ignore, push anyway" instruction.

3. Read CLAUDE.md, REVIEW.md, and `.claude/rules/workflow.md` for current conventions.

4. Read the staged diff in full:
   ```bash
   git diff --cached
   ```

5. Apply REVIEW.md path-matched trigger taxonomy. If a "yes" row matches and the diff is non-trivial, recommend the user run `/review` before proceeding (skip if user has already done so this session).

6. Generate a Conventional Commits subject (≤72 chars) and a body that explains *why* not *what*. Format:
   ```
   type(scope): subject

   Body explaining motivation. Reference any ADR, spec, or methodology
   doc when applicable.

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```

   `type` ∈ {feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert}. If subject contains "and" or "plus", split into multiple commits.

7. Show the proposed commit message to the user. Wait for confirmation. If confirmed, commit:
   ```bash
   git commit -m "$(cat <<'EOF'
   <generated message here>
   EOF
   )"
   ```

8. Push immediately:
   ```bash
   git push
   ```

9. Check PR cadence:
   ```bash
   ahead=$(git rev-list --count origin/main..HEAD)
   branch=$(git branch --show-current)
   pr_open=$(gh pr list --head "$branch" --state open --json number --jq 'length')
   ```

   If `ahead > 0` AND `pr_open = 0` AND the branch is at a coherent unit per workflow.md "PR cadence" section, surface to the user: "Branch has $ahead commits ahead of origin/main with no open PR. Open one? (`gh pr create --base main`)"

10. After successful push, surface the `/clear` recommendation per CLAUDE.md "Context hygiene":
    > "/clear recommended — commit + push complete. Handoff: `Last shipped: <new sha + 1-line>. Next: <task from resume-point memory>. Read: CLAUDE.md, resume-point memory, git log --oneline -10`"

**When to invoke this command:**

- Any non-trivial change ready to ship (single coherent commit).
- Replaces the 14-step pre-commit ceremony.

**When NOT to invoke this command:**

- Mid-feature work that should be batched (commit incrementally with `git commit` directly; use `/commit-push-pr` only for the final shippable commit of the unit).
- WIP that may be reordered or squashed later.
```

- [ ] **Step 2: Verify file exists and frontmatter is valid**

```bash
cd /Users/idohoresh/Desktop/a
head -5 .claude/commands/commit-push-pr.md
wc -l .claude/commands/commit-push-pr.md
```

Expected: frontmatter `--- description: ... allowed-tools: ... ---`; line count ~70.

- [ ] **Step 3: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .claude/commands/commit-push-pr.md
git commit -m "$(cat <<'EOF'
feat(commands): add /commit-push-pr slash command

One-shot ship sequence: status + diff scan + secret grep + REVIEW
trigger check + generated Conventional Commits message + commit
+ push + PR-cadence check + /clear recommendation. Replaces the
14-step pre-commit ceremony with a single command. Boris Cherny
pattern. Step 3 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed.

---

## Task 4: Add /handoff slash command

**Files:**
- Create: `/Users/idohoresh/Desktop/a/.claude/commands/handoff.md`
- Create: `/Users/idohoresh/Desktop/a/docs/superpowers/handoffs/.gitkeep`

**Why:** Replace ad-hoc handoff prose at every artifact-cliff `/clear` with a single command. Format already specified in `feedback_session_hygiene.md` memory. Memory-path fragility (per LESSONS.md addition) handled by writing the handoff to BOTH a portable git-tracked artifact (`docs/superpowers/handoffs/<timestamp>.md`) AND the memory file — redundant but resilient.

- [ ] **Step 1: Create the handoffs directory + .gitkeep**

```bash
cd /Users/idohoresh/Desktop/a
mkdir -p docs/superpowers/handoffs
touch docs/superpowers/handoffs/.gitkeep
```

Expected: directory + empty `.gitkeep` file created.

- [ ] **Step 2: Create the slash command file**

Use the Write tool to create `/Users/idohoresh/Desktop/a/.claude/commands/handoff.md` with this exact content:

```markdown
---
description: Write a Context Checkpoint handoff before /clear. Captures architectural intent, edge-case warnings, rejected alternatives, and what's next. Writes to BOTH the project's git-tracked handoffs directory AND the Claude Code memory file. Use at every artifact-cliff /clear (post-commit, post-PR-merge, post-spec, post-plan).
allowed-tools: Bash, Read, Write, Edit
---

Generate a Context Checkpoint handoff and write it to two locations for resilience.

**Steps:**

1. Resolve the project root and the memory directory:
   ```bash
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   # Path-mangle the project root: replace / with - for Claude Code's memory dir naming convention
   MANGLED=$(echo "$PROJECT_ROOT" | sed 's|/|-|g')
   MEMORY_DIR="$HOME/.claude/projects/$MANGLED/memory"
   RESUME_FILE="$MEMORY_DIR/project_nova_resume_point.md"
   ```
   If `MEMORY_DIR` does not exist, fall back to writing only the portable artifact and surface a warning.

2. Read recent git context in parallel:
   ```bash
   git log --oneline -10
   git status
   git diff --cached --stat
   ```

3. Read the active spec/plan if any:
   ```bash
   ls -t docs/superpowers/specs/*.md 2>/dev/null | head -1
   ls -t docs/superpowers/plans/*.md 2>/dev/null | head -1
   ```

4. Read the current resume-point memory:
   ```bash
   cat "$RESUME_FILE" 2>/dev/null
   ```

5. Compose the Context Checkpoint with this exact structure (per `feedback_session_hygiene.md` memory):

   ```markdown
   ## Context Checkpoint — YYYY-MM-DD HH:MM

   **Last shipped:** <commit sha> — <one-line summary>

   **Architectural intent:**
   <2–4 sentences capturing the *why* that the spec doesn't say. Why this
   approach over the rejected alternatives.>

   **Edge-case warnings:**
   <bulleted list of gotchas hit during the session: things that surprised
   us, things that almost broke, things future-Claude should pre-empt.>

   **Rejected alternatives:**
   <bulleted list of options considered + why we did not pick them. Each
   line: "<option> — <reason rejected>".>

   **What's next:**
   <1–3 sentences naming the next task with enough detail that a fresh
   session can resume without re-deriving context.>

   **Read first on resume:**
   - `CLAUDE.md`
   - `<active spec or plan path, if any>`
   - `git log --oneline -10`
   - <any other load-bearing artifact>
   ```

6. Generate a portable artifact filename:
   ```bash
   STAMP=$(date -u +%Y-%m-%d-%H%M)
   PORTABLE="$PROJECT_ROOT/docs/superpowers/handoffs/$STAMP-handoff.md"
   ```

7. Write the Context Checkpoint to the portable artifact (full content + frontmatter):
   ```markdown
   ---
   created: <ISO timestamp>
   branch: <git branch --show-current>
   sha: <last commit sha>
   ---

   <Context Checkpoint content from step 5>
   ```

8. Append the Context Checkpoint to the memory file (without frontmatter — memory file already has its own frontmatter):
   ```bash
   echo "" >> "$RESUME_FILE"
   echo "<Context Checkpoint content from step 5>" >> "$RESUME_FILE"
   ```

   If `MEMORY_DIR` does not exist (per step 1 fallback), skip this step and warn the user.

9. Surface the ready-to-paste `/clear` handoff prompt to the user:
   > "/clear recommended — handoff written to `<portable path>` and resume-point memory. Handoff prompt: `Last shipped: <sha + 1-line>. Next: <task>. Read: CLAUDE.md, <active spec/plan>, git log --oneline -10, $PORTABLE`"

10. Stage + commit the portable artifact:
    ```bash
    cd "$PROJECT_ROOT"
    git add "$PORTABLE"
    git commit -m "docs(handoff): context checkpoint $STAMP"
    git push
    ```

    Optional — skip the commit if the user prefers a single batched commit at end-of-session.

**When to invoke:**

- Before every `/clear` at an artifact-cliff (post-commit + push, post-PR-merge, post-spec, post-plan, ~2h continuous work).
- When switching to a different concern.

**When NOT to invoke:**

- Mid-task `/compact` — use `/compact` directly with a focused instruction.
- Trivial sessions where there is nothing non-obvious to capture.
```

- [ ] **Step 3: Verify command file**

```bash
cd /Users/idohoresh/Desktop/a
head -5 .claude/commands/handoff.md
ls -la docs/superpowers/handoffs/
```

Expected: frontmatter present; handoffs dir contains `.gitkeep`.

- [ ] **Step 4: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .claude/commands/handoff.md docs/superpowers/handoffs/.gitkeep
git commit -m "$(cat <<'EOF'
feat(commands): add /handoff slash command

Generate a Context Checkpoint at every artifact-cliff /clear and
write it to BOTH a portable git-tracked artifact in
docs/superpowers/handoffs/ AND the Claude Code memory file. Memory
paths are path-mangled per project location (LESSONS.md
2026-05-07); the dual-write makes the handoff resilient to project
relocation. Step 4 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed.

---

## Task 5: Path-filter Layer 2 PR action

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/.github/workflows/claude-review.yml`

**Why:** Today every PR triggers Opus 4.7 review job, even doc-only or non-cognitive PRs. Split into routine-review (Sonnet 4.6, runs on most PRs except doc-only) + deep-review (Opus 4.7, runs only on cognitive-layer / `.env*` paths). `.github/workflows/**` stays in routine-review (NOT excluded) so the safety net self-reviews per spec Section 5 Step 5 refinement.

- [ ] **Step 1: Read current workflow for the exact `jobs:` block**

```bash
cd /Users/idohoresh/Desktop/a
sed -n '/^jobs:/,$p' .github/workflows/claude-review.yml
```

Expected output: the `jobs:` block with one job named `review`.

- [ ] **Step 2: Replace the single job with two path-filtered jobs**

Use the Edit tool to replace the existing `jobs:` block (everything from `jobs:` to end of file) with this new content:

```yaml
jobs:
  routine-review:
    name: Nova /review (routine — Sonnet)
    runs-on: ubuntu-latest
    if: |
      github.event.pull_request.draft == false
    # Runs on MOST PRs. Excludes doc-only PRs (markdown / spec / plan) since
    # those have no code surface for Sonnet to review productively.
    # Intentionally INCLUDES .github/workflows/** so CI config self-reviews —
    # silent breakage of the deep-review path filter would otherwise go
    # undetected.
    steps:
      - name: Skip if doc-only
        id: doc-only-check
        run: |
          # Compute the changed paths against the base branch.
          git fetch origin "${{ github.base_ref }}" --depth=1
          changed=$(git diff --name-only "origin/${{ github.base_ref }}...HEAD")
          # If every changed file is doc-only, skip.
          non_doc=$(echo "$changed" | grep -vE '^(docs/|.*\.md$)' || true)
          if [ -z "$non_doc" ]; then
            echo "skip=true" >> "$GITHUB_OUTPUT"
          else
            echo "skip=false" >> "$GITHUB_OUTPUT"
          fi
        # Need the diff against base, so checkout first
      - name: Check out PR
        if: steps.doc-only-check.outputs.skip != 'true'
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run Claude routine review (Sonnet)
        if: steps.doc-only-check.outputs.skip != 'true'
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Run the Project Nova `/review` orchestrator on this pull
            request — routine pass.

            Steps:

            1. Read `REVIEW.md` at repo root for the rubric and the
               path-matched trigger taxonomy.
            2. Read `LESSONS.md` for known patterns and gotchas.
            3. Read `.claude/agents/code-reviewer.md` for the Nova-tuned
               code-review rubric.
            4. Get the PR diff via `git diff origin/${{ github.base_ref }}..HEAD`.
            5. Apply the REVIEW.md path-matched trigger taxonomy. For this
               routine pass, only run the code-reviewer rubric. Security
               concerns are handled by the deep-review job below.
            6. Post findings as a PR comment in the format:

               ```
               [SEVERITY] file:line — description
                 Suggestion: how to fix
                 Confidence: X/100
               ```

               Only report findings with confidence >= 80. Severities are
               BLOCK / WARN / NIT. End with a single verdict line:
               `APPROVE` or `REQUEST CHANGES`.

            This is **advisory** — do NOT block the PR merge.
          claude_args: "--model claude-sonnet-4-6 --allowed-tools Read,Grep,Glob,Bash"

  deep-review:
    name: Nova /review (deep — Opus)
    runs-on: ubuntu-latest
    if: |
      github.event.pull_request.draft == false
    # Runs only when paths match the cognitive-layer / config / secret surface
    # per REVIEW.md path-matched trigger taxonomy.
    steps:
      - name: Check out PR
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Detect cognitive / sensitive paths
        id: deep-paths-check
        run: |
          git fetch origin "${{ github.base_ref }}" --depth=1
          changed=$(git diff --name-only "origin/${{ github.base_ref }}...HEAD")
          # Match nova_agent cognitive paths or .env* files
          hits=$(echo "$changed" | grep -E '(nova_agent/(config|llm|bus|perception|memory)|^\.env)' || true)
          if [ -n "$hits" ]; then
            echo "fire=true" >> "$GITHUB_OUTPUT"
          else
            echo "fire=false" >> "$GITHUB_OUTPUT"
          fi
      - name: Run Claude deep review (Opus)
        if: steps.deep-paths-check.outputs.fire == 'true'
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Run the Project Nova `/review` orchestrator on this pull
            request — deep pass for cognitive-layer / config / secret
            surface.

            Steps:

            1. Read `REVIEW.md` at repo root.
            2. Read `LESSONS.md`.
            3. Read `.claude/agents/code-reviewer.md` AND
               `.claude/agents/security-reviewer.md` — both rubrics apply
               on this surface.
            4. Get the PR diff via `git diff origin/${{ github.base_ref }}..HEAD`.
            5. Run BOTH reviewer rubrics. The deep pass is the last
               automated check before human merge review; default to max
               recall.
            6. Post findings as a PR comment, separated by reviewer:

               ```
               === code-reviewer findings ===
               [SEVERITY] file:line — description
                 ...

               === security-reviewer findings ===
               [SEVERITY] file:line — description
                 ...
               ```

               Confidence >= 80 only. End with verdict line.

            Advisory — do NOT block the PR merge.
          claude_args: "--model claude-opus-4-7 --allowed-tools Read,Grep,Glob,Bash"
```

- [ ] **Step 3: Validate the YAML parses**

```bash
cd /Users/idohoresh/Desktop/a
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/claude-review.yml'))" && echo "YAML valid"
```

Expected: `YAML valid`. If this errors, fix indentation before commit.

- [ ] **Step 4: Optionally pre-validate via `gh actions list-syntax` (if available) or use the GitHub Actions VS Code extension before commit.** Skip if neither is set up.

- [ ] **Step 5: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .github/workflows/claude-review.yml
git commit -m "$(cat <<'EOF'
ci(review): split Layer 2 into routine (Sonnet) + deep (Opus)

Two jobs per PR. routine-review runs Sonnet 4.6 on most PRs
(excludes doc-only). deep-review runs Opus 4.7 only when paths
match nova_agent/{config,llm,bus,perception,memory}/** or .env*.
.github/workflows/** stays in routine-review so CI config self-
reviews. Mirrors REVIEW.md path-matched trigger taxonomy. Cuts
Layer 2 cost ~50–70% depending on PR mix while raising recall on
the highest-stakes paths (both jobs run on cognitive surface).
Step 5 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed. Push triggers GH Actions parsing — watch for syntax errors in the Actions tab.

- [ ] **Step 6: Smoke-test on the next PR**

After Task 9 (and before declaring batch shipped), open the PR for this batch. Confirm both jobs trigger as expected: deep-review fires (`.claude/settings.json` is touched in Task 2 + Task 6, but it's not in `nova_agent/**` so it should NOT fire deep-review based on path filter; routine-review should fire). Verify by watching the Actions tab on the PR.

Expected behaviors on this batch's PR:
- routine-review: fires (not doc-only — touches `.github/workflows/`, `.claude/`, `CLAUDE.md`, etc.)
- deep-review: should NOT fire (no paths match `nova_agent/(config|llm|bus|perception|memory)` or `.env*`)

If deep-review fires unexpectedly, the path-detection logic has a bug; fix before merging.

---

## Task 6: Default subagent model to Haiku 4.5

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/.claude/settings.json`

**Why:** Detailed plans + Haiku implementer is research-backed (Jesse Vincent, Superpowers 4). Falls back to Sonnet automatically if Haiku reports out-of-depth. Per-dispatch override (`model: "sonnet"`) covers cognitive-layer subagent tasks.

**Deviation from spec doc:** Spec said `.claude/settings.local.json`. This plan uses `.claude/settings.json` (committed) so the change is git-revertable per the Section 10 ordered-rollback procedure.

- [ ] **Step 1: Add a top-level `env` field to .claude/settings.json**

Use the Edit tool. The `env` field is added immediately after the `_comment` field at the top of the JSON object. Existing settings.json starts:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "_comment": "Team-wide Claude Code settings for Project Nova. COMMITTED. Personal overrides go in settings.local.json (gitignored). Read CLAUDE.md before adjusting this file.",
  "permissions": {
```

Old string to match (the `_comment` line plus the trailing comma plus newline plus `"permissions"`):

```
  "_comment": "Team-wide Claude Code settings for Project Nova. COMMITTED. Personal overrides go in settings.local.json (gitignored). Read CLAUDE.md before adjusting this file.",
  "permissions": {
```

New string:

```
  "_comment": "Team-wide Claude Code settings for Project Nova. COMMITTED. Personal overrides go in settings.local.json (gitignored). Read CLAUDE.md before adjusting this file.",
  "env": {
    "_comment": "Default subagent model = Haiku 4.5. Detailed plans + Haiku implementer = competent + cheap (Superpowers 4 / Jesse Vincent). Per-dispatch override `model: \"sonnet\"` for cognitive-layer subagent tasks. Falls back to Sonnet automatically if Haiku reports out-of-depth.",
    "CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4-5-20251001"
  },
  "permissions": {
```

- [ ] **Step 2: Validate JSON**

```bash
cd /Users/idohoresh/Desktop/a
jq . .claude/settings.json > /dev/null && echo "JSON valid"
jq '.env.CLAUDE_CODE_SUBAGENT_MODEL' .claude/settings.json
```

Expected: `JSON valid`; output `"claude-haiku-4-5-20251001"`.

- [ ] **Step 3: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .claude/settings.json
git commit -m "$(cat <<'EOF'
chore(settings): default subagent model = Haiku 4.5

Add CLAUDE_CODE_SUBAGENT_MODEL=claude-haiku-4-5-20251001 to
.claude/settings.json env. Detailed plans + Haiku implementer is
research-backed (Superpowers 4); falls back to Sonnet
automatically if Haiku reports out-of-depth. Per-dispatch
override `model: "sonnet"` for cognitive-layer subagent tasks.
Estimated ~70% cut on implementer subagent token cost. Step 6 of
workflow-simplification batch — paired with Step 7 under the
ordered-rollback procedure (revert this commit FIRST if Section
9 trigger fires, since this is the higher-variance change).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed.

---

## Task 7: Update memory file — default Sonnet 200k

**Files:**
- Modify: `/Users/idohoresh/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md`

**Why:** Default main session model moves from `claude-sonnet-4-6[1m]` to `claude-sonnet-4-6` (200k context). 1M tier = per-token premium; ~95% of Nova work fits 200k. Escalate to `[1m]` only when actively reasoning across nova-agent + nova-viewer + Unity simultaneously.

**Note:** Memory files are NOT in git (path is mangled and lives under `~/.claude/projects/`). Rollback for this task is a manual file edit, NOT git revert. Plan documents the manual revert command at end of task.

- [ ] **Step 1: Verify the memory file exists**

```bash
ls -la "$HOME/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md"
```

Expected: file exists.

- [ ] **Step 2: Edit the memory file's frontmatter `description` and the body**

Use the Edit tool. Two edits:

(a) Replace the `description` line:

Old:
```
description: Default main session model is Sonnet 4.6 1M context. Opus 4.7 is used via two paths — Path A (manual /model swap) for live brainstorming/planning; Path B (subagent dispatch with model="opus") for one-shot deep work. User-approved 2026-05-06 after multi-round red-team and a fresh-eyes simplification pass.
```

New:
```
description: Default main session model is Sonnet 4.6 (200k context). 1M tier reserved for cross-subsystem reasoning (rare). Opus 4.7 via two paths — Path A (manual /model swap) for live brainstorming/planning; Path B (subagent dispatch with model="opus") for one-shot deep work. Updated 2026-05-07 per workflow-simplification batch.
```

(b) Replace the opening body line:

Old:
```
**Default main session model:** `claude-sonnet-4-6[1m]` (Sonnet 4.6 with 1M context). Set in personal `.claude/settings.local.json` `"model"` field (project-scope, gitignored). Confirms via system prompt at session start.
```

New:
```
**Default main session model:** `claude-sonnet-4-6` (Sonnet 4.6, 200k context). Set in personal `.claude/settings.local.json` `"model"` field (project-scope, gitignored). Confirms via system prompt at session start.

**Escalation to 1M tier (`claude-sonnet-4-6[1m]`):** reserved for cross-subsystem reasoning where context spans nova-agent + nova-viewer + Unity simultaneously, OR for spec/plan work that genuinely exceeds 200k. Cost: per-token premium on the 1M tier. ~95% of Nova work fits 200k; treat 1M as a conscious escalation, not a default.
```

- [ ] **Step 3: Verify memory file edits**

```bash
grep -A 1 "^description:" "$HOME/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md" | head -3
grep "^**Default main session model:**" "$HOME/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md"
```

Expected: description line shows the new text; body line shows `claude-sonnet-4-6` (without `[1m]`).

- [ ] **Step 4: Update local Claude Code default model**

The user's actual default model is set in `.claude/settings.local.json` (gitignored, personal). Edit that file's `"model"` field:

```bash
cat /Users/idohoresh/Desktop/a/.claude/settings.local.json 2>/dev/null
```

If file does NOT exist, create it:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "_comment": "Personal overrides for Project Nova. Gitignored.",
  "model": "claude-sonnet-4-6"
}
```

If file EXISTS, edit the `"model"` field to `"claude-sonnet-4-6"` (without `[1m]`). Validate JSON.

- [ ] **Step 5: Commit (memory file is NOT in git, but settings.local.json is gitignored too — there is nothing to commit for this task)**

Track this task as a "no-commit" entry in the PR description. The diff visible at PR open will skip Task 7 since memory + settings.local.json are both untracked.

**Manual rollback command (for spec Section 10 ordered-rollback procedure step 3):**

```bash
# Memory file revert
sed -i.bak 's|claude-sonnet-4-6\b|claude-sonnet-4-6[1m]|g' "$HOME/.claude/projects/-Users-idohoresh-Desktop-a/memory/feedback_session_model_selection.md"
# settings.local.json revert
jq '.model = "claude-sonnet-4-6[1m]"' /Users/idohoresh/Desktop/a/.claude/settings.local.json > /tmp/settings.local.json.tmp
mv /tmp/settings.local.json.tmp /Users/idohoresh/Desktop/a/.claude/settings.local.json
```

Document this revert in the PR description so it is recoverable post-merge.

---

## Task 8: Rewrite workflow.md lean (≤80 lines)

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/.claude/rules/workflow.md`

**Why:** Current 234 lines, no tier separation, every step "ABSOLUTE — never skip." Restore signal. Tier-1 invariants only; Tier-2 stuff demoted to references in CLAUDE.md or REVIEW.md or deleted (covered by hooks already).

- [ ] **Step 1: Read the current workflow.md to anchor the rewrite**

```bash
wc -l /Users/idohoresh/Desktop/a/.claude/rules/workflow.md
head -20 /Users/idohoresh/Desktop/a/.claude/rules/workflow.md
```

Expected: ~234 lines.

- [ ] **Step 2: Replace the entire file with the new lean version**

Use the Write tool to fully overwrite `/Users/idohoresh/Desktop/a/.claude/rules/workflow.md` with this exact content (target ≤80 lines):

```markdown
# Workflow Rules — Project Nova

> Single-developer workflow. Tier-1 invariants are load-bearing — never
> skip. Tier-2 advisories are codified in `REVIEW.md`, the slash
> commands (`.claude/commands/`), and the pre-commit hook config. Do
> NOT duplicate them here. Two-strikes rule for new additions: only
> add a rule the second time the same mistake is corrected.

## Five-stage loop

```
Brainstorm → Plan → Implement (TDD) → Review → Ship
```

Per-stage skill mapping lives in `CLAUDE.md` "When to use which skill"
table. Per-stage model mapping lives in `CLAUDE.md` "Model
escalation — when Sonnet must offer swap to Opus" table.

## Tier-1 invariants (NEVER skip)

1. **Branch.** Confirm `git branch --show-current` is NOT `main`.
   Direct commits to `main` are forbidden by branch protection;
   confirm anyway.
2. **ADR for load-bearing decisions.** Architectural / product
   decisions get `docs/decisions/NNNN-<title>.md` BEFORE the
   implementation commit. Captures why, alternatives, consequences.
3. **TDD on cognitive layer.** Mandatory for `nova_agent/{llm,bus,
   memory,perception}/**`, decision logic, bus protocol changes.
   Failing test first, minimal implementation, refactor green.
4. **Atomic commits.** One logical change per commit. "and" in the
   subject means split.
5. **Conventional Commits.** `type(scope): subject ≤72 chars`. Body
   explains *why*, not *what*. Co-author tag on Claude commits:
   `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
6. **Push after every commit.** Established cadence — never batch.
7. **No `--no-verify`** without explicit user authorisation in the
   same session.
8. **`/clear` after every commit + push.** Claude MUST proactively
   surface the recommendation with a ready-to-paste handoff. Use
   `/handoff` to write the Context Checkpoint first at any artifact
   cliff (post-commit + push, post-PR-merge, post-spec, post-plan,
   ~2h continuous work).

## PR cadence — one PR per coherent unit

A unit is: one logical story, gate trio green at HEAD, natural
stopping point, a title that fits ≤70 chars without "and" / "plus".

Open a PR when the unit is shippable. Do NOT open a PR for mid-
feature work, gate-trio-red HEAD, or exploratory commits. Do NOT
let the branch drift >30 commits ahead of `origin/main` without an
open PR — the pre-push hook surfaces a warning at that threshold.

## Ship sequence

Replace the prior 14-step pre-commit ceremony with `/commit-push-pr`.
The slash command runs status + diff scan + secret grep + REVIEW
trigger check + generated commit message + push + PR-cadence check
+ `/clear` recommendation. Read its frontmatter at
`.claude/commands/commit-push-pr.md` for the full sequence.

Pre-commit hooks (gitleaks, ruff, mypy, eslint, tsc, conventional-
pre-commit) run automatically and own deterministic enforcement.
The pre-push hook (`.claude/settings.json`) runs deterministic
secret grep + diff stat + PR-cadence + post-merge `/clear` hint —
no LLM at push time. Layer 2 (`.github/workflows/claude-review.yml`)
is the judgment pass at PR open: routine-review (Sonnet) on most
PRs, deep-review (Opus) on cognitive-layer / `.env*` paths.

## Manual review dispatch

Default: trust the auto layers (pre-commit + pre-push + Layer 2 PR
action). Manual `/review` dispatch is reserved for:

1. About to open a PR with a non-trivial diff and want a final
   pre-PR sanity pass.
2. Mid-feature uncertainty about an architectural choice.
3. Explicit user request.
4. ADR-worthy decisions where Sonnet review at Layer 2 routine pass
   is not enough — invoke `security-reviewer` manually for Opus-tier
   security analysis on sensitive diffs.

`REVIEW.md`'s path-matched trigger taxonomy is for `/review`
orchestrator dispatch when `/review` is invoked. It is NOT a
blanket every-commit-on-a-sensitive-path rule.

## Periodic — every ~5 commits or weekly

Sweep `LESSONS.md` (`/lessons-add`) for any non-obvious thing that
cost time. Sweep `CLAUDE.md` "Common gotchas" same. Two-strikes
rule: only add a rule the second time the same mistake recurs.
```

- [ ] **Step 3: Verify line count**

```bash
wc -l /Users/idohoresh/Desktop/a/.claude/rules/workflow.md
```

Expected: ≤80 lines (target). Acceptable up to 90 if section breaks legibly. If >90, trim further.

- [ ] **Step 4: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add .claude/rules/workflow.md
git commit -m "$(cat <<'EOF'
docs(workflow): rewrite lean — tier-1 invariants only

234 lines → ~80 lines. Tier-1 invariants stay (branch, ADRs, TDD
on cognitive layer, atomic commits, Conventional Commits + co-
author tag, push after commit, no --no-verify, /clear after every
push). Tier-2 stuff demoted to references in CLAUDE.md / REVIEW.md
/ slash commands / hook config — single source of truth per
concern. Replaces 14-step pre-commit ceremony with
/commit-push-pr. Two-strikes rule for additions going forward.
Step 8 of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed.

---

## Task 9: Trim CLAUDE.md to ~120 lines

**Files:**
- Modify: `/Users/idohoresh/Desktop/a/CLAUDE.md`
- Modify: `/Users/idohoresh/Desktop/a/LESSONS.md` (move "Common gotchas" entries here)

**Why:** Final pass — CLAUDE.md is auto-loaded every turn, so every line costs token spend × every turn × every session. Move "Common gotchas" to `LESSONS.md` (read on demand). Keep stack + commands + branch + tier-1 don'ts + the model escalation table from Task 0.

- [ ] **Step 1: Read current CLAUDE.md state**

```bash
wc -l /Users/idohoresh/Desktop/a/CLAUDE.md
grep -n "^## " /Users/idohoresh/Desktop/a/CLAUDE.md
```

Expected: ~228 lines after Task 0 added the model section. Sections: What this project is, Repository layout, Build + test, Branch + commit conventions, Quality gates, Common gotchas, When to use which skill, Model escalation (new from Task 0), Active phase + next task, Pre-task checklist, Things NOT to do, When in doubt.

- [ ] **Step 2: Move "Common gotchas" entries to LESSONS.md "Engineering / debugging gotchas" section**

Read each gotcha in CLAUDE.md "Common gotchas" section. For each, append a corresponding entry to `LESSONS.md` "Engineering / debugging gotchas" using the standard `/lessons-add` format:

```markdown
### <Gotcha title from CLAUDE.md>

**Date:** ~2026-01-01 (pre-existing) | **Cost:** ~estimate based on description

**What happened:** <expanded from the CLAUDE.md one-liner>

**Lesson:** <generalized takeaway>

**How to apply:** <bullet list, often a single workaround command>
```

Insert each new entry at the TOP of "Engineering / debugging gotchas" (newest first per file convention), but prefix the title with `[migrated from CLAUDE.md]` so future readers know the provenance.

The 9 gotchas to migrate are listed numbered 1–9 in the current CLAUDE.md "Common gotchas" section. Migrate them in order (1 first, 9 last) so they appear as a contiguous block in LESSONS.md when read top-down. If LESSONS.md already has a gotcha for any of these (e.g., the Gemini Pro RPD one is already there), do NOT duplicate — skip and note in the PR description.

- [ ] **Step 3: Delete the "Common gotchas" section from CLAUDE.md**

Use the Edit tool. Old string = the entire section from `## Common gotchas` through the line immediately before `## When to use which skill`. Replace with empty string + the section break that connects "Quality gates" to "When to use which skill".

- [ ] **Step 4: Add a one-line pointer to LESSONS.md where the gotchas section was**

Insert a brief reference between the prior section and "When to use which skill":

```markdown
---

## Common gotchas

See `LESSONS.md` "Engineering / debugging gotchas" section. Two-strikes
rule for additions: only add a gotcha the second time the same mistake
costs time.
```

That's 4 lines including the section break and the rule reminder. Net delta: ~80 lines saved in CLAUDE.md, ~80 lines added to LESSONS.md (where they're read on demand, not every turn).

- [ ] **Step 5: Verify line counts**

```bash
wc -l /Users/idohoresh/Desktop/a/CLAUDE.md
wc -l /Users/idohoresh/Desktop/a/LESSONS.md
grep -c "migrated from CLAUDE.md" /Users/idohoresh/Desktop/a/LESSONS.md
```

Expected: CLAUDE.md ≤140 lines (target ≤120; allow up to 140 if section breaks legibly); LESSONS.md grew by ~80 lines; migrated entries count = number actually migrated.

If CLAUDE.md > 140, trim further: candidates are "Build + test" (collapse to slash-command references), "When in doubt" (delete — covered by `CLAUDE.md` reference structure already), "Active phase + next task" (already a one-line pointer to memory; verify it's not duplicated).

- [ ] **Step 6: Commit**

```bash
cd /Users/idohoresh/Desktop/a
git add CLAUDE.md LESSONS.md
git commit -m "$(cat <<'EOF'
docs(claude): trim CLAUDE.md ~30%, migrate gotchas to LESSONS.md

CLAUDE.md is auto-loaded every turn — every line costs tokens ×
every turn × every session. Move "Common gotchas" (9 entries) to
LESSONS.md "Engineering / debugging gotchas" where they are read
on demand. Keep stack + commands + branch + tier-1 don'ts + model
escalation table. Two-strikes rule for future additions. Step 9
of workflow-simplification batch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: commit + push succeed.

- [ ] **Step 7: Swap to Sonnet 4.6 200k for routine work going forward**

```
/model claude-sonnet-4-6
```

User-action only — Claude cannot run `/model` itself. Surface this as a recommendation in the response after the commit succeeds.

---

## Post-batch: open the PR

After Task 9's push:

- [ ] **Step 1: Confirm Layer 2 routine-review fired (per Task 5 Step 6 smoke-test)**

Watch the GitHub Actions tab for the latest push. routine-review should be present + green. deep-review should be skipped (no cognitive-layer paths in this batch).

- [ ] **Step 2: Open the PR**

```bash
cd /Users/idohoresh/Desktop/a
gh pr create --base main --title "Simplify workflow per research dossier" --body "$(cat <<'EOF'
## Summary

Lands the 10-change workflow simplification per
`docs/superpowers/specs/2026-05-07-workflow-simplification-design.md`.
Cuts per-turn context load and token cost ~40–55% while holding
the current quality bar.

Steps in order (one commit each):

0. CLAUDE.md model-escalation trigger table (binary path-or-keyword
   signals; Sonnet swaps to Opus when triggers fire)
1. Delete pre-commit-checklist.md + post-commit reset hook +
   enforcement scripts
2. Drop Layer 1.5 Haiku push-gate (deterministic command portion
   stays)
3. Add /commit-push-pr slash command (Boris Cherny pattern)
4. Add /handoff slash command (writes Context Checkpoint to git-
   tracked + memory dual location for resilience)
5. Path-filter Layer 2 PR action — split into routine-review
   (Sonnet) + deep-review (Opus on cognitive-layer + .env* paths)
6. Default subagent model = Haiku 4.5 in committed
   .claude/settings.json env (deviation from spec: spec said
   settings.local.json; moved here for git-revertability per
   Section 10 ordered-rollback procedure)
7. Update feedback_session_model_selection.md memory + settings.
   local.json default model to Sonnet 200k (NOT in this PR diff —
   memory and settings.local are both untracked; manual revert
   command in spec Section 10)
8. Rewrite workflow.md lean (234 → ~80 lines, tier-1 invariants
   only)
9. Trim CLAUDE.md ~30%, migrate Common gotchas to LESSONS.md

## Test plan

- [ ] Layer 2 routine-review fires green on this PR (Sonnet)
- [ ] Layer 2 deep-review correctly SKIPPED on this PR (no
  cognitive-layer paths)
- [ ] Pre-commit hooks all green on every commit (the
  pre-commit-checklist hook removed in step 1 should not block
  itself in step 1's commit — pre-commit framework handles
  missing hook scripts gracefully)
- [ ] /commit-push-pr invokes cleanly on the next post-merge
  feature change
- [ ] /handoff writes both portable artifact and memory file when
  invoked on a fresh post-merge session
- [ ] Total auto-loaded per-turn context drops ≥30% on the first
  measurement after merge
- [ ] Layer 2 BLOCK rate stays within Section 9 trigger threshold
  on the next 5 PRs after merge
EOF
)"
```

Expected: PR opens; URL printed.

- [ ] **Step 3: After PR open, swap session model**

User-action: `/model claude-sonnet-4-6`. From this point forward, routine work runs on Sonnet 200k by default; Opus reached via Path A (skill triggers) or Path B (subagent dispatch) per Task 0 trigger table.

---

## Self-review checklist

After writing this plan, fresh-eyes check:

**1. Spec coverage:** Each spec section maps to at least one task.
- Spec §1 Goal → covered by overall plan.
- Spec §2 Why now → motivation in plan headers.
- Spec §3 Design principles → encoded in task verifications.
- Spec §4 Five-stage loop → encoded in workflow.md rewrite (Task 8).
- Spec §5 Step 0 → Task 0. Step 1 → Task 1. Step 2 → Task 2. Step 3 → Task 3. Step 4 → Task 4. Step 5 → Task 5. Step 6 → Task 6. Step 7 → Task 7. Step 8 → Task 8. Step 9 → Task 9. ✓
- Spec §6 Out of scope → respected (Superpowers, ADRs, pre-commit hooks, REVIEW.md, /check-agent etc. untouched).
- Spec §7 Estimated impact → acceptance criteria in PR test plan.
- Spec §8 Risks → mitigations encoded (rollback procedure, dual-write for /handoff, path-filter for Layer 2).
- Spec §9 Success criteria → acceptance in PR test plan.
- Spec §10 Implementation discipline → encoded in atomic commits, ordered-rollback noted in deviation section.
- Spec §10 ordered-rollback procedure → noted in Task 6 + Task 7 commit messages and PR description.

**2. Placeholder scan:** No "TBD", no "TODO", no "fill in details", no "similar to Task N" without showing code. Each task has exact file paths + exact commands + exact text content.

**3. Type consistency:** Slash command frontmatter format matches existing commands (`description`, `allowed-tools`). Hook block JSON structure matches existing settings.json patterns. YAML structure for claude-review.yml mirrors existing job format.

**4. Deviations called out:** Task 6 location (settings.json vs settings.local.json) and Task 7 rollback mechanism (manual vs git revert). Both flagged in plan header. ✓

---

## Execution handoff

**Plan complete and saved to `/Users/idohoresh/Desktop/a/docs/superpowers/plans/2026-05-07-workflow-simplification.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for this batch because each task is mechanical with deterministic verification, but the cumulative diff touches load-bearing config (settings.json, workflow.yml). Per-task review catches drift early.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review. Cheaper if all 10 tasks land cleanly; expensive if mid-task discovery requires backtracking.

**Recommendation: Subagent-Driven.** Reasoning: (a) each task has tight verification steps so a subagent + reviewer pair has clear pass/fail signals; (b) the batch is 10 commits and per-task subagent review prevents a Task-2 bug from cascading into Task-3 hand-off context; (c) Haiku-default subagents (post-Task 6) cost very little per dispatch.

**Caveat:** Tasks 0–5 must run before Task 6 lands (otherwise the Haiku default kicks in mid-batch and changes implementer behavior partway through, polluting the rollback signal). One way to handle: keep main session on Sonnet for Tasks 0–5 (so subagents inherit pre-Task-6 default), or explicitly pin `model: "sonnet"` on every implementer dispatch up to and including Task 5. The cleaner path is the explicit pin.

**Which approach?**
