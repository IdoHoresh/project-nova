# AgentEvent Runtime Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `{event: string; data: unknown}` catch-all arm from `AgentEvent` and replace every downstream `as` cast with hand-written runtime predicates that validate WebSocket frames before they reach UI state.

**Architecture:** Each event variant gets a `isXxxEvent(value: unknown): value is XxxEvent` predicate co-located in a new `lib/eventGuards.ts`. A top-level `parseAgentEvent(raw: unknown): AgentEvent | null` dispatches by `event` string and runs the matching predicate. `useNovaSocket` calls `parseAgentEvent` after `JSON.parse`; invalid frames are dropped with a single `console.warn` (sampled, not per-frame, to avoid flooding the console on bad streams). With the catch-all gone, TypeScript's discriminated-union narrowing works on the `event` literal, so `deriveStream.ts` and `app/page.tsx` lose every `e.data as X` cast for free. The only remaining cast (`SwipeAction`) becomes a typed predicate.

**Tech Stack:** TypeScript 5 strict, Next.js 16, React 19, vitest.

**Out of scope (do NOT bundle into this plan):**
- Mirroring the typed protocol on the Python side (`nova_agent/bus/protocol.py` is referenced in the path-scoped rule but doesn't exist yet — separate ADR).
- Adding zod or any runtime-schema dependency. Hand-written predicates only — keeps the bundle small and the dependency surface clean.
- Moving the WebSocket connection logic to a context/store. Functional refactor of `useNovaSocket` only.

**Bug found during planning:** `tot.py:166` publishes a `tot_branch` event with `status: "api_error"` that is NOT modelled in `lib/types.ts`. The catch-all has been silently hiding this. The plan adds the missing `ToTBranchApiErrorData` arm and a `tot_branch.api_error` test fixture.

---

## File Structure

| Path | Action | Responsibility |
|------|--------|----------------|
| `nova-viewer/lib/types.ts` | Modify | Drop catch-all union arm; add `ToTBranchApiErrorData`; widen `ToTBranchData` to 3-arm discriminated union. |
| `nova-viewer/lib/eventGuards.ts` | Create | One predicate per event variant + top-level `parseAgentEvent`. Pure functions, no React imports. |
| `nova-viewer/lib/__tests__/eventGuards.test.ts` | Create | Vitest suite: every predicate accepts a valid frame and rejects ≥3 malformed shapes. |
| `nova-viewer/lib/websocket.ts` | Modify | Use `parseAgentEvent`; warn-and-drop invalid frames (rate-limited). |
| `nova-viewer/lib/__tests__/websocket.test.ts` | Create | Vitest suite verifying `useNovaSocket` drops malformed frames and accepts valid ones. Uses `vi.useFakeTimers` + a mock `WebSocket`. |
| `nova-viewer/lib/stream/deriveStream.ts` | Modify | Remove every `e.data as X` cast (TS narrowing handles it once the catch-all is gone). |
| `nova-viewer/lib/stream/__tests__/fixtures.ts` | Modify | Add `totBranchApiErrEv` fixture; tighten existing fixtures' return type from `AgentEvent` to the specific variant. |
| `nova-viewer/lib/stream/__tests__/deriveStream.test.ts` | Modify | Add a test asserting `tot_branch` with `status: "api_error"` is rendered as a parse-error-style branch (failure mode is identical from the user's POV). |
| `nova-viewer/app/page.tsx` | Modify | Remove every `e.data as X` cast. |
| `LESSONS.md` | Modify (Task 9) | Append a lesson about the catch-all hiding the missing `api_error` arm. |

---

## Task 1: Drop the catch-all + add the missing ToT branch arm in types.ts

**Files:**
- Modify: `nova-viewer/lib/types.ts:34-93`

- [ ] **Step 1: Replace `ToTBranchParseErrorData` block + `ToTBranchData` alias to add the api_error arm**

Open `nova-viewer/lib/types.ts`. Replace lines 28-51 with:

```typescript
// Per backend `nova_agent/decision/tot.py` publishes:
//   tot_branch (complete):    {game_id, move_idx, direction, value, reasoning, status: "complete"}
//   tot_branch (parse_error): {game_id, move_idx, direction, status: "parse_error", error}
//   tot_branch (api_error):   {game_id, move_idx, direction, status: "api_error", error}
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

export interface ToTBranchApiErrorData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  status: "api_error";
  error: string;
}

export type ToTBranchData =
  | ToTBranchCompleteData
  | ToTBranchParseErrorData
  | ToTBranchApiErrorData;
```

- [ ] **Step 2: Drop the catch-all arm from the AgentEvent union**

In the same file, replace line 93:

```typescript
  | { event: string; data: unknown };
```

with nothing (delete the line and the trailing `|` on line 92 — line 92 must end the union with `;`). The final union ends:

```typescript
  | { event: "game_over"; data: GameOverData };
```

- [ ] **Step 3: Type-check to surface every cast site**

Run: `cd nova-viewer && npx tsc --noEmit`
Expected: errors in `lib/stream/deriveStream.ts`, `lib/websocket.ts`, `app/page.tsx`, and `lib/stream/__tests__/deriveStream.test.ts` complaining about `e.data` having a discriminated type incompatible with the `as X` casts in some places, AND about the unhandled `"api_error"` arm in `applyBranch`. This is expected — Tasks 2-7 fix it.

- [ ] **Step 4: Commit**

```bash
git add nova-viewer/lib/types.ts
git commit -m "refactor(viewer): drop AgentEvent catch-all, add tot_branch api_error arm

The {event: string; data: unknown} catch-all silently hid that
nova-agent's tot.py:166 publishes status=\"api_error\" branches
that the viewer never modelled. Removing the catch-all forces
discriminated narrowing at every consumer; the next commits
remove the now-unnecessary casts."
```

(Push happens after the full sequence is green per repo convention. Don't push mid-stream.)

---

## Task 2: Create `lib/eventGuards.ts` with hand-written predicates

**Files:**
- Create: `nova-viewer/lib/eventGuards.ts`

- [ ] **Step 1: Write the file**

```typescript
import type {
  AffectVectorDTO,
  AgentEvent,
  AgentMode,
  GameOverData,
  RetrievedMemoryDTO,
  SwipeAction,
  ToTBranchApiErrorData,
  ToTBranchCompleteData,
  ToTBranchData,
  ToTBranchParseErrorData,
  ToTSelectedData,
} from "./types";

// Narrow `unknown` to a plain object record with string keys. This is the
// foundation every predicate below rests on — once a value is known to be a
// non-null object, indexed access is safe.
function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function isString(v: unknown): v is string {
  return typeof v === "string";
}

function isNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function isBoolean(v: unknown): v is boolean {
  return typeof v === "boolean";
}

function isStringOrNull(v: unknown): v is string | null {
  return v === null || isString(v);
}

function isNumberOrNull(v: unknown): v is number | null {
  return v === null || isNumber(v);
}

const SWIPE_ACTIONS: ReadonlySet<string> = new Set([
  "swipe_up",
  "swipe_down",
  "swipe_left",
  "swipe_right",
]);

export function isSwipeAction(v: unknown): v is SwipeAction {
  return isString(v) && SWIPE_ACTIONS.has(v);
}

export function isAgentMode(v: unknown): v is AgentMode {
  return v === "react" || v === "tot";
}

function isAffectVector(v: unknown): v is AffectVectorDTO {
  if (!isRecord(v)) return false;
  return (
    isNumber(v.valence) &&
    isNumber(v.arousal) &&
    isNumber(v.dopamine) &&
    isNumber(v.frustration) &&
    isNumber(v.anxiety) &&
    isNumber(v.confidence)
  );
}

function isPerceptionData(
  v: unknown,
): v is { score: number; step: number; grid?: number[][] } {
  if (!isRecord(v)) return false;
  if (!isNumber(v.score) || !isNumber(v.step)) return false;
  if (v.grid !== undefined) {
    if (!Array.isArray(v.grid)) return false;
    for (const row of v.grid) {
      if (!Array.isArray(row)) return false;
      for (const cell of row) if (!isNumber(cell)) return false;
    }
  }
  return true;
}

function isDecisionData(v: unknown): v is {
  action: string;
  reasoning: string;
  observation: string;
  confidence: string;
  affect_text?: string;
  mode?: AgentMode;
} {
  if (!isRecord(v)) return false;
  if (!isString(v.action)) return false;
  if (!isString(v.reasoning)) return false;
  if (!isString(v.observation)) return false;
  if (!isString(v.confidence)) return false;
  if (v.affect_text !== undefined && !isString(v.affect_text)) return false;
  if (v.mode !== undefined && !isAgentMode(v.mode)) return false;
  return true;
}

function isAffectEventData(
  v: unknown,
): v is AffectVectorDTO & { rpe: number; trauma_triggered: boolean } {
  if (!isAffectVector(v)) return false;
  const r = v as Record<string, unknown>;
  return isNumber(r.rpe) && isBoolean(r.trauma_triggered);
}

function isMemoryWriteData(
  v: unknown,
): v is { id: string; importance: number; tags?: string[] } {
  if (!isRecord(v)) return false;
  if (!isString(v.id) || !isNumber(v.importance)) return false;
  if (v.tags !== undefined) {
    if (!Array.isArray(v.tags)) return false;
    for (const t of v.tags) if (!isString(t)) return false;
  }
  return true;
}

function isRetrievedMemoryItem(v: unknown): v is RetrievedMemoryDTO {
  if (!isRecord(v)) return false;
  if (!isString(v.id) || !isNumber(v.importance) || !isString(v.action))
    return false;
  if (!isNumber(v.score_delta)) return false;
  if (!isStringOrNull(v.reasoning)) return false;
  if (!Array.isArray(v.tags)) return false;
  for (const t of v.tags) if (!isString(t)) return false;
  if (!Array.isArray(v.preview_grid)) return false;
  for (const row of v.preview_grid) {
    if (!Array.isArray(row)) return false;
    for (const cell of row) if (!isNumber(cell)) return false;
  }
  return true;
}

function isMemoryRetrievedData(
  v: unknown,
): v is { items: RetrievedMemoryDTO[] } {
  if (!isRecord(v)) return false;
  if (!Array.isArray(v.items)) return false;
  for (const item of v.items) if (!isRetrievedMemoryItem(item)) return false;
  return true;
}

function isModeData(v: unknown): v is { mode: AgentMode; step?: number } {
  if (!isRecord(v)) return false;
  if (!isAgentMode(v.mode)) return false;
  if (v.step !== undefined && !isNumber(v.step)) return false;
  return true;
}

function isTraumaActiveData(v: unknown): v is { active: boolean } {
  return isRecord(v) && isBoolean(v.active);
}

function isToTBranchComplete(v: unknown): v is ToTBranchCompleteData {
  if (!isRecord(v)) return false;
  return (
    v.status === "complete" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isNumber(v.value) &&
    isString(v.reasoning)
  );
}

function isToTBranchParseError(v: unknown): v is ToTBranchParseErrorData {
  if (!isRecord(v)) return false;
  return (
    v.status === "parse_error" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isString(v.error)
  );
}

function isToTBranchApiError(v: unknown): v is ToTBranchApiErrorData {
  if (!isRecord(v)) return false;
  return (
    v.status === "api_error" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isString(v.error)
  );
}

function isToTBranchData(v: unknown): v is ToTBranchData {
  return (
    isToTBranchComplete(v) ||
    isToTBranchParseError(v) ||
    isToTBranchApiError(v)
  );
}

function isToTSelectedData(v: unknown): v is ToTSelectedData {
  if (!isRecord(v)) return false;
  if (!isStringOrNull(v.game_id) || !isNumberOrNull(v.move_idx)) return false;
  if (!isSwipeAction(v.chosen_action) || !isNumber(v.chosen_value))
    return false;
  if (!isRecord(v.branch_values)) return false;
  for (const [k, val] of Object.entries(v.branch_values)) {
    if (!isSwipeAction(k)) return false;
    if (!isNumber(val)) return false;
  }
  return true;
}

function isGameOverData(v: unknown): v is GameOverData {
  if (!isRecord(v)) return false;
  if (!isNumber(v.final_score) || !isNumber(v.max_tile)) return false;
  if (!isBoolean(v.catastrophic) || !isString(v.summary)) return false;
  if (!Array.isArray(v.lessons)) return false;
  for (const l of v.lessons) if (!isString(l)) return false;
  return true;
}

// Top-level dispatcher. Returns the validated AgentEvent or null. Caller
// (useNovaSocket) is responsible for logging dropped frames.
export function parseAgentEvent(raw: unknown): AgentEvent | null {
  if (!isRecord(raw)) return null;
  const eventName = raw.event;
  const data = raw.data;
  if (!isString(eventName)) return null;

  switch (eventName) {
    case "perception":
      return isPerceptionData(data) ? { event: "perception", data } : null;
    case "decision":
      return isDecisionData(data) ? { event: "decision", data } : null;
    case "affect":
      return isAffectEventData(data) ? { event: "affect", data } : null;
    case "memory_write":
      return isMemoryWriteData(data) ? { event: "memory_write", data } : null;
    case "memory_retrieved":
      return isMemoryRetrievedData(data)
        ? { event: "memory_retrieved", data }
        : null;
    case "mode":
      return isModeData(data) ? { event: "mode", data } : null;
    case "trauma_active":
      return isTraumaActiveData(data)
        ? { event: "trauma_active", data }
        : null;
    case "tot_branch":
      return isToTBranchData(data) ? { event: "tot_branch", data } : null;
    case "tot_selected":
      return isToTSelectedData(data) ? { event: "tot_selected", data } : null;
    case "game_over":
      return isGameOverData(data) ? { event: "game_over", data } : null;
    default:
      // Unknown event names are dropped. The catch-all used to swallow these
      // silently; now they're an explicit drop. If the agent gains a new
      // event type, both lib/types.ts and this switch must be updated in
      // the same PR (per nova-viewer/AGENTS.md "Bus contract" rule).
      return null;
  }
}
```

- [ ] **Step 2: Type-check**

Run: `cd nova-viewer && npx tsc --noEmit lib/eventGuards.ts`
Expected: clean (no errors). If TS complains, fix the predicate that drifted from the type.

- [ ] **Step 3: Commit (deferred until tests pass — see Task 3)**

Don't commit yet; the file isn't reachable from any test or import, so a partial commit would land dead code. Bundle with Task 3.

---

## Task 3: Test every predicate in `eventGuards.test.ts`

**Files:**
- Create: `nova-viewer/lib/__tests__/eventGuards.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it } from "vitest";
import { parseAgentEvent, isAgentMode, isSwipeAction } from "../eventGuards";

describe("isSwipeAction", () => {
  it("accepts the four swipe directions", () => {
    expect(isSwipeAction("swipe_up")).toBe(true);
    expect(isSwipeAction("swipe_down")).toBe(true);
    expect(isSwipeAction("swipe_left")).toBe(true);
    expect(isSwipeAction("swipe_right")).toBe(true);
  });
  it("rejects everything else", () => {
    expect(isSwipeAction("up")).toBe(false);
    expect(isSwipeAction("")).toBe(false);
    expect(isSwipeAction(null)).toBe(false);
    expect(isSwipeAction(undefined)).toBe(false);
    expect(isSwipeAction(42)).toBe(false);
    expect(isSwipeAction({})).toBe(false);
  });
});

describe("isAgentMode", () => {
  it("accepts react and tot only", () => {
    expect(isAgentMode("react")).toBe(true);
    expect(isAgentMode("tot")).toBe(true);
    expect(isAgentMode("REACT")).toBe(false);
    expect(isAgentMode("")).toBe(false);
    expect(isAgentMode(null)).toBe(false);
  });
});

describe("parseAgentEvent — perception", () => {
  it("accepts a valid perception frame", () => {
    const out = parseAgentEvent({
      event: "perception",
      data: { score: 100, step: 3 },
    });
    expect(out?.event).toBe("perception");
  });
  it("accepts perception with optional grid", () => {
    const out = parseAgentEvent({
      event: "perception",
      data: { score: 0, step: 0, grid: [[2, 0], [0, 4]] },
    });
    expect(out?.event).toBe("perception");
  });
  it("rejects perception missing score", () => {
    expect(parseAgentEvent({ event: "perception", data: { step: 1 } })).toBeNull();
  });
  it("rejects perception with non-number step", () => {
    expect(
      parseAgentEvent({ event: "perception", data: { score: 1, step: "1" } }),
    ).toBeNull();
  });
  it("rejects perception with malformed grid", () => {
    expect(
      parseAgentEvent({
        event: "perception",
        data: { score: 1, step: 1, grid: [["2"]] },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — decision", () => {
  it("accepts a valid decision frame", () => {
    const out = parseAgentEvent({
      event: "decision",
      data: {
        action: "swipe_down",
        reasoning: "x",
        observation: "y",
        confidence: "medium",
      },
    });
    expect(out?.event).toBe("decision");
  });
  it("accepts decision with optional fields", () => {
    const out = parseAgentEvent({
      event: "decision",
      data: {
        action: "swipe_down",
        reasoning: "x",
        observation: "y",
        confidence: "medium",
        affect_text: "calm",
        mode: "tot",
      },
    });
    expect(out?.event).toBe("decision");
  });
  it("rejects decision missing reasoning", () => {
    expect(
      parseAgentEvent({
        event: "decision",
        data: { action: "swipe_down", observation: "y", confidence: "high" },
      }),
    ).toBeNull();
  });
  it("rejects decision with invalid mode", () => {
    expect(
      parseAgentEvent({
        event: "decision",
        data: {
          action: "swipe_down",
          reasoning: "x",
          observation: "y",
          confidence: "medium",
          mode: "panic",
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — affect", () => {
  it("accepts a valid affect frame", () => {
    const out = parseAgentEvent({
      event: "affect",
      data: {
        valence: 0,
        arousal: 0.2,
        dopamine: 0,
        frustration: 0,
        anxiety: 0,
        confidence: 0.5,
        rpe: 0,
        trauma_triggered: false,
      },
    });
    expect(out?.event).toBe("affect");
  });
  it("rejects affect with NaN value", () => {
    expect(
      parseAgentEvent({
        event: "affect",
        data: {
          valence: NaN,
          arousal: 0.2,
          dopamine: 0,
          frustration: 0,
          anxiety: 0,
          confidence: 0.5,
          rpe: 0,
          trauma_triggered: false,
        },
      }),
    ).toBeNull();
  });
  it("rejects affect missing rpe", () => {
    expect(
      parseAgentEvent({
        event: "affect",
        data: {
          valence: 0,
          arousal: 0.2,
          dopamine: 0,
          frustration: 0,
          anxiety: 0,
          confidence: 0.5,
          trauma_triggered: false,
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — tot_branch", () => {
  it("accepts a complete branch", () => {
    const out = parseAgentEvent({
      event: "tot_branch",
      data: {
        game_id: "g1",
        move_idx: 0,
        direction: "swipe_down",
        value: 0.7,
        reasoning: "merges 4s",
        status: "complete",
      },
    });
    expect(out?.event).toBe("tot_branch");
  });
  it("accepts a parse_error branch", () => {
    const out = parseAgentEvent({
      event: "tot_branch",
      data: {
        game_id: null,
        move_idx: null,
        direction: "swipe_up",
        status: "parse_error",
        error: "no JSON",
      },
    });
    expect(out?.event).toBe("tot_branch");
  });
  it("accepts an api_error branch (bug fix: was hidden by catch-all)", () => {
    const out = parseAgentEvent({
      event: "tot_branch",
      data: {
        game_id: "g1",
        move_idx: 1,
        direction: "swipe_left",
        status: "api_error",
        error: "RetryError: 429 quota",
      },
    });
    expect(out?.event).toBe("tot_branch");
  });
  it("rejects an unknown status", () => {
    expect(
      parseAgentEvent({
        event: "tot_branch",
        data: {
          game_id: "g1",
          move_idx: 0,
          direction: "swipe_down",
          status: "exploded",
          error: "x",
        },
      }),
    ).toBeNull();
  });
  it("rejects a complete branch missing reasoning", () => {
    expect(
      parseAgentEvent({
        event: "tot_branch",
        data: {
          game_id: "g1",
          move_idx: 0,
          direction: "swipe_down",
          value: 0.5,
          status: "complete",
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — tot_selected", () => {
  it("accepts a valid selected frame", () => {
    const out = parseAgentEvent({
      event: "tot_selected",
      data: {
        game_id: "g1",
        move_idx: 0,
        chosen_action: "swipe_down",
        chosen_value: 0.6,
        branch_values: { swipe_down: 0.6, swipe_up: 0.1 },
      },
    });
    expect(out?.event).toBe("tot_selected");
  });
  it("rejects branch_values with a non-swipe key", () => {
    expect(
      parseAgentEvent({
        event: "tot_selected",
        data: {
          game_id: "g1",
          move_idx: 0,
          chosen_action: "swipe_down",
          chosen_value: 0.6,
          branch_values: { foo: 0.1 },
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — memory_retrieved", () => {
  it("accepts an empty items array", () => {
    const out = parseAgentEvent({
      event: "memory_retrieved",
      data: { items: [] },
    });
    expect(out?.event).toBe("memory_retrieved");
  });
  it("accepts a populated items array", () => {
    const out = parseAgentEvent({
      event: "memory_retrieved",
      data: {
        items: [
          {
            id: "m1",
            importance: 5,
            action: "swipe_down",
            score_delta: 8,
            reasoning: null,
            tags: [],
            preview_grid: [[2, 0], [0, 0]],
          },
        ],
      },
    });
    expect(out?.event).toBe("memory_retrieved");
  });
  it("rejects items with missing preview_grid", () => {
    expect(
      parseAgentEvent({
        event: "memory_retrieved",
        data: {
          items: [
            {
              id: "m1",
              importance: 5,
              action: "swipe_down",
              score_delta: 8,
              reasoning: null,
              tags: [],
            },
          ],
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — game_over", () => {
  it("accepts a valid game_over", () => {
    const out = parseAgentEvent({
      event: "game_over",
      data: {
        final_score: 1024,
        max_tile: 256,
        catastrophic: false,
        summary: "ran out",
        lessons: ["don't merge into a corner"],
      },
    });
    expect(out?.event).toBe("game_over");
  });
  it("rejects lessons containing a non-string", () => {
    expect(
      parseAgentEvent({
        event: "game_over",
        data: {
          final_score: 1,
          max_tile: 2,
          catastrophic: false,
          summary: "",
          lessons: [42],
        },
      }),
    ).toBeNull();
  });
});

describe("parseAgentEvent — top-level rejections", () => {
  it("rejects null", () => {
    expect(parseAgentEvent(null)).toBeNull();
  });
  it("rejects a non-object", () => {
    expect(parseAgentEvent("foo")).toBeNull();
    expect(parseAgentEvent(42)).toBeNull();
  });
  it("rejects when event is missing", () => {
    expect(parseAgentEvent({ data: {} })).toBeNull();
  });
  it("rejects an unknown event name", () => {
    expect(parseAgentEvent({ event: "telemetry", data: {} })).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd nova-viewer && pnpm test lib/__tests__/eventGuards.test.ts`
Expected: all tests pass. (The implementation in Task 2 should already make them green; if any fail, the predicate has a bug — fix the predicate, do NOT loosen the test.)

- [ ] **Step 3: Commit Tasks 2 + 3 together**

```bash
git add nova-viewer/lib/eventGuards.ts nova-viewer/lib/__tests__/eventGuards.test.ts
git commit -m "feat(viewer): add hand-written runtime predicates for AgentEvent

parseAgentEvent dispatches by event name and runs a per-variant
type guard, returning null for malformed frames. Predicates use
hand-written narrowing only (no zod / runtime-schema dependency)
to keep the bundle small. Catches the api_error tot_branch shape
that the previous catch-all had been silently dropping."
```

---

## Task 4: Wire `parseAgentEvent` into `useNovaSocket`

**Files:**
- Modify: `nova-viewer/lib/websocket.ts:29-37`

- [ ] **Step 1: Replace the `onmessage` handler**

Replace lines 29-37 (`ws.onmessage = ...` block) with:

```typescript
    ws.onmessage = (e) => {
      let raw: unknown;
      try {
        raw = JSON.parse(e.data);
      } catch {
        // Malformed JSON — drop without further parsing.
        return;
      }
      const parsed = parseAgentEvent(raw);
      if (parsed === null) {
        // Frame parsed as JSON but failed schema validation. Log once per
        // session per event name to avoid flooding the console on bad
        // streams. The agent should never emit malformed events; if this
        // fires the agent code or this validator is out of sync.
        const evName =
          raw && typeof raw === "object" && "event" in raw
            ? String((raw as { event: unknown }).event)
            : "<no event>";
        if (!seenInvalidEvents.has(evName)) {
          seenInvalidEvents.add(evName);
          console.warn(
            `[useNovaSocket] dropped invalid frame for event="${evName}"`,
            raw,
          );
        }
        return;
      }
      const msg: StampedAgentEvent = { ...parsed, ts: new Date().toISOString() };
      setEvents((prev) => [...prev.slice(-99), msg]);
    };
```

- [ ] **Step 2: Add the `seenInvalidEvents` set + import**

At the top of `useNovaSocket` (right after `const [connected, setConnected] = useState(false);`), add:

```typescript
  const seenInvalidEvents = useRef<Set<string>>(new Set()).current;
```

Update the existing `import` line at the top of the file:

```typescript
import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "./types";
import { parseAgentEvent } from "./eventGuards";
```

(Keeping `seenInvalidEvents` in a `useRef` rather than module scope ensures it resets between hook unmount/remount cycles in tests; sharing across all socket instances would defeat the test reset.)

- [ ] **Step 3: Type-check the file**

Run: `cd nova-viewer && npx tsc --noEmit`
Expected: `lib/websocket.ts` is clean. Other files (deriveStream, page) still error because their casts haven't been removed yet — that's Tasks 5-6.

- [ ] **Step 4: Commit**

```bash
git add nova-viewer/lib/websocket.ts
git commit -m "refactor(viewer): validate AgentEvent frames in useNovaSocket

Pipe every parsed message through parseAgentEvent and drop any
frame that fails schema validation. Invalid frames log once per
event name (rate-limited via a useRef set) so a stuck stream
doesn't flood the console."
```

---

## Task 5: Add `useNovaSocket` test for the validator path

**Files:**
- Create: `nova-viewer/lib/__tests__/websocket.test.ts`

- [ ] **Step 1: Write the test**

```typescript
import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useNovaSocket } from "../websocket";

// Minimal fake WebSocket: captures the most recently constructed instance
// so the test can drive onopen/onmessage directly.
class FakeWebSocket {
  static last: FakeWebSocket | null = null;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  close = vi.fn();
  constructor(public url: string) {
    FakeWebSocket.last = this;
  }
}

beforeEach(() => {
  // @ts-expect-error — installing a stub on the global object
  globalThis.WebSocket = FakeWebSocket;
  FakeWebSocket.last = null;
  vi.spyOn(console, "warn").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useNovaSocket", () => {
  it("appends a stamped event for valid frames", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          event: "perception",
          data: { score: 100, step: 3 },
        }),
      });
    });
    expect(result.current.events).toHaveLength(1);
    expect(result.current.events[0].event).toBe("perception");
    expect(result.current.events[0].ts).toMatch(/\d{4}-\d{2}-\d{2}T/);
  });

  it("drops frames that fail schema validation", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          event: "perception",
          data: { score: "not a number" },
        }),
      });
    });
    expect(result.current.events).toHaveLength(0);
    expect(console.warn).toHaveBeenCalledTimes(1);
  });

  it("rate-limits the warning per event name", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    const bad = JSON.stringify({ event: "perception", data: {} });
    act(() => {
      ws.onmessage?.({ data: bad });
      ws.onmessage?.({ data: bad });
      ws.onmessage?.({ data: bad });
    });
    expect(result.current.events).toHaveLength(0);
    expect(console.warn).toHaveBeenCalledTimes(1);
  });

  it("drops malformed JSON without throwing", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    expect(() =>
      act(() => {
        ws.onmessage?.({ data: "not json {" });
      }),
    ).not.toThrow();
    expect(result.current.events).toHaveLength(0);
  });
});
```

- [ ] **Step 2: Run the test**

Run: `cd nova-viewer && pnpm test lib/__tests__/websocket.test.ts`
Expected: all 4 tests pass. If the rate-limit test fails ("called 3 times, expected 1"), the `useRef` in Task 4 is wrong — it's probably module-scope or being recreated on every render.

- [ ] **Step 3: Commit**

```bash
git add nova-viewer/lib/__tests__/websocket.test.ts
git commit -m "test(viewer): cover useNovaSocket validator + rate-limited warning"
```

---

## Task 6: Remove `as` casts from `deriveStream.ts`

**Files:**
- Modify: `nova-viewer/lib/stream/deriveStream.ts:162-308`

With the catch-all gone, TypeScript narrows `e.data` automatically when you discriminate on `e.event`. Replace each `const d = e.data as X;` with `const d = e.data;`. The `applyBranch` switch must also handle the new `api_error` arm (see Step 4 below).

- [ ] **Step 1: Drop the casts in every `if (e.event === ...)` branch**

In `deriveStream.ts`, edit lines 162-305 to remove every `as X` from `e.data`. Concretely:

- Line 164: `const d = e.data as { mode: AgentMode; step?: number };` → `const d = e.data;`
- Line 190: `const d = e.data as ToTBranchData;` → `const d = e.data;`
- Line 200: `const d = e.data as ToTSelectedData;` → `const d = e.data;`
- Line 210: `const d = e.data as AffectVectorDTO & { rpe: number; trauma_triggered: boolean };` → `const d = e.data;`
- Line 225: `const d = e.data as { items: RetrievedMemoryDTO[] };` → `const d = e.data;`
- Line 242: `const d = e.data as { active: boolean };` → `const d = e.data;`
- Line 265: `const d = e.data as GameOverData;` → `const d = e.data;`
- Lines 283-288: replace the cast block
  ```typescript
  const d = e.data as {
    action: string;
    reasoning: string;
    confidence: string;
    mode?: AgentMode;
  };
  ```
  with
  ```typescript
  const d = e.data;
  ```

- [ ] **Step 2: Replace the residual `decisionMode` cast on line 289**

Replace:
```typescript
const decisionMode = (d.mode ?? currentMode) as AgentMode | null;
```
with:
```typescript
const decisionMode: AgentMode | null = d.mode ?? currentMode;
```
(`d.mode` is already typed `AgentMode | undefined` by narrowing; `currentMode` is `AgentMode | null`; the union is `AgentMode | null`.)

- [ ] **Step 3: Replace the `action` cast on line 294**

Replace:
```typescript
const action = d.action as SwipeAction;
```
with:
```typescript
import { isSwipeAction } from "@/lib/eventGuards";
// ... at top of file ...

// then inside the decision branch:
if (!isSwipeAction(d.action)) continue;
const action = d.action;
```

The `import` line goes at the top of the file alongside the existing imports. The `if (!isSwipeAction(...))` line goes immediately before the existing `const entry: DecisionEntry = { ... }` block. This catches the (rare) case where the agent emits a string action that isn't a known swipe — instead of letting a bad frame populate the stream, we skip it. (The agent's `decide` returns `Decision.action: str`, not a `SwipeAction` Literal — so this guard is real, not theatrical.)

- [ ] **Step 4: Handle the `api_error` arm in `applyBranch`**

Find `applyBranch` at lines 104-128. The current `data.status === "complete"` check leaves the `else` branch handling both `parse_error` and the new `api_error`. Both render as a parse-error-style card from the user's POV (no value, generic "couldn't see this clearly" reasoning). The existing else branch already produces that shape — so the only change needed is to make the discriminator explicit so TS narrowing doesn't surprise us. Replace lines 105-118 with:

```typescript
  let branch: ToTBranchEntry;
  if (data.status === "complete") {
    branch = {
      action: data.direction,
      value: data.value,
      reasoning: rewordFirstPerson(data.reasoning),
      status: "complete",
    };
  } else {
    // Both parse_error and api_error render identically: failed branch with
    // no value. The distinction matters for telemetry/logs, not the card.
    branch = {
      action: data.direction,
      value: null,
      reasoning: PARSE_ERROR_REASONING,
      status: "parse_error",
    };
  }
```

- [ ] **Step 5: Type-check**

Run: `cd nova-viewer && npx tsc --noEmit`
Expected: clean for `deriveStream.ts`. `app/page.tsx` may still error — that's Task 7.

- [ ] **Step 6: Run the deriveStream test suite**

Run: `cd nova-viewer && pnpm test lib/stream/__tests__/deriveStream.test.ts`
Expected: existing tests pass. (No behavior change — only cast removal + an additional explicit branch.)

- [ ] **Step 7: Commit**

```bash
git add nova-viewer/lib/stream/deriveStream.ts
git commit -m "refactor(viewer): drop e.data casts in deriveStream

With the AgentEvent catch-all removed, TypeScript narrows
e.data automatically when we discriminate on e.event. Replace
every \`e.data as X\` cast with the bare reference. The action
cast becomes a SwipeAction predicate guard that skips bad
frames rather than letting them through."
```

---

## Task 7: Remove `as` casts from `app/page.tsx`

**Files:**
- Modify: `nova-viewer/app/page.tsx:33-103`

- [ ] **Step 1: Replace each cast with the narrowed reference**

In `app/page.tsx`, edit:

- Line 37: `const data = e.data as { items?: RetrievedMemoryDTO[] };` → `const data = e.data;`
- Line 38: `if (Array.isArray(data.items)) return data.items;` → `return data.items;` (after narrowing, `data.items` is `RetrievedMemoryDTO[]`, always defined)
- Line 47: `if (e.event === "affect") return e.data as AffectVectorDTO;` → `if (e.event === "affect") return e.data;`
- Line 56: `const d = e.data as { affect_text?: string };` → `const d = e.data;`
- Line 67: `const d = e.data as { mode?: AgentMode };` → `const d = e.data;` (then `d.mode` is `AgentMode`, not `AgentMode | undefined`, so the `=== "tot" || === "react"` check is no longer needed; replace lines 67-68 with `if (e.event === "mode") return e.data.mode;`)
- Line 78: `const d = e.data as { active?: boolean };` → `const d = e.data;`; line 79 `return Boolean(d.active);` → `return d.active;`
- Line 92: `const d = e.data as { score?: number; step?: number };` → `const d = e.data;`; lines 93-97 simplify because `d.score` and `d.step` are both `number`, never undefined:
  ```typescript
  if (e.event === "perception") {
    const d = e.data;
    score = d.score;
    if (d.score > best) best = d.score;
    move = d.step;
  } else if (e.event === "game_over") {
    games += 1;
  }
  ```

- [ ] **Step 2: Type-check**

Run: `cd nova-viewer && npx tsc --noEmit`
Expected: zero errors across the whole project.

- [ ] **Step 3: Run the full viewer test suite**

Run: `cd nova-viewer && pnpm test`
Expected: all 47 (now ~58 after this plan adds tests) tests pass.

- [ ] **Step 4: Lint**

Run: `cd nova-viewer && pnpm run lint`
Expected: zero warnings.

- [ ] **Step 5: Commit**

```bash
git add nova-viewer/app/page.tsx
git commit -m "refactor(viewer): drop e.data casts in app/page.tsx

Same removal as deriveStream — discriminated narrowing handles
every accessor now that the catch-all is gone."
```

---

## Task 8: Add `tot_branch.api_error` fixture + deriveStream test

**Files:**
- Modify: `nova-viewer/lib/stream/__tests__/fixtures.ts` (append)
- Modify: `nova-viewer/lib/stream/__tests__/deriveStream.test.ts` (append one test)

- [ ] **Step 1: Add the fixture**

Append to `fixtures.ts` (after `totBranchParseErrEv`):

```typescript
export function totBranchApiErrEv(direction: SwipeAction, moveIdx = 1): AgentEvent {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      status: "api_error",
      error: "RetryError: 429 quota exhausted",
    },
  };
}
```

- [ ] **Step 2: Add a deriveStream test for the api_error branch**

Append to `deriveStream.test.ts` inside the existing `describe("deriveStream — ToT block", ...)` (or create a new `describe` if cleaner):

```typescript
import { totBranchApiErrEv } from "./fixtures";

it("renders an api_error tot_branch as a failed branch card", () => {
  const stream = deriveStream([
    modeEv("tot"),
    totBranchEv("swipe_down", 0.7, "merges 4s"),
    totBranchApiErrEv("swipe_left"),
    totSelectedEv("swipe_down", { swipe_down: 0.7 }),
  ]);
  const block = stream.find((e) => e.kind === "tot_block") as ToTBlockEntry;
  expect(block.branches).toHaveLength(2);
  const failed = block.branches.find((b) => b.action === "swipe_left");
  expect(failed?.status).toBe("parse_error");
  expect(failed?.value).toBeNull();
});
```

(Add the necessary imports if `ToTBlockEntry` isn't already imported in this file.)

- [ ] **Step 3: Run the full test suite**

Run: `cd nova-viewer && pnpm test`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add nova-viewer/lib/stream/__tests__/fixtures.ts \
        nova-viewer/lib/stream/__tests__/deriveStream.test.ts
git commit -m "test(viewer): cover tot_branch api_error rendering

Adds a fixture and a deriveStream test for the api_error status
that nova-agent's tot.py:166 emits when an LLM call fails. The
catch-all union arm had been silently dropping these — now they
render as failed-branch cards alongside parse_error branches."
```

---

## Task 9: Final gate + LESSONS.md entry

**Files:**
- Modify: `LESSONS.md`

- [ ] **Step 1: Run the full check trio**

Run: `cd nova-viewer && pnpm test && npx tsc --noEmit && pnpm run lint`
Expected: all three green.

- [ ] **Step 2: Append a lesson to LESSONS.md**

Use the `/lessons-add` skill, or append manually. Content:

```markdown
## Discriminated-union catch-alls hide missing variants

**Date:** 2026-05-03
**Context:** Removing `{event: string; data: unknown}` from the
`AgentEvent` union turned up a third `tot_branch.status` variant
(`"api_error"`) that the agent emits but the viewer had never modelled.
The catch-all silently routed these frames through `e.data as
ToTBranchData` casts that compiled fine and crashed at runtime — except
the bus protocol is permissive enough that the bad shape just rendered
weirdly instead of throwing.

**Lesson:** A union arm of `{ tag: string; data: unknown }` defeats
discriminated narrowing in every consumer. It also defeats grep — you
can't audit which variants are handled, because the catch-all matches
everything. Hand-written runtime predicates per variant + a top-level
`parse(raw): T | null` is worth the boilerplate, because TypeScript
narrowing then becomes a real consistency check between producer and
consumer.

**How to apply:** When mirroring an external protocol (Python bus →
TS viewer), don't use a string-keyed catch-all "for safety." Either
type every variant explicitly or fail closed (return `null`) for
unknown tags. Every catch-all is a bug-hider.
```

- [ ] **Step 3: Commit**

```bash
git add LESSONS.md
git commit -m "docs(lessons): record AgentEvent catch-all anti-pattern"
```

- [ ] **Step 4: Push the whole sequence**

```bash
git push origin claude/practical-swanson-4b6468
```

(The repo convention is to push after every commit, but this plan deferred pushes so the working tree never lands in an intermediate broken state mid-task. After Task 9, the branch is at parity with the convention.)

---

## Self-Review (writing-plans skill)

**Spec coverage:**
- ✅ Remove `{event: string; data: unknown}` catch-all → Task 1
- ✅ Add hand-written predicates → Task 2
- ✅ Wire predicates into `useNovaSocket` → Task 4
- ✅ Replace casts in `deriveStream.ts` → Task 6
- ✅ Replace casts in `app/page.tsx` → Task 7
- ✅ Tests for predicates → Task 3
- ✅ Tests for socket validator + rate limit → Task 5
- ✅ Tests for tot_branch.api_error end-to-end → Task 8
- ✅ Quality gate clean → Task 9
- ✅ Bug-finding lesson captured → Task 9

**Placeholder scan:** No "TBD" / "TODO" / "implement later" / "fill in details" / "similar to Task N" / "add error handling" / "write tests for the above" — every step has actual code or an actual command.

**Type consistency check:**
- `parseAgentEvent` defined in Task 2, used in Task 4 ✅
- `isSwipeAction` defined in Task 2, used in Task 6 ✅
- `ToTBranchApiErrorData` defined in Task 1, predicate in Task 2, fixture in Task 8 ✅
- `seenInvalidEvents` in Task 4 declared as `useRef<Set<string>>(new Set()).current` — `.current` returns the `Set<string>` directly (mutable reference), so `seenInvalidEvents.has(...)` and `.add(...)` type-check ✅
- `useRef` import added in Task 4 alongside `useEffect, useState` ✅

**Risks left as out-of-scope (acknowledged, not addressed):**
- Python-side `bus/protocol.py` still doesn't exist — separate ADR.
- The `decision.action` field on the agent side is still typed `str`, not a Literal. If we want end-to-end safety, the Python side should narrow it too. Out of scope.
- The viewer's `useNovaSocket` still doesn't reconnect on close. Out of scope (separate Day-2 ticket).

**Estimated total effort:** 1.5–2 hours for an engineer with no Nova context, ~45 min for someone who's been in the codebase. Each task is independently testable and revertable.
