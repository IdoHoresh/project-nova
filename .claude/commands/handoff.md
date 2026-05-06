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
