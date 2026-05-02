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
    expect(parseAgentEvent({ data: {} })).toBeNull();
    expect(parseAgentEvent({ event: "telemetry", data: {} })).toBeNull();
  });
});
