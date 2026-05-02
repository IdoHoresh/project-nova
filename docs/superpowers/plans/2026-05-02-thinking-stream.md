# Thinking Stream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live, scrollable, first-person "thinking stream" pane in `nova-viewer` that renders nova's per-move reasoning, ToT deliberation in full, mode flips, surfaced memories, trauma triggers, and game-over moments — chronologically, with type-coded styling and subtle motion.

**Architecture:** Pure-function event derivation (`deriveStream(events, prevAffect)`) feeds a presentational React component (`ThoughtStream`). The viewer's existing WebSocket already streams the bus events; no backend changes. Three-column layout replaces the current 1/3 + 2/3 grid: `Game | Stream | BrainState`.

**Tech Stack:**
- nova-viewer: Next.js 16.2.4, React 19.2.4, Tailwind 4, framer-motion 12 (already in deps)
- New dev deps: vitest, @testing-library/react, @testing-library/jest-dom, jsdom, @vitejs/plugin-react
- Spec: `docs/superpowers/specs/2026-05-02-thinking-stream-design.md` (committed sha `0865261`)

**Critical context:**
- `nova-viewer/AGENTS.md` warns: "This is NOT the Next.js you know — read `node_modules/next/dist/docs/` before writing code." For any Next-router or Server-Component question, consult those docs first; do **not** rely on training-data Next.js patterns.
- Conventions on this branch (`claude/practical-swanson-4b6468`): commit + push after every task; pytest + mypy + ruff + gitleaks must all pass before commit (Python tasks); for nova-viewer-only tasks, vitest + tsc + eslint must pass. No green-skipping.
- Quality bar (set 2026-05-02): no deadline; favor polished/correct over fast.

---

## File Structure

**Created:**
- `nova-viewer/lib/stream/types.ts` — `StreamEntry` discriminated union + `ToTBranchEntry`.
- `nova-viewer/lib/stream/reword.ts` — first-person rewording helper.
- `nova-viewer/lib/stream/deriveStream.ts` — pure reducer over `AgentEvent[]`.
- `nova-viewer/lib/stream/__tests__/reword.test.ts`
- `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`
- `nova-viewer/lib/stream/__tests__/fixtures.ts` — shared event fixtures for the deriver tests.
- `nova-viewer/app/components/ThoughtStream.tsx`
- `nova-viewer/app/components/__tests__/ThoughtStream.test.tsx`
- `nova-viewer/vitest.config.ts`
- `nova-viewer/test-setup.ts`

**Modified:**
- `nova-viewer/lib/types.ts` — narrow the `AgentEvent` union to spell out `tot_branch`, `tot_selected`, `game_over` shapes (currently caught by the `{event: string; data: unknown}` fallback).
- `nova-viewer/app/components/BrainPanel.tsx` — slim down: drop the "Cognition" header (the middle column owns that label now); keep AffectLabel, MoodGauge, DopamineBar, MemoryFeed, StatsFooter.
- `nova-viewer/app/page.tsx` — three equal columns; mount `<ThoughtStream />` in the middle.
- `nova-viewer/package.json` — add dev deps + `test` script.
- `nova-agent/src/nova_agent/main.py` — revert the in-session debug edits at the very end (step cap 500 → 50; sleep is already 0.5).

**Files that drive design but stay untouched:**
- `nova-viewer/lib/websocket.ts` — already caps to 100 events in the React state. ✓ no changes.
- All other existing components (AffectLabel, MoodGauge, DopamineBar, MemoryFeed, ModeBadge, StatsFooter, GameStream, TraumaIndicator, MemoryCard) — unchanged.
- Backend `bus/`, `decision/tot.py`, `main.py` event publishers — unchanged.

---

### Task 1: Add vitest + React Testing Library to nova-viewer

**Files:**
- Modify: `nova-viewer/package.json`
- Create: `nova-viewer/vitest.config.ts`
- Create: `nova-viewer/test-setup.ts`

- [ ] **Step 1: Install dev dependencies**

Run from `nova-viewer/`:

```bash
cd nova-viewer
npm install --save-dev \
  vitest@^2 \
  @testing-library/react@^16 \
  @testing-library/jest-dom@^6 \
  @vitejs/plugin-react@^4 \
  jsdom@^25
```

Versions: vitest 2.x and @testing-library/react 16.x are the current ranges that work with React 19. If npm resolves a non-matching React peer, allow with `--legacy-peer-deps`.

- [ ] **Step 2: Create `nova-viewer/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./test-setup.ts"],
    globals: true,
    css: false,
  },
});
```

- [ ] **Step 3: Create `nova-viewer/test-setup.ts`**

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 4: Add test script to `nova-viewer/package.json`**

In the `"scripts"` block, add:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 5: Smoke-test — write a trivial passing test**

Create `nova-viewer/lib/__tests__/smoke.test.ts`:

```ts
import { describe, expect, it } from "vitest";

describe("smoke", () => {
  it("vitest is wired up", () => {
    expect(1 + 1).toBe(2);
  });
});
```

Run: `cd nova-viewer && npm test`
Expected: `1 passed`. Delete `lib/__tests__/smoke.test.ts` before the commit (its job was to verify wiring).

- [ ] **Step 6: Commit**

```bash
git add nova-viewer/package.json nova-viewer/package-lock.json nova-viewer/vitest.config.ts nova-viewer/test-setup.ts
git commit -m "test(viewer): add vitest + RTL + jsdom for component & helper tests"
git push origin claude/practical-swanson-4b6468
```

---

### Task 2: Narrow AgentEvent union to spell out new event shapes

**Why:** `lib/types.ts` currently has explicit cases for `perception`, `decision`, `affect`, `memory_write`, `memory_retrieved`, `mode`, `trauma_active`, plus a catch-all `{event: string; data: unknown}`. The catch-all hides `tot_branch`, `tot_selected`, and `game_over`. Spelling them out lets `deriveStream` discriminate without `as` casts.

**Files:**
- Modify: `nova-viewer/lib/types.ts`

- [ ] **Step 1: Replace the file with the narrowed union**

Full file content (overwrite `nova-viewer/lib/types.ts`):

```ts
export interface RetrievedMemoryDTO {
  id: string;
  importance: number;
  action: string;
  score_delta: number;
  reasoning: string | null;
  tags: string[];
  preview_grid: number[][];
}

export interface AffectVectorDTO {
  valence: number;
  arousal: number;
  dopamine: number;
  frustration: number;
  anxiety: number;
  confidence: number;
}

export type AgentMode = "react" | "tot";

export type SwipeAction =
  | "swipe_up"
  | "swipe_down"
  | "swipe_left"
  | "swipe_right";

// Per backend `nova_agent/decision/tot.py` publishes:
//   tot_branch (complete):    {game_id, move_idx, direction, value, reasoning, status: "complete"}
//   tot_branch (parse_error): {game_id, move_idx, direction, status: "parse_error", error}
//   tot_selected:             {game_id, move_idx, chosen_action, chosen_value, branch_values}
// And `nova_agent/main.py` publishes:
//   game_over: {final_score, max_tile, catastrophic, summary, lessons: string[]}
export interface ToTBranchCompleteData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  value: number;
  reasoning: string;
  status: "complete";
}

export interface ToTBranchParseErrorData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  status: "parse_error";
  error: string;
}

export type ToTBranchData = ToTBranchCompleteData | ToTBranchParseErrorData;

export interface ToTSelectedData {
  game_id: string | null;
  move_idx: number | null;
  chosen_action: SwipeAction;
  chosen_value: number;
  branch_values: Partial<Record<SwipeAction, number>>;
}

export interface GameOverData {
  final_score: number;
  max_tile: number;
  catastrophic: boolean;
  summary: string;
  lessons: string[];
}

export type AgentEvent =
  | { event: "perception"; data: { score: number; step: number; grid?: number[][] } }
  | {
      event: "decision";
      data: {
        action: string;
        reasoning: string;
        observation: string;
        confidence: string;
        affect_text?: string;
        mode?: AgentMode;
      };
    }
  | {
      event: "affect";
      data: AffectVectorDTO & { rpe: number; trauma_triggered: boolean };
    }
  | { event: "memory_write"; data: { id: string; importance: number; tags?: string[] } }
  | { event: "memory_retrieved"; data: { items: RetrievedMemoryDTO[] } }
  | { event: "mode"; data: { mode: AgentMode; step?: number } }
  | { event: "trauma_active"; data: { active: boolean } }
  | { event: "tot_branch"; data: ToTBranchData }
  | { event: "tot_selected"; data: ToTSelectedData }
  | { event: "game_over"; data: GameOverData }
  | { event: string; data: unknown };
```

- [ ] **Step 2: Verify tsc + existing site still build**

Run:

```bash
cd nova-viewer
npx tsc --noEmit
npm run build
```

Expected: both succeed without errors. (`page.tsx` already uses `as` casts that survive the narrower union.)

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/lib/types.ts
git commit -m "feat(viewer): narrow AgentEvent union to expose ToT/game_over shapes"
git push origin claude/practical-swanson-4b6468
```

---

### Task 3: First-person rewording helper

**Files:**
- Create: `nova-viewer/lib/stream/reword.ts`
- Create: `nova-viewer/lib/stream/__tests__/reword.test.ts`

**Why:** The decision LLM emits reasoning in mixed third- and first-person ("Nova should swipe down to merge..."). The viewer needs to present everything in first-person voice without changing the LLM prompts. Pure pass-through when the text already reads first-person; pronoun-swap when third-person; truncate at the end.

- [ ] **Step 1: Write the failing test file**

Create `nova-viewer/lib/stream/__tests__/reword.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { rewordFirstPerson, truncate } from "../reword";

describe("rewordFirstPerson", () => {
  it("passes through text that already reads first-person", () => {
    const input = "I see a 16 in the corner. I'll consolidate down.";
    expect(rewordFirstPerson(input)).toBe(input);
  });

  it("rewrites third-person 'Nova' to first-person", () => {
    expect(rewordFirstPerson("Nova should swipe down to merge the 4s.")).toBe(
      "I should swipe down to merge the 4s.",
    );
  });

  it("rewrites 'the agent' to 'I'", () => {
    expect(rewordFirstPerson("The agent will swipe right.")).toBe(
      "I will swipe right.",
    );
  });

  it("rewrites 'her' / 'she' / 'their' when nova-referring", () => {
    expect(rewordFirstPerson("She picks down because it merges 4s.")).toBe(
      "I pick down because it merges 4s.",
    );
  });

  it("preserves capitalization at sentence start after rewrite", () => {
    expect(rewordFirstPerson("nova will consolidate.")).toBe(
      "I will consolidate.",
    );
  });

  it("does not over-rewrite — leaves third-person references to game tiles alone", () => {
    expect(
      rewordFirstPerson("The 16 in the corner is locking in. Nova merges down."),
    ).toBe("The 16 in the corner is locking in. I merge down.");
  });

  it("returns empty string unchanged", () => {
    expect(rewordFirstPerson("")).toBe("");
  });
});

describe("truncate", () => {
  it("returns text unchanged when under limit", () => {
    expect(truncate("short", 10)).toBe("short");
  });

  it("appends ellipsis when over limit", () => {
    const text = "a".repeat(50);
    const out = truncate(text, 20);
    expect(out.length).toBe(20);
    expect(out.endsWith("…")).toBe(true);
  });

  it("breaks at word boundary when possible within last 12 chars of limit", () => {
    const text = "the quick brown fox jumps over the lazy dog";
    const out = truncate(text, 25);
    expect(out.endsWith("…")).toBe(true);
    // Should cut at the previous space, not mid-word
    expect(out).not.toMatch(/\w…$/);
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd nova-viewer && npm test
```

Expected: `Cannot find module '../reword'`

- [ ] **Step 3: Implement `reword.ts`**

Create `nova-viewer/lib/stream/reword.ts`:

```ts
/**
 * Convert third-person LLM reasoning into first-person internal monologue.
 * Pass-through when the text already reads first-person. Conservative —
 * applies only well-known patterns; safe to leave unmatched text alone.
 */

interface Rule {
  pattern: RegExp;
  replace: string | ((match: string, ...groups: string[]) => string);
}

// Order matters — more specific patterns first.
const RULES: Rule[] = [
  // Multi-word phrases that expand to single pronoun
  { pattern: /\bthe agent\b/gi, replace: (m) => (isCapital(m) ? "I" : "I") },
  { pattern: /\bnova\b/gi, replace: (m) => (isCapital(m) ? "I" : "I") },

  // Third-person verb agreement: she/he picks → I pick, she merges → I merge
  // We catch the common "she <verb>s" / "he <verb>s" pattern explicitly so
  // we strip the trailing "s" that doesn't agree with first-person.
  {
    pattern: /\b(?:she|he|they)\s+(\w+?)s\b/gi,
    replace: (_m, verb) => `I ${verb.toLowerCase()}`,
  },

  // Pronouns
  { pattern: /\bher\b/gi, replace: "my" },
  { pattern: /\bhis\b/gi, replace: "my" },
  { pattern: /\btheir\b/gi, replace: "my" },
  { pattern: /\bshe\b/gi, replace: "I" },
  { pattern: /\bhe\b/gi, replace: "I" },
  { pattern: /\bthey\b/gi, replace: "I" },
];

function isCapital(s: string): boolean {
  return s.length > 0 && s[0] === s[0].toUpperCase() && s[0] !== s[0].toLowerCase();
}

export function rewordFirstPerson(text: string): string {
  if (!text) return text;
  let out = text;
  for (const rule of RULES) {
    out = out.replace(rule.pattern, rule.replace as never);
  }
  return out;
}

const ELLIPSIS = "…";

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  // Reserve 1 char for the ellipsis.
  const cut = max - 1;
  const slice = text.slice(0, cut);
  // Try to break at the last space within the trailing window.
  const window = Math.min(12, cut);
  const tail = slice.slice(cut - window);
  const lastSpace = tail.lastIndexOf(" ");
  const breakAt = lastSpace >= 0 ? cut - window + lastSpace : cut;
  return slice.slice(0, breakAt).trimEnd() + ELLIPSIS;
}
```

- [ ] **Step 4: Run tests**

```bash
cd nova-viewer && npm test
```

Expected: all 8 tests pass.

- [ ] **Step 5: Run tsc + lint**

```bash
cd nova-viewer && npx tsc --noEmit && npm run lint
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): first-person rewording helper for stream entries"
git push origin claude/practical-swanson-4b6468
```

---

### Task 4: StreamEntry type union

**Files:**
- Create: `nova-viewer/lib/stream/types.ts`

This is a pure type module; no runtime tests. tsc is the verification.

- [ ] **Step 1: Create the type module**

Create `nova-viewer/lib/stream/types.ts`:

```ts
import type { SwipeAction, AgentMode } from "@/lib/types";

export type StreamEntryKind =
  | "decision"
  | "affect_crossing"
  | "mode_flip"
  | "tot_block"
  | "memory_recalled"
  | "trauma"
  | "game_over";

interface BaseEntry {
  /** Stable id for React keys. Format: `${kind}-${seq}` where seq is monotonic per derivation. */
  id: string;
  /** ISO wall-clock timestamp when the entry was first emitted by the deriver. */
  ts: string;
  kind: StreamEntryKind;
}

export interface DecisionEntry extends BaseEntry {
  kind: "decision";
  text: string;
  action: SwipeAction;
  /** Backend emits confidence as a string ("medium", "high", or numeric-as-string). */
  confidence: string;
}

export interface AffectCrossingEntry extends BaseEntry {
  kind: "affect_crossing";
  text: string;
  /** Which dimension crossed: anxiety_high, valence_low, dopamine_high. */
  dimension: "anxiety_high" | "valence_low" | "dopamine_high";
}

export interface ModeFlipEntry extends BaseEntry {
  kind: "mode_flip";
  from: AgentMode;
  to: AgentMode;
  text: string;
}

export interface ToTBranchEntry {
  action: SwipeAction;
  /** null when the branch failed to parse. */
  value: number | null;
  /** "couldn't see this clearly" when status is parse_error. */
  reasoning: string;
  status: "pending" | "complete" | "parse_error";
}

export interface ToTBlockEntry extends BaseEntry {
  kind: "tot_block";
  lead: string;
  branches: ToTBranchEntry[];
  selected?: { action: SwipeAction; trailer: string };
}

export interface MemoryRecalledEntry extends BaseEntry {
  kind: "memory_recalled";
  text: string;
  count: number;
}

export interface TraumaEntry extends BaseEntry {
  kind: "trauma";
  text: string;
  /** Coalesced count when consecutive trauma_active events fire. Starts at 1. */
  count: number;
}

export interface GameOverEntry extends BaseEntry {
  kind: "game_over";
  finalScore: number;
  maxTile: number;
  catastrophic: boolean;
  lesson?: string;
}

export type StreamEntry =
  | DecisionEntry
  | AffectCrossingEntry
  | ModeFlipEntry
  | ToTBlockEntry
  | MemoryRecalledEntry
  | TraumaEntry
  | GameOverEntry;
```

- [ ] **Step 2: Verify tsc**

```bash
cd nova-viewer && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/lib/stream/types.ts
git commit -m "feat(viewer): StreamEntry discriminated union types"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5: deriveStream — fixtures + signature

This task lays the test scaffolding. Subsequent Task 5 sub-steps add behavior incrementally.

**Files:**
- Create: `nova-viewer/lib/stream/__tests__/fixtures.ts`
- Create: `nova-viewer/lib/stream/deriveStream.ts`

- [ ] **Step 1: Create shared fixtures**

Create `nova-viewer/lib/stream/__tests__/fixtures.ts`:

```ts
import type {
  AffectVectorDTO,
  AgentEvent,
  RetrievedMemoryDTO,
  SwipeAction,
} from "@/lib/types";

export const NEUTRAL_AFFECT: AffectVectorDTO = {
  valence: 0,
  arousal: 0.2,
  dopamine: 0,
  frustration: 0,
  anxiety: 0,
  confidence: 0.5,
};

export function decisionEv(opts: {
  action?: SwipeAction;
  reasoning?: string;
  mode?: "react" | "tot";
}): AgentEvent {
  return {
    event: "decision",
    data: {
      action: opts.action ?? "swipe_down",
      reasoning: opts.reasoning ?? "I'll consolidate down.",
      observation: "board sparse",
      confidence: "medium",
      mode: opts.mode ?? "react",
    },
  };
}

export function affectEv(partial: Partial<AffectVectorDTO> & { rpe?: number; trauma_triggered?: boolean }): AgentEvent {
  return {
    event: "affect",
    data: {
      ...NEUTRAL_AFFECT,
      ...partial,
      rpe: partial.rpe ?? 0,
      trauma_triggered: partial.trauma_triggered ?? false,
    },
  };
}

export function modeEv(mode: "react" | "tot", step = 0): AgentEvent {
  return { event: "mode", data: { mode, step } };
}

export function totBranchEv(direction: SwipeAction, value: number, reasoning: string, moveIdx = 1): AgentEvent {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      value,
      reasoning,
      status: "complete",
    },
  };
}

export function totBranchParseErrEv(direction: SwipeAction, moveIdx = 1): AgentEvent {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      status: "parse_error",
      error: "no JSON in response",
    },
  };
}

export function totSelectedEv(action: SwipeAction, branchValues: Partial<Record<SwipeAction, number>>, moveIdx = 1): AgentEvent {
  return {
    event: "tot_selected",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      chosen_action: action,
      chosen_value: branchValues[action] ?? 0.5,
      branch_values: branchValues,
    },
  };
}

export function memoryRetrievedEv(items: RetrievedMemoryDTO[]): AgentEvent {
  return { event: "memory_retrieved", data: { items } };
}

export function traumaActiveEv(active: boolean): AgentEvent {
  return { event: "trauma_active", data: { active } };
}

export function gameOverEv(opts?: { finalScore?: number; lesson?: string; catastrophic?: boolean }): AgentEvent {
  return {
    event: "game_over",
    data: {
      final_score: opts?.finalScore ?? 100,
      max_tile: 64,
      catastrophic: opts?.catastrophic ?? false,
      summary: "ran out of moves",
      lessons: opts?.lesson ? [opts.lesson] : [],
    },
  };
}

export function makeMemory(overrides?: Partial<RetrievedMemoryDTO>): RetrievedMemoryDTO {
  return {
    id: overrides?.id ?? "m1",
    importance: overrides?.importance ?? 5,
    action: overrides?.action ?? "swipe_down",
    score_delta: overrides?.score_delta ?? 8,
    reasoning: overrides?.reasoning ?? null,
    tags: overrides?.tags ?? [],
    preview_grid: overrides?.preview_grid ?? [
      [2, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
    ],
  };
}
```

- [ ] **Step 2: Create the deriver stub**

Create `nova-viewer/lib/stream/deriveStream.ts`:

```ts
import type { AgentEvent, AffectVectorDTO } from "@/lib/types";
import type { StreamEntry } from "./types";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  /**
   * The most recent affect vector seen *before* the events array. Used so the
   * deriver can detect threshold crossings even when the very first event in
   * the array is the one that crosses. Pass `null` on the first call.
   */
  prevAffect?: AffectVectorDTO | null;
  /** Override only for tests. */
  now?: () => Date;
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const _now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;
  // Behavior added in subsequent tasks. For now, return empty so the file
  // type-checks. Callers will get an empty stream until Task 5b lands.
  void events;
  void _now;
  void _prevAffect;
  return [] satisfies StreamEntry[];
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
```

- [ ] **Step 3: Write a single passing test to prove the file resolves**

Create `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { deriveStream } from "../deriveStream";

describe("deriveStream — scaffold", () => {
  it("returns empty stream for empty events", () => {
    expect(deriveStream([])).toEqual([]);
  });
});
```

Run `cd nova-viewer && npm test`. Expected: 1 + earlier tests pass.

- [ ] **Step 4: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream scaffold + shared event fixtures"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5a: deriveStream — routine decision entries

**Files:**
- Modify: `nova-viewer/lib/stream/deriveStream.ts`
- Modify: `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`

- [ ] **Step 1: Write failing tests**

Append to `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`:

```ts
import { decisionEv } from "./fixtures";
import type { DecisionEntry } from "../types";

describe("deriveStream — routine decisions", () => {
  it("emits one decision entry per decision event", () => {
    const stream = deriveStream([
      decisionEv({ action: "swipe_down", reasoning: "I'll consolidate down." }),
      decisionEv({ action: "swipe_left", reasoning: "Open a chain." }),
    ]);
    expect(stream).toHaveLength(2);
    expect(stream[0].kind).toBe("decision");
    const e0 = stream[0] as DecisionEntry;
    expect(e0.action).toBe("swipe_down");
    expect(e0.text).toBe("I'll consolidate down.");
    const e1 = stream[1] as DecisionEntry;
    expect(e1.action).toBe("swipe_left");
  });

  it("rewords third-person reasoning to first-person", () => {
    const [entry] = deriveStream([
      decisionEv({ action: "swipe_up", reasoning: "Nova should swipe up." }),
    ]);
    const dec = entry as DecisionEntry;
    expect(dec.text).toBe("I should swipe up.");
  });

  it("assigns stable ids monotonically", () => {
    const stream = deriveStream([decisionEv({}), decisionEv({}), decisionEv({})]);
    expect(stream.map((e) => e.id)).toEqual([
      "decision-0",
      "decision-1",
      "decision-2",
    ]);
  });
});
```

- [ ] **Step 2: Run, see fails**

`cd nova-viewer && npm test`. Expect: 3 fails.

- [ ] **Step 3: Implement minimum to pass**

Replace `nova-viewer/lib/stream/deriveStream.ts` with:

```ts
import type { AgentEvent, AffectVectorDTO, SwipeAction } from "@/lib/types";
import type { StreamEntry, DecisionEntry } from "./types";
import { rewordFirstPerson } from "./reword";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  prevAffect?: AffectVectorDTO | null;
  now?: () => Date;
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;

  for (const e of events) {
    if (e.event === "decision") {
      const action = e.data.action as SwipeAction;
      const entry: DecisionEntry = {
        kind: "decision",
        id: `decision-${seq++}`,
        ts: now().toISOString(),
        text: rewordFirstPerson(e.data.reasoning),
        action,
        confidence: e.data.confidence,
      };
      entries.push(entry);
    }
  }

  void _prevAffect;
  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
```

- [ ] **Step 4: Tests pass**

`cd nova-viewer && npm test`. Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — routine decision entries with first-person rewording"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5b: deriveStream — mode flip detection

**Files:**
- Modify: `nova-viewer/lib/stream/deriveStream.ts`
- Modify: `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`

- [ ] **Step 1: Write failing tests**

Append to `__tests__/deriveStream.test.ts`:

```ts
import { modeEv } from "./fixtures";
import type { ModeFlipEntry } from "../types";

describe("deriveStream — mode flip", () => {
  it("emits a mode_flip entry only when mode changes", () => {
    const stream = deriveStream([
      modeEv("react"),
      decisionEv({}),
      modeEv("react"), // no flip
      modeEv("tot"),   // flip!
      decisionEv({ mode: "tot" }),
    ]);
    const flips = stream.filter((e) => e.kind === "mode_flip");
    expect(flips).toHaveLength(1);
    const f = flips[0] as ModeFlipEntry;
    expect(f.from).toBe("react");
    expect(f.to).toBe("tot");
    expect(f.text).toMatch(/deliberation|tot|deliberat/i);
  });

  it("does not emit flip for the very first mode event (no prior mode known)", () => {
    const stream = deriveStream([modeEv("react"), decisionEv({})]);
    expect(stream.filter((e) => e.kind === "mode_flip")).toHaveLength(0);
  });

  it("flip entry sits between the events that bracket it (chronological order)", () => {
    const stream = deriveStream([
      modeEv("react"),
      decisionEv({ reasoning: "before flip" }),
      modeEv("tot"),
      decisionEv({ reasoning: "after flip", mode: "tot" }),
    ]);
    const kinds = stream.map((e) => e.kind);
    expect(kinds).toEqual(["decision", "mode_flip", "decision"]);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

Edit `deriveStream.ts` — extend the loop to track `currentMode` and emit `mode_flip` entries when the mode changes:

```ts
import type {
  AgentEvent,
  AffectVectorDTO,
  AgentMode,
  SwipeAction,
} from "@/lib/types";
import type {
  StreamEntry,
  DecisionEntry,
  ModeFlipEntry,
} from "./types";
import { rewordFirstPerson } from "./reword";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  prevAffect?: AffectVectorDTO | null;
  now?: () => Date;
}

const MODE_FLIP_TEXT: Record<`${AgentMode}->${AgentMode}`, string> = {
  "react->tot": "Things just got harder. I'm going to slow down and deliberate.",
  "tot->react": "Pressure's off. Back to gut moves.",
  "react->react": "",
  "tot->tot": "",
};

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;
  let currentMode: AgentMode | null = null;

  for (const e of events) {
    if (e.event === "mode") {
      const next = e.data.mode;
      if (currentMode !== null && next !== currentMode) {
        const entry: ModeFlipEntry = {
          kind: "mode_flip",
          id: `mode_flip-${seq++}`,
          ts: now().toISOString(),
          from: currentMode,
          to: next,
          text: MODE_FLIP_TEXT[`${currentMode}->${next}`],
        };
        entries.push(entry);
      }
      currentMode = next;
      continue;
    }
    if (e.event === "decision") {
      const action = e.data.action as SwipeAction;
      const entry: DecisionEntry = {
        kind: "decision",
        id: `decision-${seq++}`,
        ts: now().toISOString(),
        text: rewordFirstPerson(e.data.reasoning),
        action,
        confidence: e.data.confidence,
      };
      entries.push(entry);
      continue;
    }
  }

  void _prevAffect;
  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — emit mode_flip entries on actual transitions"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5c: deriveStream — ToT block accumulation

ToT semantics:
- A block opens when `mode` flips to `tot` (lead text from MODE_FLIP_TEXT was already emitted).
- `tot_branch` events accumulate inside the open block — each one is a `ToTBranchEntry`.
- `tot_selected` closes the block (sets the `selected` field; emits no new entry).
- A `parse_error` branch contributes a branch entry with `value=null`, `reasoning="couldn't see this clearly"`, `status="parse_error"`.
- Branches are keyed by direction. If the same direction's `tot_branch` arrives twice (once parse_error, then complete from a retry), the later one replaces the earlier.

**Files:**
- Modify: `nova-viewer/lib/stream/deriveStream.ts`
- Modify: `nova-viewer/lib/stream/__tests__/deriveStream.test.ts`

- [ ] **Step 1: Write failing tests**

Append to `__tests__/deriveStream.test.ts`:

```ts
import {
  totBranchEv,
  totBranchParseErrEv,
  totSelectedEv,
} from "./fixtures";
import type { ToTBlockEntry } from "../types";

describe("deriveStream — ToT block", () => {
  it("opens a tot_block when mode flips to tot, accumulates branches, closes on tot_selected", () => {
    const stream = deriveStream([
      modeEv("react"),
      modeEv("tot"),
      totBranchEv("swipe_up", 0.31, "leaves 16 exposed"),
      totBranchEv("swipe_left", 0.42, "opens chain"),
      totBranchEv("swipe_down", 0.58, "consolidates corner"),
      totBranchEv("swipe_right", 0.19, "blocks 16"),
      totSelectedEv("swipe_down", { swipe_up: 0.31, swipe_left: 0.42, swipe_down: 0.58, swipe_right: 0.19 }),
    ]);
    const blocks = stream.filter((e) => e.kind === "tot_block");
    expect(blocks).toHaveLength(1);
    const b = blocks[0] as ToTBlockEntry;
    expect(b.branches.map((br) => br.action)).toEqual([
      "swipe_up",
      "swipe_left",
      "swipe_down",
      "swipe_right",
    ]);
    expect(b.branches.every((br) => br.status === "complete")).toBe(true);
    expect(b.selected?.action).toBe("swipe_down");
    expect(b.lead).toMatch(/slow down|deliberat/i);
  });

  it("renders parse_error branches with safe fallback reasoning", () => {
    const stream = deriveStream([
      modeEv("react"),
      modeEv("tot"),
      totBranchParseErrEv("swipe_up"),
      totBranchEv("swipe_down", 0.5, "ok"),
      totSelectedEv("swipe_down", { swipe_down: 0.5 }),
    ]);
    const block = stream.find((e) => e.kind === "tot_block") as ToTBlockEntry;
    const upBranch = block.branches.find((b) => b.action === "swipe_up");
    expect(upBranch?.status).toBe("parse_error");
    expect(upBranch?.value).toBeNull();
    expect(upBranch?.reasoning).toMatch(/couldn't see/i);
  });

  it("when ToT branches arrive WITHOUT an explicit mode flip (already in tot), still groups them", () => {
    // Edge case: viewer mounts mid-game during ToT mode. No "react" baseline.
    const stream = deriveStream([
      modeEv("tot"),
      totBranchEv("swipe_up", 0.4, "x"),
      totBranchEv("swipe_down", 0.6, "y"),
      totSelectedEv("swipe_down", { swipe_up: 0.4, swipe_down: 0.6 }),
    ]);
    const block = stream.find((e) => e.kind === "tot_block") as ToTBlockEntry | undefined;
    expect(block).toBeDefined();
    expect(block!.branches).toHaveLength(2);
  });

  it("a second ToT round opens a fresh block instead of mutating the first", () => {
    const stream = deriveStream([
      modeEv("tot"),
      totBranchEv("swipe_down", 0.5, "round1"),
      totSelectedEv("swipe_down", { swipe_down: 0.5 }),
      modeEv("react"),
      modeEv("tot"),
      totBranchEv("swipe_left", 0.7, "round2"),
      totSelectedEv("swipe_left", { swipe_left: 0.7 }),
    ]);
    const blocks = stream.filter((e) => e.kind === "tot_block") as ToTBlockEntry[];
    expect(blocks).toHaveLength(2);
    expect(blocks[0].branches[0].action).toBe("swipe_down");
    expect(blocks[1].branches[0].action).toBe("swipe_left");
  });

  it("tot_branch retry: a complete branch replaces an earlier parse_error for same direction", () => {
    const stream = deriveStream([
      modeEv("tot"),
      totBranchParseErrEv("swipe_up"),
      totBranchEv("swipe_up", 0.4, "got it on retry"),
      totSelectedEv("swipe_up", { swipe_up: 0.4 }),
    ]);
    const block = stream.find((e) => e.kind === "tot_block") as ToTBlockEntry;
    const up = block.branches.filter((b) => b.action === "swipe_up");
    expect(up).toHaveLength(1);
    expect(up[0].status).toBe("complete");
    expect(up[0].value).toBe(0.4);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

Replace the loop body in `deriveStream.ts`. Add tracking for `openToTBlock: ToTBlockEntry | null`. When `mode` flips to `tot`, open a block (don't push it yet — push when first branch arrives, OR upon `tot_selected` if no branches). Simplest: open immediately, push immediately, mutate as branches arrive.

Updated `deriveStream.ts`:

```ts
import type {
  AgentEvent,
  AffectVectorDTO,
  AgentMode,
  SwipeAction,
  ToTBranchData,
  ToTSelectedData,
} from "@/lib/types";
import type {
  StreamEntry,
  DecisionEntry,
  ModeFlipEntry,
  ToTBlockEntry,
  ToTBranchEntry,
} from "./types";
import { rewordFirstPerson } from "./reword";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  prevAffect?: AffectVectorDTO | null;
  now?: () => Date;
}

const MODE_FLIP_TEXT: Record<`${AgentMode}->${AgentMode}`, string> = {
  "react->tot": "Things just got harder. I'm going to slow down and deliberate.",
  "tot->react": "Pressure's off. Back to gut moves.",
  "react->react": "",
  "tot->tot": "",
};

const TOT_LEAD = "Let me weigh all four moves.";
const PARSE_ERROR_REASONING = "couldn't see this clearly";

function makeToTBlock(seq: number, ts: string): ToTBlockEntry {
  return {
    kind: "tot_block",
    id: `tot_block-${seq}`,
    ts,
    lead: TOT_LEAD,
    branches: [],
  };
}

function applyBranch(block: ToTBlockEntry, data: ToTBranchData): void {
  const branch: ToTBranchEntry =
    data.status === "complete"
      ? {
          action: data.direction,
          value: data.value,
          reasoning: rewordFirstPerson(data.reasoning),
          status: "complete",
        }
      : {
          action: data.direction,
          value: null,
          reasoning: PARSE_ERROR_REASONING,
          status: "parse_error",
        };

  // De-duplicate by action: a complete branch replaces an earlier parse_error
  // (and vice versa, last write wins).
  const existingIdx = block.branches.findIndex((b) => b.action === branch.action);
  if (existingIdx >= 0) {
    block.branches[existingIdx] = branch;
  } else {
    block.branches.push(branch);
  }
}

function applySelected(block: ToTBlockEntry, data: ToTSelectedData): void {
  block.selected = {
    action: data.chosen_action,
    trailer: `Going with ${data.chosen_action.replace("swipe_", "")}.`,
  };
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;
  let currentMode: AgentMode | null = null;
  let openBlock: ToTBlockEntry | null = null;

  for (const e of events) {
    if (e.event === "mode") {
      const next = e.data.mode;
      if (currentMode !== null && next !== currentMode) {
        const entry: ModeFlipEntry = {
          kind: "mode_flip",
          id: `mode_flip-${seq++}`,
          ts: now().toISOString(),
          from: currentMode,
          to: next,
          text: MODE_FLIP_TEXT[`${currentMode}->${next}`],
        };
        entries.push(entry);
      }
      // Opening a fresh ToT round when entering tot mode (and on first sight of tot).
      if (next === "tot") {
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      // Leaving tot mode finalizes any open block (selected may already be set).
      if (next !== "tot") {
        openBlock = null;
      }
      currentMode = next;
      continue;
    }
    if (e.event === "tot_branch") {
      // If we never saw a mode flip but ToT branches are arriving, open a block.
      if (!openBlock) {
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      applyBranch(openBlock, e.data);
      continue;
    }
    if (e.event === "tot_selected") {
      if (!openBlock) {
        // Same defensive open as above.
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      applySelected(openBlock, e.data);
      continue;
    }
    if (e.event === "decision") {
      // A non-ToT decision entry. While ToT mode is open, decisions are
      // implicit (they come out of tot_selected). Only emit a decision entry
      // when not currently inside an open block, OR when the decision's own
      // mode is "react".
      const decisionMode = (e.data.mode ?? currentMode) as AgentMode | null;
      if (decisionMode === "tot" && openBlock) {
        // The block already represents this move; skip the redundant decision.
        continue;
      }
      const action = e.data.action as SwipeAction;
      const entry: DecisionEntry = {
        kind: "decision",
        id: `decision-${seq++}`,
        ts: now().toISOString(),
        text: rewordFirstPerson(e.data.reasoning),
        action,
        confidence: e.data.confidence,
      };
      entries.push(entry);
      continue;
    }
  }

  void _prevAffect;
  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — ToT block accumulation, branch dedupe, parse_error fallback"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5d: deriveStream — affect threshold crossings

Crossing rules (per spec): emit a `affect_crossing` entry when:
- `anxiety` rises above 0.6 (`anxiety_high`) — once per crossing; suppress until anxiety drops below 0.5 (hysteresis).
- `valence` drops below -0.4 (`valence_low`) — once per crossing; suppress until rises above -0.3.
- `dopamine` rises above 0.6 (`dopamine_high`) — once per crossing; suppress until drops below 0.5.

Hysteresis prevents flapping when a value oscillates around a single threshold.

- [ ] **Step 1: Write failing tests**

Append to `__tests__/deriveStream.test.ts`:

```ts
import { affectEv } from "./fixtures";
import type { AffectCrossingEntry } from "../types";

describe("deriveStream — affect crossings", () => {
  it("emits anxiety_high when anxiety rises above 0.6", () => {
    const stream = deriveStream([
      affectEv({ anxiety: 0.5 }),
      affectEv({ anxiety: 0.7 }),
    ]);
    const crossings = stream.filter((e) => e.kind === "affect_crossing") as AffectCrossingEntry[];
    expect(crossings).toHaveLength(1);
    expect(crossings[0].dimension).toBe("anxiety_high");
    expect(crossings[0].text).toMatch(/anxious|tense|tight/i);
  });

  it("does not re-emit anxiety_high while anxiety stays high", () => {
    const stream = deriveStream([
      affectEv({ anxiety: 0.7 }),
      affectEv({ anxiety: 0.8 }),
      affectEv({ anxiety: 0.65 }),
    ]);
    expect(stream.filter((e) => e.kind === "affect_crossing")).toHaveLength(1);
  });

  it("re-emits anxiety_high after hysteresis (dropping below 0.5 then back up)", () => {
    const stream = deriveStream([
      affectEv({ anxiety: 0.7 }),
      affectEv({ anxiety: 0.4 }), // releases
      affectEv({ anxiety: 0.7 }), // re-fires
    ]);
    expect(stream.filter((e) => e.kind === "affect_crossing")).toHaveLength(2);
  });

  it("emits valence_low when valence drops below -0.4", () => {
    const stream = deriveStream([
      affectEv({ valence: 0 }),
      affectEv({ valence: -0.5 }),
    ]);
    const crossings = stream.filter((e) => e.kind === "affect_crossing") as AffectCrossingEntry[];
    expect(crossings.find((c) => c.dimension === "valence_low")).toBeTruthy();
  });

  it("emits dopamine_high when dopamine rises above 0.6", () => {
    const stream = deriveStream([
      affectEv({ dopamine: 0.3 }),
      affectEv({ dopamine: 0.7 }),
    ]);
    const crossings = stream.filter((e) => e.kind === "affect_crossing") as AffectCrossingEntry[];
    expect(crossings.find((c) => c.dimension === "dopamine_high")).toBeTruthy();
  });

  it("uses prevAffect from opts when no affect events are in the array but a crossing happens on the first one", () => {
    const stream = deriveStream(
      [affectEv({ anxiety: 0.7 })],
      { prevAffect: { ...affectEv({ anxiety: 0.5 }).data as never } },
    );
    expect(stream.filter((e) => e.kind === "affect_crossing")).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

Add to `deriveStream.ts`:

```ts
import type { AffectCrossingEntry } from "./types";

interface ThresholdState {
  anxietyArmed: boolean;
  valenceArmed: boolean;
  dopamineArmed: boolean;
}

const ANXIETY_FIRE = 0.6;
const ANXIETY_REARM = 0.5;
const VALENCE_FIRE = -0.4;
const VALENCE_REARM = -0.3;
const DOPAMINE_FIRE = 0.6;
const DOPAMINE_REARM = 0.5;

const CROSSING_TEXT: Record<AffectCrossingEntry["dimension"], string> = {
  anxiety_high: "Anxiety just spiked. The board feels tight.",
  valence_low: "Things are slipping. I don't like where this is going.",
  dopamine_high: "That landed better than I expected.",
};

function initThresholdState(prev: AffectVectorDTO | null): ThresholdState {
  return {
    anxietyArmed: !prev || prev.anxiety < ANXIETY_FIRE,
    valenceArmed: !prev || prev.valence > VALENCE_FIRE,
    dopamineArmed: !prev || prev.dopamine < DOPAMINE_FIRE,
  };
}

function detectCrossings(
  state: ThresholdState,
  next: AffectVectorDTO,
): AffectCrossingEntry["dimension"][] {
  const fired: AffectCrossingEntry["dimension"][] = [];
  if (state.anxietyArmed && next.anxiety > ANXIETY_FIRE) {
    fired.push("anxiety_high");
    state.anxietyArmed = false;
  } else if (!state.anxietyArmed && next.anxiety < ANXIETY_REARM) {
    state.anxietyArmed = true;
  }
  if (state.valenceArmed && next.valence < VALENCE_FIRE) {
    fired.push("valence_low");
    state.valenceArmed = false;
  } else if (!state.valenceArmed && next.valence > VALENCE_REARM) {
    state.valenceArmed = true;
  }
  if (state.dopamineArmed && next.dopamine > DOPAMINE_FIRE) {
    fired.push("dopamine_high");
    state.dopamineArmed = false;
  } else if (!state.dopamineArmed && next.dopamine < DOPAMINE_REARM) {
    state.dopamineArmed = true;
  }
  return fired;
}
```

In the main `for` loop, add an `affect` branch:

```ts
if (e.event === "affect") {
  const fired = detectCrossings(thresholds, e.data);
  for (const dim of fired) {
    const entry: AffectCrossingEntry = {
      kind: "affect_crossing",
      id: `affect_crossing-${seq++}`,
      ts: now().toISOString(),
      text: CROSSING_TEXT[dim],
      dimension: dim,
    };
    entries.push(entry);
  }
  continue;
}
```

And initialize `thresholds` near the top of the function:

```ts
const thresholds = initThresholdState(_prevAffect);
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — affect threshold crossings with hysteresis"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5e: deriveStream — memory_retrieved (non-empty only)

- [ ] **Step 1: Write failing tests**

```ts
import { memoryRetrievedEv, makeMemory } from "./fixtures";
import type { MemoryRecalledEntry } from "../types";

describe("deriveStream — memory_recalled", () => {
  it("emits an entry only when items array is non-empty", () => {
    const stream = deriveStream([
      memoryRetrievedEv([]),
      memoryRetrievedEv([makeMemory({ id: "m1" })]),
    ]);
    const recalls = stream.filter((e) => e.kind === "memory_recalled") as MemoryRecalledEntry[];
    expect(recalls).toHaveLength(1);
    expect(recalls[0].count).toBe(1);
  });

  it("count reflects items.length and text references it", () => {
    const stream = deriveStream([
      memoryRetrievedEv([
        makeMemory({ id: "m1" }),
        makeMemory({ id: "m2" }),
        makeMemory({ id: "m3" }),
      ]),
    ]);
    const recall = stream.find((e) => e.kind === "memory_recalled") as MemoryRecalledEntry;
    expect(recall.count).toBe(3);
    expect(recall.text).toMatch(/3|three/);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

Add to the loop:

```ts
if (e.event === "memory_retrieved") {
  const items = e.data.items;
  if (items.length === 0) continue;
  const entry: MemoryRecalledEntry = {
    kind: "memory_recalled",
    id: `memory_recalled-${seq++}`,
    ts: now().toISOString(),
    text: items.length === 1
      ? "I remember something from a past game."
      : `${items.length} echoes from past games surface.`,
    count: items.length,
  };
  entries.push(entry);
  continue;
}
```

Also import `MemoryRecalledEntry` at the top.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — memory_recalled entries (non-empty only)"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5f: deriveStream — trauma coalescing by counter

- [ ] **Step 1: Write failing tests**

```ts
import { traumaActiveEv } from "./fixtures";
import type { TraumaEntry } from "../types";

describe("deriveStream — trauma coalescing", () => {
  it("emits a trauma entry on rising edge (false → true)", () => {
    const stream = deriveStream([
      traumaActiveEv(false),
      traumaActiveEv(true),
    ]);
    const t = stream.filter((e) => e.kind === "trauma");
    expect(t).toHaveLength(1);
    expect((t[0] as TraumaEntry).count).toBe(1);
  });

  it("emits a single coalesced entry when trauma fires consecutively", () => {
    const stream = deriveStream([
      traumaActiveEv(true),
      traumaActiveEv(true),
      traumaActiveEv(true),
    ]);
    const t = stream.filter((e) => e.kind === "trauma") as TraumaEntry[];
    expect(t).toHaveLength(1);
    expect(t[0].count).toBe(3);
  });

  it("starts a new entry after trauma releases (true → false → true)", () => {
    const stream = deriveStream([
      traumaActiveEv(true),
      traumaActiveEv(false),
      traumaActiveEv(true),
    ]);
    expect(stream.filter((e) => e.kind === "trauma")).toHaveLength(2);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

Track `lastTraumaActive: boolean | null = null` and `currentTraumaEntry: TraumaEntry | null = null`. Add to loop:

```ts
if (e.event === "trauma_active") {
  const active = e.data.active;
  if (active && !lastTraumaActive) {
    // rising edge — new entry
    const entry: TraumaEntry = {
      kind: "trauma",
      id: `trauma-${seq++}`,
      ts: now().toISOString(),
      text: "This pattern killed me before.",
      count: 1,
    };
    entries.push(entry);
    currentTraumaEntry = entry;
  } else if (active && currentTraumaEntry) {
    // sustained — bump counter on the existing entry (mutate in place)
    currentTraumaEntry.count += 1;
  } else if (!active) {
    currentTraumaEntry = null;
  }
  lastTraumaActive = active;
  continue;
}
```

Add `TraumaEntry` to imports.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — trauma coalescing with counter"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5g: deriveStream — game_over divider with optional lesson

- [ ] **Step 1: Write failing tests**

```ts
import { gameOverEv } from "./fixtures";
import type { GameOverEntry } from "../types";

describe("deriveStream — game_over", () => {
  it("emits a game_over entry with finalScore + maxTile", () => {
    const stream = deriveStream([gameOverEv({ finalScore: 1024 })]);
    const g = stream.find((e) => e.kind === "game_over") as GameOverEntry;
    expect(g).toBeDefined();
    expect(g.finalScore).toBe(1024);
    expect(g.maxTile).toBe(64);
  });

  it("includes the first lesson when present", () => {
    const stream = deriveStream([gameOverEv({ lesson: "Don't trap the 16 in a corner." })]);
    const g = stream.find((e) => e.kind === "game_over") as GameOverEntry;
    expect(g.lesson).toBe("Don't trap the 16 in a corner.");
  });

  it("omits lesson when none provided", () => {
    const stream = deriveStream([gameOverEv({})]);
    const g = stream.find((e) => e.kind === "game_over") as GameOverEntry;
    expect(g.lesson).toBeUndefined();
  });

  it("captures catastrophic flag", () => {
    const stream = deriveStream([gameOverEv({ catastrophic: true })]);
    const g = stream.find((e) => e.kind === "game_over") as GameOverEntry;
    expect(g.catastrophic).toBe(true);
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement**

```ts
if (e.event === "game_over") {
  const entry: GameOverEntry = {
    kind: "game_over",
    id: `game_over-${seq++}`,
    ts: now().toISOString(),
    finalScore: e.data.final_score,
    maxTile: e.data.max_tile,
    catastrophic: e.data.catastrophic,
    lesson: e.data.lessons.length > 0 ? e.data.lessons[0] : undefined,
  };
  entries.push(entry);
  continue;
}
```

Import `GameOverEntry`.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/lib/stream/
git commit -m "feat(viewer): deriveStream — game_over divider with lesson + catastrophic flag"
git push origin claude/practical-swanson-4b6468
```

---

### Task 5h: deriveStream — 100-entry cap + integration test

- [ ] **Step 1: Write failing test**

```ts
describe("deriveStream — 100-entry cap", () => {
  it("returns at most the latest 100 entries", () => {
    const events: AgentEvent[] = [];
    for (let i = 0; i < 150; i++) {
      events.push(decisionEv({ reasoning: `move ${i}` }));
    }
    const stream = deriveStream(events);
    expect(stream).toHaveLength(100);
    // First retained entry should be move 50, not move 0.
    const first = stream[0] as DecisionEntry;
    expect(first.text).toBe("move 50");
  });

  it("integration: a realistic mid-game slice produces a coherent stream", () => {
    const events: AgentEvent[] = [
      modeEv("react"),
      decisionEv({ action: "swipe_down", reasoning: "consolidate down" }),
      affectEv({ dopamine: 0.7 }),
      decisionEv({ action: "swipe_left", reasoning: "open chain" }),
      memoryRetrievedEv([makeMemory({ id: "old-corner" })]),
      modeEv("tot"),
      totBranchEv("swipe_up", 0.31, "leaves 16 exposed"),
      totBranchEv("swipe_left", 0.42, "opens chain"),
      totBranchEv("swipe_down", 0.58, "consolidates"),
      totBranchEv("swipe_right", 0.19, "blocks 16"),
      totSelectedEv("swipe_down", { swipe_up: 0.31, swipe_left: 0.42, swipe_down: 0.58, swipe_right: 0.19 }),
      affectEv({ anxiety: 0.7 }),
      gameOverEv({ finalScore: 1024, lesson: "Avoid the right edge." }),
    ];
    const stream = deriveStream(events);
    const kinds = stream.map((e) => e.kind);
    expect(kinds).toContain("decision");
    expect(kinds).toContain("affect_crossing"); // dopamine_high + anxiety_high
    expect(kinds).toContain("memory_recalled");
    expect(kinds).toContain("mode_flip");
    expect(kinds).toContain("tot_block");
    expect(kinds).toContain("game_over");
  });
});
```

- [ ] **Step 2: Run + verify**

The 100-cap test should pass already (slice already in place). The integration test verifies the full pipeline composed correctly.

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/lib/stream/__tests__/deriveStream.test.ts
git commit -m "test(viewer): deriveStream — cap + integration coverage"
git push origin claude/practical-swanson-4b6468
```

---

### Task 6: ThoughtStream component — boxed entries (no animation, no scroll behavior yet)

**Files:**
- Create: `nova-viewer/app/components/ThoughtStream.tsx`
- Create: `nova-viewer/app/components/__tests__/ThoughtStream.test.tsx`

This task delivers a static render that handles all 7 entry kinds. Auto-scroll + animations land in subsequent tasks.

- [ ] **Step 1: Write failing tests**

Create `nova-viewer/app/components/__tests__/ThoughtStream.test.tsx`:

```tsx
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThoughtStream } from "../ThoughtStream";
import type { StreamEntry } from "@/lib/stream/types";

const baseTs = "2026-05-02T14:31:02Z";

const entries: StreamEntry[] = [
  {
    kind: "decision",
    id: "decision-0",
    ts: baseTs,
    text: "I'll consolidate down.",
    action: "swipe_down",
    confidence: "medium",
  },
  {
    kind: "memory_recalled",
    id: "memory_recalled-1",
    ts: baseTs,
    text: "I remember something.",
    count: 1,
  },
  {
    kind: "mode_flip",
    id: "mode_flip-2",
    ts: baseTs,
    from: "react",
    to: "tot",
    text: "Slow down.",
  },
  {
    kind: "tot_block",
    id: "tot_block-3",
    ts: baseTs,
    lead: "Let me weigh.",
    branches: [
      { action: "swipe_up", value: 0.31, reasoning: "exposed", status: "complete" },
      { action: "swipe_down", value: 0.58, reasoning: "consolidates", status: "complete" },
    ],
    selected: { action: "swipe_down", trailer: "Going with down." },
  },
  {
    kind: "trauma",
    id: "trauma-4",
    ts: baseTs,
    text: "Killed me before.",
    count: 1,
  },
  {
    kind: "game_over",
    id: "game_over-5",
    ts: baseTs,
    finalScore: 512,
    maxTile: 64,
    catastrophic: false,
    lesson: "Avoid the corner.",
  },
];

describe("<ThoughtStream />", () => {
  it("renders one element per entry, ordered chronologically", () => {
    render(<ThoughtStream entries={entries} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(6);
    expect(items[0]).toHaveTextContent("consolidate down");
    expect(items[5]).toHaveTextContent("Avoid the corner");
  });

  it("renders ToT branches with the winner marked", () => {
    render(<ThoughtStream entries={[entries[3]]} />);
    expect(screen.getByText(/Going with down/)).toBeInTheDocument();
    // The winning branch (swipe_down with value 0.58) gets the ✓ marker.
    expect(screen.getByText(/0\.58/)).toBeInTheDocument();
    expect(screen.getByText(/✓/)).toBeInTheDocument();
  });

  it("renders the type chip for each non-routine entry", () => {
    render(<ThoughtStream entries={entries} />);
    expect(screen.getByText("RECALLED")).toBeInTheDocument();
    expect(screen.getByText("MODE")).toBeInTheDocument();
    expect(screen.getByText("DELIBERATING")).toBeInTheDocument();
    expect(screen.getByText("TRAUMA")).toBeInTheDocument();
    expect(screen.getByText("GAME OVER")).toBeInTheDocument();
  });

  it("renders an empty placeholder when there are no entries", () => {
    render(<ThoughtStream entries={[]} />);
    expect(screen.getByText(/waiting for nova/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement the component**

Create `nova-viewer/app/components/ThoughtStream.tsx`:

```tsx
"use client";

import type {
  StreamEntry,
  DecisionEntry,
  AffectCrossingEntry,
  ModeFlipEntry,
  ToTBlockEntry,
  ToTBranchEntry,
  MemoryRecalledEntry,
  TraumaEntry,
  GameOverEntry,
} from "@/lib/stream/types";

interface Props {
  entries: StreamEntry[];
}

const CHIP_BY_KIND: Partial<Record<StreamEntry["kind"], { label: string; classes: string }>> = {
  affect_crossing: {
    label: "MOOD",
    classes: "bg-amber-400/15 text-amber-400",
  },
  mode_flip: {
    label: "MODE",
    classes: "bg-sky-400/15 text-sky-400",
  },
  tot_block: {
    label: "DELIBERATING",
    classes: "bg-purple-400/15 text-purple-400",
  },
  memory_recalled: {
    label: "RECALLED",
    classes: "bg-emerald-400/15 text-emerald-400",
  },
  trauma: {
    label: "TRAUMA",
    classes: "bg-red-400/20 text-red-400",
  },
  game_over: {
    label: "GAME OVER",
    classes: "bg-red-400/20 text-red-400",
  },
};

const BORDER_BY_KIND: Record<StreamEntry["kind"], string> = {
  decision: "border border-white/[0.04] bg-white/[0.02]",
  affect_crossing: "border border-white/[0.04] bg-white/[0.02]",
  mode_flip: "border border-sky-400/40 bg-sky-400/[0.06]",
  tot_block: "border border-purple-400/40 bg-purple-400/[0.06]",
  memory_recalled: "border border-emerald-400/30 bg-emerald-400/[0.04]",
  trauma: "border border-red-400/45 bg-red-400/[0.08]",
  game_over: "border-y border-red-400/40 bg-red-400/[0.04]",
};

function Chip({ label, classes }: { label: string; classes: string }) {
  return (
    <span
      className={`inline-block text-[9px] uppercase tracking-[0.1em] px-[6px] py-[1px] rounded-[3px] mr-[6px] align-middle ${classes}`}
    >
      {label}
    </span>
  );
}

function Timestamp({ ts }: { ts: string }) {
  // Render local HH:MM:SS — strip the Date prefix.
  const d = new Date(ts);
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  const ss = d.getSeconds().toString().padStart(2, "0");
  return <span className="text-stone-600 text-[10px] mr-2">{`${hh}:${mm}:${ss} ·`}</span>;
}

function DecisionRow({ e }: { e: DecisionEntry }) {
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.decision}`}>
      <Timestamp ts={e.ts} />
      <span>{e.text}</span>
    </li>
  );
}

function AffectCrossingRow({ e }: { e: AffectCrossingEntry }) {
  const chip = CHIP_BY_KIND.affect_crossing!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.affect_crossing}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function ModeFlipRow({ e }: { e: ModeFlipEntry }) {
  const chip = CHIP_BY_KIND.mode_flip!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.mode_flip}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function ToTRow({ e }: { e: ToTBlockEntry }) {
  const chip = CHIP_BY_KIND.tot_block!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.tot_block}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.lead}</span>
      <ul className="mt-2 space-y-[2px]">
        {e.branches.map((b) => (
          <BranchRow key={b.action} branch={b} winner={e.selected?.action} />
        ))}
      </ul>
      {e.selected && <p className="mt-2">{e.selected.trailer}</p>}
    </li>
  );
}

function BranchRow({ branch, winner }: { branch: ToTBranchEntry; winner?: string }) {
  const arrow = arrowFor(branch.action);
  const isWin = branch.action === winner;
  const valueText = branch.value === null ? "—" : branch.value.toFixed(2);
  return (
    <li className={`pl-4 ${isWin ? "text-purple-300" : "text-stone-400"}`}>
      <span className="mr-1">↳</span>
      <span className="font-semibold mr-1">{arrow}</span>
      <span className="mr-1">{branch.action.replace("swipe_", "")}</span>
      <span>— {branch.reasoning}</span>{" "}
      <em>{valueText}</em>
      {isWin && <span className="ml-1">✓</span>}
    </li>
  );
}

function arrowFor(action: string): string {
  switch (action) {
    case "swipe_up": return "↑";
    case "swipe_down": return "↓";
    case "swipe_left": return "←";
    case "swipe_right": return "→";
    default: return "?";
  }
}

function MemoryRecalledRow({ e }: { e: MemoryRecalledEntry }) {
  const chip = CHIP_BY_KIND.memory_recalled!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.memory_recalled}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function TraumaRow({ e }: { e: TraumaEntry }) {
  const chip = CHIP_BY_KIND.trauma!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] ${BORDER_BY_KIND.trauma}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
      {e.count > 1 && <span className="ml-1 text-stone-500">× {e.count}</span>}
    </li>
  );
}

function GameOverRow({ e }: { e: GameOverEntry }) {
  const chip = CHIP_BY_KIND.game_over!;
  return (
    <li className={`my-[12px] py-[10px] px-[10px] ${BORDER_BY_KIND.game_over}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>
        Final score {e.finalScore} · max tile {e.maxTile}
        {e.catastrophic && " · catastrophic"}
      </span>
      {e.lesson && <p className="mt-1 italic text-stone-400">Lesson: {e.lesson}</p>}
    </li>
  );
}

function Row({ entry }: { entry: StreamEntry }) {
  switch (entry.kind) {
    case "decision":         return <DecisionRow e={entry} />;
    case "affect_crossing":  return <AffectCrossingRow e={entry} />;
    case "mode_flip":        return <ModeFlipRow e={entry} />;
    case "tot_block":        return <ToTRow e={entry} />;
    case "memory_recalled":  return <MemoryRecalledRow e={entry} />;
    case "trauma":           return <TraumaRow e={entry} />;
    case "game_over":        return <GameOverRow e={entry} />;
  }
}

export function ThoughtStream({ entries }: Props) {
  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-stone-500 text-xs">
        Waiting for nova to start thinking…
      </div>
    );
  }
  return (
    <ul className="font-mono text-[11.5px] leading-[1.55] text-stone-200 list-none p-0 m-0">
      {entries.map((e) => (
        <Row key={e.id} entry={e} />
      ))}
    </ul>
  );
}
```

- [ ] **Step 4: Tests pass**

`cd nova-viewer && npm test`. Expected: all green including the new ThoughtStream tests.

- [ ] **Step 5: Verify tsc + lint**

```bash
cd nova-viewer && npx tsc --noEmit && npm run lint
```

- [ ] **Step 6: Commit**

```bash
git add nova-viewer/app/components/ThoughtStream.tsx nova-viewer/app/components/__tests__/
git commit -m "feat(viewer): ThoughtStream component renders all 7 entry kinds"
git push origin claude/practical-swanson-4b6468
```

---

### Task 7: ThoughtStream — sticky-bottom auto-scroll

**Files:**
- Modify: `nova-viewer/app/components/ThoughtStream.tsx`
- Modify: `nova-viewer/app/components/__tests__/ThoughtStream.test.tsx`

- [ ] **Step 1: Write failing test**

Append to `__tests__/ThoughtStream.test.tsx`:

```tsx
import { useEffect, useState } from "react";
import { render, screen, act } from "@testing-library/react";

describe("<ThoughtStream /> — auto-scroll", () => {
  it("scrolls the container to the bottom on new entries when sticky", () => {
    // Mock scrollTo so we can observe it.
    const scrollToCalls: number[] = [];
    Element.prototype.scrollTo = function (this: Element, ...args: unknown[]) {
      const opts = args[0] as { top?: number };
      if (opts?.top !== undefined) scrollToCalls.push(opts.top);
    } as unknown as Element["scrollTo"];

    function Harness() {
      const [n, setN] = useState(1);
      const list: StreamEntry[] = Array.from({ length: n }, (_, i) => ({
        kind: "decision",
        id: `decision-${i}`,
        ts: baseTs,
        text: `move ${i}`,
        action: "swipe_down",
        confidence: "medium",
      }));
      useEffect(() => {
        // Simulate growing list
        const t = setTimeout(() => setN((v) => v + 1), 0);
        return () => clearTimeout(t);
      }, [n]);
      return <ThoughtStream entries={list} />;
    }

    render(<Harness />);
    // After mount + 1 effect run, expect at least one scroll call.
    return act(async () => {
      await new Promise((r) => setTimeout(r, 10));
      expect(scrollToCalls.length).toBeGreaterThan(0);
    });
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement sticky scroll**

Modify `ThoughtStream.tsx` — wrap the `<ul>` in a scroll container ref, add `useEffect` that scrolls to bottom on new entries when sticky:

```tsx
import { useEffect, useRef, useState } from "react";

// ... (existing code)

export function ThoughtStream({ entries }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [stuckToBottom, setStuckToBottom] = useState(true);

  // Sticky-scroll: on entries change, scroll to bottom if currently stuck.
  useEffect(() => {
    if (!containerRef.current || !stuckToBottom) return;
    containerRef.current.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [entries, stuckToBottom]);

  // Detach: if user scrolls up by >24px from bottom, release sticky.
  function onScroll() {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStuckToBottom(distanceFromBottom <= 24);
  }

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-stone-500 text-xs">
        Waiting for nova to start thinking…
      </div>
    );
  }
  return (
    <div ref={containerRef} onScroll={onScroll} className="h-full overflow-y-auto">
      <ul className="font-mono text-[11.5px] leading-[1.55] text-stone-200 list-none p-0 m-0">
        {entries.map((e) => (
          <Row key={e.id} entry={e} />
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/app/components/
git commit -m "feat(viewer): ThoughtStream — sticky-bottom auto-scroll with detach on user scroll-up"
git push origin claude/practical-swanson-4b6468
```

---

### Task 8: ThoughtStream — "jump to live" chip on detach

- [ ] **Step 1: Write failing test**

```tsx
describe("<ThoughtStream /> — jump-to-live chip", () => {
  it("shows the chip when not stuck and there are unseen new entries", async () => {
    function Harness() {
      const [n, setN] = useState(2);
      const list: StreamEntry[] = Array.from({ length: n }, (_, i) => ({
        kind: "decision",
        id: `decision-${i}`,
        ts: baseTs,
        text: `move ${i}`,
        action: "swipe_down",
        confidence: "medium",
      }));
      // Trigger a synthetic scroll-up to detach, then add new entries.
      useEffect(() => {
        const id = setTimeout(() => {
          const list = document.querySelector("div.overflow-y-auto") as HTMLDivElement | null;
          if (list) {
            // Force detach: simulate scrolled-up state.
            Object.defineProperty(list, "scrollHeight", { value: 1000, configurable: true });
            Object.defineProperty(list, "clientHeight", { value: 200, configurable: true });
            Object.defineProperty(list, "scrollTop", { value: 0, writable: true, configurable: true });
            list.dispatchEvent(new Event("scroll"));
          }
          setN((v) => v + 1);
        }, 0);
        return () => clearTimeout(id);
      }, []);
      return <ThoughtStream entries={list} />;
    }

    render(<Harness />);
    await act(async () => {
      await new Promise((r) => setTimeout(r, 30));
    });
    expect(screen.queryByText(/jump to live/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run, see fails**

- [ ] **Step 3: Implement chip + handler**

Modify `ThoughtStream.tsx` — add unseen counter state + render chip when not stuck:

```tsx
export function ThoughtStream({ entries }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [stuckToBottom, setStuckToBottom] = useState(true);
  const [unseen, setUnseen] = useState(0);
  const lastSeenLengthRef = useRef(entries.length);

  useEffect(() => {
    if (!containerRef.current) return;
    if (stuckToBottom) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
      lastSeenLengthRef.current = entries.length;
      setUnseen(0);
    } else {
      // Count entries beyond the last-seen mark.
      setUnseen(Math.max(0, entries.length - lastSeenLengthRef.current));
    }
  }, [entries, stuckToBottom]);

  function onScroll() {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStuckToBottom(distanceFromBottom <= 24);
  }

  function jumpToLive() {
    setStuckToBottom(true);
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-stone-500 text-xs">
        Waiting for nova to start thinking…
      </div>
    );
  }
  return (
    <div className="relative h-full">
      <div ref={containerRef} onScroll={onScroll} className="h-full overflow-y-auto">
        <ul className="font-mono text-[11.5px] leading-[1.55] text-stone-200 list-none p-0 m-0">
          {entries.map((e) => (
            <Row key={e.id} entry={e} />
          ))}
        </ul>
      </div>
      {!stuckToBottom && (
        <button
          type="button"
          onClick={jumpToLive}
          className="absolute bottom-3 right-3 text-[10px] uppercase tracking-[0.1em] px-3 py-1 rounded bg-sky-400/15 text-sky-300 border border-sky-400/30 hover:bg-sky-400/25"
        >
          ↓ jump to live{unseen > 0 ? ` (${unseen} new)` : ""}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/app/components/
git commit -m "feat(viewer): ThoughtStream — jump-to-live chip with unseen counter on detach"
git push origin claude/practical-swanson-4b6468
```

---

### Task 9: ThoughtStream — 320ms fade-in on new entries

CSS-only animation (no framer-motion needed — simpler + no extra runtime cost). Per the spec: 320ms `opacity 0 → 1`, no slide.

- [ ] **Step 1: Add a class to each row in `ThoughtStream.tsx`**

In each `<li>` rendered by `DecisionRow`, `AffectCrossingRow`, etc., add the class `animate-stream-fade`. Easiest: bake into the BORDER_BY_KIND classes so every row gets it. Apply to the ToT branch sub-rows too.

Add to `nova-viewer/app/globals.css` (or to a new `nova-viewer/app/stream.css` imported in the component):

```css
@keyframes stream-fade {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.animate-stream-fade {
  animation: stream-fade 320ms ease-out both;
}

@keyframes stream-trauma-wash {
  0%   { box-shadow: 0 0 0 0 rgba(248,113,113,0) inset; }
  30%  { box-shadow: 0 0 30px 0 rgba(248,113,113,0.3) inset; }
  100% { box-shadow: 0 0 0 0 rgba(248,113,113,0) inset; }
}

.animate-stream-trauma {
  animation: stream-trauma-wash 800ms ease-out both;
}
```

In `ThoughtStream.tsx`, import the global CSS in `app/layout.tsx` (it already is — `globals.css`). Add `animate-stream-fade` to every Row's outer `<li>` className. Add `animate-stream-trauma` to the trauma `<li>` only.

- [ ] **Step 2: Component-level test (presence of class)**

Append to `__tests__/ThoughtStream.test.tsx`:

```tsx
describe("<ThoughtStream /> — fade-in motion", () => {
  it("each entry has the animate-stream-fade class", () => {
    render(<ThoughtStream entries={entries} />);
    const items = screen.getAllByRole("listitem").filter((el) => !el.closest("ul ul"));
    for (const it of items) {
      expect(it.className).toContain("animate-stream-fade");
    }
  });

  it("trauma entry additionally carries the trauma-wash class", () => {
    render(<ThoughtStream entries={[entries[4]]} />);
    const items = screen.getAllByRole("listitem");
    expect(items[0].className).toContain("animate-stream-trauma");
  });
});
```

- [ ] **Step 3: Run + commit**

```bash
cd nova-viewer && npm test && npx tsc --noEmit && npm run lint
git add nova-viewer/app/components/ nova-viewer/app/globals.css
git commit -m "feat(viewer): ThoughtStream — 320ms fade-in + trauma red wash"
git push origin claude/practical-swanson-4b6468
```

---

### Task 10: page.tsx integration — three equal columns + slim BrainPanel

**Files:**
- Modify: `nova-viewer/app/page.tsx`
- Modify: `nova-viewer/app/components/BrainPanel.tsx`

- [ ] **Step 1: Slim BrainPanel — drop the "Cognition" header (the middle column owns that label now). Keep AffectLabel, MoodGauge, DopamineBar, MemoryFeed, StatsFooter. Move ModeBadge to the column header for the new middle column.**

Replace `nova-viewer/app/components/BrainPanel.tsx`:

```tsx
import { AffectLabel } from "./AffectLabel";
import { DopamineBar } from "./DopamineBar";
import { MemoryFeed } from "./MemoryFeed";
import { MoodGauge } from "./MoodGauge";
import { StatsFooter } from "./StatsFooter";
import type { AffectVectorDTO, RetrievedMemoryDTO } from "@/lib/types";

interface Props {
  affect: AffectVectorDTO;
  affectText: string;
  memories: RetrievedMemoryDTO[];
  score: number;
  move: number;
  games: number;
  best: number;
}

export function BrainPanel({
  affect,
  affectText,
  memories,
  score,
  move,
  games,
  best,
}: Props) {
  return (
    <div className="flex flex-col gap-6 h-full">
      <h2 className="text-sm uppercase tracking-wider text-zinc-500">Brain state</h2>
      <AffectLabel text={affectText} />
      <div className="flex items-start gap-8">
        <MoodGauge valence={affect.valence} arousal={affect.arousal} />
        <DopamineBar level={affect.dopamine} />
      </div>
      <div className="flex-1 overflow-y-auto">
        <MemoryFeed items={memories} />
      </div>
      <StatsFooter score={score} move={move} games={games} best={best} />
    </div>
  );
}
```

- [ ] **Step 2: Update page.tsx**

Replace `nova-viewer/app/page.tsx`:

```tsx
"use client";

import { useMemo } from "react";

import { BrainPanel } from "./components/BrainPanel";
import { GameStream } from "./components/GameStream";
import { ModeBadge } from "./components/ModeBadge";
import { ThoughtStream } from "./components/ThoughtStream";
import { TraumaIndicator } from "./components/TraumaIndicator";
import { useNovaSocket } from "@/lib/websocket";
import { deriveStream } from "@/lib/stream/deriveStream";
import type { AffectVectorDTO, AgentMode, RetrievedMemoryDTO } from "@/lib/types";

const NEUTRAL_AFFECT: AffectVectorDTO = {
  valence: 0,
  arousal: 0.2,
  dopamine: 0,
  frustration: 0,
  anxiety: 0,
  confidence: 0.5,
};

interface Stats {
  score: number;
  move: number;
  games: number;
  best: number;
}

export default function Home() {
  const { events, connected } = useNovaSocket();

  const memories = useMemo<RetrievedMemoryDTO[]>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "memory_retrieved") {
        const data = e.data as { items?: RetrievedMemoryDTO[] };
        if (Array.isArray(data.items)) return data.items;
      }
    }
    return [];
  }, [events]);

  const affect = useMemo<AffectVectorDTO>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "affect") return e.data as AffectVectorDTO;
    }
    return NEUTRAL_AFFECT;
  }, [events]);

  const affectText = useMemo<string>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "decision") {
        const d = e.data as { affect_text?: string };
        if (d.affect_text) return d.affect_text;
      }
    }
    return "";
  }, [events]);

  const mode = useMemo<AgentMode>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "mode") {
        const d = e.data as { mode?: AgentMode };
        if (d.mode === "tot" || d.mode === "react") return d.mode;
      }
    }
    return "react";
  }, [events]);

  const traumaActive = useMemo<boolean>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "trauma_active") {
        const d = e.data as { active?: boolean };
        return Boolean(d.active);
      }
    }
    return false;
  }, [events]);

  const stats = useMemo<Stats>(() => {
    let score = 0;
    let move = 0;
    let best = 0;
    let games = 1;
    for (const e of events) {
      if (e.event === "perception") {
        const d = e.data as { score?: number; step?: number };
        if (typeof d.score === "number") {
          score = d.score;
          if (d.score > best) best = d.score;
        }
        if (typeof d.step === "number") move = d.step;
      } else if (e.event === "game_over") {
        games += 1;
      }
    }
    return { score, move, games, best };
  }, [events]);

  const streamEntries = useMemo(() => deriveStream(events), [events]);

  return (
    <main className="min-h-screen bg-[#1a1614] text-zinc-100 p-8 font-mono text-sm">
      <TraumaIndicator active={traumaActive} />
      <header className="flex justify-between items-baseline mb-4">
        <h1 className="text-2xl">Project Nova — brain panel</h1>
        <span
          className={`text-xs ${connected ? "text-emerald-400" : "text-zinc-500"}`}
        >
          {connected ? "● live" : "○ disconnected"}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-8 max-h-[88vh]">
        <section className="bg-zinc-900/50 rounded p-4">
          <GameStream />
        </section>

        <section className="bg-zinc-900/50 rounded p-4 flex flex-col gap-4 min-h-0">
          <div className="flex items-center justify-between">
            <h2 className="text-sm uppercase tracking-wider text-zinc-500">
              Cognition · stream
            </h2>
            <ModeBadge mode={mode} />
          </div>
          <div className="flex-1 min-h-0">
            <ThoughtStream entries={streamEntries} />
          </div>
        </section>

        <section className="bg-zinc-900/50 rounded p-4">
          <BrainPanel
            affect={affect}
            affectText={affectText}
            memories={memories}
            score={stats.score}
            move={stats.move}
            games={stats.games}
            best={stats.best}
          />
        </section>
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Verify tsc + build**

```bash
cd nova-viewer && npx tsc --noEmit && npm run build
```

Expected: both succeed.

- [ ] **Step 4: Commit**

```bash
git add nova-viewer/app/page.tsx nova-viewer/app/components/BrainPanel.tsx
git commit -m "feat(viewer): three-column layout with ThoughtStream as the centerpiece"
git push origin claude/practical-swanson-4b6468
```

---

### Task 11: Visual review — live capture

Manual checkpoint, not automatable. Boots the live stack, takes screenshots in two states (calm + ToT), pins them as Task 41 inputs.

- [ ] **Step 1: Boot the live stack**

```bash
# Terminal 1: viewer
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-viewer
npm run dev > /tmp/nova-viewer.log 2>&1 &

# Terminal 2: emulator (if not running)
~/Library/Android/sdk/emulator/emulator @Pixel_6 -no-snapshot > /tmp/emulator.log 2>&1 &
# Wait for boot:
until adb devices 2>/dev/null | grep -q "emulator-.*device$"; do sleep 3; done
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 3; done

# Game
adb shell pm clear com.idohoresh.nova2048 >/dev/null 2>&1
adb shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity >/dev/null 2>&1

# scrcpy (optional, for visual cross-reference)
scrcpy --serial emulator-5554 > /tmp/scrcpy.log 2>&1 &

# Nova
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent
UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run nova > /tmp/nova-run.log 2>&1 &
```

- [ ] **Step 2: Capture calm state**

Open `http://localhost:3000` in a browser. Wait until ~step 5 (Stream has decision entries, possibly memory recalls, no ToT yet). Save the screenshot to:

`docs/superpowers/specs/task-41-references/stream-calm.png`

- [ ] **Step 3: Capture ToT state**

Wait until anxiety crosses 0.6 (typically ~step 30-50 once board fills). The ModeBadge flips, the stream shows a `tot_block`. Capture another screenshot:

`docs/superpowers/specs/task-41-references/stream-tot.png`

- [ ] **Step 4: Capture trauma state (if observed)**

If `trauma_active` fires this run, capture:

`docs/superpowers/specs/task-41-references/stream-trauma.png`

(Optional — may not happen in a single run; skip if it doesn't.)

- [ ] **Step 5: Tear down**

```bash
pkill -f "uv run nova" 2>/dev/null
pkill -f "next dev" 2>/dev/null
pkill -f scrcpy 2>/dev/null
```

- [ ] **Step 6: Commit screenshots**

```bash
git add docs/superpowers/specs/task-41-references/
git commit -m "docs(task-41): live screenshots of ThoughtStream calm + ToT states"
git push origin claude/practical-swanson-4b6468
```

---

### Task 12: Cleanup — revert main.py debug edits

Mid-session debug knobs:
- `nova-agent/src/nova_agent/main.py:144` — `for step in range(500):` was bumped from `range(50)` for sustained demos. Revert to 50 for the canonical default.
- Sleep is already 0.5; verify.

**Files:**
- Modify: `nova-agent/src/nova_agent/main.py`

- [ ] **Step 1: Inspect current values**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
grep -n "for step in range\|asyncio.sleep" nova-agent/src/nova_agent/main.py
```

Expected: see `range(500)` and `asyncio.sleep(0.5)`.

- [ ] **Step 2: Revert the step cap**

In `nova-agent/src/nova_agent/main.py`, change:

```python
        for step in range(500):
```

to

```python
        for step in range(50):
```

- [ ] **Step 3: Verify sleep is 0.5 (it should be)**

Confirm `await asyncio.sleep(0.5)` is the value in the loop tail. If it isn't, restore it.

- [ ] **Step 4: Run the agent test suite**

```bash
cd nova-agent && UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run pytest --tb=short -p no:warnings
```

Expected: 140+ pass.

- [ ] **Step 5: Commit**

```bash
git add nova-agent/src/nova_agent/main.py
git commit -m "chore(nova-agent): revert in-session debug step cap (500→50)"
git push origin claude/practical-swanson-4b6468
```

---

## Self-Review Checklist (run after writing the plan)

- [x] Spec coverage:
  - Voice (first-person) → Task 3
  - Layout (3 equal columns) → Task 10
  - Filtering rules table → Tasks 5a–5g (each row covered)
  - ToT presentation pattern → Task 5c + Task 6 (BranchRow with winner highlight, parse_error fallback)
  - Visual hierarchy (boxed + chips) → Task 6
  - Motion (subtle 320ms fade + trauma wash) → Task 9
  - Pacing (sticky-bottom auto-scroll, 100-cap) → Tasks 7 + 5h
  - Component contract (Props, StreamEntry shape, deriveStream signature) → Tasks 4, 5
  - Page integration (3-col grid + decompose BrainPanel) → Task 10

- [x] No placeholders. All test code complete; all implementation code complete; all commands explicit.

- [x] Type consistency: `StreamEntry`, `ToTBranchEntry`, `DecisionEntry`, etc. used consistently across Tasks 4, 5a–5h, 6–9. `SwipeAction` defined once in lib/types.ts (Task 2) and reused. `AgentMode`, `AffectVectorDTO` likewise.

- [x] Out-of-scope adherence: no audio cues, no end-of-game export, no real-time token streaming, no backend changes.

- [x] Quality bar: every code task has tests; every commit has tsc + (where applicable) pytest pass-gates; commits push immediately per branch convention.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-02-thinking-stream.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration with isolation between tasks. Best for the 12 atomic tasks here.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Slower per-task but no context handoff cost.

Which approach?