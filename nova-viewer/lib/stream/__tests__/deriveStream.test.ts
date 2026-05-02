import { describe, expect, it } from "vitest";
import { deriveStream } from "../deriveStream";
import { decisionEv } from "./fixtures";
import type { DecisionEntry } from "../types";

describe("deriveStream — scaffold", () => {
  it("returns empty stream for empty events", () => {
    expect(deriveStream([])).toEqual([]);
  });
});

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
