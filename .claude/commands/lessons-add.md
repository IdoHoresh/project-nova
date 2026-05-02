---
description: Add a new lesson learned to LESSONS.md. Use immediately after solving a non-trivial bug, making a non-obvious design decision, or recovering from a failure that cost time.
allowed-tools: Read, Edit
---

Add a new lesson to `LESSONS.md` capturing what just happened so the team doesn't re-learn it.

**Steps:**

1. Read `/Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/LESSONS.md` to see current structure (sections are: Engineering / debugging gotchas, Architecture / design decisions, Workflow / process learnings, Strategic / product learnings, Failure-mode handling).

2. Decide which section the new lesson belongs in. If unclear, default to "Engineering / debugging gotchas" (broadest catch-all).

3. Compose the lesson with this exact structure (newest entries go at the TOP within their section):

   ```markdown
   ### [Title — short, specific, scannable]

   **Date:** YYYY-MM-DD | **Cost:** ~[time estimate] of [what cost time]

   **What happened:** [1-3 sentences describing the actual incident]

   **Lesson:** [1-3 sentences distilling the generalizable insight]

   **How to apply:** [1-3 sentences on how to avoid / detect / handle this in future]
   ```

4. Insert the new entry at the TOP of the chosen section (before any existing entry in that section).

5. After insertion, surface the new entry to me for confirmation. I can edit the title, refine the wording, or move sections before we commit.

6. Once confirmed, commit with message format: `docs(lessons): capture [short title]` and the standard co-author tag.

**When to invoke this command:**

- After spending >15 minutes debugging an issue that wasn't immediately obvious
- After a design decision where we chose Option B over Option A and the reasoning was non-trivial
- After a failure we recovered from (e.g., a bug bricked a workflow and we found a workaround)
- After learning something about a tool, library, or platform that contradicts the docs or common assumption

**When NOT to invoke this command:**

- Routine bug fixes where the cause was obvious from the error message
- Small typos / refactors
- Anything documented in standard library/framework docs

The bar for adding a lesson is "did this cost real time and would I want past-me to have known?"
