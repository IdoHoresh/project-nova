import { describe, expect, it } from "vitest";
import { deriveStream } from "../deriveStream";
import { decisionEv, modeEv } from "./fixtures";
import type { DecisionEntry, ModeFlipEntry } from "../types";

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
