import { describe, expect, it } from "vitest";
import { deriveStream } from "../deriveStream";
import {
  affectEv,
  decisionEv,
  modeEv,
  totBranchEv,
  totBranchParseErrEv,
  totSelectedEv,
} from "./fixtures";
import type { AffectVectorDTO } from "@/lib/types";
import type {
  AffectCrossingEntry,
  DecisionEntry,
  ModeFlipEntry,
  ToTBlockEntry,
} from "../types";

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
    // Entering tot mode emits mode_flip then opens a tot_block; the subsequent
    // tot-mode decision is absorbed into the open block (tot_selected carries it).
    const kinds = stream.map((e) => e.kind);
    expect(kinds).toEqual(["decision", "mode_flip", "tot_block"]);
  });
});

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
      { prevAffect: { ...(affectEv({ anxiety: 0.5 }).data as AffectVectorDTO) } },
    );
    expect(stream.filter((e) => e.kind === "affect_crossing")).toHaveLength(1);
  });
});
