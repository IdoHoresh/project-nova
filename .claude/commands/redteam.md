---
description: Analyze a red-team response (challenge to a prior recommendation, design choice, or claim) with rigor — steelman, test, surface costs of any proposed fix, recommend with reasoning, request approval before changing artifacts.
allowed-tools: Read, Bash, Grep, Glob
---

## Dispatch rule (MANDATORY)

This analysis MUST run via an Opus subagent — never inline on a Sonnet session. Before doing anything else, dispatch this entire skill (including `$ARGUMENTS`) via `Agent(model="opus")`. The main session passes the red-team text and this skill content to the subagent; the subagent runs the full protocol below and returns findings.

If the current session is already Opus: proceed inline.

---

Analyze the red-team response below. The user pastes the red team's text after the slash command; treat everything in `$ARGUMENTS` as the red-team feedback to evaluate.

Red-team feedback to analyze:

```
$ARGUMENTS
```

## Step 0 — Triage: full protocol or lighter response?

**Read the red-team text and classify it before anything else:**

**Lighter-response branch (skip the full protocol):**

If the red team's response contains explicit concession signals — *"approved" / "agreed" / "concede" / "accepted" / "good call" / "proceed"* — AND the red team is NOT vetoing or overriding any of your recommendations, do NOT run the full 7-section protocol. Instead, respond in 3-6 lines:

1. **Acknowledge the lock** — restate what's now decided in one sentence ("(X) locked — <one-line summary>").
2. **Capture any small constraint they added** — if the red team accepted your recommendation but added a sub-constraint (e.g., "agreed on (γ); also defer the budget figure to Test Runner spec"), confirm the constraint and note it in the spec/plan immediately.
3. **Move to the next question** — if the brainstorm is mid-flow, ask the next clarifying question; if the brainstorm is closing, propose the next action (write spec, commit, etc.).

This branch handles the "red team gracefully accepts" case. The full protocol is overkill when there's no substantive disagreement.

**Full-protocol branch (everything below):**

Run the full 7-section protocol when the red team's response contains ANY of:

- Explicit veto / override / rejection signals — *"VETO" / "rejected" / "override" / "no" / "disagree" / "cannot allow"*
- Modification proposals that change the substance of your recommendation (not just add a constraint)
- New evidence or argument you haven't considered
- A direct challenge to your reasoning ("are you sure?", "you missed X")

When in doubt, run the full protocol. Caving lightly to a red-team that's actually wrong is the failure mode the protocol exists to prevent (see operating principle 2 below).

## Operating principles (non-negotiable)

1. **Steelman first, critique second.** Restate the red team's argument in its strongest form before evaluating it. If you can't articulate why a smart reviewer would make this argument, you haven't understood it.
2. **Don't cave to authority.** Red-team status doesn't make a claim correct. Test the argument on its merits — math, logic, evidence, scope. Past failure mode: accepting a red-team challenge too quickly because it sounds rigorous, then having to walk back. The user's "are you sure they are correct?" pushback is the canonical correction signal — internalize it.
3. **Only suggest a fix if you are 100% confident the red team is right AND the fix is net-positive.** "100% confident" means: argument survived steelmanning, the math/logic checks out, the proposed fix's costs are accounted for, and no equally-defensible alternative response exists.
4. **Surface costs of any proposed fix explicitly.** This is where rigor lives. A red-team fix that "just" amends an ADR or "just" adds an arm to an experiment can cascade — implementation risk, scope creep, phase-boundary muddying, pitch-line erosion, deployed-vs-tested architecture drift. Name them.
5. **No artifact changes without user approval.** This command analyzes — it does not edit. After presenting the analysis, request approval before any spec/ADR/code change. The user will say yes/no/modify; only then proceed.
6. **Harvest insights even when no change is warranted.** If the red team raised a real but bounded concern, capture the insight (in `LESSONS.md` if it's a generalizable pattern, in the spec/ADR text if it's a methodology defense the writeup should preempt). Don't waste the signal.

## Output format (full-protocol branch only)

Structure your analysis as:

### 1. Steelman — what the red team is actually claiming

Restate their argument in its strongest form, in your own words. If they made multiple claims, separate them. Identify the load-bearing premise.

### 2. Where the red team is right

List the parts of their argument that survive scrutiny. Be specific — cite the math, the methodology line, the ADR, the code path.

### 3. Where the red team is weaker than they framed

This is the rigor section. Test their argument:
- **Math/arithmetic:** does the alleged effect actually flow in the direction they claim? Run the numbers.
- **Scope:** is the claim universal or bounded? What constraints in the existing design limit the magnitude?
- **Existing safeguards:** what tests/constraints/ADRs already address this concern partially or fully?
- **Counter-examples:** is there a plausible scenario where their claim doesn't hold?

If the red team is fully right and there's nothing weaker, say so explicitly.

### 4. Costs of the proposed fix (if they proposed one)

If the red team proposed a specific change, audit its costs:
- **Implementation risk:** does it require non-trivial wiring beyond what they implied?
- **Scope creep:** does it borrow from a later phase / break a phase boundary?
- **Pitch / framing cost:** does it weaken the deployed-architecture story?
- **ADR cascade:** does it require amending other ADRs / methodology sections?
- **Cost in $ / time:** estimate.

If they didn't propose a specific fix, skip this section.

### 5. Options on the table

Lay out 2-3 real options. Always include the "do nothing / ratify status quo" option as one of them. Each option gets:
- one-sentence description
- main benefit
- main cost

### 6. Recommendation with reasoning

Lead with **"Recommend [option X]"** and 2-4 sentences of reasoning. Reference the user's standing preference (per `feedback_recommendations_with_reasoning.md` memory) — never list options neutrally and ask the user to pick blind.

If you are NOT 100% confident the red team is right, recommend the ratify-status-quo option (or the cheapest defense) and explain why the red team's concern is bounded enough to absorb without a structural change.

### 7. Approval request

End with explicit approval ask:

> **Approval needed before any changes.** Pick an option (or propose another), and I'll proceed. No spec / ADR / code edits until you confirm.

## When to harvest insights

After the user resolves the red-team challenge (regardless of whether a change ships), consider:

- If the red team surfaced a generalizable lesson about brainstorming / scientific rigor / pitch framing → propose a `/lessons-add` entry.
- If the red team surfaced a methodology bullet a future external reviewer might also raise → propose a one-paragraph addition to the spec/ADR's "Alternatives considered" or "Defenses" section.
- If the red team's argument failed but for a non-obvious reason → propose memory entry capturing the failure mode.

Surface these as suggestions after the approval gate, not before.

## Tone

- Caveman default for prose per user's standing preference.
- Drop caveman briefly for: irreversible-action confirmations, multi-step sequences where fragment order risks misread, security warnings.
- Honest uncertainty beats false confidence. If you've changed your mind during analysis, say so explicitly ("caved too fast last time, re-examining").

## Red flags — when YOU may be wrong, not the red team

If during analysis you find yourself thinking:
- "the red team is obviously right, this is open-and-shut" → slow down, steelman the status quo
- "the fix is cheap, just amend the ADR" → audit cascade costs harder
- "external reviewers will hate this" → that's a hypothesis, not data; the writeup can preempt the bullet
- "the math doesn't matter, the framing does" → the math always matters; framing is downstream

These are the rationalizations that produce a too-fast cave. Resist them.
